using Microsoft.EntityFrameworkCore;

namespace Review.Api;

public sealed record ReadingInput(string? Equipment, string? Measurement, double Value, string? Unit, DateTimeOffset RecordedAt)
{
    public Dictionary<string, string[]> Validate()
    {
        var errors = new Dictionary<string, string[]>();
        void Check(string key, string? value) { if (string.IsNullOrWhiteSpace(value) || value.Length > 80) errors[key] = ["Required, up to 80 characters."]; }
        Check("equipment", Equipment); Check("measurement", Measurement); Check("unit", Unit);
        if (!double.IsFinite(Value)) errors["value"] = ["Must be finite."];
        if (RecordedAt == default) errors["recordedAt"] = ["A recording time is required."];
        return errors;
    }
}

public sealed class Reading
{
    public long Id { get; set; }
    public string Equipment { get; set; } = "";
    public string Measurement { get; set; } = "";
    public double Value { get; set; }
    public string Unit { get; set; } = "";
    public DateTime RecordedAtUtc { get; set; }
}

public sealed class ReadingsDb(DbContextOptions<ReadingsDb> options) : DbContext(options)
{
    public DbSet<Reading> Readings => Set<Reading>();
    protected override void OnModelCreating(ModelBuilder model) => model.Entity<Reading>().HasIndex(r => new { r.Equipment, r.RecordedAtUtc });
}

public static class ReadingEndpoints
{
    public static void MapReadings(this WebApplication app)
    {
        app.MapPost("/readings", async (ReadingInput input, ReadingsDb db) =>
        {
            var errors = input.Validate();
            if (errors.Count > 0) return Results.ValidationProblem(errors);
            var reading = new Reading { Equipment = input.Equipment!.Trim(), Measurement = input.Measurement!.Trim(), Value = input.Value, Unit = input.Unit!.Trim(), RecordedAtUtc = input.RecordedAt.UtcDateTime };
            db.Readings.Add(reading);
            await db.SaveChangesAsync();
            return Results.Created($"/readings/{reading.Id}", reading);
        }).Produces<Reading>(201).ProducesValidationProblem();
        app.MapGet("/readings/{id:long}", async (long id, ReadingsDb db) =>
            await db.Readings.FindAsync(id) is { } reading ? Results.Ok(reading) : Results.NotFound())
            .Produces<Reading>().Produces(404);
        app.MapGet("/readings", async (string? equipment, ReadingsDb db) =>
        {
            var query = db.Readings.AsNoTracking();
            if (!string.IsNullOrWhiteSpace(equipment)) query = query.Where(r => r.Equipment == equipment.Trim());
            return await query.OrderByDescending(r => r.RecordedAtUtc).ThenByDescending(r => r.Id).Take(500).ToListAsync();
        }).Produces<List<Reading>>();
    }
}
