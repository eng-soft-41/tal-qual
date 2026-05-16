# Additional Phase B — LLM Classification Test

## Goal

Test whether an LLM can classify a small sample of extracted candidates into useful analytical categories.

This phase is **not part of the MVP** and should not run at full corpus scale.

## Hypothesis

An LLM can help separate figurative similes from literal comparisons and false positives, but only after Spark has reduced the dataset to a manageable candidate set.

## Input

A small sample from:

```text
data/silver/comparison_candidates.parquet
```

Recommended sample size:

```text
50–200 candidates
```

## Suggested Labels

```text
figurative_simile
literal_comparison
idiom_or_fixed_expression
non_comparison_false_positive
unclear
```

## Test Steps

1. Sample candidates by connector type.
2. Send candidate text to the LLM.
3. Request structured JSON output.
4. Store classification results separately.
5. Manually inspect a small subset for quality.
6. Compare label distribution by connector.

## Output Fields

```text
candidate_id
candidate_full_text
llm_label
llm_confidence
llm_explanation_short
```

Optional fields:

```text
tenor
ground
vehicle_llm
vehicle_normalized
```

## Success Criteria

This phase is useful if:

- The labels are consistent enough for exploratory analysis.
- It helps estimate the proportion of figurative versus literal comparisons.
- It reveals which connectors produce cleaner candidates.
- The cost and complexity remain acceptable.

## Presentation Value

This phase can be presented as a future research direction:

> Spark handles large-scale extraction, while an LLM can later be used as a second-pass classifier on a small candidate subset to estimate quality and categorize examples.
