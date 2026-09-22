"""v2.0 三源研判链路测试：collect_asset_info / collect_scanner_results / triage_cases。

全部使用内联合成 fixture，不连真实 Redmine / 钉钉 / CMDB / 扫描器。
"""
import json
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

import collect_asset_info  # noqa: E402
import collect_scanner_results  # noqa: E402
import triage_cases  # noqa: E402


RULES = {
    "weights": {
        "asset_criticality": {"core": 1.0, "high": 0.8, "medium": 0.6, "low": 0.4},
        "exposure": {"public": 1.2, "internal": 1.0, "isolated": 0.6},
        "exploit_factor": {"public_exploit": 1.15, "none": 1.0},
    },
    "level_thresholds": {"Critical": 12.0, "High": 8.0, "Medium": 4.0},
}


def _write(path, payload):
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


class AssetNormalizeTests(unittest.TestCase):
    def test_dirty_values_fall_back_and_warn(self):
        items = [
            {"asset_ip": "10.20.1.11", "criticality": "核心", "exposure": "公网", "owner": "甲"},
            {"asset_ip": "", "criticality": "high", "exposure": "public"},  # 缺 IP 丢弃
            {"asset_ip": "10.20.1.12", "criticality": "超高", "exposure": "未知"},  # 脏值回退
        ]
        clean, warnings, dedup_removed = collect_asset_info.normalize(items, RULES)
        self.assertEqual(dedup_removed, 0)
        self.assertEqual([c["asset_ip"] for c in clean], ["10.20.1.11", "10.20.1.12"])
        first = clean[0]
        self.assertEqual((first["criticality"], first["exposure"]), ("core", "public"))
        second = clean[1]
        self.assertEqual((second["criticality"], second["exposure"]), ("medium", "internal"))
        self.assertTrue(any("脏值" in w for w in warnings))
        self.assertTrue(any("缺 asset_ip" in w for w in warnings))

    def test_same_ip_keeps_newest_record(self):
        items = [
            {"asset_ip": "10.20.1.11", "hostname": "old", "updated_at": "2026-01-01"},
            {"asset_ip": "10.20.1.11", "hostname": "new", "updated_at": "2026-09-01"},
        ]
        clean, warnings, dedup_removed = collect_asset_info.normalize(items, RULES)
        self.assertEqual(dedup_removed, 1)
        self.assertEqual(len(clean), 1)
        self.assertEqual(clean[0]["hostname"], "new")
        self.assertTrue(any("同 IP" in w for w in warnings))


class ScannerNormalizeTests(unittest.TestCase):
    def test_alias_and_case_severity(self):
        items = [
            {"asset_ip": "10.20.1.11", "cve_id": "CVE-2024-3400", "scanner_severity": "CRITICAL"},
            {"asset_ip": "10.20.1.12", "cve_id": "CVE-2024-3400", "scanner_severity": "严重"},
            {"asset_ip": "10.20.1.13", "cve_id": "CVE-2024-3400", "scanner_severity": "离谱"},
        ]
        clean, warnings = collect_scanner_results.normalize(items)
        self.assertEqual([c["scanner_severity"] for c in clean],
                         ["Critical", "Critical", "unknown"])
        self.assertTrue(any("别名" in w for w in warnings))
        self.assertTrue(any("无法识别" in w for w in warnings))

    def test_missing_ip_or_cve_dropped(self):
        items = [
            {"asset_ip": "", "cve_id": "CVE-1"},
            {"asset_ip": "10.20.1.11", "cve_id": ""},
        ]
        clean, warnings = collect_scanner_results.normalize(items)
        self.assertEqual(clean, [])
        self.assertEqual(len(warnings), 2)


