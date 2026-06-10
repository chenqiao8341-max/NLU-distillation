# qwen35 4B author_org corrected parser audit

- source: `/home/qiao/work/NLU-distillation/reports/merged/qwen35_4b_nlu_prod_author_org.json`
- method: recompute metrics from saved raw outputs using tolerant JSON-prefix scalar recovery.

## Metrics

```json
{
  "author-institution-EM": 0.38095238095238093,
  "author-institution-Partial": 0.38095238095238093,
  "author-institution-Precision": 0.40476190476190477,
  "author-institution-Recall": 0.42857142857142855,
  "author-institution-F1": 0.4126984126984127,
  "author-name-EM": 0.8863636363636364,
  "author-name-Partial": 0.9318181818181818,
  "author-name-Precision": 0.8977272727272727,
  "author-name-Recall": 0.9090909090909091,
  "author-name-F1": 0.9015151515151515,
  "author-name英文变体-EM": 0.0,
  "author-name英文变体-Partial": 0.9090909090909091,
  "author-name英文变体-Precision": 0.8621212121212121,
  "author-name英文变体-Recall": 0.5767045454545454,
  "author-name英文变体-F1": 0.681074544142726,
  "Average-EM": 0.43119266055045874,
  "Average-Partial": 0.8165137614678899,
  "Average-F1": 0.7183542502349841,
  "Null-accuracy": 0.9824561403508771
}
```
