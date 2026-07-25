# Skill Security Auditor - Technical Findings

**Project**: skill-security-auditor  
**Date**: 2026-02-11  
**Status**: Planning Complete  

---

## 1. Architecture Findings

### 1.1 Hybrid Approach Validation

Research confirms **hybrid approach** (external tools + custom integration) is optimal:

| Criterion | Build from Scratch | Off-the-shelf Only | Hybrid (Selected) |
|-----------|-------------------|-------------------|-------------------|
| Time to Market | 3-6 months | 1-2 weeks | 2-4 weeks |
| Coverage | Customizable | Limited | Customizable |
| Maintenance Burden | High | Low | Medium |
| Integration Depth | Full | Limited | Deep |
| Community Support | None | Full | Full + Custom |

**Decision**: Hybrid approach balances speed, quality, and customization.

### 1.2 Three-Layer Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    SKILL SECURITY AUDITOR                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ LAYER 1: STATIC ANALYSIS (Pre-install/CI)              │   │
│  │  • AgentVerus Scanner (ASST taxonomy)                  │   │
│  │  • Custom rules for OpenClaw-specific vectors          │   │
│  │  • SARIF output for GitHub integration                 │   │
│  └─────────────────────────────────────────────────────────┘   │
│                           ↓                                     │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ LAYER 2: THREAT INTELLIGENCE (Continuous)              │   │
│  │  • ClawSec Security Feed (CVE monitoring)              │   │
│  │  • SHA256 checksum verification                        │   │
│  │  • Reputation scoring                                  │   │
│  └─────────────────────────────────────────────────────────┘   │
│                           ↓                                     │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ LAYER 3: RUNTIME MONITORING (Post-install)             │   │
│  │  • mcp-scan proxy (traffic analysis)                   │   │
│  │  • Behavior baseline detection                         │   │
│  │  • Anomaly alerting                                    │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ ORCHESTRATION & RESPONSE                               │   │
│  │  • Unified CLI (claw audit)                            │   │
│  │  • Report aggregation                                  │   │
│  │  • Auto-remediation workflows                          │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. Tool Selection Analysis

### 2.1 AgentVerus Scanner (Primary)

**Repository**: https://github.com/agentverus/agentverus-scanner

**Strengths**:
- ✅ ASST (Agent Security Threat Taxonomy) - 11 attack types
- ✅ Trust badge system (CERTIFIED/CONDITIONAL/SUSPICIOUS/REJECTED)
- ✅ SARIF output (GitHub Code Scanning compatible)
- ✅ Can scan entire ClawHub Registry
- ✅ npm installable: `npx agentverus scan ./SKILL.md`

**ASST Taxonomy Coverage**:
```yaml
Attack_Types:
  - Prompt_Injection      # 提示词注入
  - Data_Exfiltration     # 数据外泄
  - Credential_Harvesting # 凭证收集
  - Command_Injection     # 命令注入
  - Dependency_Hijacking  # 依赖劫持
  - Tool_Poisoning        # 工具投毒
  - Memory_Manipulation   # 记忆操控
  - Excessive_Permissions # 过度权限
  - Obfuscation           # 代码混淆
  - Network_Egress        # 网络外连
  - Rug_Pull              # 恶意更新
```

**Integration Points**:
- CLI wrapper: `lib/agentverus_wrapper.py`
- Configurable severity thresholds
- JSON/SARIF output parsing
- Exit code handling

### 2.2 ClawSec (Threat Intelligence)

**Repository**: https://github.com/prompt-security/clawsec

**Strengths**:
- ✅ By Prompt Security (SentinelOne backed)
- ✅ Real-time CVE feed
- ✅ File integrity monitoring
- ✅ SHA256 verification
- ✅ Security advisory RSS

**Integration Points**:
- Feed polling: `lib/clawsec_integration.py`
- Local cache for offline operation
- Alert correlation with scan results

### 2.3 mcp-scan (Runtime)

**Repository**: https://github.com/invariantlabs-ai/mcp-scan

**Strengths**:
- ✅ Static + Dynamic scanning
- ✅ Proxy mode for traffic inspection
- ✅ Guardrails policy enforcement
- ✅ PII/Secrets detection in traffic

**Integration Points**:
- Proxy wrapper: `lib/mcpscan_proxy.py`
- Async traffic analysis
- Behavior baseline learning

---

## 3. Security Threat Model

### 3.1 Assets

| Asset | Value | Protection Level |
|-------|-------|------------------|
| User credentials (~/.clawdbot/.env) | Critical | Highest |
| SSH keys (~/.ssh/) | Critical | Highest |
| OpenClaw configuration | High | High |
| User data/memory | High | High |
| Skill code | Medium | Medium |
| Network egress logs | Medium | Medium |

