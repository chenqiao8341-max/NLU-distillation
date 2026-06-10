# qwen35-4b-time-if short-prompt local NLU evaluation

- base_url: http://127.0.0.1:8020/v1
- generated_at: 2026-06-10T17:32:50
- message_style: alpaca-user
- total_samples: 200

## Overall

```json
{
  "Average-EM": 0.7983193277310925,
  "Average-Partial": 0.7983193277310925,
  "Average-F1": 0.8226890756302522,
  "Null-accuracy": 0.9927113702623906
}
```

## 时间和if值

- samples: 200

```json
{
  "filter-start-datetime-EM": 0.8041237113402062,
  "filter-start-datetime-Partial": 0.8041237113402062,
  "filter-start-datetime-Precision": 0.8298969072164949,
  "filter-start-datetime-Recall": 0.8298969072164949,
  "filter-start-datetime-F1": 0.8298969072164949,
  "filter-end-datetime-EM": 0.75,
  "filter-end-datetime-Partial": 0.75,
  "filter-end-datetime-Precision": 0.7777777777777778,
  "filter-end-datetime-Recall": 0.7916666666666666,
  "filter-end-datetime-F1": 0.7833333333333333,
  "filter-start-if-EM": 0.8,
  "filter-start-if-Partial": 0.8,
  "filter-start-if-Precision": 0.8,
  "filter-start-if-Recall": 0.8,
  "filter-start-if-F1": 0.8,
  "filter-end-if-EM": 0.0,
  "filter-end-if-Partial": 0.0,
  "filter-end-if-Precision": 0.0,
  "filter-end-if-Recall": 0.0,
  "filter-end-if-F1": 0.0,
  "Average-EM": 0.7983193277310925,
  "Average-Partial": 0.7983193277310925,
  "Average-F1": 0.8226890756302522,
  "Null-accuracy": 0.9927113702623906
}
```
