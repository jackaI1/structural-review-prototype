# Review service design

The runnable service is independent of the confidential co-op prototype. It lets
me try submitting a fictional drawing, following a review job and retrieving a
result. Setup and the exact API contract are in the [service guide](../service-dotnet/README.md).

## Queue and files

The local .NET service accepts one PDF up to 5 MiB and stores a generated job ID
in SQLite. One worker processes jobs in arrival order. Interrupted running jobs
return to the queue on startup; finished JSON remains available after restart.
Uploaded PDFs are deleted once a terminal state has been saved. Original file
names are discarded. A lock prevents two instances sharing one data directory.

## Calculation process

A Python subprocess reads explicit synthetic member annotations using pypdf.
It computes simple uniform-load beam demands, not member adequacy, load paths
or code compliance. Unannotated drawings return an engineer-input warning.
Every result is marked as requiring engineer approval.

Keeping Python in a subprocess avoids running a second HTTP service. Arguments
are passed without a shell. Execution has a timeout and bounded output, and the
owned process group is terminated on completion, failure or shutdown. This is
not a sandbox for arbitrary untrusted files. The demo has no authentication and
is intended for one local instance on macOS, Linux or WSL.

## Checks

Python tests cover PDF parsing, illustrative values and invalid inputs. The
.NET tests use real SQLite and Python to check the HTTP workflow, upload limits,
recovery, persistence, timeout and cancellation. These checks exercise the
public service only; they make no claim about the original prototype.
