# One-Shard Refined Run Validation

Status: complete

## Parent

.scratch/phase-a-nlp-refinement/PRD.md

## What to build

Validate Phase A against the full one-shard silver candidate output. The completed slice should run the `one_shard_refined` tier, produce the durable Refined Candidate Dataset and CSV summaries, inspect the Phase A Validation Notebook outputs, and record observed counts, quality signals, limitations, and any follow-up risks.

This issue proves that Phase A works end to end over the MVP output rather than only on a small debug sample.

## Acceptance criteria

- [x] The `one_shard_refined` tier runs against the validated one-shard silver candidate dataset.
- [x] Full refined Parquet output is produced with one row per silver candidate.
- [x] Phase A CSV summaries are produced from the full refined dataset.
- [x] The Phase A Validation Notebook can inspect the full-run outputs.
- [x] Observed counts by refinement scope are recorded.
- [x] Observed counts by Structural Quality Bucket are recorded.
- [x] Top common-noun and chartable vehicle-head examples are recorded.
- [x] Known limitations from the full run are documented without overclaiming figurative/literal classification.
- [x] Parser-quality cleanup candidates are recorded for `.scratch/phase-a-nlp-refinement/issues/08-phase-a-refinement-quality-cleanup.md`.

## Blocked by

- .scratch/phase-a-nlp-refinement/issues/05-phase-a-validation-notebook.md

## Validation notes

Run command:

```bash
docker run --rm -e TAL_QUAL_PHASE_A_TIER=one_shard_refined -e TAL_QUAL_PHASE_A_LOAD_EXISTING_REFINED=0 -v /Users/ronalson/Code/engsoft/tal-qual:/home/jovyan/work -w /home/jovyan/work quay.io/jupyter/pyspark-notebook bash -lc 'python -m pip install -e /home/jovyan/work && jupyter nbconvert --to notebook --execute notebooks/04_phase_a_validation.ipynb --ExecutePreprocessor.timeout=3600 --output 04_phase_a_validation.executed.ipynb'
```

Observed run metadata:

- Refined source: `ran_one_shard_refined`.
- Requested tier: `one_shard_refined`.
- Parser model: `core_news_sm 3.8.0`.
- Silver candidate rows: 58,797.
- Refined candidate rows: 58,797.
- Full-run Parquet output: `data/gold/refined_candidates_nlp`.
- CSV outputs refreshed under `outputs/phase_a_*.csv`.
- Notebook execution time recorded by the notebook: 86.4 seconds for load/run refinement and 3.7 seconds for CSV output writing.

Counts by `nlp_refinement_scope`:

| Scope | Count |
| --- | ---: |
| `primary_nominal_article` | 36,241 |
| `clausal` | 14,723 |
| `primary_nominal_bare` | 4,520 |
| `prepositional` | 3,313 |

Counts by Structural Quality Bucket:

| Bucket | Count |
| --- | ---: |
| `clean_nominal_vehicle` | 27,926 |
| `not_in_first_slice_scope` | 18,036 |
| `url_or_symbol_noise` | 4,488 |
| `role_or_classification_risk` | 3,706 |
| `pronoun_vehicle` | 2,387 |
| `proper_name_vehicle` | 957 |
| `clausal_or_verbal_continuation` | 798 |
| `overly_long_vehicle_phrase` | 408 |
| `empty_vehicle` | 57 |
| `numeric_vehicle` | 34 |

Top clean common-noun vehicle heads:

| Lemma | Count | Representative phrase |
| --- | ---: | --- |
| `forma` | 414 | `diferente forma` |
| `espécie` | 316 | `' espécie` |
| `pessoa` | 219 | `' pessoa` |
| `homem` | 169 | `bom homem` |
| `alternativa` | 161 | `alternativa` |
| `processo` | 147 | `contínuo processo` |
| `sistema` | 134 | `' pequeno sistema planetário` |
| `meio` | 133 | `excelente meio` |
| `opção` | 132 | `baita opção` |
| `empresa` | 129 | `100 empresas mais confiáveis` |

Top chartable vehicle heads are almost identical to the clean common-noun list; the only difference in the top ten is `sistema` at 135 chartable rows because proper-name vehicles are also chartable.

Observed quality signals and limitations:

- The full run preserves one refined row for each silver candidate and the notebook can inspect the full-run Parquet plus CSV summaries.
- The refined head rankings are structurally cleaner than raw `vehicle_normalized` rankings because they aggregate on `vehicle_head_lemma`, but they still contain parser-quality artifacts.
- Quote-prefixed phrases such as `' espécie`, `' pessoa`, and `' problema` can still survive into clean rankings.
- Some noun-chunk heads are not the most useful vehicle unit, for example `controverso` selected from `rapper controverso`.
- Some uppercase, titlecase, numeric, or boilerplate-like web text still appears in representative phrases, for example `Sistema`, `Empresas`, `100 empresas mais confiáveis`, `20 países`, and `TOALHAS`-like cases recorded in issue 08.
- The validation does not classify candidates as figurative or literal. These counts are structural quality signals only.

Follow-up cleanup candidates were recorded in `.scratch/phase-a-nlp-refinement/issues/08-phase-a-refinement-quality-cleanup.md`.
