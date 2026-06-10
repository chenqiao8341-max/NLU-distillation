# ModernBERT Author/Org Business Evaluation

- model_dir: /home/chenqr/work/nlu-bert/outputs/modernbert-author-org-ner-clean-v2
- dataset: /home/chenqr/work/nlu-server/eval/作者和机构.json
- generated_at: 2026-06-09T04:27:09
- total_samples: 111

## Metrics

```json
{
  "author-name-EM": 0.4444444444444444,
  "author-name-Partial": 0.6666666666666666,
  "author-name-Precision": 0.4888888888888889,
  "author-name-Recall": 0.4666666666666667,
  "author-name-F1": 0.47407407407407404,
  "author-name英文变体-EM": 0.4222222222222222,
  "author-name英文变体-Partial": 0.4888888888888889,
  "author-name英文变体-Precision": 0.6692704826038159,
  "author-name英文变体-Recall": 0.5667901234567901,
  "author-name英文变体-F1": 0.5999198332531666,
  "author-institution-EM": 0.3076923076923077,
  "author-institution-Partial": 0.6153846153846154,
  "author-institution-Precision": 0.3076923076923077,
  "author-institution-Recall": 0.3076923076923077,
  "author-institution-F1": 0.3076923076923077,
  "Average-EM": 0.4051724137931034,
  "Average-Partial": 0.5862068965517241,
  "Average-F1": 0.4856010847390158,
  "Null-accuracy": 0.9517543859649122
}
```

## Notes

- This evaluates final business fields on `nlu-server/eval/作者和机构.json`, not BIO token labels.
- `author_name英文变体` is generated after BERT extracts `author_name`.
- Empty-vs-empty cases contribute only to `Null-accuracy`; content metrics exclude both-empty cases.
