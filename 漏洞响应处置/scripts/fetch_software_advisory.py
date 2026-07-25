#!/usr/bin/env python3
"""Fetch software CVE metadata. Primary: NVD CVE 2.0 API.

接受多个 CVE 编号一次抓取（一个软件经常涉及多 CVE）。

Schema 见 references/software_endpoints.md。

Python 3.6+ compatible.
"""
import argparse
import json
import os
import re
import ssl
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _paths import archive_dir  # noqa: E402

TIMEOUT = 20
USER_AGENT = "Mozilla/5.0 (vuln-response-skill)"
CST = timezone(timedelta(hours=8))
NVD_API = "https://services.nvd.nist.gov/rest/json/cves/2.0?cveId={cve}"
GHSA_API = "https://api.github.com/advisories?cve_id={cve}"


def _http_get(url: str, headers: Optional[dict] = None) -> Tuple[Any, str]:
    h = {"User-Agent": USER_AGENT, "Accept": "application/json"}
    if headers:
        h.update(headers)
    api_key = os.environ.get("NVD_API_KEY")
    if api_key and "services.nvd.nist.gov" in url:
        h["apiKey"] = api_key
    req = urllib.request.Request(url, method="GET", headers=h)
    ctx = ssl.create_default_context()
    with urllib.request.urlopen(req, timeout=TIMEOUT, context=ctx) as resp:
        raw = resp.read().decode("utf-8", errors="replace")
        return json.loads(raw), raw


def fetch_nvd(cve: str) -> dict:
    url = NVD_API.format(cve=cve)
    try:
        data, _ = _http_get(url)
        vulns = data.get("vulnerabilities") or []
        if not vulns:
            return {"source": "nvd", "status": "not_found", "advisory_url": f"https://nvd.nist.gov/vuln/detail/{cve}"}
        cve_obj = vulns[0].get("cve") or {}
        metrics = cve_obj.get("metrics") or {}
        cvss = None
        severity = None
        for key in ("cvssMetricV31", "cvssMetricV30", "cvssMetricV2"):
            metric_list = metrics.get(key) or []
            if metric_list:
                cvss_data = metric_list[0].get("cvssData") or {}
                cvss = cvss_data.get("baseScore")
                severity = cvss_data.get("baseSeverity") or metric_list[0].get("baseSeverity")
                break
        descriptions = cve_obj.get("descriptions") or []
        desc_zh = next((d.get("value") for d in descriptions if d.get("lang") == "zh-CN"), None)
        desc_en = next((d.get("value") for d in descriptions if d.get("lang") == "en"), None)
        cwes = []
        for w in cve_obj.get("weaknesses") or []:
            for d in w.get("description") or []:
                if d.get("lang") == "en" and d.get("value"):
                    cwes.append(d["value"])
        cpes = []
        for cfg in cve_obj.get("configurations") or []:
            for node in cfg.get("nodes") or []:
                for m in node.get("cpeMatch") or []:
                    crit = m.get("criteria")
                    if crit and crit not in cpes:
                        cpes.append(crit)
        refs = []
        for r in cve_obj.get("references") or []:
            if r.get("url"):
                refs.append({"url": r["url"], "tags": r.get("tags") or []})
        return {
            "source": "nvd",
            "status": "ok",
            "cvss": cvss,
            "severity": severity,
            "description": desc_zh or desc_en or "",
            "published": cve_obj.get("published"),
            "lastModified": cve_obj.get("lastModified"),
            "cwes": cwes,
            "cpes": cpes,
            "references": refs,
            "_raw": cve_obj,
        }
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return {"source": "nvd", "status": "not_found", "advisory_url": f"https://nvd.nist.gov/vuln/detail/{cve}"}
        return {"source": "nvd", "status": "fetch_error", "error": f"HTTP {e.code}: {e.reason}"}
    except Exception as e:
        return {"source": "nvd", "status": "fetch_error", "error": str(e)}


