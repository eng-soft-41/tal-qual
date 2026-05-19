# Como-Article Ground/Vehicle MVP

## Goal

Build a clean, visualization-ready Portuguese comparison dataset focused on
the highest-value pattern found so far:

```text
[ground] como um/uma/uns/umas [vehicle]
```

This is the closest practical Portuguese analogue to The Pudding's English
pattern:

```text
as [ground adjective] as [vehicle noun]
```

The purpose is not to extract every Portuguese simile. The purpose is to create
a small, high-precision dataset that supports visualizations of repeated
`ground -> vehicle` pairings.

## Decision

Focus the MVP on:

```text
QUALITY_WORD como um/uma/uns/umas VEHICLE
SALIENT_VERB como um/uma/uns/umas VEHICLE
```

Examples:

```text
forte como um touro
grande como um caminhão
leve como uma nuvem
leve como uma pluma no ar
livre como um passarinho
pequena como um átomo
rápida como uma flecha
duro como um osso
voar como uma borboleta
voar como um avião
```

For now, exclude:

```text
bare como
que nem
feito
igual
parece
como se fosse
```

Those forms may be useful later, but they dilute the first visualization
dataset and increase false positives.

## Pipeline

```text
Raw / Bronze corpus segments
  -> strict `como + article` regex
  -> require allowlisted ground immediately before connector
  -> extract compact vehicle phrase
  -> reject generic/role/classification matches
  -> write gold seed dataset
  -> write visualization CSVs
  -> write review sample for spaCy/manual cleanup
```

The main extraction pass should be Spark-first and regex-based. spaCy should
only be used on a short review/refinement sample, not on the full corpus.

## Pattern Contract

### Connector

Only these connectors are in scope:

```text
como um
como uma
como uns
como umas
```

### Ground

The ground must be the token immediately before `como`.

Allowed ground classes:

1. Quality words from:

   ```text
   docs/specs/references/quality.txt
   ```

   This list is intentionally larger than the tiny first-pass hand list. It
   should include quality adjectives and adjective-like states that can produce
   interpretable Portuguese comparison fingerprints:

   ```text
   forte como um touro
   frágil como uma borboleta
   grande como um caminhão
   leve como uma pluma
   rápida como uma flecha
   duro como cimento
   brilhante como cristal
   ```

   The extractor should load this file at runtime instead of hardcoding the
   list in code. Blank lines are allowed and should be ignored. Matching should
   be case-insensitive while preserving the original surface text in the output.

2. Salient verbs from:

   ```text
   docs/specs/references/verbs.txt
   ```

   This list should favor actions that produce visually meaningful comparison
   frames:

   ```text
   caiu como uma luva
   voar como uma borboleta
   voar como um avião
   flutue como uma borboleta
   corre como um raio
   ```

   The list can be larger than the first prototype list, but it is still an
   allowlist. Do not use arbitrary verb suffix matching for the MVP.

Grounds outside these reference lists should be dropped in the MVP.

### Ground Reference Hygiene

The reference lists are intentionally editable project assets. They are allowed
to grow, but changes should be reviewed against sample output.

Guidelines:

- prefer words that produce a visualizable `ground -> vehicle` distribution;
- keep inflected forms in the file when needed;
- avoid purely grammatical/function words;
- avoid broad suffix rules such as "anything ending in `-ado`";
- if a term repeatedly creates role/classification noise, remove it or add a
  specific reject rule.

The current reference files are:

```text
docs/specs/references/quality.txt
docs/specs/references/verbs.txt
```

Implementation should expose these as configurable paths, with those files as
defaults.

### Vehicle

Vehicle starts immediately after the article:

```text
forte como um touro
              ^^^^^
```

Vehicle rules:

- keep 1 to 5 tokens;
- stop at punctuation or segment boundary;
- preserve the surface phrase;
- lowercase a normalized copy;
- vehicle head is the first token for the MVP;
- reject if the first token is a pronoun, preposition, determiner, discourse
  marker, or generic abstract word.

Reject vehicle starts such as:

```text
de, do, da, dos, das
em, no, na, nos, nas
o, a, os, as
ele, ela, eu, me
todo, toda, todos, todas
é, foi, parece, quando, sempre, só
coisa, forma, tipo, espécie, parte, meio, processo, exemplo, tema
```

## Rejection Rules

Reject role/classification contexts:

```text
usado como um ...
utilizado como uma ...
conhecido como um ...
tratado como uma ...
considerado como um ...
definido como uma ...
classificado como um ...
entendido como uma ...
```

Reject vehicle phrases that:

- are longer than 5 tokens;
- start with a stopword/pronoun/generic word;
- contain obvious URLs, code, percentages, or numeric-only heads;
- are `como um todo` / `como uma forma` / similar generic structures.

## Expected Output Schema

Primary output:

```text
data/gold/como_article_ground_vehicle_candidates
```

