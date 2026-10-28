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

Built during an engineering co-op, this repository is a demonstration only.
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

No source, calculation fixtures or automated evaluation suite are available here.
The fictional video illustrates the sequence of work; it cannot independently
reproduce or validate the reported timing or engineering results.

## Why there's no code

I built this prototype during my engineering co-op. The source code, internal
design methods and project drawings are confidential and belong to the firm,
so this repository only shows the project. I am happy to walk through the architecture and design decisions in an
interview while respecting those confidentiality limits.

## Limitations

There is no installation command, runnable demo package or test suite in this
repository. The embedded video is the available demonstration. No claims about
arbitrary drawing compatibility, code compliance or unattended design can be
verified from the published material.

## Licence

No software implementation or software licence file is distributed here. This
description does not grant rights to the confidential source or project material.
Other projects with public code are on my [GitHub profile](https://github.com/jackaI1).
