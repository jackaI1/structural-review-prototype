# Public drawing review API

The public repository has only a video and README; the original co-op implementation
is confidential. This addition is an independent, synthetic workflow demonstration.
It must never imply access to that implementation or engineering validity.

## Design

Use ASP.NET Core 8 minimal APIs with EF Core SQLite as the durable queue and job
store. `POST /jobs` accepts one PDF (up to 5 MiB), persists it with a generated ID,
and returns 202 and a status URL. `GET /jobs/{id}` reports queued, running,
succeeded or failed; `GET /jobs/{id}/result` returns JSON only on success.
Swagger describes all routes. A single hosted worker reads the SQLite queue,
recovers interrupted running jobs on startup, and invokes Python without a shell.
The process has a timeout, bounded output, and process-tree cleanup on cancellation.
Terminal jobs keep results but their uploaded PDFs are deleted. No client-supplied
paths or original file names are persisted. The service runs as a single local
instance; public hosting, authentication and distributed workers are out of scope.

The new Python engine reads real PDFs with pypdf, extracts only an explicitly
specified synthetic member schedule, and computes elementary illustrative beam
loads, moments and reactions. It never selects sections or claims code compliance.
Unannotated pages produce an engineer-input warning, never fabricated members.
Every result requires engineer approval. A generated fictional drawing and tests
are the only drawing data committed.

## Approaches

A Python HTTP bridge would require a second server and its lifecycle. A subprocess
keeps this demonstration self-contained and makes timeout/cleanup explicit; it is
the implementation choice under the owner's instruction to proceed autonomously.
The confidential engine is unavailable, so recreating or publishing it is excluded.

## Verification

Python unittest covers PDF extraction, computed values, invalid/encrypted inputs
and unsupported schedules. xUnit integration tests use real SQLite and Python,
cover the HTTP workflow, upload limits, failures, restart recovery, persistence,
Swagger, timeout and cancellation. GitHub Actions installs .NET 8 and Python and
runs both suites. Keep the repo public; merge a PR only after CI succeeds.
