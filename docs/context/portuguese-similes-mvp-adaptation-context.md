# Portuguese Comparison Adaptation Context

This document preserves the broader adaptation thinking behind Tal Qual while
keeping the current project direction clear: the supported dataset is the
**Como-Article Ground/Vehicle Candidate** path.

## Current Framing

Tal Qual adapts the idea behind The Pudding's English simile analysis to
Portuguese, but Portuguese does not offer a single direct equivalent to English
`as ADJ as NOUN`.

The current project therefore focuses on the productive, inspectable frame:

```text
GROUND como um/uma/uns/umas VEHICLE
```

Examples:

```text
forte como um touro
leve como uma pluma
rápida como uma flecha
caiu como uma luva
voar como um avião
```

This gives the project an explicit **Curated Ground**, literal **Connector
Text**, and compact **Vehicle Text** that can support ground and vehicle
fingerprints.

## Why The Scope Narrowed

Earlier adaptation ideas considered a broad connector list:

```text
como
como se
tal qual
que nem
igual a
parece
feito
```

Those connectors are useful linguistic background, but they make the first
visualization dataset harder to explain and much noisier. The current workflow
does not try to detect every Portuguese simile or explicit comparison.

The current choice is intentionally narrower:

- require `como` plus an article;
- require a curated ground immediately before `como`;
- extract a compact vehicle phrase immediately after the article;
- reject generic, role/classification, URL, numeric, and discourse noise.

The result is less recall and more interpretability.

## Design Consequences

The project should prioritize:

- better **Vehicle Text** filtering inside the current pattern;
- richer **Analysis Outputs** from the **Gold Seed Dataset**;
- **WebApp-Ready Outputs** for ground pages, vehicle pages, pair rankings, and
  example explorers.

The project should avoid broadening connector scope until the current
como-article dataset is strong enough to visualize.

## Visualization Ideas That Still Fit

### Ground Fingerprints

For each ground, show its most frequent vehicle heads:

```text
forte -> touro, gigante, rocha
leve -> pluma, nuvem, pena
duro -> pedra, osso, aço
```

This is the closest Portuguese adaptation of The Pudding's adjective
fingerprint idea.

### Vehicle Fingerprints

Flip the table to show which grounds attach to a vehicle:

```text
pedra -> duro, frio, seco
luva -> caiu, encaixa, coube
avião -> voar, rápido, alto
```

This can reveal specialist vehicles, generalist vehicles, and cliche-like
dominance patterns.

### Dominance And Diversity

For each ground:

```text
ground_lemma
top_vehicle_head_lemma
top_vehicle_count
total_count
top_vehicle_share
distinct_vehicle_count
```

This supports questions like whether `caiu -> luva` is much more dominant than
`forte -> touro`.

### Example Explorer

Every ranking should be explainable through examples with:

```text
ground_text
connector_text
vehicle_text
candidate_full_text
source_file
original_line_id
```

This is important because the project remains extraction-based, not an
annotated truth set.

## Language To Preserve

Use careful project language:

- Say **candidate**, not final simile.
- Say **Vehicle Text** and **Vehicle Head**, not semantic vehicle class.
- Say **Gold Seed Dataset**, not final annotation dataset.
- Say **WebApp-Ready Output**, not notebook-only display.

Avoid claims that the project detects all similes or metaphors in Portuguese.

## Future Use

This context should inform future work when deciding whether an idea belongs in
the current workflow.

Good next steps:

- tighten vehicle boundaries;
- add review-quality metrics;
- add dominance/diversity analysis;
- produce frontend-ready tables.

Poor next steps for now:

- reintroducing all connector families;
- adding LLM classification as a required pipeline stage;
- using full-corpus spaCy parsing before the current regex path is exhausted.
