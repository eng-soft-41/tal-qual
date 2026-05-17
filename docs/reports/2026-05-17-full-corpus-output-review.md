# Full Corpus Output Review

Date: 2026-05-17

Input reviewed:

- `data/bronze/brwac_segments_full`
- `data/gold/como_article_ground_vehicle_candidates`
- `outputs/como_article_*.csv`

The full brWaC clean run produced 2,136 kept candidates, 940
`ground_lemma -> vehicle_head_lemma` pairs, 40 grounds, and 742 vehicle heads.
That is enough to prototype visualizations around repeated cliche-like
comparisons, but it is still too narrow for a broad exploratory visualization.

## Current Shape

Top grounds:

| ground | count |
| --- | ---: |
| cair | 783 |
| trabalhar | 167 |
| forte | 97 |
| duro | 83 |
| rápido | 82 |
| correr | 70 |
| leve | 70 |
| grande | 64 |
| brilhar | 61 |
| encaixar | 52 |

Top vehicle heads:

| vehicle head | count |
| --- | ---: |
| luva | 533 |
| bomba | 210 |
| raio | 38 |
| pedra | 35 |
| pássaro | 34 |
| rocha | 29 |
| pluma | 22 |
| touro | 18 |
| flecha | 14 |
| borboleta | 13 |

Strong repeated pairs:

| ground | vehicle head | count |
| --- | --- | ---: |
| cair | luva | 452 |
| cair | bomba | 208 |
| encaixar | luva | 37 |
| caber | luva | 25 |
| duro | pedra | 25 |
| leve | pluma | 21 |
| rápido | raio | 20 |
| assentar | luva | 19 |
| duro | rocha | 17 |
| forte | touro | 17 |

## Why The Dataset Is Small

The extractor only accepts:

```text
CURATED_GROUND como um/uma/uns/umas VEHICLE
```

This excludes high-volume comparison forms that probably matter for the visual
story:

- `frio como gelo`, `forte como touro`, `rápido como raio` without article.
- `que nem`, `feito`, `igual`, `parece`.
- grounds outside the curated quality/verb lists.
- comparisons where the semantic ground is not the immediate token before
  `como`.

This narrowness is useful for precision, but the full corpus confirms that this
contract will not create a large visualization dataset by itself.

## Quality Problems

Vehicle phrase boundaries are the main issue.

Observed vehicle length distribution:

| token length | candidates |
| ---: | ---: |
| 1 | 1,102 |
| 2 | 153 |
| 3 | 391 |
| 4 | 275 |
| 5 | 215 |

The 215 five-token vehicles are especially suspicious because five tokens is
the current maximum. Many are truncated clauses, not complete vehicle phrases.

Heuristic noise profile from `outputs/como_article_examples.csv`:

| signal | count |
| --- | ---: |
| contains preposition after head | 684 |
| reaches 5-token maximum | 215 |
| contains pronoun after head | 77 |
| contains conjunction after head | 68 |
| generic or modifier head | 42 |
| contains finite verb tail | 21 |
| capitalized multi-token phrase | 21 |
| contains digit | 9 |

Examples that show the problem:

- `assenta como uma luva no dia de hoje`
- `caiu como uma luva foi o Fransola`
- `caiu como uma luva ela é lindaaaaaa`
- `alto como um porco sendo castrado e desabou`
- `brilhante como um raro diamante Passou por mim`
- `correr como um profissional da F1`
- `Alegre como uma alternativa ao pós-Socrates`
- `Porto Alegre como uma cidade conectada`

Some of these are valid comparisons with overlong tails. Others are not
comparison metaphors at all; they are role, location, or classification uses.

## Recommended Filtering Improvements

1. Add a split vehicle representation.

Keep both:

- `vehicle_text_raw`: current phrase after the article.
- `vehicle_text_clean`: phrase after boundary cleanup.
- `vehicle_tail_text`: removed prepositional/clausal tail.
- `vehicle_cleaning_rule`: rule or model that changed it.

