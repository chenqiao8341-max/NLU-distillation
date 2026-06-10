# NLU Distillation Data Audit - 2026-06-09

Source: `data/processed/*/sft/all.jsonl`, rebuilt from `nlu-data/knows_nlu_20260101_20260603.jsonl` with eval-compatible output fields.

## Summary

| task | rows | positive | empty | field problems | top issues |
|---|---:|---:|---:|---:|---|
| 作者和机构 | 3968 | 1968 | 2000 | 0 | author_has_no_variants: 56 |
| 机构和国家 | 5000 | 3000 | 2000 | 0 | 国家_not_in_query: 614, 机构名称_not_in_query: 76 |
| 时间和if值 | 5000 | 3000 | 2000 | 0 | none |
| data_type | 5000 | 3000 | 2000 | 0 | none |
| topic和keywords | 5000 | 3000 | 2000 | 0 | keywords_not_in_query: 933, topics_not_in_query: 689, keywords_too_many_items: 140, topics_duplicate_items: 1 |

## Notes

- `author_org` has been rebuilt so `author_name` contains only names matched in the query; generated search variants are moved into `author_name英文变体` with `<variant>...</variant>` tags. Author institutions are also kept only when visible in the query.
- Remaining `*_not_in_query` counts in other tasks usually indicate production NLU expanded/standardized a value rather than copied it from the user query. These are risky for strict extractive SFT.
- `topic和keywords` has many values not literally present in the query because production data often stores normalized/expanded terms. This differs from the eval prompt requirement that extracted text must come from query.

## 作者和机构

