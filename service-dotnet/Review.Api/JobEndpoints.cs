using Microsoft.EntityFrameworkCore;

namespace Review.Api;

public static class JobEndpoints
{
    public static void MapJobs(this WebApplication app)
    {
        app.MapPost("/jobs", UploadAsync)
            .DisableAntiforgery() // Local API has no cookies or ambient credentials.
            .WithSummary("Upload one synthetic PDF and queue its review")
            .WithDescription("PDF only, up to 5 MiB. Returns a polling URL. Results always require engineer approval.")
            .Produces<JobStatus>(202).ProducesProblem(400).ProducesProblem(413);
        app.MapGet("/jobs/{id:guid}", async (Guid id, JobsDb db, CancellationToken token) =>
        {
            var job = await db.Jobs.AsNoTracking().SingleOrDefaultAsync(job => job.Id == id, token);
            return job is null ? Results.NotFound() : Results.Ok(JobStatus.From(job));
        }).WithSummary("Poll a queued review job").Produces<JobStatus>().Produces(404);
        app.MapGet("/jobs/{id:guid}/result", async (Guid id, JobsDb db, CancellationToken token) =>
        {
            var job = await db.Jobs.AsNoTracking().SingleOrDefaultAsync(job => job.Id == id, token);
            if (job is null) return Results.NotFound();
            return job.Status == "succeeded"
                ? Results.Content(job.ResultJson!, "application/json")
                : Results.Problem(statusCode: 409, title: "Result unavailable", detail: "Poll job status; only succeeded jobs have a result.");
        }).WithSummary("Fetch synthetic review JSON").Produces(200, contentType: "application/json")
            .Produces(404).ProducesProblem(409);
    }

    private static async Task<IResult> UploadAsync(IFormFile file, HttpRequest request,
        JobsDb db, ReviewOptions options, CancellationToken token)
    {
        if (file.Length > ReviewOptions.MaxPdfBytes)
            return Results.Problem(statusCode: 413, title: "PDF exceeds 5 MiB");
        if (file.Length < 5 || request.Form.Files.Count != 1 ||
            !Path.GetExtension(file.FileName).Equals(".pdf", StringComparison.OrdinalIgnoreCase) ||
            !file.ContentType.Equals("application/pdf", StringComparison.OrdinalIgnoreCase))
            return Results.Problem(statusCode: 400, title: "Provide one nonempty PDF file in the file field");
        await using var input = file.OpenReadStream();
        var header = new byte[5];
        await input.ReadExactlyAsync(header, token);
        if (!header.AsSpan().SequenceEqual("%PDF-"u8))
            return Results.Problem(statusCode: 400, title: "Invalid PDF signature");
        var job = new ReviewJob { Id = Guid.NewGuid() };
        var path = options.PdfPath(job.Id);
        try
        {
            await using (var output = new FileStream(path, FileMode.CreateNew, FileAccess.Write, FileShare.None, 81920, true))
            {
                await output.WriteAsync(header, token);
                await input.CopyToAsync(output, token);
            }
            db.Jobs.Add(job);
            await db.SaveChangesAsync(token);
        }
        catch
        {
            File.Delete(path);
            throw;
        }
        return Results.Accepted($"/jobs/{job.Id}", JobStatus.From(job));
    }
}
