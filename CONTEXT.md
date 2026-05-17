# Tal Qual

This context describes the current language for the Portuguese
como-article ground/vehicle dataset. The project has one supported path:
build a high-precision dataset of curated `GROUND como um/uma/uns/umas
VEHICLE` comparisons for analysis and WebApp visualizations.

## Language

**Bronze Segment**:
A boundary-safe corpus segment prepared from brWaC raw text. It preserves source
provenance and normalized text used by the extractor.
_Avoid_: raw document, silver row

**Como-Article Ground/Vehicle Candidate**:
A candidate whose surface form is curated `GROUND como um/uma/uns/umas
VEHICLE`.
_Avoid_: broad comparison candidate, all como candidate

**Curated Ground**:
The quality adjective or salient verb immediately before `como` that passes the
spec-0006 allowlist.
_Avoid_: inferred adjective, arbitrary left context

**Connector Text**:
The literal `como um`, `como uma`, `como uns`, or `como umas` between
`ground_text` and `vehicle_text`.
_Avoid_: connector family, pattern label

**Vehicle Text**:
The compact surface phrase after the article. It is the readable right-hand
side shown in review tables and examples.
_Avoid_: unbounded right context, parser phrase

**Vehicle Head**:
The first token of `vehicle_text`, used as the current aggregation key for
ground/vehicle counts.
_Avoid_: full vehicle phrase, semantic class

**Gold Seed Dataset**:
The kept candidate dataset emitted by the core extractor at
`data/gold/como_article_ground_vehicle_candidates`.
_Avoid_: final annotated dataset, classifier output

**Analysis Output**:
A compact derived table used to inspect dataset quality and distribution, such
as ground counts, vehicle counts, pair counts, examples, or review samples.
_Avoid_: notebook-only display, temporary Spark DataFrame

**WebApp-Ready Output**:
A stable analysis output shaped for direct frontend consumption.
_Avoid_: exploratory scratch table, raw Parquet dump

## Relationships

- A **Bronze Segment** may contain zero or more **Como-Article Ground/Vehicle Candidates**.
- A **Como-Article Ground/Vehicle Candidate** has one **Curated Ground**, one **Connector Text**, and one **Vehicle Text**.
- A **Vehicle Text** has one MVP **Vehicle Head**.
- The **Gold Seed Dataset** contains kept **Como-Article Ground/Vehicle Candidates**.
- **Analysis Outputs** and **WebApp-Ready Outputs** are derived from the **Gold Seed Dataset**.

## Current Priorities

- Improve **Vehicle Text** filtering without broadening the connector scope.
- Add richer **Analysis Outputs** for dominance, diversity, and review quality.
- Shape **WebApp-Ready Outputs** around ground pages, vehicle pages, pair rankings, examples, and summary metrics.

## Example Dialogue

> **Dev:** "Should we bring back `que nem` or bare `como`?"
> **Domain expert:** "No. The current dataset is the
> **Como-Article Ground/Vehicle Candidate** path. Improve **Vehicle Text**
> filtering and analysis first."
