"""
Scanner Orchestrator
Main controller coordinating all security scanners
"""

import logging
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

from lib.cisco_scanner import CiscoSkillScanner, ScanResult, Finding
from lib.clawsec_integration import ClawSecIntegration
from lib.report_generator import ReportGenerator

logger = logging.getLogger(__name__)


@dataclass
class BulkScanResult:
    """Result of bulk scanning multiple skills"""
    scan_time: str
    total_scanned: int
    results: List[ScanResult] = field(default_factory=list)
    failed_scans: List[Dict] = field(default_factory=list)
    aggregate_severity: Dict[str, int] = field(default_factory=dict)
    
    def __post_init__(self):
        if not self.aggregate_severity:
            self.aggregate_severity = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}


class ScannerOrchestrator:
    """
    Main orchestrator for skill security scanning
    Coordinates Cisco Skill Scanner, ClawSec integration, and report generation
    """
    
    def __init__(self, 
                 severity_threshold: str = "medium",
                 auto_remediate: bool = False):
        self.severity_threshold = severity_threshold
        self.auto_remediate = auto_remediate
        
        # Initialize scanners
        self.cisco_scanner = CiscoSkillScanner(severity_threshold)
        self.clawsec = ClawSecIntegration()
        self.report_gen = ReportGenerator()
        
        logger.info("ScannerOrchestrator initialized")
    
    def scan_skill(self, 
                   skill_path: str, 
                   scanners: Optional[List[str]] = None,
                   check_cve: bool = True) -> ScanResult:
        """
        Run security scan on a single skill
        
        Args:
            skill_path: Path to skill directory
            scanners: List of scanners to use ['cisco', 'clawsec'] or None for all
            check_cve: Whether to check CVE database
            
        Returns:
            ScanResult with findings
        """
        skill_path = Path(skill_path).resolve()
        
        if not skill_path.exists():
            raise FileNotFoundError(f"Skill path not found: {skill_path}")
        
        if scanners is None:
            scanners = ["cisco", "clawsec"]
        
        logger.info(f"Scanning skill: {skill_path.name} with scanners: {scanners}")
        
        all_findings = []
        scanners_used = []
        
        # Run Cisco Skill Scanner
        if "cisco" in scanners:
            logger.debug("Running Cisco Skill Scanner")
            cisco_result = self.cisco_scanner.scan(str(skill_path))
            
            if cisco_result.error:
                logger.warning(f"Cisco scanner error: {cisco_result.error}")
            else:
                all_findings.extend(cisco_result.findings)
                scanners_used.append("cisco")
        
        # Run ClawSec checks
        if "clawsec" in scanners and check_cve:
            logger.debug("Running ClawSec checks")
            clawsec_findings = self._run_clawsec_checks(skill_path)
            all_findings.extend(clawsec_findings)
            scanners_used.append("clawsec")
        
        # Calculate severity counts
        severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}
        for finding in all_findings:
            sev = finding.severity.lower()
            if sev in severity_counts:
                severity_counts[sev] += 1
        
        # Build final result
        result = ScanResult(
            skill_name=skill_path.name,
            skill_path=str(skill_path),
            scan_time=datetime.now().isoformat(),
            findings=all_findings,
            severity_counts=severity_counts,
            scanners_used=scanners_used
        )
        
        logger.info(f"Scan complete: {len(all_findings)} findings ({severity_counts})")
        
        # Auto-remediation if enabled
        if self.auto_remediate and severity_counts.get("critical", 0) > 0:
            self._auto_remediate(skill_path)
        
        return result
    
    def scan_all_skills(self, 
                       skills_dir: Optional[str] = None,
                       max_workers: int = 4) -> BulkScanResult:
        """
        Scan all skills in a directory
        
        Args:
            skills_dir: Directory containing skills, or None for default
            max_workers: Maximum parallel scan workers
            
        Returns:
            BulkScanResult with all results
        """
        if skills_dir is None:
            skills_dir = os.getenv(
                "OPENCLAW_SKILLS_DIR",
                str(Path.home() / ".openclaw" / "skills")
            )
        
        skills_dir = Path(skills_dir)
        
        if not skills_dir.exists():
            raise FileNotFoundError(f"Skills directory not found: {skills_dir}")
        
        # Find all skill directories
        skill_paths = [p for p in skills_dir.iterdir() if p.is_dir()]
        logger.info(f"Found {len(skill_paths)} skills to scan in {skills_dir}")
        
        results = []
        failed = []
        aggregate = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}
        
        # Scan in parallel
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_path = {
                executor.submit(self._scan_skill_safe, str(path)): path 
                for path in skill_paths
            }
            
            for future in as_completed(future_to_path):
                path = future_to_path[future]
                try:
                    result = future.result()
                    results.append(result)
                    
                    # Aggregate severity counts
                    for sev, count in result.severity_counts.items():
                        aggregate[sev] += aggregate.get(sev, 0) + count
                        
                except Exception as e:
                    logger.error(f"Scan failed for {path}: {e}")
                    failed.append({
                        "skill_path": str(path),
                        "error": str(e)
                    })
        
        return BulkScanResult(
            scan_time=datetime.now().isoformat(),
            total_scanned=len(results),
            results=results,
            failed_scans=failed,
            aggregate_severity=aggregate
        )
    
    def _scan_skill_safe(self, skill_path: str) -> ScanResult:
        """Wrapper for safe scanning with error handling"""
        try:
            return self.scan_skill(skill_path)
        except Exception as e:
            logger.error(f"Safe scan failed for {skill_path}: {e}")
            return ScanResult(
                skill_name=Path(skill_path).name,
                skill_path=skill_path,
                scan_time=datetime.now().isoformat(),
                error=str(e)
            )
    
    def _run_clawsec_checks(self, skill_path: Path) -> List[Finding]:
        """Run ClawSec threat intelligence checks"""
        findings = []
        
        # Check CVE database
        threats = self.clawsec.check_cve_database(skill_path.name)
        
        for threat in threats:
            finding = Finding(
                rule_id=threat.cve_id,
                attack_type="known_vulnerability",
                severity=threat.severity,
                message=f"Known vulnerability: {threat.description}",
                file_path=str(skill_path),
                confidence=1.0,
                remediation=f"Update to patched version: {', '.join(threat.patched_versions)}"
            )
            findings.append(finding)
        
        return findings
    
    def _auto_remediate(self, skill_path: Path):
        """Auto-remediate critical findings by quarantining skill"""
        logger.warning(f"Auto-remediation triggered for {skill_path.name}")
        
        # Create quarantine directory
        quarantine_dir = Path(__file__).parent.parent / "quarantine"
        quarantine_dir.mkdir(exist_ok=True)
        
        # Move skill to quarantine
        import shutil
        quarantine_path = quarantine_dir / skill_path.name
        
        try:
            shutil.move(str(skill_path), str(quarantine_path))
            logger.info(f"Skill quarantined: {quarantine_path}")
            
            # Create quarantine marker
            marker = quarantine_path / ".QUARANTINED"
            marker.write_text(f"Quarantined at {datetime.now().isoformat()}\n")
            
        except Exception as e:
            logger.error(f"Failed to quarantine {skill_path}: {e}")
    
    def get_scanner_status(self) -> Dict:
        """Get status of all scanners"""
        return {
            "cisco_scanner": {
                "available": self.cisco_scanner.is_available(),
                "version": self.cisco_scanner.get_version()
            },
            "clawsec": {
                "feed_url": self.clawsec.feed_url,
                "cache_loaded": self.clawsec._cache_loaded
            },
            "orchestrator": {
                "severity_threshold": self.severity_threshold,
                "auto_remediate": self.auto_remediate
            }
        }
