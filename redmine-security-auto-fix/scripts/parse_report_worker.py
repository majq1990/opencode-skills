#!/usr/bin/env python3
"""Small subprocess worker used to isolate parser crashes and hangs."""

from __future__ import annotations

import json
import sys

from report_parser import parse_report


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass
    result = parse_report(sys.argv[1])
    sys.stdout.write(json.dumps(result, ensure_ascii=False))
