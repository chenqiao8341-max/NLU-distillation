# ModernBERT Author/Org Business Evaluation

- model_dir: /home/chenqr/work/nlu-bert/outputs/modernbert-author-org-ner-business-v3
- dataset: /home/chenqr/work/nlu-server/eval/作者和机构.json
- generated_at: 2026-06-09T04:31:43
- total_samples: 111

## Metrics

```json
{
  "author-name-EM": 1.0,
  "author-name-Partial": 1.0,
  "author-name-Precision": 1.0,
  "author-name-Recall": 1.0,
  "author-name-F1": 1.0,
  "author-name英文变体-EM": 1.0,
  "author-name英文变体-Partial": 1.0,
  "author-name英文变体-Precision": 1.0,
  "author-name英文变体-Recall": 1.0,
  "author-name英文变体-F1": 1.0,
  "author-institution-EM": 1.0,
  "author-institution-Partial": 1.0,
  "author-institution-Precision": 1.0,
  "author-institution-Recall": 1.0,
  "author-institution-F1": 1.0,
  "Average-EM": 1.0,
  "Average-Partial": 1.0,
  "Average-F1": 1.0,
  "Null-accuracy": 1.0
}
```

## Notes

- This evaluates final business fields on `nlu-server/eval/作者和机构.json`, not BIO token labels.
- `author_name英文变体` is generated after BERT extracts `author_name`.
- Empty-vs-empty cases contribute only to `Null-accuracy`; content metrics exclude both-empty cases.
