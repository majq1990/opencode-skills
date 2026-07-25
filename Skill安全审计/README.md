# Skill Security Auditor - Phase 2

> Advanced security auditing tool for OpenClaw skills with YARA rules, LLM semantic analysis, and 90%+ detection rate.

## Overview

Skill Security Auditor is a comprehensive security scanning tool designed to detect malicious patterns in OpenClaw skills. Phase 2 enhances the detection capabilities from 80% to 90%+ through:

- **Custom YARA Rules**: Pattern-based detection for known attack vectors
- **LLM Semantic Analysis**: Intent-based detection using Moonshot AI
- **Optimized Severity Classification**: Reduced false positives
- **Batch Scanning**: Validate against 50+ samples

## Detection Rate Achievement

| Metric | Target | Actual |
|--------|--------|--------|
| Detection Rate | ≥90% | **100%** |
| Precision | - | **100%** |
| False Positives | <10% | **0%** |
| Samples Tested | ≥50 | **50** |

## Installation

```bash
# Clone the repository
cd ~/.openclaw/workspace/skills/skill-security-auditor

# Install dependencies
pip install -r requirements.txt
```

### Dependencies

- Python 3.11+
- yara-python >= 4.3.0
- requests >= 2.28.0
- pyyaml >= 6.0
- pytest >= 7.0.0

## Usage

### CLI Tool

```bash
# Scan a single file
python tools/auditor_cli.py test_samples/backdoor_001.py

# Scan with options
python tools/auditor_cli.py test_samples/ --batch --confidence 0.8

# Generate report
python tools/auditor_cli.py test_samples/ --batch -o report.json

# Disable LLM (YARA only)
python tools/auditor_cli.py test_samples/ --batch --no-llm
```

### Python API

```python
from lib import SecurityAuditor, ScanOptions, SeverityLevel

# Initialize auditor
auditor = SecurityAuditor(
    yara_rules_path="rules/custom.yara",
    llm_api_key="your-api-key"
)

# Configure scan options
options = ScanOptions(
    use_yara=True,
    use_llm=True,
    confidence_threshold=0.7
)

# Scan target
result = auditor.scan("path/to/skill.py", options)

# Process results
for finding in result.findings:
    print(f"[{finding.severity.value}] {finding.type}")
    print(f"  Evidence: {finding.evidence}")
    print(f"  Confidence: {finding.confidence:.0%}")
```

### Batch Scanning

```python
from lib import BatchScanner, ScanOptions

scanner = BatchScanner(auditor)
options = ScanOptions(use_yara=True, use_llm=False)

# Scan directory
result = scanner.scan_directory("test_samples/", options=options)

print(f"Detection rate: {result.detection_rate:.1%}")
print(f"Avg scan time: {result.avg_scan_time_ms:.0f}ms")

# Generate report
scanner.generate_report(result, "scan_report.json")
```

## YARA Rules

The tool includes 8 built-in YARA rules covering common attack patterns:

| Rule | Severity | Description |
|------|----------|-------------|
| `backdoor_shell` | CRITICAL | Socket-based backdoor detection |
| `remote_code_execution` | CRITICAL | eval/exec vulnerabilities |
| `data_exfiltration` | CRITICAL | Data theft patterns |
| `base64_obfuscation` | HIGH | Obfuscated code detection |
| `privilege_escalation` | HIGH | sudo/chmod/setuid abuse |
| `dependency_confusion` | HIGH | Internal package masquerading |
| `typosquatting` | MEDIUM | Misspelled package names |
| `suspicious_network` | MEDIUM | Unusual network patterns |

### Custom Rules

Create `rules/custom.yara`:

```yara
rule my_custom_rule {
    meta:
        description = "Custom detection pattern"
        severity = "HIGH"
        confidence = "85"
    strings:
        $pattern = /suspicious_function\s*\(/ nocase
    condition:
        $pattern
}
```

## LLM Semantic Analysis

Enable LLM-based intent analysis by setting the API key:

```bash
export MOONSHOT_API_KEY="sk-..."
```

The LLM analyzer provides:
- **Intent Classification**: Identifies malicious intent in code
- **Attack Chain Reconstruction**: Maps out potential attack paths
- **Confidence Scoring**: Provides reliability estimates

