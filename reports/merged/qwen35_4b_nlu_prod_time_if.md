# qwen35-4b-nlu-prod-time-if local NLU evaluation

- base_url: http://127.0.0.1:8000/v1
- generated_at: 2026-06-09T16:32:52
- total_samples: 235

## Overall

```json
{
  "Average-EM": 0.5545454545454546,
  "Average-Partial": 0.5545454545454546,
  "Average-F1": 0.7272727272727273,
  "Null-accuracy": 0.9975961538461539
}
```

## 时间和if值

- samples: 235

```json
{
  "filter-end-datetime-EM": 0.6,
  "filter-end-datetime-Partial": 0.6,
  "filter-end-datetime-Precision": 0.6,
  "filter-end-datetime-Recall": 0.6,
  "filter-end-datetime-F1": 0.6,
  "filter-end-if-EM": 0.0,
  "filter-end-if-Partial": 0.0,
  "filter-end-if-Precision": 0.0,
  "filter-end-if-Recall": 0.0,
  "filter-end-if-F1": 0.0,
  "filter-start-datetime-EM": 0.5164835164835165,
  "filter-start-datetime-Partial": 0.5164835164835165,
  "filter-start-datetime-Precision": 0.7252747252747253,
  "filter-start-datetime-Recall": 0.7252747252747253,
  "filter-start-datetime-F1": 0.7252747252747253,
  "filter-start-if-EM": 0.8888888888888888,
  "filter-start-if-Partial": 0.8888888888888888,
  "filter-start-if-Precision": 0.8888888888888888,
  "filter-start-if-Recall": 0.8888888888888888,
  "filter-start-if-F1": 0.8888888888888888,
  "Average-EM": 0.5545454545454546,
  "Average-Partial": 0.5545454545454546,
  "Average-F1": 0.7272727272727273,
  "Null-accuracy": 0.9975961538461539
}
```
