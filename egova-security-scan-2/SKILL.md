---
name: egova-security-scan
description: |
  egova-security-scanner 工具的 Claude Code 入口。当用户提出"扫描 IP X.X.X.X 漏洞"、
  "对 X 做安全扫描"、"渗透测试 X"、"爆破 X 的密码"、"egova-scan X" 这类需求时触发。
  能力: nmap 主机端口扫描 + nuclei 模板漏扫 + ZAP 登录态扫描 + hydra 密码爆破 + 
  LLM validator 复验, 输出统一 HTML 安全报告。需要本地仓库 D:\git\egova-security-scanner\
  与 WSL2 docker 环境。
trigger_keywords:
  - 安全扫描
  - 漏洞扫描
  - 渗透测试
  - egova-scan
  - 爆破密码
  - 主机扫描
  - web 漏扫
when_to_use: |
  必须满足三个条件: (1) 用户给出明确的扫描目标 IP/域名; (2) 用户为该资产的所有者
  或已获书面授权; (3) 用户明确表达想做安全扫描/渗透测试。
when_not_to_use: |
  不要触发: (a) 仅询问安全概念但无扫描需求; (b) 目标是第三方资产无授权;
  (c) 用户只是问 vuln-response (CVE 处置) 等其他 skill 的功能。
---

# egova-security-scan

`egova-security-scanner` 是一套多 agent 自动化安全扫描工具，基于 nmap / nuclei / 
ZAP / hydra + LangGraph orchestrator + Claude validator (可选)，输入 IP/域名输出 
HTML 安全报告。MDASH 启发的五阶段流水线: prepare → scan_host → scan_authed → 
brute → validate → report。

## 仓库与环境

- 仓库: `D:\git\egova-security-scanner\`
- venv: `D:\git\egova-security-scanner\.venv\Scripts\`
- CLI: `D:\git\egova-security-scanner\.venv\Scripts\egova-scan.exe`
- GitHub: https://github.com/majq1990/egova-security-scanner (private)
- Docker: WSL2 docker daemon (Docker Desktop integration)

## 标准使用流程

### 1) 收集授权
扫描任何目标前必须确认: 是否自有资产 / 是否已书面授权 / 是否允许爆破。若有疑虑直接拒绝。

### 2) 选择模式

**主机+web 扫描 (无侵入)**:
```powershell
cd D:\git\egova-security-scanner
$env:SCANNER_RUNS_DIR='D:\git\egova-security-scanner\runs'
.\.venv\Scripts\egova-scan.exe run <target> --port <port> --url <url> --no-validator
```

**含爆破 (高侵入, 需授权)**:
```powershell
.\.venv\Scripts\egova-scan.exe run <target> --port <port> --url <url> `
  --config targets/dvwa.config.yaml --with-brute --no-validator
```

**Web UI 模式**:
```powershell
.\.venv\Scripts\egova-scan.exe serve --host 127.0.0.1 --port 8765
```
打开 http://127.0.0.1:8765, 表单提交扫描任务。

### 3) 阅读报告

输出在 `runs/<run_id>/`:
- `report.html` — 给人看
- `findings.dedup.json` — 给程序消费
- `scan_host/*.xml /*.jsonl` — 原始 nmap / nuclei 输出
- `brute/*.txt` — 原始 hydra 输出 (含命中凭证)

### 4) 链式触发版本探测（HARD RULE, 必走）

**报告生成后, 必须调用 `xinchuang-pkg-probe` 续跑第三方软件版本探测**, 把目标节点的实际部署版本回填到钉钉 AI 表格 (`信创第三方软件拉包打包矩阵` baseId G1DKw2zgV2RXpGMNTPNyZ0XYVB5r9YAn), 并按 `yyyymmdd-OS_VER` 批次落问题表。

两条触发通道任一即可（双保险设计）:

**A. CLI 显式触发** — 用户在调 `egova-scan run` 时已加 `--with-probe`:
```powershell
.\.venv\Scripts\egova-scan.exe run <target> --port <port> --url <url> --no-validator `
  --with-probe --probe-scanner <scanner_ip> --probe-nodes <node1,node2,...>
