# PRD: Portuguese Simile Candidate Explorer MVP

Status: ready-for-agent

## Problem Statement

The project needs a focused MVP that proves whether Apache Spark can process a meaningful Brazilian Portuguese web corpus subset and extract useful explicit comparison candidates for later analysis. The current spec establishes the broad idea, but the implementation contract needs to reflect the decisions made during review: the MVP must run on a real brWaC shard, preserve corpus boundaries, emit one row per connector match, use high-value narrow connector patterns, and produce inspectable silver and gold datasets.

The user does not need a perfect figurative-language detector at this stage. They need a defensible Big Data capstone prototype that answers whether connector-based extraction is feasible, which comparison connectors appear most often, which raw comparison phrases appear frequently, and which patterns look promising enough for future visualization work.

## Solution

Build a small, non-overengineered Spark-based extraction MVP with a reusable extraction module and a notebook-driven workflow. The MVP should run inside the Jupyter Docker Stacks PySpark notebook image, using Docker as the expected runtime for development and demonstration. The notebook will run first on a tiny sample for sanity checks, then on one full compressed brWaC shard as the required MVP corpus. The pipeline will read raw text, treat `<END>` markers as paragraph/document boundaries, normalize text for matching, extract one candidate row per high-value connector match, save the full silver dataset as Parquet, and produce compact CSV summaries for inspection.

The MVP should validate the extraction goal first. A frontend visualization app may be built later, but frontend-ready data contracts are not part of this PRD.

## User Stories

1. As a capstone presenter, I want the MVP to run on a real brWaC shard, so that the project demonstrates meaningful Spark-based text processing rather than only sample-file parsing.
2. As a capstone presenter, I want a tiny sample run before the real shard run, so that extraction behavior can be checked quickly before processing larger data.
3. As a data explorer, I want the pipeline to process one full compressed brWaC shard, so that the MVP has enough volume to produce meaningful connector and vehicle frequencies.
4. As a data explorer, I want `<END>` markers treated as hard boundaries, so that extracted candidates do not cross unrelated paragraph or document fragments.
5. As a data explorer, I want original text preserved separately from match text, so that examples remain faithful to the source corpus.
6. As a data explorer, I want lowercase matching with accents preserved, so that matching is case-insensitive without distorting Portuguese text.
7. As a data explorer, I want only high-value narrow connector patterns, so that the candidate pool is not flooded by generic `como` noise.
8. As a data explorer, I want no generic `como` pattern in the MVP, so that classification, additive, example, and procedural uses remain out of the initial extraction scope.
9. As a data explorer, I want `como um`, `como uma`, `como uns`, and `como umas` matched as an article-gated `como` family, so that nominal comparison candidates are captured without broadening to every `como`.
10. As a data explorer, I want `como se` treated as a clausal comparison pattern, so that it remains analyzable without pretending it is the same as a noun-phrase vehicle.
11. As a data explorer, I want bare `que nem` matched, so that a comparison-heavy Portuguese connector is captured even when the right side does not begin with an article.
12. As a data explorer, I want bare `tal qual` matched, so that an uncommon but comparison-heavy connector is included without over-constraining it.
13. As a data explorer, I want `parece`, `parecia`, and `pareceu` with `um` or `uma` matched, so that common appearance comparison variants are captured.
14. As a data explorer, I want `feito`, `feita`, `feitos`, and `feitas` with indefinite articles matched, so that agreement-aware comparison forms are captured while excluding broad participial noise.
15. As a data explorer, I want `igual a/ao/à/aos/às` matched, so that standard prepositional comparison forms are captured.
16. As a data explorer, I want `igual um/uma/uns/umas` matched, so that colloquial article-based comparison forms are included.
17. As a data explorer, I want `igualzinho` variants matched separately, so that their frequency and noise profile can be analyzed without collapsing them into `igual`.
18. As a data explorer, I want one silver row per connector match, so that multiple candidates in the same source segment are not silently dropped.
19. As a data explorer, I want each candidate to include exact matched text, so that surface forms such as `como uma`, `igual ao`, and `feita umas` remain inspectable.
20. As a data explorer, I want `connector_family` and `pattern_type` fields, so that I can aggregate both broad connector families and precise subtypes.
21. As a data explorer, I want a `comparison_form` field, so that clausal patterns such as `como se` can be distinguished from nominal article/preposition patterns.
22. As a data explorer, I want `vehicle_raw` to start after the exact matched connector phrase, so that vehicle aggregation is not polluted by connector articles or prepositions.
23. As a data explorer, I want `vehicle_normalized` in addition to `vehicle_raw`, so that simple aggregation can collapse casing, spacing, and surrounding punctuation differences.
24. As a data explorer, I want leading articles preserved in `vehicle_normalized`, so that the MVP avoids hidden linguistic merging decisions.
25. As a data explorer, I want right context to stop at punctuation, boundary, or 120 characters, so that candidates remain readable and do not swallow whole paragraphs.
26. As a data explorer, I want `candidate_full_text` to include a compact left and right context window, so that examples are readable in CSVs and notebook tables.
27. As a data explorer, I want `text_before` capped at 80 characters, so that the silver table stays compact while still giving enough local context.
28. As a data explorer, I want source provenance fields, so that extracted candidates can be traced back to their input shard and segment.
29. As a data explorer, I want deterministic candidate IDs, so that reruns over the same corpus and rules produce stable candidate identifiers.
30. As a data explorer, I want character offsets defined against normalized segment text, so that offsets have a clear and reproducible meaning.
31. As a data explorer, I want full silver output saved as Parquet, so that Spark-native analysis can continue without CSV limitations.
32. As a data explorer, I want compact CSV outputs for summaries and candidate samples, so that MVP results can be inspected without Spark.
33. As a data explorer, I want connector-family counts, so that I can see which broad comparison families dominate the shard.
34. As a data explorer, I want pattern-type counts, so that I can compare exact extraction rules and identify noisy or promising subtypes.
35. As a data explorer, I want top vehicle counts globally, so that repeated right-context phrases can be inspected across the corpus.
36. As a data explorer, I want top vehicle counts by connector family, so that different connector families can be compared.
37. As a data explorer, I want top vehicle counts by pattern type, so that exact rules can be evaluated separately.
38. As a data explorer, I want deterministic stratified sample examples by pattern type, so that examples are stable across reruns and cover each pattern.
39. As a data explorer, I want examples deduplicated for sampling, so that repeated web boilerplate does not dominate qualitative inspection.
40. As a data explorer, I want silver rows to preserve all occurrences, so that corpus frequency remains accurate even when sample outputs deduplicate examples.
41. As a developer, I want extraction logic in a small reusable module, so that the notebook stays readable and the rules can be tested in isolation.
42. As a developer, I want the notebook to handle orchestration, charting, and output writing, so that the presentation workflow remains simple.
43. As a developer, I want the MVP to run in a Dockerized Jupyter PySpark environment, so that the Spark runtime is reproducible across development and presentation machines.
44. As a developer, I want tests to be useful but not a hard MVP blocker, so that the first priority remains an end-to-end Spark run over the required shard.
45. As a future frontend builder, I want the MVP outputs to validate extraction feasibility first, so that visualization requirements can be designed later from real data rather than guessed upfront.

