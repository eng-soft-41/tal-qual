# Tal Qual

This context describes the language used for the Portuguese comparison-candidate analysis project. It keeps linguistic and dataset terms stable across specs, issues, notebooks, and implementation notes.

## Language

**Comparison Candidate**:
A corpus excerpt selected by connector-based rules as a possible explicit comparison.
_Avoid_: simile, final simile

**Silver Candidate**:
A comparison candidate emitted by the Spark extraction layer before linguistic refinement.
_Avoid_: raw simile, final vehicle row

**NLP Refinement Layer**:
A post-extraction analysis layer that enriches silver candidates with structured linguistic fields while preserving the original candidate rows.
_Avoid_: NLP filtering test, final classifier

**Vehicle Structure Refinement**:
The first NLP refinement slice that turns a right-context window into a syntactic vehicle phrase and head when possible.
_Avoid_: adjective extraction, figurative classification

**Primary Nominal Article Candidate**:
A silver candidate whose connector pattern gives an article cue that the right side likely starts as a noun phrase.
_Avoid_: guaranteed simile, guaranteed noun

**Primary Nominal Bare Candidate**:
A silver candidate from a bare comparison connector whose right side may be noun-like but has weaker syntactic cues than article-gated patterns.
_Avoid_: generic bare connector, low-quality candidate

**Vehicle Phrase**:
The readable noun phrase extracted from the right side of a comparison candidate.
_Avoid_: right context, full clause

**Vehicle Head**:
The main noun or pronoun inside a vehicle phrase used as the preferred aggregation unit.
_Avoid_: full vehicle phrase, raw vehicle string

**Aggregate-Eligible Vehicle**:
A vehicle head considered suitable for default vehicle-frequency charts.
_Avoid_: all extracted vehicles, any right-context token

**Clean Common-Noun Vehicle**:
A vehicle head that is a common noun and passes conservative noun-vehicle rules.
_Avoid_: proper-name vehicle, chartable vehicle

**Chartable Vehicle**:
A vehicle head suitable for exploratory vehicle charts, including clean common nouns and selected proper names.
_Avoid_: clean common-noun vehicle, all extracted heads

**Structural Quality Bucket**:
A deterministic label describing the syntactic usability of a refined candidate.
_Avoid_: figurative label, literal label, sentiment

**Phase A Validation Notebook**:
A notebook that demonstrates whether the NLP refinement layer improves vehicle structure and candidate quality.
_Avoid_: frontend app, production dashboard

**Refined Candidate Dataset**:
A durable dataset produced by the NLP refinement layer for downstream analysis.
_Avoid_: notebook-only result, replacement silver dataset

## Relationships

- A **Silver Candidate** is a kind of **Comparison Candidate**.
- The **NLP Refinement Layer** enriches one or more **Silver Candidates**.
- **Vehicle Structure Refinement** happens before optional ground-adjective extraction.
- A **Primary Nominal Article Candidate** and a **Primary Nominal Bare Candidate** are both first-slice targets for **Vehicle Structure Refinement**.
- A **Vehicle Phrase** has zero or one **Vehicle Head**.
- An **Aggregate-Eligible Vehicle** is a **Vehicle Head** that passes default charting rules.
- A **Clean Common-Noun Vehicle** is stricter than a **Chartable Vehicle**.
- A **Structural Quality Bucket** is not a figurative or literal classification.
- A **Phase A Validation Notebook** presents the **Refined Candidate Dataset** without replacing it.
- A **Refined Candidate Dataset** preserves **Silver Candidate** identity and adds NLP-derived fields.

## Example dialogue

> **Dev:** "Should Phase A delete noisy rows from the silver output?"
> **Domain expert:** "No — Phase A is an **NLP Refinement Layer**. It should enrich **Silver Candidates** and mark quality, not replace the original extraction."

## Flagged ambiguities

- "NLP filtering" sounded like a destructive subset operation; resolved: Phase A is an **NLP Refinement Layer** that may add quality flags while preserving silver candidates.
- "Aggregate eligible" was too broad as a single concept; resolved: Phase A distinguishes **Clean Common-Noun Vehicle** from broader **Chartable Vehicle**.
