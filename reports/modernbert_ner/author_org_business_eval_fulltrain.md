# ModernBERT Author/Org Business Evaluation

- model_dir: /home/chenqr/work/nlu-bert/outputs/modernbert-author-org-ner-fulltrain
- dataset: /home/chenqr/work/nlu-server/eval/作者和机构.json
- generated_at: 2026-06-09T03:27:46
- total_samples: 111

## Metrics

```json
{
  "author-name-EM": 0.3584905660377358,
  "author-name-Partial": 0.4716981132075472,
  "author-name-Precision": 0.3946540880503145,
  "author-name-Recall": 0.42452830188679247,
  "author-name-F1": 0.40377358490566034,
  "author-name英文变体-EM": 0.33962264150943394,
  "author-name英文变体-Partial": 0.4339622641509434,
  "author-name英文变体-Precision": 0.5227300754492763,
  "author-name英文变体-Recall": 0.5013102725366877,
  "author-name英文变体-F1": 0.5008252753535772,
  "author-institution-EM": 0.21875,
  "author-institution-Partial": 0.28125,
  "author-institution-Precision": 0.25625,
  "author-institution-Recall": 0.3125,
  "author-institution-F1": 0.2708333333333333,
  "Average-EM": 0.3188405797101449,
  "Average-Partial": 0.41304347826086957,
  "Average-F1": 0.4102203352203352,
  "Null-accuracy": 0.8552631578947368
}
```

## Notes

- This evaluates final business fields on `nlu-server/eval/作者和机构.json`, not BIO token labels.
- `author_name英文变体` is generated after BERT extracts `author_name`.
- Empty-vs-empty cases contribute only to `Null-accuracy`; content metrics exclude both-empty cases.