### 3.2 Threat Actors

| Actor | Motivation | Capability |
|-------|------------|------------|
| Script Kiddie | Reputation | Low |
| Cybercriminal | Financial | Medium |
| APT | Espionage | High |
| Insider | Disgruntled | High |

### 3.3 Attack Vectors (Priority)

```
High Priority:
├── Prompt Injection via skill description
├── Data exfiltration to attacker-controlled servers
├── Credential harvesting from environment files
└── Dependency hijacking (typosquatting, malicious packages)

Medium Priority:
├── Command injection through shell tool
├── Memory manipulation (context poisoning)
└── Excessive permission requests

Low Priority:
├── Code obfuscation
└── Network egress monitoring
```

---

## 4. Implementation Technical Decisions

### 4.1 Language Selection

| Component | Language | Rationale |
|-----------|----------|-----------|
| Core orchestrator | Python | Rich ecosystem, async support |
| AgentVerus wrapper | Node.js | Native npm integration |
| mcp-scan wrapper | Python | Native uvx integration |
| CLI tools | Python | Click/Typer for UX |
| Tests | Python | pytest ecosystem |

### 4.2 Configuration Schema

```yaml
# config/security-auditor.yaml
scanner:
  agentverus:
    enabled: true
    severity_threshold: medium  # low/medium/high/critical
    fail_on: [critical, high]   # severity levels that fail CI
  
  clawsec:
    enabled: true
    feed_poll_interval: 3600    # seconds
    cache_ttl: 86400           # seconds
  
  mcpscan:
    enabled: true
    proxy_port: 8080
    traffic_sample_rate: 1.0    # 0.0-1.0

remediation:
  auto_isolate: true           # Auto-quarantine suspicious skills
  auto_rotate_credentials: false  # Suggest only (safety)
  
reporting:
  format: sarif                # sarif/json/markdown
  output_dir: ./security-reports
  github_integration: true
```

### 4.3 Database Schema (SQLite)

```sql
-- scan_results table
CREATE TABLE scan_results (
    id INTEGER PRIMARY KEY,
    skill_name TEXT NOT NULL,
    skill_path TEXT NOT NULL,
    scanner TEXT NOT NULL,  -- agentverus/clawsec/mcpscan
    severity TEXT,          -- critical/high/medium/low/info
    attack_type TEXT,       -- ASST taxonomy
    description TEXT,
    remediation TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- threat_intel table
CREATE TABLE threat_intel (
    id INTEGER PRIMARY KEY,
    skill_name TEXT,
    cve_id TEXT,
    severity TEXT,
    description TEXT,
    published_at TIMESTAMP,
    fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- runtime_events table
CREATE TABLE runtime_events (
    id INTEGER PRIMARY KEY,
    skill_name TEXT,
    event_type TEXT,        -- network/file/credential
    details TEXT,
    severity TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## 5. Risk Findings

### 5.1 High Risks

| ID | Risk | Mitigation |
|----|------|------------|
| R1 | AgentVerus false negatives on novel attacks | Keep signatures updated, use defense-in-depth |
| R2 | mcp-scan performance impact on latency | Async processing, sampling mode |
| R3 | ClawSec feed poisoning | Signature verification, fallback to static |

### 5.2 Compliance Considerations

- **GDPR**: Runtime monitoring may capture PII - implement data retention policies
- **SOC2**: Audit logs required for all scan actions
- **ISO27001**: Document control effectiveness measurement

---

## 6. Performance Benchmarks

| Metric | Target | Notes |
|--------|--------|-------|
| Scan time per skill | < 30s | AgentVerus + ClawSec |
| Runtime overhead | < 10% | mcp-scan proxy |
| Memory usage | < 100MB | Peak during scan |
| False positive rate | < 5% | Tuned thresholds |
| Detection rate | > 95% | Known attack patterns |

---

## 7. References

### 7.1 External Resources

- [AgentVerus Scanner](https://github.com/agentverus/agentverus-scanner)
- [ClawSec by Prompt Security](https://github.com/prompt-security/clawsec)
- [mcp-scan by Invariant](https://github.com/invariantlabs-ai/mcp-scan)
- [ASST Taxonomy Paper](https://arxiv.org/abs/2500.xxxxx) (if available)

### 7.2 Internal Resources

- `SPEC.yaml` - SDD specification
- `task_plan.md` - Implementation roadmap
- `progress.md` - Session logs

---

**Next Actions**:
1. Create Notion technical specification page
2. Finalize SPEC.yaml with detailed contracts
3. Prepare for external audit (Claude review)

**Document Version**: 1.0  
**Last Updated**: 2026-02-11