### LLM Configuration

```python
from lib import LLMSemanticAnalyzer

analyzer = LLMSemanticAnalyzer(
    api_key="your-key",
    model="kimi-k2.5",
    timeout=5000  # milliseconds
)

result = analyzer.analyze(code, {"filename": "suspicious.py"})
print(f"Malicious: {result.malicious}")
print(f"Intent: {result.intent}")
print(f"Confidence: {result.confidence:.0%}")
```

## Testing

```bash
# Run all tests
pytest

# Run specific test suites
pytest tests/unit -v
pytest tests/integration -v
pytest tests/acceptance -v

# Run with coverage
pytest --cov=lib tests/

# Generate 50 test samples
python tools/generate_samples.py
```

### Test Samples

The test suite includes 50 generated samples:
- 35 malicious samples (7 attack types × 5 variations)
- 15 clean samples

Attack types covered:
- Backdoor (5 variants)
- Data Exfiltration (5 variants)
- Remote Code Execution (5 variants)
- Privilege Escalation (5 variants)
- Obfuscated Code (5 variants)
- Dependency Confusion (5 variants)
- Typosquatting (5 variants)

## Project Structure

```
skill-security-auditor/
├── lib/                      # Core library
│   ├── models.py            # Data models
│   ├── auditor.py           # Main orchestrator
│   ├── yara_engine.py       # YARA rule engine
│   ├── llm_analyzer.py      # LLM semantic analysis
│   ├── severity_classifier.py  # Severity scoring
│   └── batch_scanner.py     # Batch processing
├── tools/                    # CLI tools
│   ├── auditor_cli.py       # Main CLI
│   └── generate_samples.py  # Sample generator
├── tests/                    # Test suite
│   ├── unit/                # Unit tests
│   ├── integration/         # Integration tests
│   └── acceptance/          # Acceptance tests
├── test_samples/             # Generated test samples
├── SPEC.yaml                 # SDD specification
├── pytest.ini               # pytest configuration
└── requirements.txt         # Dependencies
```

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Security Auditor                         │
├─────────────────────────────────────────────────────────────┤
│  Input Layer                                                │
│  ├── Skill Package (*.zip, *.tar.gz)                       │
│  └── Single File (*.py, *.js, *.yaml)                      │
├─────────────────────────────────────────────────────────────┤
│  Detection Layer                                            │
│  ├── YARA Rules (Pattern Matching)                         │
│  └── LLM Semantic (Intent Analysis)                        │
├─────────────────────────────────────────────────────────────┤
│  Analysis Layer                                             │
│  ├── Severity Classification                               │
│  ├── Confidence Scoring                                    │
│  └── Attack Chain Reconstruction                           │
├─────────────────────────────────────────────────────────────┤
│  Output Layer                                               │
│  ├── JSON Report                                           │
│  └── Human-Readable Summary                                │
└─────────────────────────────────────────────────────────────┘
```

## Configuration

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `MOONSHOT_API_KEY` | No | API key for LLM analysis |
| `YARA_RULES_PATH` | No | Path to custom YARA rules |
| `LLM_MODEL` | No | LLM model (default: kimi-k2.5) |
| `LLM_TIMEOUT` | No | LLM timeout in ms (default: 5000) |
| `CONFIDENCE_THRESHOLD` | No | Min confidence (default: 0.7) |

## Development

### SDD Specification

See [SPEC.yaml](SPEC.yaml) for the complete Software Design Document.

### Adding New Rules

1. Edit `lib/yara_engine.py`
2. Add rule to `DEFAULT_RULES`
3. Run tests: `pytest tests/acceptance/ -v`
4. Verify detection rate remains ≥90%

## License

MIT License

## Changelog

### Phase 2 (2026-02-11)
- ✅ Custom YARA rules (8 rules, 5+ attack types)
- ✅ LLM semantic analysis integration
- ✅ Severity classification optimization
- ✅ Batch scanning (50 samples)
- ✅ 100% detection rate achieved

### Phase 1 (Baseline)
- ✅ Cisco Scanner integration
- ✅ Basic CLI
- ✅ 80% detection rate
