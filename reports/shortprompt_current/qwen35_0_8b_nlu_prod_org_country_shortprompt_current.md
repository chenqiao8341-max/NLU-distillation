# qwen35-0.8b-org-country short-prompt local NLU evaluation

- base_url: http://127.0.0.1:8020/v1
- generated_at: 2026-06-10T16:48:42
- message_style: alpaca-user
- total_samples: 200

## Overall

```json
{
  "Average-EM": 0.625,
  "Average-Partial": 0.6458333333333334,
  "Average-F1": 0.6435185185185186,
  "Null-accuracy": 0.8533333333333334
}
```

## 机构和国家

- samples: 200

```json
{
  "机构名称-EM": 0.5730337078651685,
  "机构名称-Partial": 0.5955056179775281,
  "机构名称-Precision": 0.5955056179775281,
  "机构名称-Recall": 0.5898876404494382,
  "机构名称-F1": 0.5917602996254682,
  "国家-EM": 0.7090909090909091,
  "国家-Partial": 0.7272727272727273,
  "国家-Precision": 0.7272727272727273,
  "国家-Recall": 0.7272727272727273,
  "国家-F1": 0.7272727272727273,
  "Average-EM": 0.625,
  "Average-Partial": 0.6458333333333334,
  "Average-F1": 0.6435185185185186,
  "Null-accuracy": 0.8533333333333334
}
```
