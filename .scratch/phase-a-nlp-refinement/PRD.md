# PRD: Phase A NLP Refinement Layer

Status: ready-for-agent

## Problem Statement

The current Portuguese Simile Candidate Explorer MVP proves that Apache Spark can process one full brWaC shard and extract explicit comparison candidates from narrow connector patterns. It emits a useful silver candidate table and compact gold summaries, but the current `vehicle_raw` and `vehicle_normalized` fields are bounded right-context strings rather than reliable linguistic vehicles.

That limitation makes the next analysis step fragile. The project can answer MVP questions about connector frequency and rough right-context frequency, but it cannot yet support stronger Pudding-inspired analyses such as clean vehicle rankings, noun reuse across patterns, or later adjective-to-vehicle fingerprints. The current top vehicle outputs include clausal continuations, empty strings, pronouns, numbers, and boilerplate-like phrases because the system has not separated syntactic vehicle structure from generic right context.

The user needs a next phase that improves structured linguistic information without overclaiming. Phase A should refine silver candidates after Spark extraction, not replace the Spark MVP, and should preserve the project’s defensible framing: Spark performs corpus-scale extraction; NLP enriches the reduced candidate set for analysis.

## Solution

Build an NLP Refinement Layer that reads the existing silver candidate dataset, preserves one row per Silver Candidate, and writes a Refined Candidate Dataset with additional linguistic fields.

The first implementation slice should focus on Vehicle Structure Refinement. It should use Portuguese NLP to identify a Vehicle Phrase and Vehicle Head where possible, assign Structural Quality Buckets, and distinguish Clean Common-Noun Vehicles from broader Chartable Vehicles. It should carry all silver rows forward, but optimize first for Primary Nominal Article Candidates and Primary Nominal Bare Candidates.

The phase should produce durable Parquet and CSV outputs plus a Phase A Validation Notebook. The notebook should demonstrate whether Phase A improves the data by comparing the MVP’s rough `vehicle_normalized` rankings against refined `vehicle_head_lemma` rankings, showing quality buckets, and surfacing examples by pattern type and refinement scope.

Phase A should not classify figurative versus literal meaning. It should produce deterministic structural signals that make later LLM or human classification more effective.

## User Stories

