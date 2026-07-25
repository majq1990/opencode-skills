"""
ClawSec Integration
Handles CVE database checks and SHA256 checksum verification
"""

import hashlib
import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Dict
import json

logger = logging.getLogger(__name__)


@dataclass
class ThreatIntel:
    """Threat intelligence entry"""
    cve_id: str
    severity: str
    description: str
    skill_name: str
    affected_versions: List[str] = field(default_factory=list)
    patched_versions: List[str] = field(default_factory=list)
    references: List[str] = field(default_factory=list)
    published_date: str = ""


@dataclass
class ChecksumResult:
    """Result of checksum verification"""
    valid: bool
    computed_hash: str
    expected_hash: str
    file_path: str
    message: str


class ClawSecIntegration:
    """
    Integration with ClawSec threat intelligence feed
    """
    
    def __init__(self, feed_url: Optional[str] = None):
        self.feed_url = feed_url or os.getenv(
            "CLAWSEC_FEED_URL", 
            "https://api.clawsec.io/v1/feed"
        )
        self._cve_cache: Dict[str, List[ThreatIntel]] = {}
        self._cache_loaded = False
    
    def check_cve_database(self, skill_name: str) -> List[ThreatIntel]:
        """
        Query ClawSec CVE database for skill vulnerabilities
        
        Args:
            skill_name: Name of the skill to check
            
        Returns:
            List of threat intelligence entries
        """
        # Load cache if not already loaded
        if not self._cache_loaded:
            self._load_cve_cache()
        
        # Check cache for skill
        threats = self._cve_cache.get(skill_name.lower(), [])
        
        # Also check by partial match
        for cached_name, cached_threats in self._cve_cache.items():
            if skill_name.lower() in cached_name or cached_name in skill_name.lower():
                if cached_name != skill_name.lower():
                    threats.extend(cached_threats)
        
        logger.info(f"Found {len(threats)} CVE entries for {skill_name}")
        return threats
    
    def verify_checksum(self, skill_path: str, expected_hash: str) -> ChecksumResult:
        """
        Verify skill integrity using SHA256
        
        Args:
            skill_path: Path to skill directory
            expected_hash: Expected SHA256 hash
            
        Returns:
            ChecksumResult with verification status
        """
        skill_path = Path(skill_path)
        
        if not skill_path.exists():
            return ChecksumResult(
                valid=False,
                computed_hash="",
                expected_hash=expected_hash,
                file_path=str(skill_path),
                message=f"Skill path not found: {skill_path}"
            )
        
        try:
            # Compute hash of skill directory contents
            computed_hash = self._compute_directory_hash(skill_path)
            
            valid = computed_hash.lower() == expected_hash.lower()
            
            if valid:
                message = "Checksum verification passed"
                logger.info(f"Checksum valid for {skill_path}")
            else:
                message = f"Checksum mismatch! Expected: {expected_hash}, Got: {computed_hash}"
                logger.warning(f"Checksum mismatch for {skill_path}")
            
            return ChecksumResult(
                valid=valid,
                computed_hash=computed_hash,
                expected_hash=expected_hash,
                file_path=str(skill_path),
                message=message
            )
            
        except Exception as e:
            logger.error(f"Checksum verification failed: {e}")
            return ChecksumResult(
                valid=False,
                computed_hash="",
                expected_hash=expected_hash,
                file_path=str(skill_path),
                message=f"Verification error: {str(e)}"
            )
    
    def compute_skill_hash(self, skill_path: str) -> str:
        """
        Compute SHA256 hash of skill directory
        
        Args:
            skill_path: Path to skill directory
            
        Returns:
            SHA256 hash string
        """
        return self._compute_directory_hash(Path(skill_path))
    
    def _compute_directory_hash(self, path: Path) -> str:
        """Compute SHA256 hash of directory contents"""
        sha256 = hashlib.sha256()
        
        # Get all files sorted for consistent hashing
        files = sorted(path.rglob('*'))
        
        for file_path in files:
            if file_path.is_file():
                # Include relative path in hash
                rel_path = str(file_path.relative_to(path))
                sha256.update(rel_path.encode())
                
                # Include file content in hash
                try:
                    with open(file_path, 'rb') as f:
                        for chunk in iter(lambda: f.read(8192), b''):
                            sha256.update(chunk)
                except Exception as e:
                    logger.warning(f"Could not read {file_path}: {e}")
        
        return sha256.hexdigest()
    
    def _load_cve_cache(self):
        """Load CVE database from cache or API"""
        try:
            # In production, this would fetch from ClawSec API
            # For now, use local cache file
            cache_path = Path(__file__).parent.parent / "config" / "cve_cache.json"
            
            if cache_path.exists():
                with open(cache_path, 'r') as f:
                    data = json.load(f)
                    self._cve_cache = self._parse_cve_cache(data)
                    logger.info(f"Loaded {len(self._cve_cache)} CVE entries from cache")
            else:
                logger.warning("CVE cache not found, using empty database")
                self._cve_cache = {}
            
            self._cache_loaded = True
            
        except Exception as e:
            logger.error(f"Failed to load CVE cache: {e}")
            self._cve_cache = {}
            self._cache_loaded = True
    
    def _parse_cve_cache(self, data: Dict) -> Dict[str, List[ThreatIntel]]:
        """Parse CVE cache data"""
        cache = {}
        
        for skill_name, entries in data.get("cves", {}).items():
            threats = []
            for entry in entries:
                threat = ThreatIntel(
                    cve_id=entry.get("cve_id", "UNKNOWN"),
                    severity=entry.get("severity", "unknown"),
                    description=entry.get("description", ""),
                    skill_name=skill_name,
                    affected_versions=entry.get("affected_versions", []),
                    patched_versions=entry.get("patched_versions", []),
                    references=entry.get("references", []),
                    published_date=entry.get("published_date", "")
                )
                threats.append(threat)
            cache[skill_name.lower()] = threats
        
        return cache
    
    def refresh_cve_database(self) -> bool:
        """
        Refresh CVE database from ClawSec feed
        
        Returns:
            True if successful
        """
        try:
            # In production, this would fetch from API
            # For now, just reload local cache
            self._cache_loaded = False
            self._load_cve_cache()
            logger.info("CVE database refreshed")
            return True
        except Exception as e:
            logger.error(f"Failed to refresh CVE database: {e}")
            return False
