# Four-task NLU Data and Evaluation Parser Audit - 2026-06-09

Scope: `data_type`, `机构和国家`, `时间和if值`, `topic和keywords`; `作者和机构` excluded because its author variant issue was already fixed separately.

## Training Data vs Eval Format

| task | train rows | eval rows | expected fields | eval fields | positives | empty | top issues |
| --- | ---: | ---: | --- | --- | ---: | ---: | --- |
| data_type | 5000 | 310 | `data_type` | `data_type` | 3000 | 2000 | data_type_empty_with_explicit_marker:103 |
| 机构和国家 | 5000 | 235 | `机构名称, 国家` | `国家, 机构名称` | 3000 | 2000 | 国家_not_visible_in_query:634, country_value_in_机构名称:163, 机构名称_not_visible_in_query:77 |
| 时间和if值 | 5000 | 235 | `filter_start_datetime, filter_end_datetime, filter_start_if, filter_end_if` | `filter_end_datetime, filter_end_if, filter_start_datetime, filter_start_if` | 3000 | 2000 | none |
| topic和keywords | 5000 | 183 | `topics, keywords` | `keywords, topics` | 3000 | 2000 | keywords_uses_comma_separator:2723, keywords_not_visible_in_query:2538, topics_not_visible_in_query:701, topics_uses_comma_separator:532, keywords_too_many_items_gt10:140, topics_duplicate_items:1, keywords_duplicate_items:1 |

### data_type training data

Non-empty fields: data_type=3000
Issues: data_type_empty_with_explicit_marker=103
- Sample `data_type_empty_with_explicit_marker`:
  - `{"input": "中国本土企业在AKT抑制剂领域的早期研发布局有哪些？包括处于临床前或早期临床阶段的创新药物及其特点。研究类型：Review,Basic_Research。发布时间：2021年-至今。影响因子(IF)值:无限制。", "output": {"data_type": ""}}`
  - `{"input": "宫颈腺癌的诊断标准、分期指南及最新治疗策略有哪些？研究类型：Review。发布时间：近3年。影响因子(IF)值:无限制。", "output": {"data_type": ""}}`
  - `{"input": "万和假体植入手术的基本流程、术前准备和术后管理要点是什么？研究类型：Review。发布时间：无限制。影响因子(IF)值:无限制。", "output": {"data_type": ""}}`

### 机构和国家 training data

Non-empty fields: 机构名称=2295, 国家=1792
Issues: 国家_not_visible_in_query=634, country_value_in_机构名称=163, 机构名称_not_visible_in_query=77
- Sample `国家_not_visible_in_query`:
  - `{"input": "北京积水潭医院聊城医院抗衰老与形体修复医学中心护士工作流程规范（含护士长、各班次、手术室、门诊及围手术期护理与健康教育流程）", "bad": "中国", "output": {"机构名称": "北京积水潭医院", "国家": "中国"}}`
  - `{"input": "患者因“咳嗽咳痰伴背痛4月余，加重3天”入院，2026.02.28 启东市第三人民医院 胸部CT（TCT2602280543）：右肺下叶占位伴周围阻塞性肺炎，T5椎体骨质破坏，两侧胸腔少量积液，肿瘤性病变可能大。2026-03-02 我院临检检验报告：白细胞 13.0x10^9/L↑，中性粒细胞绝对值 9.58x10^9/L↑，C反应蛋白 78.6mg/L↑，血清淀粉样蛋白A 161.4mg/L↑。2026-03-03 上海正影医学影像诊断中心 PETCT（PCT0006416）：1.a.右肺下叶背段团块灶伴FDG代谢异常增高；T5/T6椎间隙及椎体两旁软组织灶伴FDG代谢异常增高，病灶累及T", "bad": "中国", "output": {"机构名称": "启东市第三人民医院", "国家": "中国"}}`
  - `{"input": "20世纪50年代中华医学杂志发表的关于儿童片山热的研究文献", "bad": "中国", "output": {"机构名称": "中华医学杂志", "国家": "中国"}}`
