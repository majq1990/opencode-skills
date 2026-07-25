#!/usr/bin/env python3
"""
claw-audit: CLI for Skill Security Auditor
Usage: claw-audit scan <skill-path>
"""

import argparse
import logging
import os
import sys
from pathlib import Path

# Add lib to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.scanner_orchestrator import ScannerOrchestrator
from lib.report_generator import ReportGenerator

# Setup logging
def setup_logging(verbose: bool = False):
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


def cmd_scan(args):
    """Scan a single skill"""
    setup_logging(args.verbose)
    
    skill_path = Path(args.skill_path).resolve()
    
    if not skill_path.exists():
        print(f"❌ Error: Skill path not found: {skill_path}", file=sys.stderr)
        return 1
    
    print(f"🔍 Scanning skill: {skill_path.name}")
    print(f"   Path: {skill_path}")
    print()
    
    # Initialize orchestrator
    orchestrator = ScannerOrchestrator(
        severity_threshold=args.severity,
        auto_remediate=args.auto_remediate
    )
    
    # Run scan
    try:
        result = orchestrator.scan_skill(
            str(skill_path),
            scanners=args.scanners,
            check_cve=not args.no_cve
        )
    except Exception as e:
        print(f"❌ Scan failed: {e}", file=sys.stderr)
        return 1
    
    # Handle errors
    if result.error:
        print(f"❌ Scan error: {result.error}", file=sys.stderr)
        return 1
    
    # Display results
    print(f"✅ Scan complete in {result.scan_duration_ms}ms")
    print()
    
    # Summary
    total = len(result.findings)
    if total == 0:
        print("🟢 No security issues detected")
    else:
        print("📊 Findings Summary:")
        print()
        
        severity_icons = {
            "critical": "🔴",
            "high": "🟠",
            "medium": "🟡",
            "low": "🟢",
            "info": "🔵"
        }
        
        for sev in ["critical", "high", "medium", "low", "info"]:
            count = result.severity_counts.get(sev, 0)
            icon = severity_icons.get(sev, "⚪")
            if count > 0:
                print(f"  {icon} {sev.upper()}: {count}")
        
        print()
        
        # Detailed findings
        if args.detailed:
            print("📋 Detailed Findings:")
            print()
            for i, finding in enumerate(result.findings, 1):
                icon = severity_icons.get(finding.severity.lower(), "⚪")
                print(f"  {icon} #{i} [{finding.severity.upper()}] {finding.attack_type}")
                print(f"     Rule: {finding.rule_id}")
                print(f"     File: {finding.file_path}", end="")
                if finding.line_number > 0:
                    print(f":{finding.line_number}")
                else:
                    print()
                print(f"     {finding.message[:80]}{'...' if len(finding.message) > 80 else ''}")
                print()
    
    # Generate output files
    report_gen = ReportGenerator()
    
    if args.output:
        # Determine format from extension or flag
        output_path = Path(args.output)
        
        if args.format == "sarif" or output_path.suffix == ".sarif":
            report_gen.generate_sarif(result, str(output_path))
            print(f"📄 SARIF report saved: {output_path}")
            
        elif args.format == "json" or output_path.suffix == ".json":
            json_report = report_gen.generate_json(result)
            output_path.write_text(json_report)
            print(f"📄 JSON report saved: {output_path}")
            
        elif args.format == "markdown" or output_path.suffix in [".md", ".markdown"]:
            md_report = report_gen.generate_markdown(result)
            output_path.write_text(md_report)
            print(f"📄 Markdown report saved: {output_path}")
    
    # Print to stdout if requested
    if args.stdout:
        report_gen = ReportGenerator()
        if args.format == "json":
            print(report_gen.generate_json(result))
        elif args.format == "markdown":
            print(report_gen.generate_markdown(result))
    
    # Exit code based on severity
    if result.severity_counts.get("critical", 0) > 0:
        return 2  # Critical issues found
    elif result.severity_counts.get("high", 0) > 0:
        return 1  # High issues found
    
    return 0


