# qwen35-4b-nlu-prod-time-if local NLU evaluation

- base_url: http://127.0.0.1:8012/v1
- generated_at: 2026-06-10T09:04:26
- total_samples: 200

## Overall

```json
{
  "Average-EM": 0.2711864406779661,
  "Average-Partial": 0.2711864406779661,
  "Average-F1": 0.5847457627118644,
  "Null-accuracy": 0.9956204379562044
}
```

## 时间和if值

- samples: 200

```json
{
  "filter-end-datetime-EM": 0.75,
  "filter-end-datetime-Partial": 0.75,
  "filter-end-datetime-Precision": 0.75,
  "filter-end-datetime-Recall": 0.75,
  "filter-end-datetime-F1": 0.75,
  "filter-end-if-EM": 0.0,
  "filter-end-if-Partial": 0.0,
  "filter-end-if-Precision": 0.0,
  "filter-end-if-Recall": 0.0,
  "filter-end-if-F1": 0.0,
  "filter-start-datetime-EM": 0.17525773195876287,
  "filter-start-datetime-Partial": 0.17525773195876287,
  "filter-start-datetime-Precision": 0.5567010309278351,
  "filter-start-datetime-Recall": 0.5567010309278351,
  "filter-start-datetime-F1": 0.5567010309278351,
  "filter-start-if-EM": 0.6666666666666666,
  "filter-start-if-Partial": 0.6666666666666666,
  "filter-start-if-Precision": 0.6666666666666666,
  "filter-start-if-Recall": 0.6666666666666666,
  "filter-start-if-F1": 0.6666666666666666,
  "Average-EM": 0.2711864406779661,
  "Average-Partial": 0.2711864406779661,
  "Average-F1": 0.5847457627118644,
  "Null-accuracy": 0.9956204379562044
}
```