- Sample `country_value_in_机构名称`:
  - `{"input": "美国INSTI用药趋势分析", "bad": "美国", "output": {"机构名称": "美国", "国家": "美国"}}`
  - `{"input": "三阴性乳腺癌的一线和二线治疗方案及中国与美国临床诊疗指南推荐对比", "bad": "中国", "output": {"机构名称": "中国；美国", "国家": "中国；美国"}}`
  - `{"input": "三阴性乳腺癌的一线和二线治疗方案及中国与美国临床诊疗指南推荐对比", "bad": "美国", "output": {"机构名称": "中国；美国", "国家": "中国；美国"}}`
- Sample `机构名称_not_visible_in_query`:
  - `{"input": "hongkong Wenlei Peng", "bad": "香港", "output": {"机构名称": "香港", "国家": "香港"}}`
  - `{"input": "美国一项系统回顾了1963年至2015年间54项研究的Meta分析显示，住院医师抑郁症状的总体患病率高达28.8%，且随时间推移呈上升趋势[2]。马来西亚一家三级培训医院的横断面研究发现，25.1%的住院医师存在抑郁症状[3]。沙特阿拉伯麦加地区的研究报道显示，住院医师的焦虑和抑郁的患病率分别为39.5%和20.9%[4]。立陶宛关于医务工作者自杀倾向的研究发现，30.4%存在终生自杀风险，11.4%有过自杀计划，2.5%曾自杀未遂；回归分析确认：缺乏稳定关系、高抑郁和高焦虑是重要风险因素[5]。沙特阿拉伯的一项研究结果显示，81.22%的住院医师在至少一个疲劳综合征子量表上得分较高[16]。", "bad": "巴勒斯坦针对250名住院医师和实习生的研究", "output": {"机构名称": "马来西亚一家三级培训医院；沙特阿拉伯麦加地区的研究；立陶宛关于医务工作者自杀倾向的研究；巴西全国性调查；肯尼亚的一项横断面研究；巴勒斯坦针对250名住院医师和实习生的研究；沙特阿拉伯一项覆盖426名住院医生的研究；美国多项研究；美国培训生住院医师和研究员的大规模研究", "国家": "马来西亚；沙特阿拉伯；立陶宛；巴西；肯尼亚；巴勒斯坦；沙特阿拉伯；美国；美国"}}`
  - `{"input": "美国一项系统回顾了1963年至2015年间54项研究的Meta分析显示，住院医师抑郁症状的总体患病率高达28.8%，且随时间推移呈上升趋势[2]。马来西亚一家三级培训医院的横断面研究发现，25.1%的住院医师存在抑郁症状[3]。沙特阿拉伯麦加地区的研究报道显示，住院医师的焦虑和抑郁的患病率分别为39.5%和20.9%[4]。立陶宛关于医务工作者自杀倾向的研究发现，30.4%存在终生自杀风险，11.4%有过自杀计划，2.5%曾自杀未遂；回归分析确认：缺乏稳定关系、高抑郁和高焦虑是重要风险因素[5]。沙特阿拉伯的一项研究结果显示，81.22%的住院医师在至少一个疲劳综合征子量表上得分较高[16]。", "bad": "美国多项研究", "output": {"机构名称": "马来西亚一家三级培训医院；沙特阿拉伯麦加地区的研究；立陶宛关于医务工作者自杀倾向的研究；巴西全国性调查；肯尼亚的一项横断面研究；巴勒斯坦针对250名住院医师和实习生的研究；沙特阿拉伯一项覆盖426名住院医生的研究；美国多项研究；美国培训生住院医师和研究员的大规模研究", "国家": "马来西亚；沙特阿拉伯；立陶宛；巴西；肯尼亚；巴勒斯坦；沙特阿拉伯；美国；美国"}}`

### 时间和if值 training data

Non-empty fields: filter_start_datetime=2971, filter_end_datetime=112, filter_start_if=642, filter_end_if=0
Issues: none detected by these checks.

### topic和keywords training data