def fetch_ghsa(cve: str) -> dict:
    url = GHSA_API.format(cve=cve)
    headers = {"Accept": "application/vnd.github+json"}
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    try:
        data, _ = _http_get(url, headers=headers)
        # data 是 list（advisories）
        advs = data if isinstance(data, list) else data.get("data") or []
        if not advs:
            return {"source": "ghsa", "status": "not_found"}
        adv = advs[0]
        fixed_versions = []
        for v in adv.get("vulnerabilities") or []:
            for r in v.get("patched_versions") or []:
                if r:
                    fixed_versions.append(r)
            fr = v.get("first_patched_version")
            if fr:
                fixed_versions.append(fr)
        return {
            "source": "ghsa",
            "status": "ok",
            "ghsa_id": adv.get("ghsa_id"),
            "summary": adv.get("summary"),
            "severity": adv.get("severity"),
            "cvss": (adv.get("cvss") or {}).get("score"),
            "fixed_versions": list(dict.fromkeys(fixed_versions)),
            "html_url": adv.get("html_url"),
            "_raw": adv,
        }
    except urllib.error.HTTPError as e:
        return {"source": "ghsa", "status": "fetch_error", "error": f"HTTP {e.code}: {e.reason}"}
    except Exception as e:
        return {"source": "ghsa", "status": "fetch_error", "error": str(e)}


def cnvd_placeholder(cve: str) -> dict:
    return {
        "source": "cnvd",
        "status": "needs_render",
        "advisory_url": f"https://www.cnvd.org.cn/flaw/list.htm?number={cve}",
        "note": "CNVD 是 SPA，请用 scrapling skill 渲染并提取 CNVD 编号 + 受影响版本（国产软件兜底必看）",
    }


def fetch_one(cve: str, sources: List[str]) -> dict:
    entry = {
        "cve_id": cve,
        "fetched_at": datetime.now(CST).isoformat(timespec="seconds"),
        "vendor_lookups": [],
    }
    for src in sources:
        print(f"[fetch-software] {cve} <- {src}", file=sys.stderr)
        if src == "nvd":
            r = fetch_nvd(cve)
        elif src == "ghsa":
            r = fetch_ghsa(cve)
        elif src == "cnvd":
            r = cnvd_placeholder(cve)
        else:
            r = {"source": src, "status": "fetch_error", "error": f"unknown source {src}"}
        entry["vendor_lookups"].append(r)
        print(f"[fetch-software] {cve} <- {src} -> {r.get('status')}", file=sys.stderr)
        if src == "nvd":
            time.sleep(0.7)  # NVD 限速 5/30s 友好间隔
    return entry


def main() -> int:
    ap = argparse.ArgumentParser(description="Fetch software CVE metadata (NVD/GHSA)")
    ap.add_argument("cve_ids", nargs="+", help="CVE list, e.g. CVE-2024-31449 CVE-2024-46981")
    ap.add_argument("--software", required=True, help="软件标识 (e.g. redis / mysql)，必须在 software_inventory.md 白名单内")
    ap.add_argument("--sources", default="nvd,ghsa,cnvd",
                    help="Comma-separated sources, subset of {nvd,ghsa,cnvd}; default 'nvd,ghsa,cnvd'")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    cve_pat = re.compile(r"^CVE-\d{4}-\d{4,7}$")
    cves = [c.strip().upper() for c in args.cve_ids]
    bad = [c for c in cves if not cve_pat.match(c)]
    if bad:
        print(f"[fetch-software] invalid CVE ids: {bad}", file=sys.stderr)
        return 2

    sources = [s.strip() for s in args.sources.split(",") if s.strip()]
    valid = {"nvd", "ghsa", "cnvd"}
    bad_src = [s for s in sources if s not in valid]
    if bad_src:
        print(f"[fetch-software] unknown source(s): {bad_src}", file=sys.stderr)
        return 2

    result = {
        "software": args.software.lower(),
        "fetched_at": datetime.now(CST).isoformat(timespec="seconds"),
        "cves": [fetch_one(c, sources) for c in cves],
    }

    ts = datetime.now(CST).strftime("%Y%m%d%H%M%S")
    out = (Path(args.out) if args.out
           else archive_dir() / f"sw-{result['software']}-{ts}_scan.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(str(out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
