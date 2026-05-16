# MVP Spec and README Alignment

Status: complete

## Parent

.scratch/portuguese-similes-mvp/PRD.md

## What to build

Align the visible project documentation with the implemented MVP. This slice should update the project-facing spec and README-style instructions so a reader can understand the Docker runtime, one-shard requirement, actual pipeline outputs, observed limitations, and how to rerun the notebook.

## Acceptance criteria

- [x] The project documentation describes Docker as the expected PySpark/Jupyter runtime.
- [x] The documentation states that one full compressed brWaC shard is the required MVP corpus tier.
- [x] The documentation describes the implemented bronze, silver, and gold outputs.
- [x] The documentation lists the actual high-value connector patterns and schema fields used by the implementation.
- [x] The documentation explains how to rerun the notebook and where to find generated outputs.
- [x] The documentation captures limitations observed during the one-shard validation run.
- [x] The documentation keeps frontend visualization as downstream context, not part of the current MVP acceptance criteria.

## Blocked by

- .scratch/portuguese-similes-mvp/issues/05-one-shard-end-to-end-notebook-validation.md

## Completion notes

- Updated `README.md` with the Docker runtime, one-shard corpus requirement, rerun command, implemented output paths, extraction contract, observed counts, and limitations.
- Updated `docs/specs/0001-portuguese-similes-mvp-spec.md` so the project-facing spec matches the implemented MVP instead of the earlier sample-only draft.
- Kept frontend visualization as downstream context only; notebook charts and inspectable CSV outputs remain the MVP validation surface.
