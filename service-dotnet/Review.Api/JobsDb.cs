using Microsoft.EntityFrameworkCore;

namespace Review.Api;

public sealed class ReviewJob
{
    public Guid Id { get; set; }
    public string Status { get; set; } = "queued";
    public DateTime CreatedUtc { get; set; } = DateTime.UtcNow;
    public DateTime? FinishedUtc { get; set; }
    public string? Error { get; set; }
    public string? ResultJson { get; set; }
}

public sealed class JobsDb(DbContextOptions<JobsDb> options) : DbContext(options)
{
    public DbSet<ReviewJob> Jobs => Set<ReviewJob>();
    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        modelBuilder.Entity<ReviewJob>().HasIndex(job => new { job.Status, job.CreatedUtc });
    }
}

public sealed record JobStatus(Guid Id, string Status, DateTime CreatedUtc, DateTime? FinishedUtc, string? Error)
{
    public static JobStatus From(ReviewJob job) => new(job.Id, job.Status, job.CreatedUtc, job.FinishedUtc, job.Error);
}