Rows: 3968; positive: 1968; empty: 2000.
Non-empty fields: author_name=1954, author_name英文变体=1898, author_institution=437
Issues: author_has_no_variants=56
Sample `author_has_no_variants`:
- {"input": "胃癌是最常见的恶性肿瘤之一，2022年全球新发病患者近97万例，死亡近66万例［1］。我国是胃癌高发国家之一，每年新发及死亡病例数占全球患者数量的近一半，统计结果显示我国晚期胃癌患者比例仍明显高于日本、韩国等国家［2］。即便在当前最优一线治疗条件下，晚期胃癌患者的预后仍然较差。转化治疗是指通过系统性抗肿瘤治疗，将初始不可切除的晚期肿瘤降期至可行根治性手术达到R0切除的状态，从而为晚期患者提供潜在治愈机会的治疗策略。在胃癌领域，目前转化治疗主要针对伴有单一或少数不可切除因素的Ⅳ期患者，如腹膜转移、肝转移、远处淋巴结转移及卵巢转移（Krukenberg瘤），主要分布在Yoshida分型中的大多数2型、部分3型及极少数4型［3］。胃癌的转化治疗应区别于新辅助治疗（针对潜在可切除的局部进展期胃癌）和晚期一线治疗（针对不可切除的Ⅳ期胃癌，但以延长生存、控制症状为主要目标，不以转化手术为核心治疗手段）。一、化疗时代胃癌的转化治疗CONVO-GC-1研究评估亚洲多中心Ⅳ期胃癌转化治疗的安全性，并指出无论初始Yoshida分型如何，R0切除患者的中位生存时间均显著延长［4］。GIRCG研究纳入了45例初始不可切除的Ⅳ期胃癌患者，R0切除率达到66.6%［5］。 2017年发表的AIO-FLOT3Ⅱ期研究采用FLOT方案治疗胃癌患者。该研究中B组患者主要为Ⅳ期胃癌中Yoshid
- {"input": "精准的细胞自噬调控作用\n自噬是细胞维持内环境稳态的核心机制，海藻糖是目前公认的、安全有效的天然自噬诱导剂，其自噬调控作用已得到广泛证实。海藻糖诱导自噬的机制主要包括：①抑制mTOR信号通路：mTOR是细胞自噬的核心负调控因子，海藻糖可通过抑制Akt/mTOR信号通路，解除mTOR对自噬起始复合物ULK1/Atg13/FIP200的抑制作用，启动自噬体的形成[135]；②激活AMPK信号通路：AMPK是细胞能量感受器，也是自噬的正调控因子，海藻糖可激活AMPK，通过AMPK/mTOR/ULK1通路进一步促进自噬[136]；③促进自噬流的正常进行：海藻糖不仅能促进自噬体的形成，还能促进自噬体与溶酶体的融合，保证自噬流的完整，避免自噬体累积导致的细胞损伤[137]。\n\n海藻糖的自噬调控作用具有高度的安全性与选择性，不会引发过度自噬导致的细胞死亡，仅在细胞应激状态下增强自噬，清除受损细胞器与错误折叠的蛋白质，维持细胞内环境稳态[138]。研究证实，海藻糖可通过激活自噬，在阿尔茨海默病、帕金森病、亨廷顿舞蹈症等神经退行性疾病模型中，清除细胞内异常聚集的致病蛋白，减轻神经元损伤[139]；在代谢性疾病中，可通过激活自噬改善胰岛素抵抗，减轻肝脏脂质沉积[140]；在心血管疾病中，可通过激活自噬保护心肌细胞，减轻心肌缺血再灌注损伤.请帮我查找出与每段话最相关的参考文献"

## 机构和国家

Rows: 5000; positive: 3000; empty: 2000.
Non-empty fields: 机构名称=2295, 国家=1792
Issues: 国家_not_in_query=614, 机构名称_not_in_query=76
Sample `国家_not_in_query`:
- {"input": "北京积水潭医院聊城医院抗衰老与形体修复医学中心护士工作流程规范（含护士长、各班次、手术室、门诊及围手术期护理与健康教育流程）", "bad": ["中国"], "output": {"机构名称": "北京积水潭医院", "国家": "中国"}}
- {"input": "患者因“咳嗽咳痰伴背痛4月余，加重3天”入院，2026.02.28 启东市第三人民医院 胸部CT（TCT2602280543）：右肺下叶占位伴周围阻塞性肺炎，T5椎体骨质破坏，两侧胸腔少量积液，肿瘤性病变可能大。2026-03-02 我院临检检验报告：白细胞 13.0x10^9/L↑，中性粒细胞绝对值 9.58x10^9/L↑，C反应蛋白 78.6mg/L↑，血清淀粉样蛋白A 161.4mg/L↑。2026-03-03 上海正影医学影像诊断中心 PETCT（PCT0006416）：1.a.右肺下叶背段团块灶伴FDG代谢异常增高；T5/T6椎间隙及椎体两旁软组织灶伴FDG代谢异常增高，病灶累及T5椎体下缘及T6椎体上缘；综上均考虑感染性病变，结核可能，建议病检除外恶性。b.两肺多发结节伴钙化，FDG代谢未见异常增高，考虑良性可能，建议定期随诊。c.两肺散在纤维炎性灶，两侧胸膜增厚，左肺底胸膜钙化，两侧胸腔少量积液。2.a.前列腺两侧外周带多发低密度灶，FDG代谢异常增高，建议活检除外恶性。b.前列腺钙化灶。c.双侧闭孔及腹股沟区多发淋巴结，FDG代谢轻度增高，考虑反应性增生可能大，建议随诊。3.肝右叶囊肿/囊性灶。右肾囊肿/囊性灶。4.颅脑FDG代谢未见异常增高。双侧上颌窦慢性炎症。5.甲状腺两叶密度不均，FDG代谢未见异常，考虑良性表现，建议超声随诊。6.脊柱
Sample `机构名称_not_in_query`:
- {"input": "hongkong Wenlei Peng", "bad": ["香港"], "output": {"机构名称": "香港", "国家": "香港"}}
- {"input": "美国一项系统回顾了1963年至2015年间54项研究的Meta分析显示，住院医师抑郁症状的总体患病率高达28.8%，且随时间推移呈上升趋势[2]。马来西亚一家三级培训医院的横断面研究发现，25.1%的住院医师存在抑郁症状[3]。沙特阿拉伯麦加地区的研究报道显示，住院医师的焦虑和抑郁的患病率分别为39.5%和20.9%[4]。立陶宛关于医务工作者自杀倾向的研究发现，30.4%存在终生自杀风险，11.4%有过自杀计划，2.5%曾自杀未遂；回归分析确认：缺乏稳定关系、高抑郁和高焦虑是重要风险因素[5]。沙特阿拉伯的一项研究结果显示，81.22%的住院医师在至少一个疲劳综合征子量表上得分较高[16]。巴西全国性调查发现，疲劳综合征筛查阳性率为37.0%[17]。肯尼亚的一项横断面研究发现，47.3%的住院医师存在高风险疲劳综合征。巴勒斯坦报道的针对250名住院医师和实习生的研究结果显示，个人相关疲劳和工作相关疲劳的发生率分别高达81.2%和75.2%。在沙特阿拉伯一项覆盖426名住院医生的研究报告称,81.22%的参与者在至少一个疲劳综合征子量表上得分较高[8]。在美国，多项研究也证实了疲劳综合征的高发。纳入1118名住院医师的全国性调查结果显示，42%的住院医师存在疲劳综合征[9]。针对美国培训生住院医师和研究员的大规模研究发现，50.0%的培训生有疲劳综合征症状，

## 时间和if值

Rows: 5000; positive: 3000; empty: 2000.
Non-empty fields: filter_start_datetime=2971, filter_end_datetime=112, filter_start_if=642, filter_end_if=0
Issues: none detected by structural checks.

## data_type

Rows: 5000; positive: 3000; empty: 2000.
Non-empty fields: data_type=3000
Issues: none detected by structural checks.

## topic和keywords

Rows: 5000; positive: 3000; empty: 2000.
Non-empty fields: topics=2996, keywords=2976
Issues: keywords_not_in_query=933, topics_not_in_query=689, keywords_too_many_items=140, topics_duplicate_items=1, keywords_duplicate_items=1
Sample `keywords_not_in_query`:
- {"input": "影响母乳喂养持续时间的相关因素有哪些？", "bad": ["影响因素"], "output": {"topics": "母乳喂养", "keywords": "持续时间, 影响因素"}}
- {"input": "针对孕29+6周、宫颈长度18mm伴宫缩、胎儿侧脑室囊肿及腹围位于第5.1百分位的病例，评估羊膜腔穿刺的临床必要性及术后早产与并发症风险。", "bad": ["术后风险"], "output": {"topics": "羊膜腔穿刺,早产,并发症", "keywords": "孕29+6周,宫颈长度18mm伴宫缩,胎儿侧脑室囊肿,腹围位于第5.1百分位,临床必要性,术后风险"}}
Sample `keywords_too_many_items`:
- {"input": "检索关于“HLH、IMCD样淋巴增生与NMDA受体自身免疫性脑炎”患者的鉴别诊断流程，要求证据为“近10年相关临床指南”中关于“感染”的“红旗征象”或“排除标准”，或“近3年发表于IF≥5期刊、关于其诊断策略与结局的真实世界研究或系统评价”。", "count": 12, "output": {"topics": "HLH, IMCD样淋巴增生, NMDA受体自身免疫性脑炎", "keywords": "鉴别诊断, 感染, 红旗征象, 排除标准, 诊断策略, 结局, 临床指南, 真实世界研究, 系统评价, 近10年, 近3年, IF≥5"}}
- {"input": "检索关于“小肠细菌过度生长（SIBO）”在“癌症患者慢性腹泻”背景下的诊断标准，要求证据为“近10年临床指南或专家共识”中关于诊断路径的部分，或“近3年发表于IF≥5期刊、关于其氢呼气试验或小肠液培养的系统评价或诊断准确性研究”。", "count": 11, "output": {"topics": "小肠细菌过度生长 (SIBO)", "keywords": "癌症患者, 慢性腹泻, 诊断标准, 诊断路径, 氢呼气试验, 小肠液培养, 系统评价, 诊断准确性研究, 近10年临床指南, 近3年文献, IF≥5"}}
Sample `topics_not_in_query`:
- {"input": "中国痤疮患者皮肤表面痤疮丙酸杆菌（Cutibacterium acnes, C. acnes）的系统发育型（Phylotype）分布特征研究。", "bad": ["痤疮丙酸杆菌 (Cutibacterium acnes)"], "output": {"topics": "痤疮丙酸杆菌 (Cutibacterium acnes)", "keywords": "中国, 痤疮患者, 系统发育型 (Phylotype), 分布特征"}}
- {"input": "最近五年内 LIRI 巨噬细胞 溶酶体功能障碍 胞葬作用 研究路径 决策分析 的评论或综述", "bad": ["LIRI (Liver Ischemia-Reperfusion Injury)"], "output": {"topics": "LIRI (Liver Ischemia-Reperfusion Injury)", "keywords": "巨噬细胞, 溶酶体功能障碍, 胞葬作用, 研究路径, 决策分析, 综述, 评论"}}
Sample `topics_duplicate_items`:
- {"input": "RVO-ME抗VEGF治疗指南；RVO-ME应答不佳处理策略；RVO-ME药物转换推荐；RVO-ME早期疗效评估指南", "output": {"topics": "RVO-ME, RVO-ME", "keywords": "抗VEGF治疗, 应答不佳处理策略, 药物转换, 早期疗效评估"}}
