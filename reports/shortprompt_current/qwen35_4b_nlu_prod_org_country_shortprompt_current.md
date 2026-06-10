# qwen35-4b-org-country short-prompt local NLU evaluation

- base_url: http://127.0.0.1:8020/v1
- generated_at: 2026-06-10T17:25:38
- message_style: alpaca-user
- total_samples: 200

## Overall

```json
{
  "Average-EM": 0.6893939393939394,
  "Average-Partial": 0.7196969696969697,
  "Average-F1": 0.7218234981392876,
  "Null-accuracy": 0.8933333333333333
}
```

## 机构和国家

- samples: 200

```json
{
  "机构名称-EM": 0.5813953488372093,
  "机构名称-Partial": 0.627906976744186,
  "机构名称-Precision": 0.627906976744186,
  "机构名称-Recall": 0.6383720930232558,
  "机构名称-F1": 0.6311709506323949,
  "国家-EM": 0.8913043478260869,
  "国家-Partial": 0.8913043478260869,
  "国家-Precision": 0.8913043478260869,
  "国家-Recall": 0.8913043478260869,
  "国家-F1": 0.8913043478260869,
  "Average-EM": 0.6893939393939394,
  "Average-Partial": 0.7196969696969697,
  "Average-F1": 0.7218234981392876,
  "Null-accuracy": 0.8933333333333333
}
```
