# qwen35-0.8b-nlu-prod-author-org local NLU evaluation

- base_url: http://127.0.0.1:8010/v1
- generated_at: 2026-06-10T00:43:27
- total_samples: 200

## Overall

```json
{
  "Average-EM": 0.14224137931034483,
  "Average-Partial": 0.23275862068965517,
  "Average-F1": 0.21357279722329245,
  "Null-accuracy": 0.9945945945945946
}
```

## 作者和机构

- samples: 200

```json
{
  "author-institution-EM": 0.0625,
  "author-institution-Partial": 0.0625,
  "author-institution-Precision": 0.0625,
  "author-institution-Recall": 0.0625,
  "author-institution-F1": 0.0625,
  "author-name-EM": 0.29,
  "author-name-Partial": 0.31,
  "author-name-Precision": 0.31862068965517243,
  "author-name-Recall": 0.312,
  "author-name-F1": 0.3125925925925926,
  "author-name英文变体-EM": 0.02,
  "author-name英文变体-Partial": 0.21,
  "author-name英文变体-Precision": 0.20167857142857146,
  "author-name英文变体-Recall": 0.14267437423687424,
  "author-name英文变体-F1": 0.1628962969654459,
  "Average-EM": 0.14224137931034483,
  "Average-Partial": 0.23275862068965517,
  "Average-F1": 0.21357279722329245,
  "Null-accuracy": 0.9945945945945946
}
```