Non-empty fields: topics=2996, keywords=2976
Issues: keywords_uses_comma_separator=2723, keywords_not_visible_in_query=2538, topics_not_visible_in_query=701, topics_uses_comma_separator=532, keywords_too_many_items_gt10=140, topics_duplicate_items=1, keywords_duplicate_items=1
- Sample `keywords_uses_comma_separator`:
  - `{"input": "影响母乳喂养持续时间的相关因素有哪些？", "output": {"topics": "母乳喂养", "keywords": "持续时间, 影响因素"}}`
  - `{"input": "人尿激肽原酶（尤瑞克林）治疗进展性脑梗死或早期神经功能恶化（END）的临床研究证据及疗效评估。", "output": {"topics": "人尿激肽原酶（尤瑞克林）,进展性脑梗死,早期神经功能恶化（END）", "keywords": "临床研究证据,疗效评估"}}`
  - `{"input": "制动时间与关节僵硬的临床阈值及危险因素分析", "output": {"topics": "关节僵硬", "keywords": "制动时间, 临床阈值, 危险因素"}}`
- Sample `keywords_not_visible_in_query`:
  - `{"input": "影响母乳喂养持续时间的相关因素有哪些？", "bad": "影响因素", "output": {"topics": "母乳喂养", "keywords": "持续时间, 影响因素"}}`
  - `{"input": "针对孕29+6周、宫颈长度18mm伴宫缩、胎儿侧脑室囊肿及腹围位于第5.1百分位的病例，评估羊膜腔穿刺的临床必要性及术后早产与并发症风险。", "bad": "术后风险", "output": {"topics": "羊膜腔穿刺,早产,并发症", "keywords": "孕29+6周,宫颈长度18mm伴宫缩,胎儿侧脑室囊肿,腹围位于第5.1百分位,临床必要性,术后风险"}}`
  - `{"input": "PPAR信号通路与", "bad": "机制", "output": {"topics": "PPAR信号通路", "keywords": "机制, 相互作用, 疾病关联"}}`
- Sample `topics_uses_comma_separator`:
  - `{"input": "人尿激肽原酶（尤瑞克林）治疗进展性脑梗死或早期神经功能恶化（END）的临床研究证据及疗效评估。", "output": {"topics": "人尿激肽原酶（尤瑞克林）,进展性脑梗死,早期神经功能恶化（END）", "keywords": "临床研究证据,疗效评估"}}`
  - `{"input": "针对孕29+6周、宫颈长度18mm伴宫缩、胎儿侧脑室囊肿及腹围位于第5.1百分位的病例，评估羊膜腔穿刺的临床必要性及术后早产与并发症风险。", "output": {"topics": "羊膜腔穿刺,早产,并发症", "keywords": "孕29+6周,宫颈长度18mm伴宫缩,胎儿侧脑室囊肿,腹围位于第5.1百分位,临床必要性,术后风险"}}`
  - `{"input": "检索关于“HLH、IMCD样淋巴增生与NMDA受体自身免疫性脑炎”患者的鉴别诊断流程，要求证据为“近10年相关临床指南”中关于“感染”的“红旗征象”或“排除标准”，或“近3年发表于IF≥5期刊、关于其诊断策略与结局的真实世界研究或系统评价”。", "output": {"topics": "HLH, IMCD样淋巴增生, NMDA受体自身免疫性脑炎", "keywords": "鉴别诊断, 感染, 红旗征象, 排除标准, 诊断策略, 结局, 临床指南, 真实世界研究, 系统评价, 近10年, 近3年, IF≥5"}}`
