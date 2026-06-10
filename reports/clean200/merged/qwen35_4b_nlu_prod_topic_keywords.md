# qwen35-4b-nlu-prod-topic-keywords local NLU evaluation

- base_url: http://127.0.0.1:8012/v1
- generated_at: 2026-06-10T10:09:34
- total_samples: 200

## Overall

```json
{
  "Average-EM": 0.1348973607038123,
  "Average-Partial": 0.25806451612903225,
  "Average-F1": 0.19659451008424617,
  "Null-accuracy": 0.2822966507177033
}
```

## topic和keywords

- samples: 200

```json
{
  "keywords-EM": 0.0718562874251497,
  "keywords-Partial": 0.2275449101796407,
  "keywords-Precision": 0.1754491017964072,
  "keywords-Recall": 0.19040490447676076,
  "keywords-F1": 0.1754814048227222,
  "topics-EM": 0.19540229885057472,
  "topics-Partial": 0.28735632183908044,
  "topics-Precision": 0.21743295019157088,
  "topics-Recall": 0.22413793103448276,
  "topics-F1": 0.2168582375478927,
  "Average-EM": 0.1348973607038123,
  "Average-Partial": 0.25806451612903225,
  "Average-F1": 0.19659451008424617,
  "Null-accuracy": 0.2822966507177033
}
```
