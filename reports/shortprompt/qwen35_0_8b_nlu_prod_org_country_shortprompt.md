# qwen35-0.8b-org-country short-prompt local NLU evaluation

- base_url: http://127.0.0.1:8020/v1
- generated_at: 2026-06-10T12:33:09
- message_style: alpaca-user
- total_samples: 200

## Overall

```json
{
  "Average-EM": 0.7083333333333334,
  "Average-Partial": 0.7430555555555556,
  "Average-F1": 0.7268518518518519,
  "Null-accuracy": 0.8951048951048951
}
```

## 机构和国家

- samples: 200

```json
{
  "机构名称-EM": 0.7078651685393258,
  "机构名称-Partial": 0.7528089887640449,
  "机构名称-Precision": 0.7303370786516854,
  "机构名称-Recall": 0.7247191011235955,
  "机构名称-F1": 0.7265917602996255,
  "国家-EM": 0.7090909090909091,
  "国家-Partial": 0.7272727272727273,
  "国家-Precision": 0.7272727272727273,
  "国家-Recall": 0.7272727272727273,
  "国家-F1": 0.7272727272727273,
  "Average-EM": 0.7083333333333334,
  "Average-Partial": 0.7430555555555556,
  "Average-F1": 0.7268518518518519,
  "Null-accuracy": 0.8951048951048951
}
```