Schema:

```text
candidate_id: string
source_file: string
original_line_id: long
segment_id: integer

pattern_type: string
connector: string
matched_text: string
candidate_full_text: string
text_before: string

tenor_text: string
tenor_lemma: string
tenor_confidence: string

ground_text: string
ground_lemma: string
ground_type: string
ground_source: string
ground_reference_path: string

vehicle_text: string
vehicle_lemma: string
vehicle_head: string
vehicle_head_lemma: string
vehicle_phrase_length_tokens: integer

filter_label: string
reject_reason: string
confidence: double
needs_review: boolean

char_start: integer
char_end: integer
connector_start: integer
connector_end: integer
vehicle_start: integer
vehicle_end: integer
```

Field notes:

- `ground_type` should be `quality_adjective` or `salient_verb`.
- `ground_source` should be `quality_reference` or `verb_reference`.
- `ground_reference_path` should identify which allowlist file matched the
  ground.
- `tenor_text` is optional and approximate. It should not block inclusion.
- primary gold output should contain kept rows only; rejected rows may be
  sampled separately for debugging.

## Visualization Outputs

Write compact CSVs:

```text
outputs/como_article_ground_vehicle_counts.csv
outputs/como_article_vehicle_ground_counts.csv
outputs/como_article_ground_counts.csv
outputs/como_article_vehicle_counts.csv
outputs/como_article_examples.csv
outputs/como_article_review_sample.csv
```

### Ground -> Vehicle Counts

```text
ground_lemma,vehicle_head_lemma,count
forte,touro,12
leve,pluma,8
rápido,raio,7
duro,pedra,6
```

### Vehicle -> Ground Counts

```text
vehicle_head_lemma,ground_lemma,count
pedra,duro,6
pedra,frio,3
luva,caiu,25
```

### Example Table

```text
ground_text,vehicle_text,tenor_text,candidate_full_text
forte,touro,Sentia-se,Sentia-se forte como um touro
leve,pluma,o programa saiu,o programa saiu leve como uma pluma no ar
```

## Possible Visualizations

### 1. Ground Fingerprints

For each ground, show its top vehicles:

```text
forte -> touro, carvalho, gigante, cavalo
leve  -> pluma, nuvem, carícia
duro  -> pedra, osso, cimento, vidro
```

This is the closest adaptation of The Pudding's adjective fingerprint view.

### 2. Vehicle Fingerprints

Flip the table:

```text
pedra -> duro, frio, seco
borboleta -> leve, livre, voar
luva -> caiu, cabe, encaixa
```

This supports specialist/generalist analysis.

### 3. Cliché / Dominance View

For each ground, calculate whether one vehicle dominates:

```text
ground_lemma
top_vehicle_head_lemma
top_vehicle_count
total_count
top_vehicle_share
distinct_vehicle_count
```

Example:

```text
caiu -> luva may be highly dominant
forte -> touro/carvalho/gigante may be more distributed
```

### 4. Small Multiples

Small bar charts per ground:

```text
forte  [touro | carvalho | gigante | cavalo]
leve   [pluma | nuvem | carícia]
rápido [raio | flecha | bala]
```

### 5. Example Explorer

Click a `ground -> vehicle` pair and show example sentences.

Minimum fields:

```text
ground_text
connector_text
vehicle_text
candidate_full_text
source_file
original_line_id
```

### 6. Portuguese Adaptation Note

The visualization should explicitly explain:

> English has a very regular `as ADJ as NOUN` pattern. Portuguese does not have
> one exact equivalent, so this prototype focuses on the productive frame
> `GROUND como um/uma VEHICLE`.

This turns the limitation into part of the story.

## Current Implementation

Core code:

```text
src/tal_qual/bronze.py
src/tal_qual/como_article_ground_vehicle.py
```

Core notebook:

```text
notebooks/01_como_article_ground_vehicle_mvp.ipynb
```

The notebook uses a Spark-native prefilter before the Python extraction UDF and
is the only supported run path.

The current full-shard sweet-spot Spark configuration is:

```text
TAL_QUAL_SPARK_MASTER=local[4]
TAL_QUAL_SPARK_PARALLELISM=4
TAL_QUAL_SPARK_SHUFFLE_PARTITIONS=4
```

The implementation should keep deepening this path rather than adding broader
connector families.

## Success Criteria

This MVP is successful when:

- the output has hundreds to a few thousand high-precision rows;
- examples are manually inspectable in one sitting;
- the top pairs include recognizable comparisons such as:

  ```text
  forte -> touro
  leve -> pluma
  rápido -> raio
  duro -> pedra/osso
  claro -> água/cristal
  voar -> borboleta/avião
  caiu -> luva
  ```

- the CSVs are sufficient to build the first visualization prototype;
- the project story is clear and no longer depends on unfinished broad
  extraction work.
