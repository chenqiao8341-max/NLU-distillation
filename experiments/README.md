# Experiments

训练和评测运行建议统一放这里。

```text
experiments/
  runs/          # 每次运行的配置、日志、checkpoint 索引
  wandb/         # wandb 离线或本地缓存
  tensorboard/   # tensorboard event 文件
```

LLaMA-Factory 当前配置里已有：

```yaml
report_to: none
```

后续可以切换为 `wandb`、`tensorboard`、`swanlab` 或 `mlflow`。
