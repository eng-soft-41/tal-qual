# Phase A Refinement Quality Cleanup

Status: complete

## Parent

.scratch/phase-a-nlp-refinement/PRD.md

## What to build

Tighten Phase A Vehicle Structure Refinement after the validation notebook and full one-shard run expose concrete parser-quality issues. The goal is not perfect semantic interpretation. The goal is to reduce obvious structural noise that currently leaks into Clean Common-Noun and Chartable Vehicle rankings.

Use observed notebook examples as regression fixtures where possible.

## Acceptance criteria

- [x] Malformed heads or phrases with quote/apostrophe artifacts are excluded from clean and chartable rankings, including examples like `mole''Ai`.
- [x] Symbol and punctuation noise detection catches malformed vehicle phrases that currently survive as clean nouns.
- [x] Noun-chunk head choice is improved or guarded for cases where spaCy selects an adjective-like or modifier-like head, such as `controverso` from `rapper controverso`.
- [x] Uppercase or titlecase web-noise heads are reviewed and either preserved deliberately as proper names or excluded when they are obvious boilerplate/noise, including examples like `TOALHAS`.
- [x] Cleanup keeps legitimate proper-name vehicles chartable when they are structurally usable.
- [x] Focused tests cover each noisy example category discovered from the validation notebook or full one-shard run.
- [x] Documentation or comments continue to state that Phase A is structural refinement, not figurative/literal classification.

## Observed examples to consider

- `mole''Ai` from a malformed phrase like `'' bunda mole''Ai`.
- `controverso` selected from `rapper controverso`, where the more useful structural head may be `rapper`.
- uppercase or visually noisy heads such as `TOALHAS`.
- punctuation-heavy or quote-heavy phrases that are currently being treated as clean common nouns.
- quote-prefixed clean-ranking phrases from the full one-shard run, including `' espécie`, `' pessoa`, and `' problema`.
- numeric or boilerplate-like phrases still counted as clean nouns when spaCy selects a noun head, including `100 empresas mais confiáveis` and `20 países`.
- bare-pattern artifacts such as `sequer` appearing as a chartable `que_nem_bare` head.

## Blocked by

- .scratch/phase-a-nlp-refinement/issues/06-one-shard-refined-run-validation.md

## Completion notes

- Added structural guards for quote/apostrophe artifacts, number-prefixed noun phrases, all-caps common-noun web noise, and bare-connector artifacts such as `sequer`.
- Adjusted noun-chunk head selection so `rapper controverso` can use the earlier noun `rapper` when the parser selects a later modifier-like noun as root.
- Kept structurally usable proper names chartable, including all-caps proper names such as `NASA`.
- Reran the `one_shard_refined` validation notebook with `TAL_QUAL_PHASE_A_LOAD_EXISTING=0`; row parity remains 58,797 silver rows and 58,797 refined rows.
- Updated README and the Phase A spec with the post-cleanup quality-bucket counts and cleanup behavior.
