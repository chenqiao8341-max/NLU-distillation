# qwen35-4b-topic-keywords short-prompt local NLU evaluation

- base_url: http://127.0.0.1:8020/v1
- generated_at: 2026-06-10T17:35:48
- message_style: alpaca-user
- total_samples: 200

## Overall

```json
{
  "Average-EM": 0.028846153846153848,
  "Average-Partial": 0.0625,
  "Average-F1": 0.04391025641025641,
  "Null-accuracy": 0.9186602870813397
}
```

## topic和keywords

- samples: 200

```json
{
  "topics-EM": 0.05504587155963303,
  "topics-Partial": 0.07339449541284404,
  "topics-Precision": 0.05504587155963303,
  "topics-Recall": 0.05504587155963303,
  "topics-F1": 0.05504587155963303,
  "keywords-EM": 0.0,
  "keywords-Partial": 0.050505050505050504,
  "keywords-Precision": 0.03367003367003367,
  "keywords-Recall": 0.03198653198653199,
  "keywords-F1": 0.03164983164983165,
  "Average-EM": 0.028846153846153848,
  "Average-Partial": 0.0625,
  "Average-F1": 0.04391025641025641,
  "Null-accuracy": 0.9186602870813397
}
```
