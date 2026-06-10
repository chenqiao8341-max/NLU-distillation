# qwen35-0.8b-topic-keywords short-prompt local NLU evaluation

- base_url: http://127.0.0.1:8020/v1
- generated_at: 2026-06-10T12:37:51
- message_style: alpaca-user
- total_samples: 200

## Overall

```json
{
  "Average-EM": 0.125,
  "Average-Partial": 0.21474358974358973,
  "Average-F1": 0.1991696337850184,
  "Null-accuracy": 0.42105263157894735
}
```

## topic和keywords

- samples: 200

```json
{
  "topics-EM": 0.22929936305732485,
  "topics-Partial": 0.3248407643312102,
  "topics-Precision": 0.25636942675159236,
  "topics-Recall": 0.2770700636942675,
  "topics-F1": 0.2605095541401274,
  "keywords-EM": 0.01935483870967742,
  "keywords-Partial": 0.1032258064516129,
  "keywords-Precision": 0.1266914805624483,
  "keywords-Recall": 0.17142857142857143,
  "keywords-F1": 0.13703823058661768,
  "Average-EM": 0.125,
  "Average-Partial": 0.21474358974358973,
  "Average-F1": 0.1991696337850184,
  "Null-accuracy": 0.42105263157894735
}
```
