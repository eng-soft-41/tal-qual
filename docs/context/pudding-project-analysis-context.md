# Context — The Pudding “Comparisons as Predictable as the Sunrise”

Source: https://pudding.cool/2026/05/similes/

## 1. Project summary

The Pudding’s **“Comparisons as Predictable as the Sunrise”** is an interactive visual essay about English similes in popular fiction.

The project analyzes roughly **200,000 similes** extracted from tens of thousands of fiction books, focusing on the highly regular structure:

```text
as [adjective] as [noun / noun phrase]
```

Example:

```text
as dry as sawdust
as still as a mouse
as hard as a rock
```

The project intentionally narrows the scope to this pattern because it is easier to identify programmatically than looser figurative forms such as “eyes like daggers” or metaphorical phrases.

## 2. Core linguistic model

The project frames similes using three parts:

```text
Tenor   → the thing being described
Ground  → the shared quality, usually an adjective
Vehicle → the comparison image, usually a noun or noun phrase
```

Example:

```text
My mouth has gone as dry as sawdust.
```

- **Tenor:** my mouth
- **Ground:** dry
- **Vehicle:** sawdust

For the analysis, the project mostly simplifies the structure to:

```text
as [ground adjective] as [vehicle noun]
```

This makes the dataset easier to count, compare, group, and visualize.

## 3. Analysis overview

The central idea is that similes become measurable when reduced to repeated pairings between adjectives and nouns.

The project asks questions such as:

- Which nouns are most commonly paired with each adjective?
- Which adjectives are dominated by a single cliché?
- Which adjectives have a broader range of comparison vehicles?
- Which nouns are “specialists,” strongly associated with one adjective?
- Which nouns are “generalists,” reused across many adjectives?
- Which similes are literal, figurative, clichéd, playful, or ironic?

The project treats each adjective as having a kind of **fingerprint**: a distribution of the nouns that follow it.

For example, an adjective like `dry` may be dominated by a few common vehicles such as `bone`, `desert`, or `dust`, while another adjective may have a flatter distribution with many less predictable choices.

## 4. NLP and extraction techniques

The project uses NLP techniques to scan fiction text for grammatical patterns matching the target simile structure.

The extraction process includes:

1. **Pattern detection**
   - Search for the “as ___ as ___” construction.
   - Restrict the ground to common adjectives.
   - Capture candidate vehicle nouns or short noun phrases.

2. **Frequency filtering**
   - Focus on the top 500 most-used adjectives from a word-frequency corpus.
   - Keep patterns that appear frequently enough to support aggregate analysis.

3. **Syntactic simplification**
   - Prefer cases where the ground is an adjective.
   - Prefer vehicles that are nouns, mono-grams, or bi-grams.
   - Remove overly complex one-off phrases when they add too much noise for statistical analysis.

4. **False-positive filtering**
   - Remove non-figurative or structurally unhelpful cases such as:
     - common functional expressions like `as soon as`
     - pronoun endings such as `as tall as him`
     - proper nouns such as `as fast as John`
     - possessive endings such as `as nasty as their reputation`
     - literal comparisons that are not useful as figurative similes

## 5. LLM-assisted filtering and categorization

The project uses LLMs as a second-pass review layer after rule-based and NLP extraction.

According to the project’s methods section, the author used **three LLM systems — Gemini, OpenAI, and Anthropic —** to help:

- detect false positives
- decide whether a candidate was figurative or literal
- extract and normalize the tenor
- extract and normalize the vehicle
- assist with judging whether similar vehicle phrases should be merged

This is important because the raw pattern match is not enough. A phrase can match the structure but still be a poor analytical candidate.

Example issues:

```text
as soon as possible
as tall as him
as fast as John
as nasty as their reputation
```

These may contain the surface pattern but do not behave like clean figurative similes.

LLMs were also useful in the blurrier parts of **vehicle aggregation**. For example:

```text
wolf
the wolf
wolves
a pack of wolves
```

Humans may understand these as related images, but a program initially sees them as different strings.

The project combines several techniques for this aggregation step:

- text normalization
- embedding similarity
- synonym detection
- containment checks
- LLM judging
- conservative human-like review logic

The project deliberately avoids over-merging. For example, `cat` and `kitten` may be related, but they can represent different figurative images and are kept separate in the original project’s framing.

## 6. Main visualizations and interactions

### 6.1 Introductory guessing interaction

The reader is invited to complete a simile such as:

```text
My mouth has gone as dry as ______
```

This works as a playful entry point. It puts the reader in the position of a writer choosing a comparison, then reveals that many people and authors reach for similar patterns.

### 6.2 Adjective fingerprints

Each adjective is visualized as a distribution of its most common vehicle nouns.

Concept:

```text
as dry as [bone, desert, dust, sawdust, ...]
```

The visualization shows whether an adjective is:

- cliché-heavy
- dominated by one vehicle
- spread across many vehicles
- supported by a long tail of rare comparisons

### 6.3 Small multiples of adjective shapes

The project shows many adjectives as compact bar charts.

Each small chart represents one adjective, and each bar represents a top vehicle noun.

This allows readers to compare distribution shapes quickly:

- tall spike → one dominant cliché
- gradual slope → more variety
- long tail → many rare or creative choices

### 6.4 Specialists and generalists

The project flips the analysis from adjectives to nouns.

Instead of asking:

```text
What nouns follow this adjective?
```

It asks:

```text
How many adjectives use this noun as a vehicle?
```

Some nouns are **specialists**, strongly attached to one adjective:

```text
cool as a cucumber
```

Other nouns are **generalists**, appearing across many different qualities:

```text
hot as hell
cute as hell
sexy as hell
dark as hell
```

The project uses a predictability/diversity score based on Simpson’s diversity index to quantify this behavior.

### 6.5 Generalist noun case studies

The project explores specific nouns that behave in interesting ways:

- **cat** — used across many qualities and behaviors
- **stone** — often used for hardness, stillness, silence, emotional absence
- **child** — associated with helplessness, innocence, vulnerability
- **hell** — often functions less as a literal vehicle and more as an intensifier

### 6.6 Ironic similes

The project identifies similes that invert expectations, such as:

```text
as clear as mud
```

These are treated as a smaller but expressive category. They often work by pairing a positive adjective with an unexpected or contradictory vehicle.

## 7. What makes the project effective

The project works because it combines:

- a narrow linguistic pattern
- a large text corpus
- careful NLP extraction
- LLM-assisted cleanup
- conservative aggregation
- simple but expressive statistics
- highly readable visual storytelling

The scope is intentionally constrained. Instead of trying to detect every kind of figurative language, the project focuses on one measurable form and explores it deeply.

## 8. Lessons for adaptation

The most important lesson is that the project is not only about similes. It is about finding a linguistic structure that is:

- common enough to produce data
- regular enough to extract
- expressive enough to tell stories
- interpretable enough to visualize

For a Portuguese adaptation, the same principle matters more than copying the exact English structure.
