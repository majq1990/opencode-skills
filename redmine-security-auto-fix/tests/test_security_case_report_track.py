"""v2.0 报告生成与次日跟踪测试：gen_security_report / track_case_state / asset_triage_link。

全部使用内联合成 fixture，不连真实 Redmine / 钉钉。
"""
import json
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

import gen_security_report  # noqa: E402
import track_case_state  # noqa: E402
import asset_triage_link  # noqa: E402


RULES = {
    "version": "2.0.0",
    "approved_by": "待批准",
    "weights": {
        "asset_criticality": {"core": 1.0, "high": 0.8, "medium": 0.6, "low": 0.4},
        "exposure": {"public": 1.2, "internal": 1.0, "isolated": 0.6},
        "exploit_factor": {"public_exploit": 1.15, "none": 1.0},
    },
    "level_thresholds": {"Critical": 12.0, "High": 8.0, "Medium": 4.0},
    "sla_hours": {"Critical": 4, "High": 24, "Medium": 72, "Low": 336},
}


def _cases_doc():
    return {
        "meta": {
            "date": "2026-09-22",
            "formula": RULES["weights"] and "risk_score = round(cvss * w, 2)",
            "rules_version": "2.0.0",
            "source_files": {"cve": "a/cve_2026-09-22.json", "scan": "a/scan.json", "asset": "a/asset.json"},
            "dedup_key": ["asset_ip", "cve_id", "port"],
            "dedup_window_days": 7,
        },
        "stats": {
            "cve_raw": 1, "cve_clean": 1, "scan_raw": 2, "scan_clean": 2,
            "asset_raw": 2, "asset_clean": 2, "case_count": 2, "dedup_removed": 0,
            "unmapped_assets": 1, "unmapped_cve": 0, "unaffected_cve": 0,
            "levels": {"Critical": 1, "High": 1, "Medium": 0, "Low": 0},
        },
        "cases": [
            {
                "case_id": "SC-2026-09-22-001", "cve_id": "CVE-2024-3400",
                "title": "PAN-OS 命令注入", "cvss_score": 9.8, "has_public_exploit": True,
                "in_kev": True, "published": "2024-04-12", "asset_ip": "10.20.1.11",
                "hostname": "gw-web-01", "business": "门户", "service": "nginx",
                "criticality": "core", "exposure": "public", "asset_weight": 1.0,
                "exposure_factor": 1.2, "exploit_factor": 1.15, "risk_score": 13.52,
                "level": "Critical", "sla_hours": 4, "due_at": "2026-09-22 13:00",
                "owner": "", "owner_source": "fallback", "department": "安全组",
                "port": 443, "scanner_severity": "Critical", "last_seen": "2026-09-20",
                "evidence_ref": "E-001", "status": "open", "cve_source_url": "https://nvd.test",
            },
            {
                "case_id": "SC-2026-09-22-002", "cve_id": "CVE-2026-1111",
                "title": "TestVault 未授权访问", "cvss_score": 9.8, "has_public_exploit": True,
                "in_kev": True, "published": "2024-04-12", "asset_ip": "10.20.1.12",
                "hostname": "db-01", "business": "数据库", "service": "mysql",
                "criticality": "high", "exposure": "internal", "asset_weight": 0.8,
                "exposure_factor": 1.0, "exploit_factor": 1.15, "risk_score": 9.02,
                "level": "High", "sla_hours": 24, "due_at": "2026-09-23 09:00",
                "owner": "王磊", "owner_source": "asset_owner", "department": "运维组",
                "port": 3306, "scanner_severity": "High", "last_seen": "2026-09-20",
                "evidence_ref": "", "status": "open", "cve_source_url": "",
            },
        ],
        "unmapped_assets": [{"finding_id": "S3", "asset_ip": "10.99.9.9", "hostname": "ghost",
                             "cve_id": "CVE-2024-3400", "scanner_severity": "Low"}],
        "unaffected_cve": [],
        "warnings": ["[scan] S1 测试告警"],
    }


class GenReportTests(unittest.TestCase):
    def test_report_todo_state_written(self):
        doc = _cases_doc()
        with tempfile.TemporaryDirectory() as directory:
            tmp = Path(directory)
            cases_path = tmp / "cases.json"
            cases_path.write_text(json.dumps(doc, ensure_ascii=False), encoding="utf-8")
            rc = gen_security_report.main([
                "--cases", str(cases_path), "--date", "2026-09-22",
                "--project", "测试项目",
            ])
            self.assertEqual(rc, 0)
            from security_case_lib import work_path
            out = Path(work_path("output"))
            report = (out / "security_report_2026-09-22.md").read_text(encoding="utf-8")
            todo = (out / "todo_2026-09-22.md").read_text(encoding="utf-8")
            state = json.loads((out / "case_state_2026-09-22.json").read_text(encoding="utf-8"))
        self.assertIn("待复核（本报告未经人工签字，禁止推送）", report)
        self.assertIn("SC-2026-09-22-001", report)
        self.assertIn("13.52", report)
        self.assertIn("### 责任人：王磊", todo)
        self.assertIn("### 责任人：待指派", todo)  # owner 为空时按"待指派"分组
        self.assertEqual(state["status"], "pending_review")
        self.assertEqual(len(state["cases"]), 2)

    def test_missing_date_stops(self):
        with self.assertRaises(SystemExit) as ctx:
            gen_security_report.main([])
        self.assertEqual(ctx.exception.code, 2)