## Implementation Decisions

- The required MVP corpus is one full compressed brWaC shard. A tiny sample may be used as a smoke test, but the MVP is not complete if it only runs on hand-written examples.
- The pipeline should support run tiers: a sample sanity run, a required one-shard brWaC run, and an optional multi-shard or full-corpus run.
- The implementation should be a small reusable extraction module plus a notebook. The module should hold connector pattern definitions, normalization helpers, candidate extraction logic, and gold aggregation helpers. The notebook should start Spark, select inputs, call extraction functions, write outputs, and show charts/tables.
- Docker is the expected runtime for the MVP. Use the Jupyter Docker Stacks PySpark notebook image as the development and demonstration environment, mounting the repository into the container and exposing the Jupyter and Spark UI ports.
- The Docker runtime should support JupyterLab for the notebook workflow and expose Spark UI for run inspection.
- The design should avoid package or CLI overengineering until the MVP questions are answered.
- Spark is the main processing tool. Pandas may be used only after aggregation when data is small enough for notebook visualization or single-file inspection outputs.
- `<END>` markers must be treated as hard paragraph/document boundaries before extraction. Candidate windows must not cross those boundaries.
- Matching is case-insensitive by using lowercase match text. Accents are preserved.
- The MVP must emit one silver row per connector match, not one row per line or paragraph.
- The MVP must not include a generic `como` pattern.
- The high-value connector patterns are article-gated `como`, clausal `como se`, bare `que nem`, bare `tal qual`, appearance-family `parecer` with indefinite articles, agreement-aware `feito` with indefinite articles, and `igual`/`igualzinho` prepositional and article subtypes.
- `parecer` variants include `parece`, `parecia`, and `pareceu` with `um` or `uma`.
- `feito` variants include `feito`, `feita`, `feitos`, and `feitas` with `um`, `uma`, `uns`, or `umas`.
- `como` article variants include `como um`, `como uma`, `como uns`, and `como umas`.
- `igual` subtypes include prepositional forms and article forms. `igualzinho` subtypes should be separate from `igual` subtypes.
- `que nem` and `tal qual` remain bare connector patterns.
- `como se` is treated as a clausal comparison form. Article/preposition-based patterns are treated as nominal forms.
- The silver schema should use `connector_family`, `pattern_type`, `comparison_form`, and `matched_text`. The older ambiguous `connector` field should be dropped.
- `matched_text` is the exact source phrase matched by the regex, including article or preposition.
- `vehicle_raw` starts immediately after `matched_text`.
- `vehicle_normalized` is derived with simple lowercase, whitespace collapse, and surrounding punctuation trimming. It preserves leading Portuguese articles by default.
- Right-context extraction ends at the first punctuation boundary, `<END>` boundary, or 120 characters after the matched connector phrase. The punctuation boundary includes comma, period, exclamation mark, question mark, semicolon, and colon.
- `candidate_full_text` is a compact readable context window: up to 80 characters before the matched connector, the exact matched connector phrase, and the extracted right context.
- `text_before` stores the capped 80-character left context, not the full pre-match segment.
- Silver provenance should include source file identity, original input line identity before `<END>` splitting, segment identity after `<END>` splitting, deterministic candidate ID, and character offsets.
- `candidate_id` should be deterministic, based on source file, segment identity, offsets, pattern type, and matched text.
- `char_start` and `char_end` are zero-based offsets in normalized segment text, with `char_end` exclusive.
- Full silver output should be written as Parquet.
- Candidate CSV output should be a deterministic sample rather than a full large CSV. The default sample size is 5,000 candidates ordered by source file, segment identity, offset, and pattern type.
- Gold outputs should include connector-family counts, pattern-type counts, top vehicles globally, top vehicles by family, top vehicles by pattern, and sample examples.
- Gold vehicle outputs should use `vehicle_normalized` and include occurrence counts. Where useful, they should also include distinct candidate text counts to expose repeated boilerplate.
- Silver keeps all occurrences. Sample examples may deduplicate by candidate text or candidate text plus normalized vehicle before selecting examples.
- `sample_examples` should include up to 20 deterministic examples per pattern type, ordered by source file, segment identity, and offset.
- Frontend visualization is downstream context only. Frontend-ready JSON outputs and app data contracts are out of scope for this MVP.