For example:

| raw | clean | tail |
| --- | --- | --- |
| `luva no dia de hoje` | `luva` | `no dia de hoje` |
| `bomba no meu colo` | `bomba` | `no meu colo` |
| `pássaro com asas de anjo` | `pássaro` | `com asas de anjo` |

This lets visualizations aggregate on clean heads while still showing the
original phrase in example cards.

2. Trim likely adjunct tails after the vehicle head.

High-impact first rules:

- For known idiom heads like `luva`, `bomba`, `raio`, trim most `em/no/na/nos/nas/para/pra/ao/aos/de/do/da/dos/das` tails.
- For physical object vehicles, allow short noun-complement tails only when
  they identify the vehicle itself: `bolo de noiva`, `estrela de cinema`.
- Reject or trim after finite verbs: `foi`, `é`, `era`, `fica`, `tem`, `deve`.
- Reject or trim after pronoun tails: `ele`, `ela`, `me`, `mim`, `minha`,
  `seu`, `sua`, `isso`.
- Treat conjunction tails as suspicious unless the phrase is a coordinated
  vehicle: `caçador ou arranjador de votos` should likely be review-only.

3. Add a `comparison_use_type`.

Not every match is useful for a metaphor visualization. Classify candidates as:

- `comparison`: likely simile/metaphor.
- `idiom`: fixed expression such as `cair como uma luva`.
- `classification`: `Porto Alegre como uma cidade conectada`.
- `role`: `trabalhar como um profissional`.
- `literal_extent`: `alto como um prédio`, `grande como um caminhão`.
- `noise`.

This avoids throwing away useful data too early while giving the WebApp a clean
default view.

4. Use spaCy after the current Spark prefilter, not before it.

The full corpus produced only a few thousand candidates after prefiltering, so
spaCy can be applied cheaply at candidate level. Do not run spaCy over all
bronze rows.

Useful spaCy checks:

- parse `vehicle_text_raw` and keep the noun chunk head as `vehicle_head_clean`;
- identify whether the phrase starts with a noun/proper noun/adjective;
- detect clause tails by verb tokens after the head;
- detect proper-name/location patterns such as `Porto Alegre como uma cidade`;
- lemmatize vehicle heads more reliably than the current lowercase copy.

5. Add review columns rather than hard rejects first.

Before deleting candidates, add:

- `quality_label`: `keep`, `trimmed`, `review`, `reject`.
- `quality_reason`: machine-readable rule list.
- `visualization_ready`: boolean.

This gives us a measurable cleanup loop and protects against over-filtering.

## Visualization Readiness

Use the current full output for an initial cliche/repetition prototype, not for
a broad semantic map.

Good first visualizations:

- ground pages for high-signal grounds: `cair`, `duro`, `leve`, `rápido`,
  `forte`, `livre`, `voar`, `brilhar`;
- pair ranking: `cair -> luva`, `cair -> bomba`, `duro -> pedra`,
  `leve -> pluma`, `forte -> touro`;
- dominance view: how much a ground is dominated by its top vehicle.

Avoid using all 742 vehicle heads as equal-quality entities until cleanup is in
place. Many are one-off proper names, role nouns, or tail-contaminated phrases.

## Suggested Next Slice

Implement a candidate-level quality pass that reads the gold candidate DataFrame
and appends cleaned vehicle fields plus quality labels. Start with deterministic
rules, then add spaCy only for cases the rules cannot confidently classify.

Acceptance target for the next run:

- preserve raw candidate count for audit;
- produce a `visualization_ready` subset;
- reduce five-token vehicle phrases by at least 60%;
- keep canonical pairs stable: `cair -> luva`, `cair -> bomba`,
  `duro -> pedra`, `leve -> pluma`, `forte -> touro`;
- emit WebApp-ready tables from the cleaned fields, not from raw
  `vehicle_text`.
