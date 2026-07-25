#!/usr/bin/env python3
"""Fetch CVE advisories from 6 vendors. JSON API first, scrapling fallback.

Output schema documented in references/vendor_endpoints.md.

Python 3.6+ compatible (no PEP 563/585/604 syntax).
"""
import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import quote

import urllib.request
import urllib.error
import ssl

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _paths import archive_dir  # noqa: E402

TIMEOUT = 15
USER_AGENT = "Mozilla/5.0 (vuln-response-skill)"
CST = timezone(timedelta(hours=8))


def _http_json(method: str, url: str, body: Optional[dict] = None) -> Tuple[Any, str]:
    headers = {"User-Agent": USER_AGENT, "Accept": "application/json"}
    data = None
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, method=method, headers=headers)
    ctx = ssl.create_default_context()
    with urllib.request.urlopen(req, timeout=TIMEOUT, context=ctx) as resp:
        raw = resp.read().decode("utf-8", errors="replace")
        return json.loads(raw), raw


def fetch_ubuntu(cve: str) -> dict:
    url = f"https://ubuntu.com/security/cves/{cve}.json"
    try:
        data, _ = _http_json("GET", url)
        affected = sorted({
            (pkg.get("name"), st.get("release_codename") or st.get("release"))
            for pkg in data.get("packages", [])
            for st in pkg.get("statuses", [])
            if st.get("status") in ("released", "needed", "deferred", "pending")
        })
        return {
            "vendor": "ubuntu",
            "status": "ok",
            "advisory_url": f"https://ubuntu.com/security/{cve}",
            "advisory_id": ", ".join(n.get("reference", "") for n in data.get("notices", []) if n.get("reference")) or None,
            "cvss": _first_float(data.get("cvss3")),
            "affected_versions": [f"{name} ({rel})" for name, rel in affected if rel],
            "summary": (data.get("description") or "").strip()[:500],
            "_raw": data,
        }
    except Exception as e:
        return {"vendor": "ubuntu", "status": "fetch_error", "error": str(e),
                "advisory_url": f"https://ubuntu.com/security/{cve}"}


def fetch_redhat(cve: str) -> dict:
    url = f"https://access.redhat.com/hydra/rest/securitydata/cve/{cve.upper()}.json"
    try:
        data, _ = _http_json("GET", url)
        releases = sorted({r.get("product_name") for r in data.get("affected_release", []) if r.get("product_name")})
        return {
            "vendor": "redhat",
            "status": "ok",
            "advisory_url": f"https://access.redhat.com/security/cve/{cve.lower()}",
            "advisory_id": data.get("name"),
            "cvss": _first_float((data.get("cvss3") or {}).get("cvss3_base_score")),
            "affected_versions": list(releases),
            "summary": (data.get("bugzilla", {}).get("description") or data.get("statement") or "").strip()[:500],
            "_raw": data,
        }
    except Exception as e:
        return {"vendor": "redhat", "status": "fetch_error", "error": str(e),
                "advisory_url": f"https://access.redhat.com/security/cve/{cve.lower()}"}


def fetch_kylin(cve: str) -> dict:
    url = "https://support.kylinos.cn/protalweb/security/cve/list"
    try:
        data, _ = _http_json("POST", url, {"page": 1, "size": 10, "keyword": cve})
        records = (data.get("data") or {}).get("records") or data.get("records") or []
        match = next((r for r in records if cve.upper() in (r.get("cveNumber") or "").upper()), None)
        if not match:
            return {"vendor": "kylin", "status": "not_found",
                    "advisory_url": f"https://support.kylinos.cn/#/security/cveDetail?allTitle={cve}",
                    "note": "麒麟列表接口未返回该 CVE，需 PlayWrightFetcher 兜底或人工核查"}
        return {
            "vendor": "kylin",
            "status": "ok",
            "advisory_url": f"https://support.kylinos.cn/#/security/cveDetail?allTitle={cve}",
            "advisory_id": match.get("cveNumber"),
            "affected_versions": _split_lines(match.get("affectedProduct")),
            "fixed_in": match.get("fixedVersion"),
            "summary": (match.get("description") or "").strip()[:500],
            "_raw": match,
        }
    except Exception as e:
        return {"vendor": "kylin", "status": "fetch_error", "error": str(e),
                "advisory_url": f"https://support.kylinos.cn/#/security/cveDetail?allTitle={cve}"}


