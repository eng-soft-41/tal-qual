# MVP Spec and README Alignment

Status: ready-for-agent

## Parent

.scratch/portuguese-similes-mvp/PRD.md

## What to build

Align the visible project documentation with the implemented MVP. This slice should update the project-facing spec and README-style instructions so a reader can understand the Docker runtime, one-shard requirement, actual pipeline outputs, observed limitations, and how to rerun the notebook.

## Acceptance criteria

- [ ] The project documentation describes Docker as the expected PySpark/Jupyter runtime.
- [ ] The documentation states that one full compressed brWaC shard is the required MVP corpus tier.
- [ ] The documentation describes the implemented bronze, silver, and gold outputs.
- [ ] The documentation lists the actual high-value connector patterns and schema fields used by the implementation.
- [ ] The documentation explains how to rerun the notebook and where to find generated outputs.
- [ ] The documentation captures limitations observed during the one-shard validation run.
- [ ] The documentation keeps frontend visualization as downstream context, not part of the current MVP acceptance criteria.

## Blocked by

- .scratch/portuguese-similes-mvp/issues/05-one-shard-end-to-end-notebook-validation.md

