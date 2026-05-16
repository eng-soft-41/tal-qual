# Additional Phase A — NLP Filtering Test

## Goal

Test whether simple NLP processing improves candidate quality after Spark extraction.

This phase is **not part of the MVP**. It should run only on the reduced silver candidate dataset.

## Hypothesis

NLP can help identify cleaner vehicle phrases and reduce obvious false positives.

## Possible Tools

```text
spaCy Portuguese model
NLTK tokenization
Spark NLP, if a Spark-native option is desired
```

## Input

```text
data/silver/comparison_candidates.parquet
```

## Test Steps

1. Load a sample of candidates.
2. Tokenize `candidate_full_text` or `text_after`.
3. Identify likely nouns or noun phrases after the connector.
4. Remove punctuation and stopwords.
5. Compare `vehicle_raw` with `vehicle_nlp`.
6. Manually inspect a small sample.

## Output Fields

```text
candidate_id
vehicle_raw
vehicle_nlp
nlp_notes
```

## Success Criteria

This phase is useful if:

- It improves vehicle extraction readability.
- It reduces obvious junk phrases.
- It creates better data for visualizations.
- It does not make the pipeline too complex.

## Presentation Value

This phase can be presented as a future improvement:

> After Spark reduces the corpus to candidate comparisons, NLP can refine the smaller dataset by improving vehicle extraction and filtering low-quality candidates.
