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

These tests cover the public service and fictional inputs, including queue recovery,
invalid uploads and stopping the Python process. They do not validate the
confidential prototype.

## Licence

The independent code and synthetic fixture under `service-dotnet/` are [MIT
licensed](service-dotnet/LICENSE). That licence grants no rights to the original
co-op prototype, confidential material or demonstration video.
