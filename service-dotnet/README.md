# Synthetic drawing review service

A .NET 8 minimal API demonstrates asynchronous drawing intake and review:
upload a PDF, poll a durable job, and fetch JSON from a Python subprocess.
This is an independent public implementation. The original co-op engine is
confidential and is not included, invoked or reconstructed here.

The supplied Python engine reads an explicit **synthetic member schedule** from
PDF text. It computes elementary illustrative beam demands and always marks
results as requiring engineer approval. It does not infer framing from arbitrary
geometry, size members, model load paths or check building codes.

## Run locally

Prerequisites: .NET **8 SDK**, Python **3.9+**, and a shell. From the repository root:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r service-dotnet/engine/requirements.txt
export Review__Python="$PWD/.venv/bin/python"
dotnet run --project service-dotnet/Review.Api --urls http://127.0.0.1:5080
```

On Windows use `.venv\Scripts\python.exe` and PowerShell environment-variable
syntax. The service runs in the foreground; **Ctrl+C** stops the worker and its
active Python process. Swagger UI is at <http://127.0.0.1:5080/swagger> and the
OpenAPI document is at `/swagger/v1/swagger.json`.

Use only the fictional sample or your own synthetic/public drawings. This local
demo has no authentication; keep it bound to loopback. Do not expose it as a
public upload service. Antiforgery is disabled for the file endpoint because
there are no cookie credentials; no CORS policy is enabled.

## HTTP workflow

```sh
curl -i -F 'file=@service-dotnet/samples/synthetic-framing.pdf;type=application/pdf' \
  http://127.0.0.1:5080/jobs
# HTTP 202, Location: /jobs/<id>

curl http://127.0.0.1:5080/jobs/<id>
# {"id":"...","status":"queued|running|succeeded|failed",...}

curl http://127.0.0.1:5080/jobs/<id>/result
# JSON on success; HTTP 409 until succeeded (also 409 for failed jobs).
```

| Endpoint | Response |
| --- | --- |
| `POST /jobs` | Multipart `file`; 202 with status JSON and `Location` |
| `GET /jobs/{id}` | 200 with status, UTC timestamps and safe error code; 404 if unknown |
| `GET /jobs/{id}/result` | 200 JSON; 409 if unavailable; 404 if unknown |
| `GET /health` | 200 with `synthetic-demo` mode; process liveness only |

Uploads must contain exactly one nonempty `.pdf` file with `application/pdf`
content type and a `%PDF-` signature. PDFs over **5 MiB** receive 413; invalid
metadata/signatures receive 400. Total requests are limited to 5 MiB + 64 KiB
(including multipart overhead). Full PDF parsing runs asynchronously; malformed,
encrypted or unsupported PDFs become failed jobs rather than synchronous 400s.
Missing/invalid multipart fields receive 400 or 415 from ASP.NET Core binding.

The worker processes one job at a time in arrival order. Terminal error codes are
`engine_failed`, `engine_timeout`, and `engine_output_limit`; uploaded text,
Python stderr and machine paths are not returned. The default subprocess timeout
is **30 seconds**, and each output pipe is limited to **256 Ki characters**.

## Synthetic engine contract

The committed sample contains this exact text annotation:

```text
BEAM B1 SPAN_M=4 TRIBUTARY_M=3 LOAD_KPA=2.5
```

Each case-sensitive `BEAM` annotation needs a unique alphanumeric ID (initial
letter; `_` and `-` also allowed, maximum 32 characters) and all three values in
that order. Values must be finite, positive and at most 100. The parser accepts
1-50 unencrypted pages and at most 200 annotated members. Incomplete annotations
or duplicate IDs fail review. A drawing with no annotations returns an empty
member list and an engineer-input warning; it never invents framing.

For the sample, `w = load × tributary width = 7.5 kN/m`,
`M = wL²/8 = 15 kN m`, and each support reaction `R = wL/2 = 15 kN`.
These assume a simply supported beam with uniform load. No section adequacy or
engineering approval is inferred. JSON contains `schemaVersion`, `mode`, input
`sha256`, `pageCount`, `members`, `warnings`, and `requiresEngineerApproval: true`.
Regenerate the entirely fictional PDF with:

```sh
.venv/bin/python service-dotnet/engine/make_sample.py
```

## Persistence and configuration

SQLite is the durable queue; there is no in-memory-only enqueue step. EF Core
creates the initial schema with `EnsureCreated` (this initial demo has no schema
migration history). Before evolving the schema, add a migration strategy rather
than running against incompatible old databases.

Default storage is `data/` alongside the built executable. The DB stores generated
job IDs, status, timestamps, safe error codes and result JSON. Original file names
are discarded. Upload paths use generated GUIDs. PDFs are deleted after terminal
state is committed; startup removes leftover terminal/orphan uploads and requeues
interrupted `running` jobs. Completed JSON persists across restarts.

| Environment variable | Default |
| --- | --- |
| `Review__Python` | `python3` on PATH |
| `Review__EngineScript` | `engine/review.py` alongside executable |
| `Review__DataDirectory` | `data/` alongside executable |
| `Review__TimeoutSeconds` | `30` (allowed: 1-300) |

An exclusive file handle prevents two service instances sharing a data directory.
There is one worker per instance. Pending work resumes after graceful shutdown
or a crash. Subprocess arguments use `ArgumentList`, without a shell. The runner
logs owned PID/start time and reaps its process tree on timeout or shutdown.
There is no process sandbox or hard CPU/memory quota: inputs are limited and the
service is intended for controlled local synthetic use. Database records/results
have no automatic expiry. Stop the service and remove its data directory to reset
this demonstration. Do not commit runtime data.

## Test and publish

```sh
.venv/bin/python -m unittest discover -s service-dotnet/engine -v
REVIEW_TEST_PYTHON="$PWD/.venv/bin/python" dotnet test service-dotnet/Review.sln --disable-build-servers

dotnet publish service-dotnet/Review.Api -c Release -o /tmp/review-publish
Review__Python="$PWD/.venv/bin/python" dotnet /tmp/review-publish/Review.Api.dll \
  --urls http://127.0.0.1:5080
```

The published output includes `engine/review.py`; install Python dependencies
separately. Tests use real SQLite files, the real parser and subprocesses; HTTP
tests use an in-process ASP.NET TestServer with no listening port. Test factories
stop hosts and delete temporary data. Lifecycle tests reap owned Python processes
on failure paths. GitHub Actions runs both suites and verifies publish output.
