namespace Review.Api;

public sealed class ReviewOptions
{
    public const long MaxPdfBytes = 5 * 1024 * 1024;
    public const long MaxRequestBytes = MaxPdfBytes + 64 * 1024;
    public string DataDirectory { get; set; } = Path.Combine(AppContext.BaseDirectory, "data");
    public string Python { get; set; } = "python3";
    public string EngineScript { get; set; } = Path.Combine(AppContext.BaseDirectory, "engine", "review.py");
    public int TimeoutSeconds { get; set; } = 30;
    public string UploadDirectory => Path.Combine(DataDirectory, "uploads");
    public string PdfPath(Guid id) => Path.Combine(UploadDirectory, id.ToString("N") + ".pdf");
}
