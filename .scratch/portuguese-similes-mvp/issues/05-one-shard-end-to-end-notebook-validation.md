# One-Shard End-to-End Notebook Validation

Status: ready-for-agent

## Parent

.scratch/portuguese-similes-mvp/PRD.md

## What to build

Validate the MVP end to end by running the notebook workflow against one full compressed brWaC shard. The completed slice should demonstrate that the Dockerized Spark notebook can process the required corpus tier, produce bronze/silver/gold outputs, show basic visualizations, and record enough observed results and limitations to support the capstone presentation.

## Acceptance criteria

- [ ] The notebook runs against one full compressed brWaC shard as the required MVP corpus.
- [ ] The run produces the expected bronze, silver, and gold outputs.
- [ ] At least two notebook visualizations are shown from generated aggregation data.
- [ ] A candidate examples table is shown with connector family, pattern type, candidate text, and vehicle fields.
- [ ] Observed connector and pattern counts from the one-shard run are recorded.
- [ ] Known limitations are documented from actual output inspection.
- [ ] The MVP answers whether connector-based extraction is feasible on a meaningful brWaC subset.

## Blocked by

- .scratch/portuguese-similes-mvp/issues/04-vehicle-normalization-and-gold-aggregations.md

