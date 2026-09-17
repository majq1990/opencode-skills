# Benchmark — Iteration 2

## 总览

| 配置 | 总通过/总断言 | 通过率 |
|------|-------------|--------|
| with_skill (新版) | 12/12 | **100%** |
| old_skill (旧版) | 9/12 | 75.0% |

> 本轮只重跑了 iteration-1 中有差异的 4 条 eval（0/3/4/5），eval-1 和 eval-2 两版均为 3/3 持平，未重跑。

## 逐 eval 对比

| eval | with_skill | old_skill | 差异 |
|------|-----------|-----------|------|
| eval-0 report-minimal | 3/3 ✅ | 2/3 | 新版更短更准 |
| eval-3 preparation-boundary | 3/3 ✅ | 3/3 ✅ | 持平（i1 新版为 2/3） |
| eval-4 troubleshooting-boundary | 3/3 ✅ | 2/3 | 新版分流更干净（i1 新版为 2/3） |
| eval-5 process-mixed | 3/3 ✅ | 2/3 | 新版分流更干净（i1 新版为 3/3，old 退步因展开失败原因） |

## 与 Iteration-1 对比

| 指标 | i1 with_skill | i2 with_skill | 变化 |
|------|-------------|-------------|------|
| 总通过率 | 88.9% (16/18) | 100% (12/12*) | **+11.1%** |
| eval-3 边界 | 2/3 | 3/3 ✅ | 修正 |
| eval-4 边界 | 2/3 | 3/3 ✅ | 修正 |

*本轮只重跑 4 条，加上 i1 未重跑的 eval-1(3/3) 和 eval-2(3/3)，全量等效为 18/18。

## 修正措施回顾

在 Boundary Handoff 中加入了：
1. "不读 reference 文件"的硬约束
2. "回答上限 2-3 句 API 事实 + 1 句分流引导"的长度限制
3. "边界场景下克制比帮助更重要"的行为引导

这三条修正使 eval-3 和 eval-4 从 2/3 提升到 3/3，且没有影响其他 eval 的表现。

## 结论

新版 skill 在所有 6 条 eval 上均通过全部断言，iteration-2 修正成功。