- Sample `keywords_too_many_items_gt10`:
  - `{"input": "检索关于“HLH、IMCD样淋巴增生与NMDA受体自身免疫性脑炎”患者的鉴别诊断流程，要求证据为“近10年相关临床指南”中关于“感染”的“红旗征象”或“排除标准”，或“近3年发表于IF≥5期刊、关于其诊断策略与结局的真实世界研究或系统评价”。", "count": 12, "output": {"topics": "HLH, IMCD样淋巴增生, NMDA受体自身免疫性脑炎", "keywords": "鉴别诊断, 感染, 红旗征象, 排除标准, 诊断策略, 结局, 临床指南, 真实世界研究, 系统评价, 近10年, 近3年, IF≥5"}}`
  - `{"input": "检索关于“小肠细菌过度生长（SIBO）”在“癌症患者慢性腹泻”背景下的诊断标准，要求证据为“近10年临床指南或专家共识”中关于诊断路径的部分，或“近3年发表于IF≥5期刊、关于其氢呼气试验或小肠液培养的系统评价或诊断准确性研究”。", "count": 11, "output": {"topics": "小肠细菌过度生长 (SIBO)", "keywords": "癌症患者, 慢性腹泻, 诊断标准, 诊断路径, 氢呼气试验, 小肠液培养, 系统评价, 诊断准确性研究, 近10年临床指南, 近3年文献, IF≥5"}}`
  - `{"input": "检索关于“肿瘤相关性肾功能不全”在“淋巴瘤患者”背景下的诊断与鉴别诊断，要求证据为“近10年肿瘤肾病或血液肿瘤学临床指南”中关于肾功能损害评估的部分，或“近3年发表于IF≥5期刊、关于淋巴瘤肾脏浸润或梗阻性肾病诊断标志物的系统评价或诊断准确性研究”。", "count": 12, "output": {"topics": "肿瘤相关性肾功能不全, 淋巴瘤", "keywords": "诊断, 鉴别诊断, 肾功能损害评估, 肾脏浸润, 梗阻性肾病, 诊断标志物, 临床指南, 系统评价, 诊断准确性研究, 近10年, 近3年, IF≥5"}}`
- Sample `topics_not_visible_in_query`:
  - `{"input": "中国痤疮患者皮肤表面痤疮丙酸杆菌（Cutibacterium acnes, C. acnes）的系统发育型（Phylotype）分布特征研究。", "bad": "痤疮丙酸杆菌 (Cutibacterium acnes)", "output": {"topics": "痤疮丙酸杆菌 (Cutibacterium acnes)", "keywords": "中国, 痤疮患者, 系统发育型 (Phylotype), 分布特征"}}`
  - `{"input": "最近五年内 LIRI 巨噬细胞 溶酶体功能障碍 胞葬作用 研究路径 决策分析 的评论或综述", "bad": "LIRI (Liver Ischemia-Reperfusion Injury)", "output": {"topics": "LIRI (Liver Ischemia-Reperfusion Injury)", "keywords": "巨噬细胞, 溶酶体功能障碍, 胞葬作用, 研究路径, 决策分析, 综述, 评论"}}`
  - `{"input": "检索关于“小肠细菌过度生长（SIBO）”在“癌症患者慢性腹泻”背景下的诊断标准，要求证据为“近10年临床指南或专家共识”中关于诊断路径的部分，或“近3年发表于IF≥5期刊、关于其氢呼气试验或小肠液培养的系统评价或诊断准确性研究”。", "bad": "小肠细菌过度生长 (SIBO)", "output": {"topics": "小肠细菌过度生长 (SIBO)", "keywords": "癌症患者, 慢性腹泻, 诊断标准, 诊断路径, 氢呼气试验, 小肠液培养, 系统评价, 诊断准确性研究, 近10年临床指南, 近3年文献, IF≥5"}}`
- Sample `topics_duplicate_items`:
  - `{"input": "RVO-ME抗VEGF治疗指南；RVO-ME应答不佳处理策略；RVO-ME药物转换推荐；RVO-ME早期疗效评估指南", "output": {"topics": "RVO-ME, RVO-ME", "keywords": "抗VEGF治疗, 应答不佳处理策略, 药物转换, 早期疗效评估"}}`
- Sample `keywords_duplicate_items`:
  - `{"input": "乳腺 S100B 乳铁蛋白 碘 甲状腺激素 调控机制 综述 近10年; 母乳 S100B 乳铁蛋白 吸收利用 机制 综述 近10年", "output": {"topics": "乳腺；母乳", "keywords": "S100B, 乳铁蛋白, 碘, 甲状腺激素, 调控机制, 综述, 近10年；S100B, 乳铁蛋白, 吸收利用, 机制, 综述, 近10年"}}`

