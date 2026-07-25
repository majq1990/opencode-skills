#!/usr/bin/env python3
"""
Test runner for malicious skill samples
"""

import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.scanner_orchestrator import ScannerOrchestrator
from lib.report_generator import ReportGenerator

TEST_SAMPLES = [
    "prompt-injection-skill",
    "credential-harvester-skill", 
    "data-exfiltration-skill",
    "command-injection-skill",
    "dependency-confusion-skill",
    "malicious-code-execution-skill",
    "network-egress-skill",
    "privilege-escalation-skill",
    "obfuscation-skill",
    "backdoor-skill"
]

EXPECTED_ATTACKS = {
    "prompt-injection-skill": "prompt_injection",
    "credential-harvester-skill": "credential_harvesting",
    "data-exfiltration-skill": "data_exfiltration",
    "command-injection-skill": "command_injection",
    "dependency-confusion-skill": "dependency_confusion",
    "malicious-code-execution-skill": "malicious_code_execution",
    "network-egress-skill": "network_egress",
    "privilege-escalation-skill": "privilege_escalation",
    "obfuscation-skill": "obfuscation",
    "backdoor-skill": "backdoor"
}

def main():
    print("=" * 60)
    print("Skill Security Auditor - Detection Rate Test")
    print("=" * 60)
    print()
    
    orchestrator = ScannerOrchestrator()
    results = {}
    detected_count = 0
    
    fixtures_dir = Path(__file__).parent / "fixtures"
    
    for sample in TEST_SAMPLES:
        skill_path = fixtures_dir / sample
        print(f"Testing: {sample}...", end=" ", flush=True)
        
        try:
            result = orchestrator.scan_skill(str(skill_path))
            
            high_or_critical = [f for f in result.findings if f.severity in ["critical", "high"]]
            medium_or_above = [f for f in result.findings if f.severity in ["critical", "high", "medium"]]
            
            results[sample] = {
                "total_findings": len(result.findings),
                "high_critical": len(high_or_critical),
                "medium_above": len(medium_or_above),
                "attack_types": list(set(f.attack_type for f in result.findings))
            }
            
            if medium_or_above:
                detected_count += 1
                print(f"✅ DETECTED ({len(medium_or_above)} issues)")
            else:
                print(f"❌ Not detected")
                
        except Exception as e:
            print(f"❌ Error: {e}")
            results[sample] = {"error": str(e)}
    
    print()
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print()
    
    detection_rate = (detected_count / len(TEST_SAMPLES)) * 100
    print(f"Total samples: {len(TEST_SAMPLES)}")
    print(f"Detected: {detected_count}")
    print(f"Detection rate: {detection_rate:.1f}%")
    print()
    
    print("Detailed Results:")
    print("-" * 60)
    for sample, result in results.items():
        expected = EXPECTED_ATTACKS.get(sample, "unknown")
        attack_types = result.get("attack_types", [])
        detected = expected in attack_types or result.get("medium_above", 0) > 0
        
        status = "✅" if detected else "❌"
        print(f"{status} {sample}")
        print(f"   Expected: {expected}")
        print(f"   Found: {', '.join(attack_types) if attack_types else 'None'}")
        print(f"   Issues: {result.get('medium_above', 0)} medium+")
        print()
    
    # Save results to JSON
    report = {
        "test_date": str(Path(__file__).stat().st_mtime),
        "total_samples": len(TEST_SAMPLES),
        "detected": detected_count,
        "detection_rate": detection_rate,
        "results": results
    }
    
    report_path = Path(__file__).parent / "detection_test_results.json"
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\nResults saved to: {report_path}")

if __name__ == "__main__":
    main()
