using Microsoft.AspNetCore.Http.Features;
using Microsoft.Data.Sqlite;
using Microsoft.EntityFrameworkCore;
using Microsoft.OpenApi.Models;
using Review.Api;

var builder = WebApplication.CreateBuilder(args);
var options = new ReviewOptions();
builder.Configuration.GetSection("Review").Bind(options);
if (options.TimeoutSeconds is < 1 or > 300)
    throw new InvalidOperationException("Review:TimeoutSeconds must be between 1 and 300.");
options.DataDirectory = Path.GetFullPath(options.DataDirectory);
Directory.CreateDirectory(options.UploadDirectory);
// Held for the host lifetime, preventing two workers from sharing the same queue.
using var ownership = new FileStream(Path.Combine(options.DataDirectory, "service.lock"),
    FileMode.OpenOrCreate, FileAccess.ReadWrite, FileShare.None);
builder.WebHost.ConfigureKestrel(server => server.Limits.MaxRequestBodySize = ReviewOptions.MaxRequestBytes);
builder.Services.Configure<FormOptions>(form => form.MultipartBodyLengthLimit = ReviewOptions.MaxRequestBytes);
builder.Services.AddSingleton(options);
var connection = new SqliteConnectionStringBuilder
{
    DataSource = Path.Combine(options.DataDirectory, "jobs.db"), Pooling = false,
}.ToString();
builder.Services.AddDbContext<JobsDb>(db => db.UseSqlite(connection));
builder.Services.AddSingleton<PythonEngine>();
builder.Services.AddHostedService<ReviewWorker>();
builder.Services.AddProblemDetails();
builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen(swagger => swagger.SwaggerDoc("v1", new OpenApiInfo
{
    Title = "Synthetic drawing review API", Version = "v1",
    Description = "Independent public workflow demo. Illustrative calculations; all results require engineer approval.",
}));
var app = builder.Build();
app.Lifetime.ApplicationStopped.Register(ownership.Dispose);
app.UseExceptionHandler();
app.UseSwagger();
app.UseSwaggerUI();
using (var scope = app.Services.CreateScope())
    await scope.ServiceProvider.GetRequiredService<JobsDb>().Database.EnsureCreatedAsync();
app.MapJobs();
app.MapGet("/health", () => Results.Ok(new { status = "ok", mode = "synthetic-demo" }));
await app.RunAsync();
public partial class Program { }
