"""
Skill Security Auditor - Phase 2
Multi-engine security scanning with YARA rules and LLM semantic analysis
"""

import os
import json
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SeverityLevel(Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"


@dataclass
class Finding:
    """Security finding data class"""
    rule_id: str
    type: str
    severity: SeverityLevel
    confidence: float
    evidence: str
    file_path: str
    line_number: Optional[int] = None
    description: str = ""
    remediation: str = ""


@dataclass
class ScanResult:
    """Scan result container"""
    target: str
    findings: List[Finding] = field(default_factory=list)
    scan_time_ms: int = 0
    engines_used: List[str] = field(default_factory=list)
    error: Optional[str] = None

    @property
    def critical_count(self) -> int:
        return sum(1 for f in self.findings if f.severity == SeverityLevel.CRITICAL)

    @property
    def high_count(self) -> int:
        return sum(1 for f in self.findings if f.severity == SeverityLevel.HIGH)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "target": self.target,
            "findings": [
                {
                    "rule_id": f.rule_id,
                    "type": f.type,
                    "severity": f.severity.value,
                    "confidence": f.confidence,
                    "evidence": f.evidence,
                    "file_path": f.file_path,
                    "line_number": f.line_number,
                    "description": f.description,
                    "remediation": f.remediation
                }
                for f in self.findings
            ],
            "scan_time_ms": self.scan_time_ms,
            "engines_used": self.engines_used,
            "summary": {
                "total": len(self.findings),
                "critical": self.critical_count,
                "high": self.high_count
            }
        }


@dataclass
class ScanOptions:
    """Scan configuration options"""
    use_yara: bool = True
    use_llm: bool = True
    use_cisco: bool = True
    confidence_threshold: float = 0.7
    severity_filter: Optional[List[SeverityLevel]] = None
