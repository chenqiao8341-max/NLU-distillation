# author_org Schema

## Input

- `query` or `question`: 用户原始问题。

## Target

- `author_name`: 作者名。
- `author_name_en_variants`: 作者英文变体。ModernBERT 路线建议由规则或词典补齐，不直接交给 NER 模型生成。
- `author_institution`: 作者机构。

## Existing Assets

- Legacy project: `/home/qiao/work/nlu-bert`
- Eval data: `/home/qiao/work/nlu-server/eval/作者和机构.json`
- Expanded train data: `/home/qiao/work/nlu-server/eval/作者和机构_互联网扩展3k.json`
- Existing model: `/home/qiao/work/nlu-bert/outputs/modernbert-author-org-ner`
