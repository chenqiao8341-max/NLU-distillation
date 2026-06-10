# ModernBERT NER - institution

- model_path: /home/qiao/models/BERT/ModernBERT-base
- model_dir: /home/qiao/work/NLU-distillation/experiments/modernbert_single_slot/institution
- data_dir: /home/qiao/work/NLU-distillation/data/processed_single/institution/bio
- generated_at: 2026-06-10T16:40:47
- train_samples: 7176
- valid_samples: 896
- test_samples: 400

## Test Metrics

```json
{
  "token_accuracy": 0.9818682128642328,
  "entity_precision": 0.65,
  "entity_recall": 0.9,
  "entity_f1": 0.7548387096774194,
  "entity_true_count": 130,
  "entity_pred_count": 180,
  "entity_tp_count": 117,
  "label_list": [
    "O",
    "B-INSTITUTION",
    "I-INSTITUTION"
  ],
  "by_entity": {
    "INSTITUTION": {
      "tp": 117,
      "pred": 180,
      "true": 130,
      "precision": 0.65,
      "recall": 0.9,
      "f1": 0.7548387096774194
    }
  }
}
```

## Test Metrics By Source

```json
{
  "eval_author_org": {
    "token_accuracy": 0.9915269042627534,
    "entity_precision": 0.7126436781609196,
    "entity_recall": 0.9393939393939394,
    "entity_f1": 0.8104575163398693,
    "entity_true_count": 66,
    "entity_pred_count": 87,
    "entity_tp_count": 62,
    "label_list": [
      "O",
      "B-INSTITUTION",
      "I-INSTITUTION"
    ],
    "by_entity": {
      "INSTITUTION": {
        "tp": 62,
        "pred": 87,
        "true": 66,
        "precision": 0.7126436781609196,
        "recall": 0.9393939393939394,
        "f1": 0.8104575163398693
      }
    }
  },
  "eval_org_country": {
    "token_accuracy": 0.9694485005054476,
    "entity_precision": 0.5913978494623656,
    "entity_recall": 0.859375,
    "entity_f1": 0.7006369426751594,
    "entity_true_count": 64,
    "entity_pred_count": 93,
    "entity_tp_count": 55,
    "label_list": [
      "O",
      "B-INSTITUTION",
      "I-INSTITUTION"
    ],
    "by_entity": {
      "INSTITUTION": {
        "tp": 55,
        "pred": 93,
        "true": 64,
        "precision": 0.5913978494623656,
        "recall": 0.859375,
        "f1": 0.7006369426751594
      }
    }
  }
}
```
