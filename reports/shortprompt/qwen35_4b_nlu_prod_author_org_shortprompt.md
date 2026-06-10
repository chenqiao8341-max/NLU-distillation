# qwen35-4b-author-org short-prompt local NLU evaluation

- base_url: http://127.0.0.1:8020/v1
- generated_at: 2026-06-10T13:05:11
- message_style: alpaca-user
- total_samples: 200

## Overall

```json
{
  "Average-EM": 0.5666666666666667,
  "Average-Partial": 0.8916666666666667,
  "Average-F1": 0.8575298527649253,
  "Null-accuracy": 0.972972972972973
}
```

## 作者和机构

- samples: 200

```json
{
  "author-name-EM": 0.9230769230769231,
  "author-name-Partial": 0.9326923076923077,
  "author-name-Precision": 0.9407051282051282,
  "author-name-Recall": 0.9519230769230769,
  "author-name-F1": 0.9439102564102565,
  "author-name英文变体-EM": 0.14563106796116504,
  "author-name英文变体-Partial": 0.8932038834951457,
  "author-name英文变体-Precision": 0.8534069490380171,
  "author-name英文变体-Recall": 0.7616357146090156,
  "author-name英文变体-F1": 0.7958624400995025,
  "author-institution-EM": 0.7575757575757576,
  "author-institution-Partial": 0.7575757575757576,
  "author-institution-Precision": 0.7727272727272727,
  "author-institution-Recall": 0.7878787878787878,
  "author-institution-F1": 0.7777777777777778,
  "Average-EM": 0.5666666666666667,
  "Average-Partial": 0.8916666666666667,
  "Average-F1": 0.8575298527649253,
  "Null-accuracy": 0.972972972972973
}
```