## Report Parser Audit

| model | task | samples | F1 | finish | parser-related issues |
| --- | --- | ---: | ---: | --- | --- |
| 0.8B | data_type | 310 | 0.7356 | stop:310 | none |
| 0.8B | 机构和国家 | 235 | 0.1240 | stop:235 | none |
| 0.8B | 时间和if值 | 235 | 0.2410 | stop:235 | none |
| 0.8B | topic和keywords | 183 | 0.5019 | stop:181, length:2 | none |
| 4B | data_type | 310 | 0.8600 | stop:310 | none |
| 4B | 机构和国家 | 235 | 0.6522 | stop:235 | none |
| 4B | 时间和if值 | 235 | 0.7273 | stop:235 | none |
| 4B | topic和keywords | 183 | 0.4406 | stop:183 | none |


## Additional Evaluation Logic Checks

### Re-scoring with comma-aware multi-value splitting

The current `ExtractionEvaluator._split_multi_values` splits multi-value fields only on `；`, `;`, and newlines. A diagnostic comma-aware scorer was run to estimate whether this changes report conclusions.

| model | task | F1 current | F1 comma-aware | EM delta | Partial delta | conclusion |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| 0.8B | data_type | 0.7356 | 0.7356 | 0.0000 | 0.0000 | no effect |
| 0.8B | 机构和国家 | 0.1240 | 0.1240 | 0.0000 | 0.0000 | no F1 effect |
| 0.8B | 时间和if值 | 0.2410 | 0.2410 | 0.0000 | 0.0000 | no effect |
| 0.8B | topic和keywords | 0.5019 | 0.5019 | +0.0246 | +0.0574 | EM/Partial mildly undercount comma-separated exact/list overlap; F1 unchanged |
| 4B | data_type | 0.8600 | 0.8600 | 0.0000 | 0.0000 | no effect |
| 4B | 机构和国家 | 0.6522 | 0.6522 | +0.0217 | +0.0217 | EM/Partial mildly affected; F1 unchanged |
| 4B | 时间和if值 | 0.7273 | 0.7273 | 0.0000 | 0.0000 | no effect |
| 4B | topic和keywords | 0.4406 | 0.4406 | +0.0279 | +0.0418 | EM/Partial mildly undercount comma-separated exact/list overlap; F1 unchanged |

This does not explain the main F1 scores, but the evaluator should probably accept `,` and `，` as list separators for `topics`, `keywords`, `机构名称`, `国家`, and `data_type` if future reports care about EM/Partial.

### data_type explicit marker leak in training data

Among training rows whose output is empty, 103 inputs still contain an explicit `研究类型：...` marker. The missed English source labels are mostly:

| source label in query | count among empty outputs |
| --- | ---: |
| Review | 80 |
| Basic_Research | 19 |
| RCT | 15 |
| Observational_Study | 14 |
| Meta_Analysis/Systematic_Review | 8 |
| Case_Series/Case_Report | 3 |

This is a real training-label error: the query visibly requests research types, but `data_type` was written as empty. The report parser itself did not show an analogous English-label loss in current 0.8B/4B `data_type` reports.

## Audit Conclusions

- `时间和if值`: no structural training-data problem found in this pass; current 0.8B/4B reports have no parser-loss symptom.
- `data_type`: training data has a smaller but real label bug: explicit English `研究类型` markers are sometimes mapped to empty. Needs rebuild/mapping fix before further training.
- `机构和国家`: training data has substantial semantic noise. It includes inferred/standardized country values not visible in query and sometimes puts country/region values into `机构名称`. This conflicts with both the SFT instruction and eval format.
- `topic和keywords`: training data is the noisiest. It uses comma separators despite the instruction saying Chinese semicolons, includes many expanded/normalized values not literally present in query, and sometimes over-extracts long constraint phrases into keywords.
- Current report parsing for these four tasks is mostly internally consistent: raw outputs, parsed outputs, and stored metrics reproduce; no clear field-loss parser bug was found. The main evaluator weakness found is comma separator compatibility for EM/Partial, not F1.
