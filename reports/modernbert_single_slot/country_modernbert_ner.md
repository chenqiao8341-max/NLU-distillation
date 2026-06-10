# ModernBERT NER - country

- model_path: /home/qiao/models/BERT/ModernBERT-base
- model_dir: /home/qiao/work/NLU-distillation/experiments/modernbert_single_slot/country
- data_dir: /home/qiao/work/NLU-distillation/data/processed_single/country/bio
- generated_at: 2026-06-10T16:40:51
- train_samples: 4000
- valid_samples: 500
- test_samples: 200

## Test Metrics

```json
{
  "token_accuracy": 0.9953948107379536,
  "entity_precision": 0.972972972972973,
  "entity_recall": 0.6101694915254238,
  "entity_f1": 0.7500000000000001,
  "entity_true_count": 59,
  "entity_pred_count": 37,
  "entity_tp_count": 36,
  "label_list": [
    "O",
    "B-COUNTRY",
    "I-COUNTRY"
  ],
  "by_entity": {
    "COUNTRY": {
      "tp": 36,
      "pred": 37,
      "true": 59,
      "precision": 0.972972972972973,
      "recall": 0.6101694915254238,
      "f1": 0.7500000000000001
    }
  }
}
```

## Test Metrics By Source

```json
{
  "eval_org_country": {
    "token_accuracy": 0.9953948107379536,
    "entity_precision": 0.972972972972973,
    "entity_recall": 0.6101694915254238,
    "entity_f1": 0.7500000000000001,
    "entity_true_count": 59,
    "entity_pred_count": 37,
    "entity_tp_count": 36,
    "label_list": [
      "O",
      "B-COUNTRY",
      "I-COUNTRY"
    ],
    "by_entity": {
      "COUNTRY": {
        "tp": 36,
        "pred": 37,
        "true": 59,
        "precision": 0.972972972972973,
        "recall": 0.6101694915254238,
        "f1": 0.7500000000000001
      }
    }
  }
}
```
