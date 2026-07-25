# Benchmark — Iteration 1

## 总览

| 配置 | 总通过/总断言 | 通过率 |
|------|-------------|--------|
| with_skill (新版) | 16/18 | 88.9% |
| old_skill (旧版) | 17/18 | 94.4% |

## 逐 eval 对比

| eval | with_skill | old_skill | 差异 |
|------|-----------|-----------|------|
| eval-0 report-minimal | 3/3 ✅ | 2/3 | 新版更短更准 |
| eval-1 token-rule | 3/3 ✅ | 3/3 ✅ | 持平 |
| eval-2 notice-signing | 3/3 ✅ | 3/3 ✅ | 持平 |
| eval-3 preparation-boundary | 2/3 | 3/3 ✅ | 旧版分流更干净 |
| eval-4 troubleshooting-boundary | 2/3 | 3/3 ✅ | 旧版分流更干净 |
| eval-5 process-mixed | 3/3 ✅ | 3/3 ✅ | 持平 |

## 分析

### 新版优于旧版
- **eval-0 (report-minimal)**：新版严格控制了字段数量，没有展开 medias 附件和可选字段。旧版展开了过多内容。

### 旧版优于新版
- **eval-3 (preparation-boundary)**：旧版干净利落地拒绝并引导到 preparation-guide；新版虽然做了分流提示，但仍然展开了 client_id/secret/AK/SK 等 API 参数细节。
- **eval-4 (troubleshooting-boundary)**：旧版严格遵守"不展开"约束；新版虽然做了分流提示，但仍然展开了防火墙策略、URL 自检等排障链路细节。

### 持平
- eval-1、eval-2、eval-5 两者表现一致，均通过全部断言。

## 结论

新版在"接口事实查询"类问题（eval-0/1/2/5）上表现更好或持平，尤其是更短更准。
新版在"边界分流"类问题（eval-3/4）上弱于旧版——分流提示后仍然输出了应由其他 skill 处理的内容。

## 下一轮修正方向

1. **加强 Boundary Handoff 的克制性**：在 Boundary Handoff 话术模板中明确"分流后只给最简接口路径确认，不展开参数和排障细节"。
2. **在 Output Contract 中补一条边界规则**：当判断为边界问题时，回答上限为 2-3 句 API 事实 + 分流话术，不再读 reference 展开内容。
