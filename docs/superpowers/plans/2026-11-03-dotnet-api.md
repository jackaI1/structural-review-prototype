# Drawing review API implementation plan

> **For agentic workers:** Use superpowers:executing-plans to implement task-by-task.

**Goal:** Add a working public .NET 8 workflow around an independent synthetic Python engine.
**Architecture:** Minimal HTTP endpoints, SQLite durable queue, one hosted worker, bounded Python subprocess.
**Tech Stack:** .NET 8, EF Core SQLite, Swashbuckle, xUnit, Python 3.9+, pypdf.
**Spec:** `docs/superpowers/specs/2026-11-03-dotnet-api-design.md`

## Global constraints

- Preserve the existing video and confidentiality account.
- Publish only independent source and synthetic drawings; never private records.
- Use a feature branch, run all suites, open a PR, merge after CI passes, keep repo public.
- Single local service instance; no authentication or public hosting in this change.

## Review focus

- Oversized, misleading or malformed uploads must be rejected without stranded files.
- Engine timeout/cancellation must reap owned processes and release resources.
- Interrupted work must resume after restart without losing durable jobs.
- Unsupported drawings must never fabricate engineering results.
- Python failures must become safe terminal statuses without leaking paths/content.

### Task 1: Synthetic engine

**Files:** `service-dotnet/engine/{review.py,test_review.py,make_sample.py,requirements.txt}`, `service-dotnet/samples/synthetic-framing.pdf`
**Interface:** `review.py INPUT_PDF` writes one JSON object to stdout, nonzero on invalid PDF.
- [ ] Write failing unittest cases for schedule extraction, moment/reaction literals, unannotated and malformed/encrypted PDFs.
- [ ] Run `python -m unittest discover -s service-dotnet/engine -v`; observe missing implementation.
- [ ] Implement extraction, finite positive limits and engineer-review-only JSON; generate sample.
- [ ] Run the whole Python suite and render/inspect the fictional drawing; commit.

### Task 2: Durable API

**Files:** `service-dotnet/Review.Api/*`, `service-dotnet/Review.Api.Tests/*`, `service-dotnet/Review.sln`
**Interfaces:** `POST /jobs` (multipart file), `GET /jobs/{id}`, `GET /jobs/{id}/result`; worker consumes SQLite queued jobs.
- [ ] Scaffold net8.0 projects; write HTTP tests first against an empty API, observe 404 failures.
- [ ] Implement PDF validation, generated file paths, SQLite state, Python subprocess and worker.
- [ ] Add failure/recovery/process lifecycle regression tests before their corresponding behavior.
- [ ] Run `dotnet test service-dotnet/Review.sln` and Python suite; commit.

### Task 3: Publish

**Files:** `.github/workflows/test.yml`, `.gitignore`, `README.md`, `service-dotnet/README.md`
- [ ] Document commands, API examples, limits and synthetic scope; add skills paths.
- [ ] CI runs Python unittest and `dotnet test` on .NET 8, including real subprocess integration.
- [ ] Run suites, release publish, independent code review and cleanup verification.
- [ ] Push feature branch; open/link PR; merge with squash after successful CI; verify public visibility.
