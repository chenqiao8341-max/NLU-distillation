# qwen35-0.8b-nlu-prod-topic-keywords local NLU evaluation

- base_url: http://127.0.0.1:8010/v1
- generated_at: 2026-06-09T23:08:34
- total_samples: 200

## Overall

```json
{
  "Average-EM": 0.22025316455696203,
  "Average-Partial": 0.3367088607594937,
  "Average-F1": 0.2820809570176659,
  "Null-accuracy": 0.023923444976076555
}
```

## topic和keywords

- samples: 200

```json
{
  "keywords-EM": 0.11224489795918367,
  "keywords-Partial": 0.25510204081632654,
  "keywords-Precision": 0.24039115646258505,
  "keywords-Recall": 0.22612973760932945,
  "keywords-F1": 0.22205090827539808,
  "topics-EM": 0.32663316582914576,
  "topics-Partial": 0.41708542713567837,
  "topics-Precision": 0.3458961474036851,
  "topics-Recall": 0.34087102177554435,
  "topics-F1": 0.3412060301507538,
  "Average-EM": 0.22025316455696203,
  "Average-Partial": 0.3367088607594937,
  "Average-F1": 0.2820809570176659,
  "Null-accuracy": 0.023923444976076555
}
```