1. As a data explorer, I want silver candidates preserved in the refined dataset, so that Phase A remains traceable to the Spark extraction output.
2. As a data explorer, I want every refined row to keep the original candidate identity, so that I can join Phase A results back to silver candidates and examples.
3. As a data explorer, I want Phase A to add NLP-derived fields without mutating silver output, so that the MVP remains reproducible and auditable.
4. As a data explorer, I want right-context strings separated from syntactic vehicles, so that vehicle charts are not polluted by generic continuations.
5. As a data explorer, I want a Vehicle Phrase field, so that examples remain readable for qualitative inspection.
6. As a data explorer, I want a Vehicle Head field, so that vehicle counts can aggregate around the main noun or pronoun.
7. As a data explorer, I want a Vehicle Head lemma field, so that plural and inflected forms can be grouped more cleanly.
8. As a data explorer, I want vehicle head part-of-speech metadata, so that nouns, proper names, pronouns, numbers, and verbal continuations can be separated.
9. As a data explorer, I want vehicle phrase token length, so that overly long spans can be identified and excluded from default charts.
10. As a data explorer, I want vehicle extraction confidence, so that uncertain NLP results can be inspected separately.
11. As a data explorer, I want Primary Nominal Article Candidates refined first, so that article-gated connector patterns produce cleaner vehicle candidates.
12. As a data explorer, I want Primary Nominal Bare Candidates included in the first refinement slice, so that `que_nem` and `tal_qual` remain part of the early analysis.
13. As a data explorer, I want `que_nem` and `tal_qual` reported separately from article-gated candidates, so that weaker syntactic cues do not get hidden.
14. As a data explorer, I want clausal patterns carried forward with a clausal scope, so that `como_se` does not dominate noun-vehicle rankings.
15. As a data explorer, I want prepositional equality patterns carried forward with a prepositional scope, so that `igual a/ao/à` can be analyzed without pretending it always yields a noun vehicle.
16. As a data explorer, I want a Structural Quality Bucket on each row, so that obvious noise categories are visible before semantic classification.
17. As a data explorer, I want empty vehicle spans identified, so that punctuation-adjacent matches do not pollute vehicle rankings.
18. As a data explorer, I want pronoun vehicles identified, so that cases such as `que nem eu` can be preserved but excluded from default noun charts.
19. As a data explorer, I want numeric vehicles identified, so that equality or numeric continuations can be separated from comparison imagery.
20. As a data explorer, I want proper-name vehicles preserved, so that culturally interesting examples can be inspected later.
21. As a data explorer, I want proper-name vehicles excluded from the strict common-noun chart by default, so that conservative noun rankings stay defensible.
22. As a data explorer, I want URL-like or symbol-heavy spans identified, so that web noise can be excluded from charts.
23. As a data explorer, I want overly long vehicle phrases flagged, so that boilerplate-like spans do not dominate examples.
24. As a data explorer, I want role or classification risk identified heuristically, so that phrases like `trabalha como advogado` can be marked as structurally risky.
25. As a data explorer, I want role or classification risk to be non-final, so that Phase A does not overclaim semantic classification.
26. As a data explorer, I want Clean Common-Noun Vehicle flags, so that conservative charts can focus on defensible noun vehicles.
27. As a data explorer, I want Chartable Vehicle flags, so that broader exploratory charts can include selected proper-name vehicles.
28. As a data explorer, I want separate common-noun and chartable-vehicle summaries, so that conservative and exploratory readings do not get mixed.
29. As a data explorer, I want top vehicle heads globally, so that I can see whether NLP refinement produces cleaner comparison images.
30. As a data explorer, I want top vehicle heads by pattern type, so that connector patterns can be compared after refinement.
31. As a data explorer, I want counts by refinement scope, so that I can understand how much of the silver data belongs to each structural family.
32. As a data explorer, I want counts by Structural Quality Bucket, so that I can quantify noise and clean candidate proportions.
33. As a data explorer, I want side-by-side examples of raw and refined vehicles, so that I can judge whether NLP refinement improves readability.
34. As a capstone presenter, I want a Phase A Validation Notebook, so that I can show the before/after effect of NLP refinement visually.
35. As a capstone presenter, I want durable Phase A CSV outputs, so that presentation tables and future visualizations do not depend on rerunning notebook cells.
36. As a capstone presenter, I want durable Phase A Parquet output, so that downstream Spark or Python analysis can continue from a structured dataset.
37. As a capstone presenter, I want Spark to remain the corpus-scale extraction layer, so that the class requirement remains clearly satisfied.
38. As a capstone presenter, I want spaCy to run after Spark reduction, so that NLP is applied to a manageable candidate set rather than the whole corpus.
39. As a developer, I want a small testable refinement module, so that vehicle extraction rules can be tested independently from notebooks.
40. As a developer, I want run-tier helpers, so that Phase A can run quickly on a deterministic sample and fully on the one-shard silver output.
41. As a developer, I want a deterministic sample-debug tier, so that refinement logic can be tuned without repeatedly processing the full candidate set.
42. As a developer, I want final acceptance to require the full one-shard refined run, so that Phase A proves it can process the MVP output end to end.
43. As a developer, I want parse text construction to be explicit, so that NLP behavior can be tested and explained.
44. As a developer, I want the first slice to parse connector plus vehicle text, so that vehicle extraction has connector cues without extra left-context ambiguity.
45. As a future analyst, I want ground adjective extraction deferred until vehicle refinement is stable, so that adjective-to-vehicle analysis is not built on noisy vehicle units.
46. As a future analyst, I want Phase A to avoid figurative/literal labels, so that semantic classification remains a distinct later phase.
47. As a future frontend builder, I want Phase A outputs to be compact and chart-ready, so that future dashboards can use cleaner vehicle fields.