def cmd_scan_all(args):
    """Scan all skills in directory"""
    setup_logging(args.verbose)
    
    skills_dir = args.skills_dir or os.getenv(
        "OPENCLAW_SKILLS_DIR",
        str(Path.home() / ".openclaw" / "skills")
    )
    
    print(f"🔍 Scanning all skills in: {skills_dir}")
    print()
    
    orchestrator = ScannerOrchestrator(
        severity_threshold=args.severity,
        auto_remediate=args.auto_remediate
    )
    
    try:
        result = orchestrator.scan_all_skills(skills_dir, max_workers=args.workers)
    except Exception as e:
        print(f"❌ Bulk scan failed: {e}", file=sys.stderr)
        return 1
    
    print(f"✅ Scanned {result.total_scanned} skills")
    print()
    
    # Aggregate results
    print("📊 Aggregate Severity:")
    severity_icons = {
        "critical": "🔴",
        "high": "🟠",
        "medium": "🟡",
        "low": "🟢",
        "info": "🔵"
    }
    
    for sev in ["critical", "high", "medium", "low", "info"]:
        count = result.aggregate_severity.get(sev, 0)
        icon = severity_icons.get(sev, "⚪")
        print(f"  {icon} {sev.upper()}: {count}")
    
    print()
    
    # Show skills with issues
    skills_with_issues = [
        r for r in result.results 
        if len(r.findings) > 0
    ]
    
    if skills_with_issues:
        print(f"⚠️  {len(skills_with_issues)} skills with security issues:")
        print()
        for r in skills_with_issues:
            critical = r.severity_counts.get("critical", 0)
            high = r.severity_counts.get("high", 0)
            print(f"  - {r.skill_name}: {len(r.findings)} findings (🔴{critical} 🟠{high})")
        print()
    
    if result.failed_scans:
        print(f"❌ {len(result.failed_scans)} scans failed")
    
    return 0


def cmd_status(args):
    """Check scanner status"""
    setup_logging(args.verbose)
    
    orchestrator = ScannerOrchestrator()
    status = orchestrator.get_scanner_status()
    
    print("🔧 Scanner Status")
    print()
    
    cisco = status["cisco_scanner"]
    print(f"Cisco Skill Scanner:")
    print(f"  Available: {'✅ Yes' if cisco['available'] else '❌ No'}")
    print(f"  Version: {cisco['version']}")
    print()
    
    clawsec = status["clawsec"]
    print(f"ClawSec Integration:")
    print(f"  Feed URL: {clawsec['feed_url']}")
    print(f"  Cache Loaded: {'✅ Yes' if clawsec['cache_loaded'] else '❌ No'}")
    print()
    
    orch = status["orchestrator"]
    print(f"Orchestrator:")
    print(f"  Severity Threshold: {orch['severity_threshold']}")
    print(f"  Auto-remediation: {'✅ Enabled' if orch['auto_remediate'] else '❌ Disabled'}")
    
    return 0


def main():
    parser = argparse.ArgumentParser(
        prog='claw-audit',
        description='Security auditor for OpenClaw skills'
    )
    
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # scan command
    scan_parser = subparsers.add_parser(
        'scan',
        help='Scan a single skill'
    )
    scan_parser.add_argument(
        'skill_path',
        help='Path to skill directory'
    )
    scan_parser.add_argument(
        '-s', '--scanners',
        nargs='+',
        choices=['cisco', 'clawsec'],
        default=None,
        help='Scanners to use (default: all)'
    )
    scan_parser.add_argument(
        '--severity',
        choices=['critical', 'high', 'medium', 'low', 'info'],
        default='medium',
        help='Minimum severity to report'
    )
    scan_parser.add_argument(
        '--no-cve',
        action='store_true',
        help='Skip CVE database check'
    )
    scan_parser.add_argument(
        '--auto-remediate',
        action='store_true',
        help='Auto-quarantine skills with critical issues'
    )
    scan_parser.add_argument(
        '-o', '--output',
        help='Output file path'
    )
    scan_parser.add_argument(
        '-f', '--format',
        choices=['sarif', 'json', 'markdown'],
        default='markdown',
        help='Output format'
    )
    scan_parser.add_argument(
        '--stdout',
        action='store_true',
        help='Also print report to stdout'
    )
    scan_parser.add_argument(
        '-d', '--detailed',
        action='store_true',
        help='Show detailed findings'
    )
    scan_parser.set_defaults(func=cmd_scan)
    
    # scan-all command
    scan_all_parser = subparsers.add_parser(
        'scan-all',
        help='Scan all skills in directory'
    )
    scan_all_parser.add_argument(
        'skills_dir',
        nargs='?',
        help='Skills directory (default: OPENCLAW_SKILLS_DIR)'
    )
    scan_all_parser.add_argument(
        '-w', '--workers',
        type=int,
        default=4,
        help='Parallel scan workers (default: 4)'
    )
    scan_all_parser.add_argument(
        '--severity',
        choices=['critical', 'high', 'medium', 'low', 'info'],
        default='medium',
        help='Minimum severity to report'
    )
    scan_all_parser.add_argument(
        '--auto-remediate',
        action='store_true',
        help='Auto-quarantine skills with critical issues'
    )
    scan_all_parser.set_defaults(func=cmd_scan_all)
    
    # status command
    status_parser = subparsers.add_parser(
        'status',
        help='Check scanner status'
    )
    status_parser.set_defaults(func=cmd_status)
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    return args.func(args)


if __name__ == '__main__':
    sys.exit(main())