class TriageTests(unittest.TestCase):
    def test_level_of_thresholds(self):
        th = RULES["level_thresholds"]
        self.assertEqual(triage_cases.level_of(12.0, th), "Critical")
        self.assertEqual(triage_cases.level_of(8.0, th), "High")
        self.assertEqual(triage_cases.level_of(4.0, th), "Medium")
        self.assertEqual(triage_cases.level_of(3.9, th), "Low")

    def test_dedup_keeps_latest_last_seen(self):
        findings = [
            {"finding_id": "A", "asset_ip": "1", "cve_id": "C", "port": 443, "last_seen": "2026-09-01"},
            {"finding_id": "B", "asset_ip": "1", "cve_id": "C", "port": 443, "last_seen": "2026-09-02"},
        ]
        kept, removed = triage_cases.dedup(findings, ["asset_ip", "cve_id", "port"])
        self.assertEqual(len(kept), 1)
        self.assertEqual(kept[0]["finding_id"], "B")
        self.assertEqual(len(removed), 1)

    def test_end_to_end_scoring_and_owner_fallback(self):
        cve_doc = {"meta": {"record_count_raw": 1}, "items": [{
            "cve_id": "CVE-2024-3400", "title": "PAN-OS 命令注入", "cvss_score": 9.8,
            "has_public_exploit": True, "in_kev": True, "published": "2024-04-12",
            "source_url": "https://example.test/cve",
        }]}
        asset_doc = {"meta": {"record_count_raw": 2}, "items": [
            {"asset_ip": "10.20.1.11", "hostname": "gw-web-01", "business": "门户",
             "service": "nginx", "criticality": "core", "exposure": "public",
             "owner": "", "department": "安全组"},
            {"asset_ip": "10.20.1.12", "hostname": "db-01", "business": "数据库",
             "service": "mysql", "criticality": "high", "exposure": "internal",
             "owner": "王磊", "department": "运维组"},
        ]}
        scan_doc = {"meta": {"record_count_raw": 3}, "items": [
            {"finding_id": "S1", "asset_ip": "10.20.1.11", "hostname": "gw-web-01",
             "port": 443, "cve_id": "CVE-2024-3400", "scanner_severity": "critical",
             "last_seen": "2026-09-20", "owner": "扫描器说的"},
            {"finding_id": "S2", "asset_ip": "10.20.1.12", "hostname": "db-01",
             "port": 3306, "cve_id": "CVE-2024-3400", "scanner_severity": "high",
             "last_seen": "2026-09-20"},
            {"finding_id": "S3", "asset_ip": "10.99.9.9", "hostname": "ghost",
             "port": 80, "cve_id": "CVE-2024-3400", "scanner_severity": "low",
             "last_seen": "2026-09-20"},
        ]}
        with tempfile.TemporaryDirectory() as directory:
            tmp = Path(directory)
            cve_path, asset_path, scan_path = tmp / "cve.json", tmp / "asset.json", tmp / "scan.json"
            out_path = tmp / "cases.json"
            _write(cve_path, cve_doc)
            _write(asset_path, asset_doc)
            _write(scan_path, scan_doc)
            rc = triage_cases.main([
                "--cve", str(cve_path), "--asset", str(asset_path), "--scan", str(scan_path),
                "--date", "2026-09-22", "--out", str(out_path),
            ])
            self.assertEqual(rc, 0)
            doc = json.loads(out_path.read_text(encoding="utf-8"))
        # S1: 9.8 * 1.0(core) * 1.2(public) * 1.15(exp) = 13.52 → Critical
        # S2: 9.8 * 0.8(high) * 1.0(internal) * 1.15 = 9.02 → High
        # S3: 台账外资产 → unmapped
        self.assertEqual(doc["stats"]["case_count"], 2)
        self.assertEqual(doc["stats"]["unmapped_assets"], 1)
        self.assertEqual(doc["stats"]["levels"], {"Critical": 1, "High": 1, "Medium": 0, "Low": 0})
        top = doc["cases"][0]
        self.assertEqual((top["asset_ip"], top["level"]), ("10.20.1.11", "Critical"))
        self.assertEqual(top["owner_source"], "fallback")  # 台账缺责任人 → 兜底
        db_case = doc["cases"][1]
        self.assertEqual((db_case["owner"], db_case["owner_source"]), ("王磊", "asset_owner"))
        self.assertTrue(any("owner" in w and "不一致" in w for w in doc["warnings"]))

    def test_zero_cases_stops(self):
        cve_doc = {"meta": {}, "items": []}
        asset_doc = {"meta": {}, "items": [{"asset_ip": "10.20.1.11", "criticality": "core",
                                            "exposure": "public", "owner": "甲"}]}
        scan_doc = {"meta": {}, "items": [{"asset_ip": "10.20.1.11", "cve_id": "CVE-X",
                                           "port": 1, "scanner_severity": "low"}]}
        with tempfile.TemporaryDirectory() as directory:
            tmp = Path(directory)
            for name, doc in (("cve.json", cve_doc), ("asset.json", asset_doc), ("scan.json", scan_doc)):
                _write(tmp / name, doc)
            with self.assertRaises(SystemExit) as ctx:
                triage_cases.main([
                    "--cve", str(tmp / "cve.json"), "--asset", str(tmp / "asset.json"),
                    "--scan", str(tmp / "scan.json"), "--date", "2026-09-22",
                    "--out", str(tmp / "cases.json"),
                ])
        self.assertEqual(ctx.exception.code, 2)


if __name__ == "__main__":
    unittest.main()
