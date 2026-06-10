# ModernBERT Author/Org Business Evaluation

- model_dir: /home/chenqr/work/nlu-bert/outputs/modernbert-author-org-ner
- dataset: /home/chenqr/work/nlu-server/eval/作者和机构.json
- generated_at: 2026-06-09T04:24:15
- total_samples: 111

## Metrics

```json
{
  "author-name-EM": 0.5106382978723404,
  "author-name-Partial": 0.6595744680851063,
  "author-name-Precision": 0.5283687943262411,
  "author-name-Recall": 0.5425531914893617,
  "author-name-F1": 0.5319148936170213,
  "author-name英文变体-EM": 0.425531914893617,
  "author-name英文变体-Partial": 0.6170212765957447,
  "author-name英文变体-Precision": 0.630713362565678,
  "author-name英文变体-Recall": 0.6247044917257684,
  "author-name英文变体-F1": 0.6144164500316212,
  "author-institution-EM": 0.4782608695652174,
  "author-institution-Partial": 0.6521739130434783,
  "author-institution-Precision": 0.4782608695652174,
  "author-institution-Recall": 0.4782608695652174,
  "author-institution-F1": 0.4782608695652174,
  "Average-EM": 0.4700854700854701,
  "Average-Partial": 0.6410256410256411,
  "Average-F1": 0.5545091722349247,
  "Null-accuracy": 0.9473684210526315
}
```

## Notes

- This evaluates final business fields on `nlu-server/eval/作者和机构.json`, not BIO token labels.
- `author_name英文变体` is generated after BERT extracts `author_name`.
- Empty-vs-empty cases contribute only to `Null-accuracy`; content metrics exclude both-empty cases.