## Implementation Decisions

- Phase A is an NLP Refinement Layer, not a destructive filtering step.
- The Refined Candidate Dataset preserves Silver Candidate identity and adds NLP-derived fields.
- The first implementation priority is Vehicle Structure Refinement.
- Optional ground adjective extraction is deferred until vehicle fields and quality buckets are stable.
- Phase A should use spaCy Portuguese as the first implementation path.
- Spark remains the corpus-scale extraction engine. spaCy runs after Spark has reduced the corpus to silver candidates.
- Spark NLP is not the first implementation path. It may be revisited only if the project later requires NLP to be Spark-native.
- NLTK is not sufficient for the first implementation path because Phase A needs POS, lemmatization, and head extraction rather than only tokenization.
- Phase A should support two run tiers: `sample_debug` and `one_shard_refined`.
- `sample_debug` should be deterministic and pattern-stratified for fast refinement inspection.
- `one_shard_refined` should process all silver candidates from the validated one-shard MVP run and is required for final Phase A acceptance.
- Phase A should carry every silver row forward, even rows outside the first vehicle-refinement target scopes.
- Each row should receive an `nlp_refinement_scope`.
- Primary Nominal Article Candidates include `como_article`, `feito_article`, `parecer_article`, `igual_article`, and `igualzinho_article`.
- Primary Nominal Bare Candidates include `que_nem_bare` and `tal_qual_bare`.
- Clausal candidates include `como_se`.
- Prepositional candidates include `igual_preposition` and `igualzinho_preposition`.
- Primary Nominal Bare Candidates are first-slice targets, but they should be reported separately from article-gated candidates because their right side has weaker syntactic cues.
- The first vehicle-refinement slice should parse a controlled text window built from the matched connector phrase plus `vehicle_raw`.
- Phase A should not parse only `vehicle_raw` for the first slice because that loses connector and article cues.
- Phase A should not parse full candidate context for the first vehicle slice because left context can add ambiguity before ground extraction exists.
- Vehicle extraction should use an inspectable hybrid strategy: noun chunks first, POS-based fallback, and dependency head metadata when available.
- The Vehicle Phrase is the readable extracted noun phrase for examples and inspection.
- The Vehicle Head is the main noun, proper noun, pronoun, or other head-like token from the phrase.
- The Vehicle Head lemma is the preferred aggregation key for refined vehicle charts.
- Structural Quality Buckets should describe syntactic usability, not figurative meaning.
- Initial Structural Quality Buckets include clean nominal vehicle, pronoun vehicle, proper-name vehicle, numeric vehicle, empty vehicle, clausal or verbal continuation, overly long vehicle phrase, URL or symbol noise, role or classification risk, parser uncertain, and not in first-slice scope.
- Role or classification risk should be a first-slice heuristic based on structural and left-context signals, not a final semantic judgment.
- Role or classification risk should preserve rows while allowing charts to exclude risky candidates by default.
- Phase A should use two chart eligibility flags: Clean Common-Noun Vehicle and Chartable Vehicle.
- Clean Common-Noun Vehicle is conservative and should require a common noun head, a non-empty lemma, short phrase length, and a clean nominal bucket.
- Chartable Vehicle is broader and may include selected proper-name vehicles while still excluding pronouns, numerals, empty heads, URL-like spans, verbal continuations, clausal continuations, and overly long phrases.
- Phase A should write a durable Refined Candidate Dataset as Parquet.
- The refined Parquet output should be one row per Silver Candidate.
- The refined output should preserve core silver fields such as provenance, connector metadata, raw and normalized vehicle fields, candidate text, and offsets.
- The refined output should add fields for refinement scope, parse text, vehicle phrase, vehicle head, vehicle head lemma, head POS, phrase length, extraction confidence, clean common-noun eligibility, chartable eligibility, reject reason, Structural Quality Bucket, NLP model name, and NLP model version.
- Phase A should write compact CSV summaries for scope counts, quality bucket counts, top common-noun vehicle heads, top chartable vehicle heads, top vehicle heads by pattern, and refinement examples.
- Phase A should add a validation notebook that demonstrates before/after vehicle quality, scope counts, quality bucket counts, refined vehicle rankings, and examples by pattern and bucket.
- The validation notebook is the presentation and inspection surface, while Parquet and CSV outputs are the durable data contract.
- The implementation should favor a deep, testable refinement module with a narrow interface over embedding extraction logic directly in the notebook.
- The notebook should orchestrate loading, running, charting, and inspection, not own the vehicle extraction rules.
- The spec already captures the canonical Phase A contract and should guide issue creation.