def fetch_openeuler(cve: str) -> dict:
    url = ("https://www.openeuler.org/api-cve/cve-security-notice-server/securitynotice/findAll"
           f"?keyword={quote(cve)}&pages=1&size=20&type=cve")
    try:
        data, _ = _http_json("GET", url)
        records = ((data.get("result") or {}).get("records") or [])
        match = next((r for r in records if cve.upper() in (r.get("cveId") or "").upper()), None)
        if not match:
            return {"vendor": "openeuler", "status": "not_found",
                    "advisory_url": f"https://www.openeuler.org/zh/security/security-bulletins/?searchKey={cve}",
                    "note": "openEuler 列表接口未返回该 CVE"}
        sa_id = match.get("securityNoticeNo")
        return {
            "vendor": "openeuler",
            "status": "ok",
            "advisory_url": f"https://www.openeuler.org/zh/security/security-bulletins/detail/?id={sa_id}",
            "advisory_id": sa_id,
            "affected_versions": _split_lines(match.get("affectedProduct")),
            "cvss": _first_float(match.get("cvssScore") or match.get("cvss")),
            "summary": (match.get("summary") or "").strip()[:500],
            "_raw": match,
        }
    except Exception as e:
        return {"vendor": "openeuler", "status": "fetch_error", "error": str(e),
                "advisory_url": f"https://www.openeuler.org/zh/security/security-bulletins/?searchKey={cve}"}


def fetch_anolis(cve: str) -> dict:
    return {
        "vendor": "anolis",
        "status": "needs_render",
        "advisory_url": f"https://anas.openanolis.cn/cves/detail/{cve}",
        "note": "ANSA 没稳定 JSON 接口，请在 propose 阶段用 scrapling skill 渲染 advisory_url 后人工补 advisory_id 和 affected_versions"
    }


def fetch_uos(cve: str) -> dict:
    return {
        "vendor": "uos",
        "status": "needs_render",
        "advisory_url": "https://src.uniontech.com/#/security_advisory",
        "note": "统信 UOS 公告中心是 SPA，请在 propose 阶段用 scrapling 渲染、搜索关键字后人工补字段"
    }


def _split_lines(s: Any) -> List[str]:
    if not s:
        return []
    return [line.strip() for line in re.split(r"[\n,;；、]+", str(s)) if line.strip()]


def _first_float(v: Any) -> Optional[float]:
    try:
        return float(v) if v not in (None, "", "N/A") else None
    except (TypeError, ValueError):
        return None


VENDORS = {
    "ubuntu": fetch_ubuntu,
    "redhat": fetch_redhat,
    "kylin": fetch_kylin,
    "openeuler": fetch_openeuler,
    "anolis": fetch_anolis,
    "uos": fetch_uos,
}


def main() -> int:
    ap = argparse.ArgumentParser(description="Fetch CVE advisories from vendors")
    ap.add_argument("cve_id", help="e.g. CVE-2026-31431")
    ap.add_argument("--vendors", default="all",
                    help=f"Comma-separated subset of {list(VENDORS)}; default 'all'")
    ap.add_argument("--out", default=None, help="Output JSON path (default _archive/<cve>_scan_<ts>.json)")
    args = ap.parse_args()

    cve = args.cve_id.strip().upper()
    if not re.match(r"^CVE-\d{4}-\d{4,7}$", cve):
        print(f"[fetch] invalid CVE id: {cve}", file=sys.stderr)
        return 2

    selected = list(VENDORS) if args.vendors == "all" else [v.strip() for v in args.vendors.split(",")]
    unknown = [v for v in selected if v not in VENDORS]
    if unknown:
        print(f"[fetch] unknown vendor(s): {unknown}", file=sys.stderr)
        return 2

    result = {
        "cve_id": cve,
        "fetched_at": datetime.now(CST).isoformat(timespec="seconds"),
        "vendors": [],
    }
    for v in selected:
        print(f"[fetch] {v} ...", file=sys.stderr)
        try:
            entry = VENDORS[v](cve)
        except Exception as e:
            entry = {"vendor": v, "status": "fetch_error", "error": f"unhandled: {e}"}
        result["vendors"].append(entry)
        print(f"[fetch] {v} -> {entry.get('status')}", file=sys.stderr)

    ts = datetime.now(CST).strftime("%Y%m%d%H%M%S")
    out = Path(args.out) if args.out else archive_dir() / f"{cve}_scan_{ts}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(str(out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
