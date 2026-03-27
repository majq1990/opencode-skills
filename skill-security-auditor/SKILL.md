# Skill Security Auditor

## Metadata

- **Name**: skill-security-auditor
- **Version**: 1.1.0
- **Author**: Galatea / OpenClaw Team
- **Category**: Security
- **Description**: OpenClaw skill security auditor with Cisco AI Skill Scanner integration

## Requirements

- Python 3.8+
- Cisco AI Skill Scanner (`pip install cisco-ai-skill-scanner[all]`)
- Dependencies in `requirements.txt`

## Installation

```bash
pip install cisco-ai-skill-scanner[all]
```

## Usage

### As CLI Tool

```bash
# Scan single skill
./tools/claw-audit.py scan <skill-path>

# Scan all skills
./tools/claw-audit.py scan-all

# Check status
./tools/claw-audit.py status
```

### As Python Module

```python
from lib.scanner_orchestrator import ScannerOrchestrator

orchestrator = ScannerOrchestrator()
result = orchestrator.scan_skill("/path/to/skill")

for finding in result.findings:
    print(f"{finding.severity}: {finding.message}")
```

## Commands

### scan

Scan a single skill for security issues.

**Arguments**:
- `skill_path`: Path to skill directory

**Options**:
- `-s, --scanners`: Scanners to use (cisco, clawsec)
- `--severity`: Minimum severity (critical, high, medium, low, info)
- `--no-cve`: Skip CVE database check
- `--auto-remediate`: Auto-quarantine critical issues
- `-o, --output`: Output file path
- `-f, --format`: Output format (sarif, json, markdown)
- `--stdout`: Print to stdout
- `-d, --detailed`: Show detailed findings

### scan-all

Scan all skills in a directory.

**Arguments**:
- `skills_dir`: Skills directory (optional, uses OPENCLAW_SKILLS_DIR)

**Options**:
- `-w, --workers`: Parallel workers (default: 4)
- `--severity`: Minimum severity
- `--auto-remediate`: Auto-quarantine

### status

Check scanner status and availability.

## Output Formats

### SARIF 2.1.0

GitHub Code Scanning compatible format.

### Markdown

Human-readable report with severity icons and recommendations.

### JSON

Machine-readable format for programmatic consumption.

## Threat Categories

AITech classification system:

1. Prompt Injection
2. Data Exfiltration
3. Credential Harvesting
4. Command Injection
5. Dependency Confusion
6. Malicious Code Execution
7. Network Egress
8. Privilege Escalation
9. Obfuscation
10. Backdoor
11. Supply Chain Attack

## Configuration

### Environment Variables

- `OPENCLAW_SKILLS_DIR`: Default skills directory
- `CISCO_SCANNER_THRESHOLD`: Severity threshold
- `CLAWSEC_FEED_URL`: Threat feed URL
- `AUDIT_AUTO_REMEDIATE`: Enable auto-remediation

### Config Files

- `config/default.yaml`: Default settings
- `config/cve_cache.json`: CVE database cache

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success, no critical/high issues |
| 1 | High severity findings |
| 2 | Critical severity findings |

## Development

### Running Tests

```bash
pytest tests/ -v --cov=lib
```

### Adding New Scanners

1. Implement scanner class in `lib/`
2. Add to `ScannerOrchestrator`
3. Update SPEC.yaml
4. Add tests

## Changelog

### 1.1.0 (2026-02-11)

- Migrated from AgentVerus to Cisco AI Skill Scanner
- Unified Python stack (removed Node.js dependency)
- AITech threat classification
- SARIF 2.1.0 output format

### 1.0.0

- Initial release with AgentVerus
- Basic static analysis
- ASST taxonomy
