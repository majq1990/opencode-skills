"""
Cisco Skill Scanner Wrapper
Handles integration with Cisco AI Skill Scanner for static analysis
"""

import subprocess
import json
import os
import logging
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from pathlib import Path
import tempfile

logger = logging.getLogger(__name__)


@dataclass
class Finding:
    """Security finding from Cisco Skill Scanner"""
    rule_id: str
    attack_type: str
    severity: str  # critical, high, medium, low, info
    message: str
    file_path: str
    line_number: int = 0
    confidence: float = 0.0
    code_snippet: str = ""
    remediation: str = ""


@dataclass  
class ScanResult:
    """Result of scanning a skill"""
    skill_name: str
    skill_path: str
    scan_time: str
    findings: List[Finding] = field(default_factory=list)
    severity_counts: Dict[str, int] = field(default_factory=dict)
    scanners_used: List[str] = field(default_factory=list)
    scan_duration_ms: int = 0
    error: Optional[str] = None


class CiscoSkillScanner:
    """
    Wrapper for Cisco AI Skill Scanner
    Provides unified interface for static security analysis
    """
    
    # AITech Threat Classification
    AITECH_ATTACK_TYPES = [
        "prompt_injection",
        "data_exfiltration", 
        "credential_harvesting",
        "command_injection",
        "dependency_confusion",
        "malicious_code_execution",
        "network_egress",
        "privilege_escalation",
        "obfuscation",
        "backdoor",
        "supply_chain_attack"
    ]
    
    SEVERITY_ORDER = ["critical", "high", "medium", "low", "info"]
    
    def __init__(self, severity_threshold: str = "medium"):
        self.severity_threshold = severity_threshold
        self._scanner_available = None
        
    def is_available(self) -> bool:
        """Check if Cisco Skill Scanner is installed and available"""
        if self._scanner_available is not None:
            return self._scanner_available
            
        try:
            # Check if skill-scanner CLI is available
            import shutil
            scanner_path = shutil.which("skill-scanner")
            if scanner_path is None:
                self._scanner_available = False
                return False
                
            result = subprocess.run(
                [scanner_path, "--help"],
                capture_output=True,
                text=True,
                timeout=5
            )
            self._scanner_available = result.returncode == 0
            return self._scanner_available
        except (subprocess.TimeoutExpired, FileNotFoundError):
            self._scanner_available = False
            return False
            return False
    
    def get_version(self) -> str:
        """Get Cisco Skill Scanner version"""
        try:
            # Try to get version from pip
            result = subprocess.run(
                ["pip3", "show", "cisco-ai-skill-scanner"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if line.startswith('Version:'):
                        return line.split(':')[1].strip()
            return "unknown"
        except Exception as e:
            logger.error(f"Failed to get scanner version: {e}")
            return "unknown"
    
    def scan(self, skill_path: str, output_format: str = "sarif") -> ScanResult:
        """
        Execute Cisco Skill Scanner on a skill directory
        
        Args:
            skill_path: Path to skill directory
            output_format: Output format (sarif, json)
            
        Returns:
            ScanResult with findings
        """
        import time
        from datetime import datetime
        
        start_time = time.time()
        skill_path = Path(skill_path).resolve()
        
        if not skill_path.exists():
            return ScanResult(
                skill_name=skill_path.name,
                skill_path=str(skill_path),
                scan_time=datetime.now().isoformat(),
                error=f"Skill path not found: {skill_path}"
            )
        
        if not self.is_available():
            return ScanResult(
                skill_name=skill_path.name,
                skill_path=str(skill_path),
                scan_time=datetime.now().isoformat(),
                error="Cisco Skill Scanner not available. Install with: pip install cisco-ai-skill-scanner[all]"
            )
        
        try:
            # Create temporary output file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.sarif', delete=False) as tmp:
                output_file = tmp.name
            
            # Build scan command using skill-scanner CLI
            import shutil
            scanner_path = shutil.which("skill-scanner")
            if scanner_path is None:
                return ScanResult(
                    skill_name=skill_path.name,
                    skill_path=str(skill_path),
                    scan_time=datetime.now().isoformat(),
                    error="skill-scanner command not found in PATH"
                )
            
            cmd = [
                scanner_path,
                "scan",
                str(skill_path),
                "--output", output_file,
                "--format", "sarif"
            ]
            
            logger.info(f"Running Cisco scan: {' '.join(cmd)}")
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60  # 60 second timeout per skill
            )
            
            duration_ms = int((time.time() - start_time) * 1000)
            
            if result.returncode != 0:
                logger.error(f"Cisco scanner failed: {result.stderr}")
                return ScanResult(
                    skill_name=skill_path.name,
                    skill_path=str(skill_path),
                    scan_time=datetime.now().isoformat(),
                    scan_duration_ms=duration_ms,
                    error=f"Scanner failed: {result.stderr}"
                )
            
            # Parse SARIF output
            findings = self._parse_sarif(output_file)
            
            # Clean up temp file
            os.unlink(output_file)
            
            # Calculate severity counts
            severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}
            for finding in findings:
                sev = finding.severity.lower()
                if sev in severity_counts:
                    severity_counts[sev] += 1
            
            return ScanResult(
                skill_name=skill_path.name,
                skill_path=str(skill_path),
                scan_time=datetime.now().isoformat(),
                findings=findings,
                severity_counts=severity_counts,
                scanners_used=["cisco"],
                scan_duration_ms=duration_ms
            )
            
        except subprocess.TimeoutExpired:
            return ScanResult(
                skill_name=skill_path.name,
                skill_path=str(skill_path),
                scan_time=datetime.now().isoformat(),
                error="Scan timeout after 60 seconds"
            )
        except Exception as e:
            logger.exception("Unexpected error during scan")
            return ScanResult(
                skill_name=skill_path.name,
                skill_path=str(skill_path),
                scan_time=datetime.now().isoformat(),
                error=f"Scan error: {str(e)}"
            )
    
    def _parse_sarif(self, sarif_path: str) -> List[Finding]:
        """Parse SARIF 2.1.0 output from Cisco scanner"""
        findings = []
        
        try:
            with open(sarif_path, 'r') as f:
                sarif_data = json.load(f)
            
            # Extract runs
            runs = sarif_data.get('runs', [])
            
            for run in runs:
                # Get rules for mapping
                rules = {}
                tool = run.get('tool', {})
                driver = tool.get('driver', {})
                for rule in driver.get('rules', []):
                    rules[rule.get('id')] = rule
                
                # Extract results
                for result in run.get('results', []):
                    finding = self._parse_result(result, rules)
                    if finding:
                        findings.append(finding)
                        
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse SARIF JSON: {e}")
        except Exception as e:
            logger.exception("Error parsing SARIF")
            
        return findings
    
    def _parse_result(self, result: Dict, rules: Dict) -> Optional[Finding]:
        """Parse a single SARIF result into Finding"""
        try:
            rule_id = result.get('ruleId', 'UNKNOWN')
            rule = rules.get(rule_id, {})
            
            # Get severity
            severity = result.get('level', 'warning')
            severity_map = {
                'error': 'high',
                'warning': 'medium',
                'note': 'info'
            }
            severity = severity_map.get(severity, severity)
            
            # Check rule properties for severity override
            rule_props = rule.get('properties', {})
            if 'security-severity' in rule_props:
                cvss = float(rule_props['security-severity'])
                if cvss >= 9.0:
                    severity = 'critical'
                elif cvss >= 7.0:
                    severity = 'high'
                elif cvss >= 4.0:
                    severity = 'medium'
                else:
                    severity = 'low'
            
            # Get message
            message = result.get('message', {}).get('text', 'No description')
            
            # Get location
            locations = result.get('locations', [])
            file_path = 'unknown'
            line_number = 0
            code_snippet = ""
            
            if locations:
                location = locations[0]
                physical = location.get('physicalLocation', {})
                artifact = physical.get('artifactLocation', {})
                file_path = artifact.get('uri', 'unknown')
                
                region = physical.get('region', {})
                line_number = region.get('startLine', 0)
                code_snippet = region.get('snippet', {}).get('text', '')
            
            # Determine attack type from rule
            attack_type = self._classify_attack_type(rule_id, message, rule)
            
            # Get remediation if available
            remediation = rule.get('help', {}).get('text', '')
            
            return Finding(
                rule_id=rule_id,
                attack_type=attack_type,
                severity=severity,
                message=message,
                file_path=file_path,
                line_number=line_number,
                confidence=rule_props.get('confidence', 0.8),
                code_snippet=code_snippet,
                remediation=remediation
            )
            
        except Exception as e:
            logger.error(f"Error parsing result: {e}")
            return None
    
    def _classify_attack_type(self, rule_id: str, message: str, rule: Dict) -> str:
        """Classify finding into AITech attack type"""
        message_lower = message.lower()
        rule_id_lower = rule_id.lower()
        
        # Check rule properties first
        tags = rule.get('properties', {}).get('tags', [])
        for tag in tags:
            tag_lower = tag.lower()
            for attack_type in self.AITECH_ATTACK_TYPES:
                if attack_type.replace('_', '') in tag_lower.replace('-', '').replace('_', ''):
                    return attack_type
        
        # Pattern matching
        patterns = {
            'prompt_injection': ['prompt injection', 'jailbreak', 'instruction override', 'system prompt leak'],
            'data_exfiltration': ['exfiltrat', 'data leak', 'sensitive data', 'pii', 'credential'],
            'credential_harvesting': ['credential', 'password', 'api key', 'token', 'secret'],
            'command_injection': ['command injection', 'os command', 'shell injection', 'exec('],
            'dependency_confusion': ['dependency', 'package confusion', 'typosquatting', 'namespace'],
            'malicious_code_execution': ['code execution', 'eval(', 'exec(', 'arbitrary code'],
            'network_egress': ['network', 'http request', 'external call', 'outbound'],
            'privilege_escalation': ['privilege', 'permission', 'authorization', 'access control'],
            'obfuscation': ['obfuscat', 'encoded', 'encrypted payload', 'base64'],
            'backdoor': ['backdoor', 'remote access', 'reverse shell', 'command and control'],
            'supply_chain_attack': ['supply chain', 'build process', 'ci/cd', 'pipeline']
        }
        
        for attack_type, keywords in patterns.items():
            for keyword in keywords:
                if keyword in message_lower or keyword in rule_id_lower:
                    return attack_type
        
        return "unknown"
