# Structural Review Prototype

A confidential prototype that assembles drawing-derived framing into a structural model for gravity-load review with engineer approval.

https://github.com/user-attachments/assets/348eca62-70fb-4e97-a164-1fd147c58ca4

*The demo uses a fictional house and synthetic data. No real drawings appear.*

## Overview

A residential gravity review starts with drawings that describe framing on
separate floors. An engineer must connect those depictions, establish a load
path and check members against the demands transmitted through the structure.

The prototype brings drawing interpretation and structural review into one
workflow. It extracts PDF geometry, assembles a model and presents the
interpretation for engineer approval before calculations proceed. Results remain
subject to engineering judgement.

Built during an engineering co-op, the original prototype is demonstrated by the video only.
The video recreates the workflow on a fictional house with simplified,
illustrative values. It is not engineering output.

## How it works

The architecture is described only at the level of general engineering practice:

1. Extract vector geometry from drawing PDFs.
2. Classify geometric depictions of structural members.
3. Assemble the floors into a three-dimensional structural model.
4. Present the interpretation for an engineer to review and approve.
5. Carry gravity loads down through the structure.
6. Check members against their calculated demands and present results for review.

The demonstration includes reviewing suggested member changes. An engineer
remains responsible for accepting the interpretation and the resulting design.
No implementation modules, internal formats or design tables are published.

## Design decisions and trade-offs

- Engineer approval separates a proposed interpretation from an accepted model.
  Drawing extraction does not itself establish a correct load path.
- A combined model connects floors that appear separately in drawings. Model
  completeness still depends on the engineer's review of the source information.
- Keeping the implementation confidential limits public reproducibility. This
  repository provides an architectural account and demonstration, not a runnable
  engineering tool.

## Results and evaluation

Achieved in testing: a residential gravity review went from four hours to ten
minutes, with an engineer verifying the workflow. This is a reported
measurement, not a public benchmark.

The original prototype source, calculation fixtures and evaluation suite are not available here.
The independent public service below has its own synthetic fixtures and automated tests.
The fictional video illustrates the sequence of work; it cannot independently
reproduce or validate the reported timing or engineering results.

## Why there's no code

I built this prototype during my engineering co-op. The source code, internal
design methods and project drawings are confidential and belong to the firm,
so this repository only demonstrates that original project. I am happy to walk through the architecture and design decisions in an
interview while respecting those confidentiality limits.

## Limitations

The embedded video demonstrates the original prototype. The independent public
service below is runnable and tested, but its synthetic engine does not implement
the original structural workflow. No claims about
arbitrary drawing compatibility, code compliance or unattended design can be
verified from the published material.

## Public .NET workflow demo

[`service-dotnet/`](service-dotnet/README.md) is a new, independent public example:
an ASP.NET Core 8 minimal API accepts a drawing PDF, queues review work in SQLite
via EF Core, calls a Python subprocess, and exposes polling and JSON results.
Swagger documents the endpoints. It includes a generated fictional framing plan,
xUnit integration tests and Python tests, run by GitHub Actions.

The Python demo reads explicit synthetic schedule annotations and computes
illustrative uniform-load beam demands. It does not reproduce the confidential
engine, interpret arbitrary framing geometry, select sections or check code
compliance. Every result requires engineer approval. See the linked guide for
setup, curl examples, limits and restart behavior.

## Skills demonstrated

- **C# / ASP.NET Core 8:** PDF upload, asynchronous review status and JSON result
  endpoints in [`JobEndpoints.cs`](service-dotnet/Review.Api/JobEndpoints.cs).
- **EF Core / SQLite:** durable job state and restart recovery in
  [`JobsDb.cs`](service-dotnet/Review.Api/JobsDb.cs) and
  [`ReviewWorker.cs`](service-dotnet/Review.Api/ReviewWorker.cs).
- **Python interoperability:** bounded subprocess execution, cancellation and
  cleanup in [`PythonEngine.cs`](service-dotnet/Review.Api/PythonEngine.cs), calling
  the independent [`review.py`](service-dotnet/engine/review.py).
- **OpenAPI, xUnit and CI:** Swagger configuration in
  [`Program.cs`](service-dotnet/Review.Api/Program.cs), real HTTP/SQLite/Python
  [integration tests](service-dotnet/Review.Api.Tests), and
  [GitHub Actions](.github/workflows/test.yml).

## Licence

The independent public implementation and synthetic fixture under `service-dotnet/`
are [MIT licensed](service-dotnet/LICENSE). The original co-op prototype is not
distributed here; this licence grants no rights to confidential source or project
material or to the original demonstration video.
Other projects with public code are on my [GitHub profile](https://github.com/jackaI1).
