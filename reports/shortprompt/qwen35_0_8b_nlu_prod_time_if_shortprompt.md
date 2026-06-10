# qwen35-0.8b-time-if short-prompt local NLU evaluation

- base_url: http://127.0.0.1:8020/v1
- generated_at: 2026-06-10T12:35:33
- message_style: alpaca-user
- total_samples: 200

## Overall

```json
{
  "Average-EM": 0.26229508196721313,
  "Average-Partial": 0.26229508196721313,
  "Average-F1": 0.5368852459016393,
  "Null-accuracy": 0.9897810218978103
}
```

## 时间和if值

- samples: 200

```json
{
  "filter-start-datetime-EM": 0.17525773195876287,
  "filter-start-datetime-Partial": 0.17525773195876287,
  "filter-start-datetime-Precision": 0.520618556701031,
  "filter-start-datetime-Recall": 0.520618556701031,
  "filter-start-datetime-F1": 0.520618556701031,
  "filter-end-datetime-EM": 0.6923076923076923,
  "filter-end-datetime-Partial": 0.6923076923076923,
  "filter-end-datetime-Precision": 0.6923076923076923,
  "filter-end-datetime-Recall": 0.6923076923076923,
  "filter-end-datetime-F1": 0.6923076923076923,
  "filter-start-if-EM": 0.5,
  "filter-start-if-Partial": 0.5,
  "filter-start-if-Precision": 0.5,
  "filter-start-if-Recall": 0.5,
  "filter-start-if-F1": 0.5,
  "filter-end-if-EM": 0.0,
  "filter-end-if-Partial": 0.0,
  "filter-end-if-Precision": 0.0,
  "filter-end-if-Recall": 0.0,
  "filter-end-if-F1": 0.0,
  "Average-EM": 0.26229508196721313,
  "Average-Partial": 0.26229508196721313,
  "Average-F1": 0.5368852459016393,
  "Null-accuracy": 0.9897810218978103
}
```
