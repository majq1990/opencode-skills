# 视觉细查 sub-agent prompt 模板

主线程派 4 个并行 sub-agent（每个 3-4 名考生）时使用此模板。

## 调用方式

```
Agent(
  subagent_type="general-purpose",
  description="视觉细查考生X-Y",
  run_in_background=True,
  prompt=<填充以下模板>
)
```

## Prompt 模板

```
你的任务是对 N 位考生的"性能安全认证实操"答卷做视觉细查，输出每个采分点的 found 值。

## 考生列表
1. **<attempt> <姓名>**
   - Q1: `D:\<workdir>\_extracted\<attempt>_<姓名>__Q1_*\`
   - Q2: `D:\<workdir>\_extracted\<attempt>_<姓名>__Q2_*\`
（每个目录里有 text_only.txt + media/imageN.png）

如果 Q1/Q2 是同一份文件（重复上传），只看一份；如未交标 missing。

## 视觉判断标准

### Q1 巡检报告类（必看截图统计区有数据）
- **P2-1 zip 巡检报告**：找 "生成 zip" / "archive" 截图 → true/false
- **P2-2 dameng / P2-4 mysql / P2-6 os / P2-7 redis**：
  - true=统计表至少 1 行真实数据
  - partial=仅基本信息有数据，统计表全空
  - false=只是页头/文件列表/未做/missing
- **P2-3 microservice**："需解决 dump 路径预警"
  - true=统计表有真实数据 + 修复 dump 路径配置
  - partial=有数据但无修复 / 修了但表空
  - false=空白
- **P2-5 nginx**："需解决日志切割预警"
  - true=报告 + logrotate 修复过程截图
  - partial=只看了报告
  - false=未做
- **P1-1 内网访问**：浏览器URL=true / curl终端=false / 缺=missing
- **P1-4 nginx 状态**：必须两块（统计分布 + 10s耗时节点分布）；缺一段=partial

### Q2 安全
- **S1-1 雷池登录**：登录页/仪表盘带URL=true / 仅命令行=partial / 无=false
- **S3-1 弱密码**：直接看 text_only 末尾清单数量，输出 count 字段
- **S2-1 应用中心放开**（三要素）：①DevTools 32018拦截 ②wafconf/url 注释 getapps ③reload+应用中心恢复 → factors_met (0-3)
- **S2-2 操作日志拦截**（三要素）：①取 operatelog URL ②echo>>url ③reload+接口403
- **S2-3 CC防护**（三要素）：①取 login URL ②echo>>cc-url+reload ③【加分】ab攻击+31001日志（has_ab_attack=true/false）

## 输出 JSON

```json
{
  "<attempt>_<姓名>": {
    "P1-1": {"check":"URL", "found":"true|partial|false|missing", "evidence":"..."},
    "P1-4": {"check":"统计分布+10s", "found":..., "evidence":"..."},
    "P2-1": {"found":..., "evidence":"..."},
    "P2-2": {"found":..., "evidence":"..."},
    "P2-3": {"found":..., "evidence":"..."},
    "P2-4": {"found":..., "evidence":"..."},
    "P2-5": {"found":..., "evidence":"..."},
    "P2-6": {"found":..., "evidence":"..."},
    "P2-7": {"found":..., "evidence":"..."},
    "S1-1": {"found":..., "evidence":"..."},
    "S2-1": {"factors_met":0-3, "evidence":"..."},
    "S2-2": {"factors_met":0-3, "evidence":"..."},
    "S2-3": {"factors_met":0-3, "has_ab_attack":true|false, "evidence":"..."},
    "S3-1": {"count":N, "evidence":"..."}
  },
  ...
}
```

## 工作要点
- 每个采分点只看 1-2 张关键图，用 Read 工具读 PNG
- evidence 写明 imageN.png + 关键内容描述
- 重复提交（如 _v1/_v2）只看一份
- 报告输出严格 JSON，最后单独打印
```

## 整合阶段

每个 sub-agent 输出存到 `<workdir>/_visual/visual_<range>.json`（主线程负责保存，不要 sub-agent 写文件）。
全部完成后跑 `python scripts/grading_v2.py <workdir>` 综合校准。

视觉数据深合并逻辑（grading_v2.py 已实现）：同一考生跨文件的 code 合并而非覆盖。