class TrackStateTests(unittest.TestCase):
    def _state(self, due_past, due_future):
        base = _cases_doc()
        c0, c1 = base["cases"]
        c0["due_at"] = due_past
        c1["due_at"] = due_future
        return {
            "date": "2026-09-22", "project": "测试项目", "rules_version": "2.0.0",
            "status": "pending_review",
            "cases": [dict(c, status="open", track_history=[{"date": "2026-09-22", "action": "created"}]) for c in (c0, c1)],
            "review_log": [],
        }

    def test_overdue_progress_and_pending_verify(self):
        with tempfile.TemporaryDirectory() as directory:
            tmp = Path(directory)
            state_path = tmp / "case_state.json"
            state_path.write_text(
                json.dumps(self._state("2026-09-21 13:00", "2026-09-23 09:00"), ensure_ascii=False),
                encoding="utf-8")
            progress_path = tmp / "progress.json"
            progress_path.write_text(json.dumps({
                "SC-2026-09-22-002": {"status": "fixed", "by": "王磊", "note": "已升级并复测"},
            }, ensure_ascii=False), encoding="utf-8")
            rc = track_case_state.main([
                "--date", "2026-09-23", "--state", str(state_path), "--progress", str(progress_path),
            ])
            self.assertEqual(rc, 0)
            reminder = (Path(track_case_state.__file__).parent.parent
                        / "work" / "security_case" / "output" / "nextday_reminder_2026-09-23.md")
            md = reminder.read_text(encoding="utf-8")
            state = json.loads(state_path.read_text(encoding="utf-8"))
        self.assertIn("超期未闭环（1 项）", md)
        self.assertIn("SC-2026-09-22-001", md)
        self.assertIn("待验证（1 项，责任人已回报修复）", md)
        self.assertIn("| fixed |", md)
        # 回填备注只进状态文件 track_history，不进提醒 md
        self.assertNotIn("已升级并复测", md)
        self.assertEqual(state["track_log"][-1]["overdue"], 1)
        self.assertEqual(state["track_log"][-1]["pending_verify"], 1)
        # track_history 已记录状态流转
        c2 = [c for c in state["cases"] if c["case_id"] == "SC-2026-09-22-002"][0]
        self.assertEqual(c2["status"], "fixed")
        self.assertEqual(c2["track_history"][-1]["by"], "王磊")

    def test_missing_state_stops(self):
        with self.assertRaises(SystemExit) as ctx:
            track_case_state.main(["--date", "2026-09-23", "--state", "Z:/no/such.json"])
        self.assertEqual(ctx.exception.code, 2)


class AssetTriageLinkTests(unittest.TestCase):
    def test_attach_matches_and_counts(self):
        vulns = [
            {"id": 1, "name": "PAN-OS RCE", "cve": "cve-2024-3400"},
            {"id": 2, "name": "多CVE漏洞", "cve": ["CVE-2024-3400", "CVE-2026-1111"]},
            {"id": 3, "name": "无CVE漏洞", "cve": ""},
        ]
        summary = asset_triage_link.attach(vulns, _cases_doc())
        self.assertEqual(summary["matched_vulns"], 2)
        self.assertEqual(summary["unmatched_vulns"], 1)
        self.assertEqual(summary["case_links"], 3)  # v1 命中 1 案件，v2 命中 2 案件
        self.assertEqual(vulns[0]["asset_triage"][0]["case_id"], "SC-2026-09-22-001")
        self.assertEqual(len(vulns[1]["asset_triage"]), 2)
        self.assertNotIn("asset_triage", vulns[2])

    def test_render_section_empty_when_no_match(self):
        vulns = [{"id": 1, "name": "无命中", "cve": "CVE-9999-0001"}]
        asset_triage_link.attach(vulns, _cases_doc())
        self.assertEqual(asset_triage_link.render_section(vulns, {}), "")

    def test_render_section_table_alignment(self):
        vulns = [{"id": 1, "name": "PAN-OS RCE", "cve": "CVE-2024-3400"}]
        asset_triage_link.attach(vulns, _cases_doc())
        section = asset_triage_link.render_section(vulns, {"rules_version": "2.0.0", "date": "2026-09-22"})
        self.assertIn("## 资产对照与责任人", section)
        data_rows = [l for l in section.splitlines() if "| SC-2026-09-22-001 |" in l]
        self.assertEqual(len(data_rows), 1)
        cols = [c.strip() for c in data_rows[0].strip("|").split("|")]
        self.assertEqual(len(cols), 8)
        self.assertEqual(cols[2], "SC-2026-09-22-001")


if __name__ == "__main__":
    unittest.main()
