# Vehicle Structure Refinement for First-Slice Scopes

Status: complete

## Parent

.scratch/phase-a-nlp-refinement/PRD.md

## What to build

Add Vehicle Structure Refinement for the first-slice scopes: Primary Nominal Article Candidates and Primary Nominal Bare Candidates. The completed slice should enrich refined rows with Vehicle Phrase, Vehicle Head, head lemma, head part of speech, phrase length, and extraction confidence while carrying clausal and prepositional rows forward without pretending they are default noun-vehicle rows.

Use Portuguese spaCy as the first implementation path, but keep the extraction interface testable so unit tests can use lightweight parser-output doubles where needed.

## Acceptance criteria

- [x] Primary Nominal Article Candidates receive attempted Vehicle Phrase and Vehicle Head extraction.
- [x] Primary Nominal Bare Candidates receive attempted Vehicle Phrase and Vehicle Head extraction and remain distinguishable from article-gated candidates.
- [x] Clausal and prepositional rows are carried forward without default noun-vehicle extraction.
- [x] Vehicle Phrase, Vehicle Head, Vehicle Head lemma, Vehicle Head POS, vehicle phrase token length, and extraction confidence fields are populated when extraction succeeds.
- [x] Rows with no noun-like vehicle target remain present with empty or null vehicle structure fields.
- [x] The extraction strategy prefers noun chunks and falls back to inspectable POS-based extraction.
- [x] NLP model name and version metadata are recorded on refined rows.
- [x] Focused tests cover representative article-gated candidates, bare candidates, no-head cases, and non-target scopes.

## Blocked by

- .scratch/phase-a-nlp-refinement/issues/01-scope-labeled-refined-candidate-dataset.md
