# qwen35-0.8b-time-if short-prompt local NLU evaluation

- base_url: http://127.0.0.1:8020/v1
- generated_at: 2026-06-10T16:51:02
- message_style: alpaca-user
- total_samples: 200

## Overall

```json
{
  "Average-EM": 0.7377049180327869,
  "Average-Partial": 0.7377049180327869,
  "Average-F1": 0.7696721311475411,
  "Null-accuracy": 0.9883381924198251
}
```

## 时间和if值

- samples: 200

```json
{
  "filter-start-datetime-EM": 0.7938144329896907,
  "filter-start-datetime-Partial": 0.7938144329896907,
  "filter-start-datetime-Precision": 0.8298969072164949,
  "filter-start-datetime-Recall": 0.8298969072164949,
  "filter-start-datetime-F1": 0.8298969072164949,
  "filter-end-datetime-EM": 0.5384615384615384,
  "filter-end-datetime-Partial": 0.5384615384615384,
  "filter-end-datetime-Precision": 0.5641025641025641,
  "filter-end-datetime-Recall": 0.5769230769230769,
  "filter-end-datetime-F1": 0.5692307692307692,
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
  "Average-EM": 0.7377049180327869,
  "Average-Partial": 0.7377049180327869,
  "Average-F1": 0.7696721311475411,
  "Null-accuracy": 0.9883381924198251
}
```
