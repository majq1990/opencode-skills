"""
Report Generator
Generates security reports in SARIF 2.1.0, Markdown, and JSON formats
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import asdict

from lib.cisco_scanner import ScanResult, Finding

logger = logging.getLogger(__name__)


class ReportGenerator:
    """Generate security reports in multiple formats"""
    
    SARIF_VERSION = "2.1.0"
    SARIF_SCHEMA = "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json"
    
    def __init__(self):
        self.tool_name = "skill-security-auditor"
        self.tool_version = "1.1.0"
    
    def generate_sarif(self, scan_result: ScanResult, output_path: str) -> bool:
        """
        Generate SARIF 2.1.0 report
        
        Args:
            scan_result: Scan results to convert
            output_path: Path to write SARIF file
            
        Returns:
            True if successful
        """
        try:
            sarif = self._build_sarif(scan_result)
            
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w') as f:
                json.dump(sarif, f, indent=2)
            
            logger.info(f"SARIF report written to: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to generate SARIF: {e}")
            return False
    
    def generate_markdown(self, scan_result: ScanResult) -> str:
        """
        Generate human-readable Markdown report
        
        Args:
            scan_result: Scan results to convert
            
        Returns:
            Markdown formatted string
        """
        lines = []
        
        # Header
        lines.append("# Security Audit Report")
        lines.append("")
        lines.append(f"**Skill:** `{scan_result.skill_name}`")
        lines.append(f"**Path:** `{scan_result.skill_path}`")
        lines.append(f"**Scan Time:** {scan_result.scan_time}")
        lines.append(f"**Scanners Used:** {', '.join(scan_result.scanners_used)}")
        lines.append("")
        
        # Error handling
        if scan_result.error:
            lines.append("## ⚠️ Scan Error")
            lines.append("")
            lines.append(f"```")
            lines.append(scan_result.error)
            lines.append(f"```")
            lines.append("")
            return "\n".join(lines)
        
        # Summary
        lines.append("## Summary")
        lines.append("")
        
        total = len(scan_result.findings)
        lines.append(f"**Total Findings:** {total}")
        lines.append("")
        
        if total == 0:
            lines.append("✅ No security issues detected.")
            lines.append("")
        else:
            # Severity table
            lines.append("### Severity Breakdown")
            lines.append("")
            lines.append("| Severity | Count |")
            lines.append("|----------|-------|")
            
            for sev in ["critical", "high", "medium", "low", "info"]:
                count = scan_result.severity_counts.get(sev, 0)
                icon = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢", "info": "🔵"}.get(sev, "⚪")
                lines.append(f"| {icon} {sev.upper()} | {count} |")
            
            lines.append("")
            
            # Risk assessment
            critical = scan_result.severity_counts.get("critical", 0)
            high = scan_result.severity_counts.get("high", 0)
            
            if critical > 0:
                lines.append("### 🚨 Risk Assessment: CRITICAL")
                lines.append("")
                lines.append("This skill has **critical security vulnerabilities** and should NOT be installed or used.")
            elif high > 0:
                lines.append("### ⚠️ Risk Assessment: HIGH")
                lines.append("")
                lines.append("This skill has high-severity security issues. Use with extreme caution.")
            else:
                lines.append("### ℹ️ Risk Assessment: MODERATE")
                lines.append("")
                lines.append("This skill has some security findings. Review before use.")
            
            lines.append("")
        
        # Findings details
        if scan_result.findings:
            lines.append("## Findings")
            lines.append("")
            
            for i, finding in enumerate(scan_result.findings, 1):
                lines.append(self._format_finding_markdown(finding, i))
                lines.append("")
        
        # Recommendations
        lines.append("## Recommendations")
        lines.append("")
        
        if scan_result.findings:
            lines.append("1. **Review all findings** before installing or using this skill")
            lines.append("2. **Prioritize critical and high severity** issues")
            lines.append("3. **Consider alternative skills** if security posture is concerning")
            lines.append("4. **Monitor skill behavior** if installation proceeds")
        else:
            lines.append("✅ No immediate action required based on static analysis.")
            lines.append("- Always review skill code manually before installation")
            lines.append("- Monitor skill behavior during use")
        
        lines.append("")
        
        # Footer
        lines.append("---")
        lines.append(f"*Generated by {self.tool_name} v{self.tool_version}*")
        lines.append(f"*Report format: SARIF {self.SARIF_VERSION} compatible*")
        
        return "\n".join(lines)
    
    def generate_json(self, scan_result: ScanResult) -> str:
        """
        Generate JSON report for programmatic consumption
        
        Args:
            scan_result: Scan results to convert
            
        Returns:
            JSON formatted string
        """
        data = {
            "tool": {
                "name": self.tool_name,
                "version": self.tool_version
            },
            "scan": {
                "skill_name": scan_result.skill_name,
                "skill_path": scan_result.skill_path,
                "scan_time": scan_result.scan_time,
                "duration_ms": scan_result.scan_duration_ms,
                "scanners_used": scan_result.scanners_used,
                "error": scan_result.error
            },
            "summary": {
                "total_findings": len(scan_result.findings),
                "severity_counts": scan_result.severity_counts
            },
            "findings": [
                asdict(f) for f in scan_result.findings
            ]
        }
        
        return json.dumps(data, indent=2)
    
    def _build_sarif(self, scan_result: ScanResult) -> Dict:
        """Build SARIF 2.1.0 document from scan results"""
        
        # Build rules from findings
        rules = []
        rule_ids = set()
        
        for finding in scan_result.findings:
            if finding.rule_id not in rule_ids:
                rule_ids.add(finding.rule_id)
                rules.append({
                    "id": finding.rule_id,
                    "name": finding.attack_type,
                    "shortDescription": {
                        "text": finding.message[:100] if len(finding.message) > 100 else finding.message
                    },
                    "fullDescription": {
                        "text": finding.message
                    },
                    "help": {
                        "text": finding.remediation or "Review and remediate the security issue."
                    },
                    "properties": {
                        "security-severity": self._severity_to_cvss(finding.severity),
                        "tags": ["security", finding.attack_type]
                    }
                })
        
        # Build results
        results = []
        for finding in scan_result.findings:
            result = {
                "ruleId": finding.rule_id,
                "level": self._severity_to_level(finding.severity),
                "message": {
                    "text": finding.message
                },
                "locations": [{
                    "physicalLocation": {
                        "artifactLocation": {
                            "uri": finding.file_path
                        },
                        "region": {
                            "startLine": finding.line_number,
                            "snippet": {
                                "text": finding.code_snippet
                            }
                        }
                    }
                }],
                "properties": {
                    "attackType": finding.attack_type,
                    "confidence": finding.confidence
                }
            }
            results.append(result)
        
        # Build SARIF document
        sarif = {
            "$schema": self.SARIF_SCHEMA,
            "version": self.SARIF_VERSION,
            "runs": [{
                "tool": {
                    "driver": {
                        "name": self.tool_name,
                        "version": self.tool_version,
                        "informationUri": "https://github.com/openclaw/skill-security-auditor",
                        "rules": rules
                    }
                },
                "results": results,
                "invocations": [{
                    "executionSuccessful": scan_result.error is None,
                    "startTimeUtc": scan_result.scan_time
                }]
            }]
        }
        
        return sarif
    
    def _format_finding_markdown(self, finding: Finding, index: int) -> str:
        """Format a single finding as Markdown"""
        severity_icons = {
            "critical": "🔴",
            "high": "🟠",
            "medium": "🟡",
            "low": "🟢",
            "info": "🔵"
        }
        
        icon = severity_icons.get(finding.severity.lower(), "⚪")
        
        lines = []
        lines.append(f"### {icon} Finding #{index}: {finding.attack_type.upper()}")
        lines.append("")
        lines.append(f"**Severity:** `{finding.severity.upper()}`")
        lines.append(f"**Rule ID:** `{finding.rule_id}`")
        lines.append(f"**Confidence:** {finding.confidence:.0%}")
        lines.append("")
        lines.append(f"**File:** `{finding.file_path}`")
        if finding.line_number > 0:
            lines.append(f"**Line:** {finding.line_number}")
        lines.append("")
        lines.append(f"**Description:**")
        lines.append(f"{finding.message}")
        lines.append("")
        
        if finding.code_snippet:
            lines.append("**Code:**")
            lines.append("```python")
            lines.append(finding.code_snippet)
            lines.append("```")
            lines.append("")
        
        if finding.remediation:
            lines.append(f"**Remediation:** {finding.remediation}")
        
        return "\n".join(lines)
    
    def _severity_to_level(self, severity: str) -> str:
        """Convert severity to SARIF level"""
        mapping = {
            "critical": "error",
            "high": "error",
            "medium": "warning",
            "low": "note",
            "info": "note"
        }
        return mapping.get(severity.lower(), "warning")
    
    def _severity_to_cvss(self, severity: str) -> float:
        """Convert severity to CVSS score approximation"""
        mapping = {
            "critical": 9.5,
            "high": 8.0,
            "medium": 5.5,
            "low": 3.0,
            "info": 0.0
        }
        return mapping.get(severity.lower(), 5.0)