## Testing Decisions

- Good Phase A tests should verify observable refinement behavior rather than spaCy internals.
- Tests should cover refinement scope mapping from pattern type.
- Tests should cover parse text construction from matched connector text and `vehicle_raw`.
- Tests should cover vehicle phrase and Vehicle Head extraction for representative article-gated candidates.
- Tests should cover Vehicle Head lemma and POS propagation from the refinement interface.
- Tests should cover Primary Nominal Bare Candidate handling for `que_nem_bare` and `tal_qual_bare`.
- Tests should cover clausal and prepositional scopes being carried forward without being treated as default noun-vehicle rows.
- Tests should cover Structural Quality Bucket assignment for clean nominal, pronoun, numeric, empty, URL-like, overly long, parser-uncertain, and not-in-first-slice cases.
- Tests should cover role or classification risk heuristics with examples such as role/profession and classification-like contexts.
- Tests should cover Clean Common-Noun Vehicle eligibility separately from Chartable Vehicle eligibility.
- Tests should verify that proper names can be preserved and chartable without being clean common-noun vehicles.
- Tests should verify that refined rows preserve candidate identity and core silver fields.
- Tests should verify that all silver rows can be carried forward even when no vehicle head is extracted.
- Tests should cover deterministic sample-debug selection behavior.
- Tests should cover aggregation output behavior for scope counts, quality bucket counts, top common-noun heads, top chartable heads, and examples.
- Unit tests should follow the existing Python `unittest` convention in the repository.
- The canonical local unit-test command should remain the UV-backed unittest command described in the repo ADR.
- Tests should use tiny sample candidate rows and lightweight fakes where possible.
- If spaCy model availability makes unit tests fragile, extraction logic should be structured so parser output can be represented by small test doubles.
- Notebook execution against the full one-shard refined tier is useful validation, but focused unit tests should not depend on the real brWaC shard.

## Out of Scope

- Mutating or replacing the silver candidate dataset.
- Re-running corpus-scale connector extraction as part of Phase A.
- Full-corpus processing beyond the existing one-shard MVP output.
- Generic `como` extraction.
- Figurative versus literal classification.
- Cliché, playful, ironic, or idiomatic semantic classification.
- LLM-based classification.
- Human review UI.
- Frontend application or dashboard implementation.
- Production CLI packaging beyond what is needed to run the refinement workflow.
- Spark NLP integration as the initial implementation path.
- Perfect noun phrase extraction on noisy web text.
- Perfect semantic vehicle extraction.
- Ground adjective extraction in the first implementation slice.
- Tenor extraction.
- Embedding similarity, synonym merging, or semantic vehicle clustering.
- Over-merging proper names, common nouns, and related vehicle concepts.

## Further Notes

- Phase A should be presented as a post-Spark refinement experiment that improves structured linguistic information for analysis.
- The strongest immediate win is to stop treating every right-context string as a vehicle.
- The project should keep using careful language: silver output contains comparison candidates and rough right-context vehicles; Phase A produces refined vehicle phrases and heads.
- The Pudding-style adjective fingerprint analysis remains downstream until Phase A vehicle fields are stable and optional ground adjective extraction has been evaluated.
- Phase A should make the next LLM or human classification phase easier by producing better samples and clearer structural buckets.
- The refined Phase A spec lives in the project specs and is the source of truth for implementation issues.
