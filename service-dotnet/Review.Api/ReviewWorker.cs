using Microsoft.EntityFrameworkCore;

namespace Review.Api;

public sealed class ReviewWorker(IServiceScopeFactory scopes, PythonEngine engine,
    ReviewOptions options, ILogger<ReviewWorker> logger) : BackgroundService
{
    protected override async Task ExecuteAsync(CancellationToken stoppingToken)
    {
        try
        {
            using (var scope = scopes.CreateScope())
            {
                var db = scope.ServiceProvider.GetRequiredService<JobsDb>();
                // Only one service instance may use this data directory.
                await db.Jobs.Where(job => job.Status == "running")
                    .ExecuteUpdateAsync(update => update.SetProperty(job => job.Status, "queued"), stoppingToken);
                var pending = await db.Jobs.Where(job => job.Status == "queued")
                    .Select(job => job.Id).ToListAsync(stoppingToken);
                var retained = pending.Select(options.PdfPath).ToHashSet(StringComparer.Ordinal);
                foreach (var file in Directory.EnumerateFiles(options.UploadDirectory, "*.pdf"))
                    if (!retained.Contains(file)) File.Delete(file);
            }
            while (!stoppingToken.IsCancellationRequested)
            {
                using var scope = scopes.CreateScope();
                var db = scope.ServiceProvider.GetRequiredService<JobsDb>();
                var job = await db.Jobs.Where(job => job.Status == "queued")
                    .OrderBy(job => job.CreatedUtc).FirstOrDefaultAsync(stoppingToken);
                if (job is null)
                {
                    await Task.Delay(250, stoppingToken);
                    continue;
                }
                job.Status = "running";
                await db.SaveChangesAsync(stoppingToken);
                try
                {
                    job.ResultJson = await engine.RunAsync(options.PdfPath(job.Id), stoppingToken);
                    job.Status = "succeeded";
                }
                catch (EngineException error)
                {
                    job.Status = "failed";
                    job.Error = error.Code;
                }
                job.FinishedUtc = DateTime.UtcNow;
                await db.SaveChangesAsync(stoppingToken);
                File.Delete(options.PdfPath(job.Id));
            }
        }
        catch (OperationCanceledException) when (stoppingToken.IsCancellationRequested) { }
        catch (Exception error)
        {
            // Infrastructure faults stop the host rather than silently abandoning jobs.
            logger.LogError(error, "Review worker stopped unexpectedly");
            throw;
        }
    }
}
