# ModernBERT NER - org_country

- model_path: /home/chenqr/models/BERT/ModernBERT-base
- model_dir: /home/chenqr/work/NLU-distillation/experiments/modernbert_ner/org_country
- data_dir: /home/chenqr/work/NLU-distillation/data/processed/org_country/bio
- generated_at: 2026-06-08T11:09:58
- train_samples: 4000
- valid_samples: 500
- test_samples: 500

## Test Metrics

```json
{
  "token_accuracy": 0.9776804875955017,
  "entity_precision": 0.7222222222222222,
  "entity_recall": 0.6658536585365854,
  "entity_f1": 0.6928934010152284,
  "entity_true_count": 410,
  "entity_pred_count": 378,
  "entity_tp_count": 273,
  "label_list": [
    "O",
    "B-INSTITUTION",
    "I-INSTITUTION",
    "B-COUNTRY",
    "I-COUNTRY"
  ],
  "by_entity": {
    "COUNTRY": {
      "tp": 43,
      "pred": 62,
      "true": 65,
      "precision": 0.6935483870967742,
      "recall": 0.6615384615384615,
      "f1": 0.6771653543307087
    },
    "INSTITUTION": {
      "tp": 230,
      "pred": 316,
      "true": 345,
      "precision": 0.7278481012658228,
      "recall": 0.6666666666666666,
      "f1": 0.6959152798789712
    }
  }
}
```
