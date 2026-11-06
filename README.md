# Structural Review Prototype

I built a house drawing review prototype because I wanted to follow how weight passes through the floors without piecing together every plan by hand.

## Overview

The beams and other supporting parts of a house appear on several drawing sheets. I
needed to connect those plans to follow gravity loads, the weight carried down
through the structure, and check the parts carrying them. During my engineering co-op
I built a prototype that brings those steps together. An engineer checks its
interpretation before the calculations continue.

I share that work here through a video of a fictional house. The original source and
drawings belong to the firm and remain confidential. I added a separate local service
as a personal project: upload the included fictional PDF, follow its review status
and read the result. It uses simple sample calculations, not the original engine.

## Try the sample service

Use macOS, Linux or Windows Subsystem for Linux (WSL), with the .NET 8 software
development kit (SDK) and Python 3.9 or newer. From the repository root:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r service-dotnet/engine/requirements.txt
export Review__Python="$PWD/.venv/bin/python"
dotnet run --project service-dotnet/Review.Api --urls http://127.0.0.1:5080
```

Open <http://127.0.0.1:5080/swagger>, the service's interactive request page, to
upload `service-dotnet/samples/synthetic-framing.pdf` through `POST /jobs`. Use the
returned ID with `GET /jobs/{id}` to check progress, then `GET /jobs/{id}/result` to
read the JSON result, a structured text record. Stop the service with Ctrl-C. The
[service guide](service-dotnet/README.md) has command-line examples, settings, tests
and restart behavior.

## Record equipment readings

I can also keep a local log of measurements alongside the drawing review, for example a load reading for a beam. Each entry records the equipment name, measurement, value, unit and time. Start the service as above, then open the interactive request page at <http://127.0.0.1:5080/swagger> and use `POST /readings` with:

```json
{"equipment":"beam-A","measurement":"load","value":12.5,"unit":"kN","recordedAt":"2026-01-01T12:00:00Z"}
```

Use `GET /readings?equipment=beam-A` to see its recent entries, or `GET /readings/{id}` for one entry. The list returns at most 500 entries, newest first. The service checks required fields and stores entries in a separate local SQLite file. The readings are an independent log, not calculated structural results. Like the review service, this has no login and should only be used locally with non-sensitive data.

## Watch a simulated feeder on Windows

I added a separate feeder monitor to practise watching equipment readings over time alongside the measurement log. It generates fictional voltage, current and breaker states, plots recent current and flags readings outside example limits. These are not readings from the building, and the limits are not engineering advice. Acknowledging an alarm records that it was seen; it does not change the simulated breaker.

On Windows, install the .NET 8 SDK and SQL Server Express LocalDB. From the repository root, run:

```powershell
dotnet run --project feeder-monitor/Feeder.Desktop
```

The app connects to the `FeederMonitor` LocalDB database, creates its initial tables, and starts the simulation. Select an alarm and choose **Acknowledge selected** to save its acknowledgement. Close the window to stop the feed. To use another SQL Server instance, set the `FEEDER_SQL` environment variable to its connection string before starting. Use only a trusted local database and synthetic data. The app stores readings in its own database; it does not read the service log or alter structural calculations.

The default limits are 108–132 V and 100 A, or an open breaker. The chart shows up to 120 recent current values; older data stays in SQL Server. There is no automatic retention policy. The database uses an initial schema created on first run, not migrations; remove the demo database before changing its schema.

## What the sample does

I can use the service to try the upload-and-review sequence without the confidential
prototype. It keeps queued work and finished results in a local SQLite database, a
database stored in one file, so restarting it doesn't lose the queue. One worker
passes each PDF to a Python script and stores the result.

The script reads explicit beam annotations in the fictional drawing and calculates
illustrative loads, bending moments (the turning effect inside a beam) and reactions
(the forces at its supports). It does not recognise arbitrary framing, select member
sizes or check building codes. Drawings without the sample annotations return a
warning instead of invented members. Keep this unauthenticated demo on the local
machine and use synthetic or public files.

[Service design](docs/review-service.md) explains the queue, file handling and
process limits. The service's source and tests are public; every result still
requires engineer review.

## Original prototype demo

https://github.com/user-attachments/assets/348eca62-70fb-4e97-a164-1fd147c58ca4

The video uses a fictional house and simplified values. It shows drawing geometry
being assembled into a model, an engineer reviewing the interpretation, gravity loads
being carried through the floors, and suggested member changes being reviewed. It is
not engineering output.

In testing of the original prototype, a residential gravity review went from four
hours to ten minutes with an engineer verifying the workflow. That is a reported
measurement. The video and separate sample service cannot reproduce or validate it,
and the confidential calculation methods are not published here.

## Tests

```sh
.venv/bin/python -m unittest discover -s service-dotnet/engine -v
REVIEW_TEST_PYTHON="$PWD/.venv/bin/python" dotnet test service-dotnet/Review.sln --disable-build-servers
```

The feeder monitor uses a background simulator, a view model that exposes data and commands to the Windows interface, and Entity Framework Core to save records in SQL Server. Its tests cover alarm rules, view model updates, SQL Server storage in a container, and a Windows UI automation check. A Windows workflow builds and publishes the app, while a Linux workflow runs the container test.

The automated workflow also runs a Postman collection (a saved set of HTTP requests) with Newman, and checks the OpenAPI description used by the interactive page. The readings tests include concurrent submissions.

These tests cover the public service and fictional inputs, including queue recovery,
invalid uploads and stopping the Python process. They do not validate the
confidential prototype.

## Licence

The independent code and synthetic fixture under `service-dotnet/` are [MIT
licensed](service-dotnet/LICENSE). That licence grants no rights to the original
co-op prototype, confidential material or demonstration video.
