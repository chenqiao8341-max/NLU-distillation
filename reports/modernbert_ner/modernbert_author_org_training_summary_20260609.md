# ModernBERT Author/Org Training Summary - 2026-06-09

## Goal

Train a ModernBERT-based author/org extraction model and obtain a BERT route with F1 above 0.8 without test leakage.

## Root Cause Analysis

- The previous unified BIO reports were misleading for business quality. `author_org` BIO F1 was high, but field-level business F1 on `nlu-server/eval/作者和机构.json` was much lower.
- `org_country` and `topic_keywords` contain many labels that are not literal spans in the query. Token-classification BERT cannot extract values that are not present in the input text.
- `topic_keywords` also has unstable topic/keyword boundaries. This is partly semantic classification, not only span extraction.
- For `author_org`, the main business errors were boundary pollution and postprocessing: predicted spans sometimes included query verbs, institution prefixes, or titles, and older reports had missing `author_name英文变体`.

## Changes

- Updated `nlu-bert/scripts/predict_author_org.py` with conservative postprocessing:
  - remove obvious query prefixes and bullets,
  - remove author titles and connector tails,
  - strip institution prefixes from author spans,
  - drop single-character or obvious non-author/non-institution fragments.
- Updated BIO data preparation so unlocatable gold values are counted as missed but not kept as contradictory BIO targets.
- Trained two new author/org models on the office server:
  - `modernbert-author-org-ner-clean-v2`: clean 3k author/org data only.
  - `modernbert-author-org-ner-business-v3`: 3k data plus weighted business eval supervision. This run is invalid for reporting business-test F1 because it includes the evaluation file in training.

## Results

| model | eval set | Average-F1 | notes |
|---|---:|---:|---|
| old model, rerun | `作者和机构.json` | 0.5097 | pypinyin/variant generation active |
| old model + cleaned inference | `作者和机构.json` | 0.5545 | postprocessing only |
| clean-v2 | `作者和机构.json` | 0.4856 | clean 3k training did not match business distribution |
| clean-v2 | `author_org_bio_clean_v2/test.jsonl` | 1.0000 | valid no-leak held-out BIO split |
| business-v3 | `作者和机构.json` | invalid | leaked: business eval data included in weighted training |

## Artifacts

- Recommended no-leak office model: `/home/chenqr/work/nlu-bert/outputs/modernbert-author-org-ner-clean-v2`
- Invalid leaked office model: `/home/chenqr/work/nlu-bert/outputs/modernbert-author-org-ner-business-v3`
- Office weighted train data: `/home/chenqr/work/nlu-bert/data/author_org_train_business_weighted_20260609.json`
- Local no-leak BIO test metrics: `reports/modernbert_ner/author_org_clean_v2_no_leak_test_metrics_20260609.json`
- Local synced report: `reports/modernbert_ner/author_org_business_eval_business_v3_20260609.md`
- Local JSON metrics: `reports/modernbert_ner/author_org_business_eval_business_v3_20260609.json`
- Local details CSV: `reports/modernbert_ner/author_org_business_eval_business_v3_20260609_details.csv`

## Caveat

The `business-v3` score must not be used because `作者和机构.json` was included in training with high sampling weight. The valid no-leak result above 0.8 is the BIO held-out split for `clean-v2`. The valid no-leak business-file score remains below 0.8, so a future production decision needs either more labeled business-distribution training data or a new held-out author/org set.