```
CLI 在 report 后自动调 `~/.claude/skills/xinchuang-pkg-probe/scripts/run.sh`,
此时 Claude 无需再手动调 skill (避免重复)。

**B. LLM 编排触发** — 用户只说"扫一下 X 漏洞"未带 --with-probe, 或扫描通过 web UI / 直接调编排器跑完:
报告生成后, Claude **必须**主动用 Skill 工具调用 `/xinchuang-pkg-probe`, 传入与扫描相同的 scanner+nodes 信息. 触发示例:
```
/xinchuang-pkg-probe --scanner 101.200.233.112 --nodes 101.200.85.159,101.200.180.202,101.200.151.219
```
或自然语言: "对刚扫的 3 节点跑版本探测, 扫描机 101.200.233.112"

**不触发的例外**: 仅当扫描目标**不是信创一键部署节点**(如 DVWA、外部 demo) 才可省略 probe; 任何指向 qijian/oneinstall_v2 产出节点的扫描都必走。

## 数据契约

每个 finding 含: `id, stage, target, title, severity, cvss, cve, cwe, evidence, 
engine, template, validated, validator_reason, validator_confidence, tags`.
完整 schema: `schemas/finding.schema.json`.

## 配置文件示例

参见 `targets/dvwa.config.yaml` 和 `targets/eurbanmis.config.yaml`. 顶层 keys:
`scan_host / scan_authed / brute / validate / report`. 每个 stage 可设 `_disabled: true` 跳过.

## 常见情况

- **目标是 SPA / token auth**: scan_authed 需要 `ScriptAuthConfig` (auth/script.py),
  不能用 form-based. 见 v0.5 路线.
- **prod 爆破**: 默认 rate_limit=slow (1 thread + 2s wait), 用户授权后才可调整.
- **docker 失败**: 检查 Docker Desktop WSL Integration; 引擎镜像会自动 fallback
  `docker.1ms.run` 国内 mirror.
- **没有 ANTHROPIC_API_KEY**: validator 自动降级到 MockValidator, 不阻塞流水线.

## 已知限制 (v0.5)

1. SPA Script-based auth 已搭骨架, 但 login API URL 需逐应用配置
2. LLM validator 真模型需 ANTHROPIC_API_KEY (sk-ant-)
3. 单机 threading 调度; 多并发请用 Celery (TODO)

## 触发示例

✅ "扫一下 182.92.5.151:38081 的安全漏洞" → 调 egova-scan run + 出报告  
✅ "对我们的 demo 站做渗透测试，含密码爆破" → 调 egova-scan run --with-brute  
✅ "起 egova-scan 的 web UI" → 调 egova-scan serve  
❌ "OWASP top 10 是哪十个" → 不触发, 这是概念问题

---

# v9 渗透流水线 (麒舰 SPA 专用, 2026-06 现役)

麒舰(eurbanpro 等 Vue SPA)本地 CLI 跑不通(SPA+captcha+SM2+首登改密)。现役方案 = 扫描机
跑 `v9-full-scan.sh` 全套(登录→ZAP Spider→playwright SPA crawl→Active Scan→业务挖掘→OOB
盲打→nuclei→DB 探测→7 节渗透报告), 由 demo webhook 自动触发(钉钉群 `#安全扫描` 部署消息)。

## 现役资源
- webhook: `demo.egova.com.cn/scan-webhook/api/v1/scan-deploy`(Bearer Redmine key)
- 扫描机镜像: cn-beijing `m-2zedkto6di3sji4upvb2` / **cn-wulanchabu `m-0jlg4vp2svutpuq67nl3`**(同名"安全扫描-egova-cli-v2")
- webhook 按 region 选镜像: `.env` 配 `SCANNER_IMAGE_MAP=cn-beijing=...,cn-wulanchabu=...`(维持"跟随目标 IP 反查 region/vpc/sg"设计)
- 乌兰察布网络: VPC `vpc-0jl32yi9rx5ovum932wnz` / VSwitch `vsw-0jlfj7todyuefm058cws1`(zone-c) / SG `sg-0jl65keaomy0jmi59l17` / KeyPair `mjqegova-ed25519`
- 脚本(本机 git `D:\git\egova-security-scanner-webhook\scripts\`): v9-full-scan/v9-batch-run/v9-merge-reports/v9-pentest/zap-manual-scan/playwright-spa-crawl/business-vuln-hunt/oob-blind-hunt/privesc-hunt/init-account/url_endpoint/get-token + push/relay。webhook scp_scripts() 自动推全套到扫描机 /root/

## 麒舰关键坑(必读)
1. **免登录拿 token**(现役最优): `POST /usercenter-api/oauth/extras/token` JSON body `{"grant_type":"client_credentials","client_id":"unity-client","client_secret":"unity"}` → 3 秒拿 token, 免 captcha/SM2/改密。`get-token.sh` 已封装。`unity-client/unity` 硬编码弱凭证本身是 HIGH(CWE-798)。
2. **业务 API 靠 `x-authorization: bearer <token>` header 鉴权, 不是 cookie**。用 cookie 测未授权 = 假阳性。
3. **首登强制改密**(playwright 登录路径): 默认 `eGova@2023Yhzx` → 检测 firstLoginFlag 自动改 `Egova@123`。
4. **captcha** = ant `<Image>` data URI(`img.ant-image-img`), 喂 demo OCR `/captcha-ocr/api/ocr`。不点 img 刷新(弹预览 modal), Enter 提交后别 fallback click(captcha 已过期)。
5. **SPA 探索只有 playwright crawl 有效**(74 端点); ZAP AJAX Spider(API 路径是 `ajaxSpider` 不是 spiderAjax) + katana 对 Vue SPA 实测判死。
6. **签名 nonce+ts+sig**: 防重放实测失效(nonce 可重放+ts 无时效=MEDIUM CWE-294)。改 URL 参数破坏签名 → IDOR/SSRF 重放类被挡。
7. **端点去重**: URL 带 nonce/ts/sig, 按完整 URL 去重虚高(94→真实 74)。`url_endpoint.py` 剔除动态参数算真实端点。
8. **OOB 盲打(Log4j/SpEL/Fastjson/SSRF)默认始终保留**, 即使 0 回连也不删, 遇老版才扫得出。
9. **ZAP daemon 不能公网直接访问**(设计只给本地工具): 即使 SG 放行 8090 外部 HTTP 也不响应。**正解 = SSH 隧道** `ssh -i key -N -L 8090:127.0.0.1:8090 root@<scanner>` → 本机 `127.0.0.1:8090/UI/`。
10. **扫描机权限隔离不直连 demo**: 报告中转走 webhook orchestrator 或本机 v9-relay-push.sh。

## 释放扫描机别忘清孤儿快照
`DeleteInstance` 后查 `DescribeSnapshots --Usage none` 删孤儿快照(共用 disk 的不连带删)。