## Testing Decisions

- The first priority is an end-to-end Spark run over one full brWaC shard. Tests are valuable but are not a hard blocker for MVP validation.
- Good tests should verify observable extraction behavior rather than internal implementation details. Tests should assert candidate rows, fields, offsets, boundaries, and normalized values from representative input strings.
- The extraction module is the best candidate for focused tests because it encapsulates the deepest logic behind a small interface.
- Useful extraction tests include `<END>` boundary handling, one row per match, expanded connector variants, exclusion of generic `como`, `vehicle_raw` starting after `matched_text`, capped left context, right-context punctuation limits, simple vehicle normalization, and deterministic ID inputs.
- Spark integration tests are optional for this MVP. If added, they should be small and use tiny in-memory or temporary sample data rather than the real brWaC shard.
- There is no prior test suite in the repo yet, so the first tests should establish lightweight conventions without blocking the MVP run.

## Out of Scope

- Generic `como` extraction.
- NLP filtering with spaCy, NLTK, or Spark NLP.
- LLM-based classification.
- Figurative versus literal classification.
- Tenor, ground, and semantic vehicle extraction.
- Metaphor detection beyond explicit comparison candidates.
- Human review UI.
- Frontend visualization app implementation.
- Frontend-ready JSON contracts.
- HDFS integration.
- Real-time processing.
- Production-grade packaging, CLI, deployment, or orchestration.
- Full-corpus processing as a hard requirement.
- Perfect deduplication or semantic merging of vehicles.
- Lemmatization, synonym merging, embeddings, or similarity clustering.

## Further Notes

- The MVP should be presented as a Spark-based exploratory pipeline for extracting and visualizing explicit comparison candidates in Portuguese, not as a perfect simile detector.
- The local brWaC clean corpus is already present as gzipped text shards and is suitable for this capstone because it provides enough volume, noisy web variety, and line-oriented text for Spark ingestion.
- Prior context suggests the narrow second-stage connector patterns preserve a large candidate pool while excluding much of the generic connector noise.
- The future frontend should be designed after this MVP produces real distribution data and representative examples.
