# Cleaned Four-task Training Data Audit - 2026-06-09

| task | rows | positive | empty | non-empty fields | top issues |
| --- | ---: | ---: | ---: | --- | --- |
| data_type | 5000 | 3000 | 2000 | data_type=3000 | none |
| 机构和国家 | 5000 | 3000 | 2000 | 机构名称=2245, 国家=1349 | none |
| 时间和if值 | 5000 | 3000 | 2000 | filter_start_datetime=2973, filter_end_datetime=117, filter_start_if=681, filter_end_if=2 | none |
| topic和keywords | 5000 | 3000 | 2000 | topics=2764, keywords=2862 | keywords_too_many_items_gt10:52, topics_too_many_items_gt10:1 |

## data_type

Issues: none

## 机构和国家

Issues: none

## 时间和if值

Issues: none

## topic和keywords

Issues: keywords_too_many_items_gt10=52, topics_too_many_items_gt10=1
- Sample `keywords_too_many_items_gt10`:
  - `{"input": "由这篇精神分裂症加速衰老系统综述引出的问题是：170 篇文献提示死亡率、痴呆风险、BrainAGE、认知下降、端粒缩短和炎症/氧化应激信号后，哪些 SCZ 患者需要更早纳入认知和躯体老化监测？请结合长期随访、躯体共病和早发精神病管理文献，给出分层依据和不确定性。", "count": 14, "output": {"topics": "精神分裂症", "keywords": "加速衰老；死亡率；痴呆风险；BrainAGE；认知下降；端粒缩短；炎症；氧化应激；长期随访；躯体共病；早发精神病；躯体老化监测；分层依据；不确定性"}}`
  - `{"input": "子宫内膜异位症（EMs）患者子宫内膜孕激素抵抗导致反复种植失败的分子机制研究，重点探讨炎症因子（IL-1β、COX-2）对孕激素受体（PR）亚型（PR-A/PR-B）比例失衡、整合素β3（integrin β3）及白血病抑制因子（LIF）表达下调及蜕膜化障碍的影响。", "count": 12, "output": {"topics": "子宫内膜异位症（EMs）", "keywords": "孕激素抵抗；反复种植失败；分子机制；炎症因子；IL-1β；COX-2；孕激素受体；PR-A/PR-B；整合素β3；白血病抑制因子；LIF；蜕膜化障碍"}}`
  - `{"input": "胃肠道肿瘤（胃癌、结直肠癌）在全球及中国（特别是浙江省）的最新流行病学数据（发病率、死亡率、趋势），以及传统筛查方法（如内镜）在依从性、资源消耗、漏诊率等方面的具体痛点和挑战。研究类型：Review/Observational_Study。发布时间：2020年-至今。研究类型：Review/Observational_Study。发布时间：2020年-至今。影响因子(IF)值:无限制。", "count": 14, "output": {"topics": "胃肠道肿瘤；胃癌；结直肠癌", "keywords": "全球；中国；浙江省；流行病学数据；发病率；死亡率；趋势；筛查方法；内镜；依从性；资源消耗；漏诊率；痛点；挑战"}}`
- Sample `topics_too_many_items_gt10`:
  - `{"input": "非霍奇金淋巴瘤合并脓毒血症、感染性休克、真菌血流感染、真菌性尿路感染及急性肾衰竭患者，在呼吸衰竭、心律失常、贫血、低血糖及电解质紊乱背景下，使用卡泊芬净进行抗感染治疗的临床安全性与有效性评价。", "count": 12, "output": {"topics": "非霍奇金淋巴瘤；脓毒血症；感染性休克；真菌血流感染；真菌性尿路感染；急性肾衰竭；呼吸衰竭；心律失常；贫血；低血糖；电解质紊乱；卡泊芬净", "keywords": "抗感染治疗；临床安全性；有效性评价"}}`

