# qwen35-4b-author-org short-prompt local NLU evaluation

- base_url: http://127.0.0.1:8020/v1
- generated_at: 2026-06-10T17:19:20
- message_style: alpaca-user
- total_samples: 200

## Overall

```json
{
  "Average-EM": 0.5491803278688525,
  "Average-Partial": 0.8729508196721312,
  "Average-F1": 0.83908088562358,
  "Null-accuracy": 0.964769647696477
}
```

## 作者和机构

- samples: 200

```json
{
  "author-name-EM": 0.9047619047619048,
  "author-name-Partial": 0.9142857142857143,
  "author-name-Precision": 0.9222222222222222,
  "author-name-Recall": 0.9333333333333333,
  "author-name-F1": 0.9253968253968254,
  "author-name英文变体-EM": 0.1346153846153846,
  "author-name英文变体-Partial": 0.8846153846153846,
  "author-name英文变体-Precision": 0.8439190617075233,
  "author-name英文变体-Recall": 0.7543122942762366,
  "author-name英文变体-F1": 0.7875231034501939,
  "author-institution-EM": 0.7142857142857143,
  "author-institution-Partial": 0.7142857142857143,
  "author-institution-Precision": 0.7285714285714285,
  "author-institution-Recall": 0.7428571428571429,
  "author-institution-F1": 0.7333333333333334,
  "Average-EM": 0.5491803278688525,
  "Average-Partial": 0.8729508196721312,
  "Average-F1": 0.83908088562358,
  "Null-accuracy": 0.964769647696477
}
```
