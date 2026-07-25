"""集中所有 ztoa 凭据 + worksheetId + controlId。

凭据从环境变量读，没设置时用 D:\\git\\ztoa-mcp\\.env 兜底（开发机方便）。
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# === ztoa OpenAPI 凭据 ===
ZTOA_BASE_URL = os.getenv("ZTOA_BASE_URL", "https://ztoa.egova.com.cn")
ZTOA_APP_KEY = os.getenv("ZTOA_OPENAPI_APP_KEY", "")
ZTOA_SIGN = os.getenv("ZTOA_OPENAPI_SIGN", "")

# 兜底从 ztoa-mcp/.env 读
if not (ZTOA_APP_KEY and ZTOA_SIGN):
    env_path = Path("D:/git/ztoa-mcp/.env")
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            k = k.strip(); v = v.strip().strip('"').strip("'")
            if k == "ZTOA_OPENAPI_APP_KEY" and not ZTOA_APP_KEY:
                ZTOA_APP_KEY = v
            elif k == "ZTOA_OPENAPI_SIGN" and not ZTOA_SIGN:
                ZTOA_SIGN = v

assert ZTOA_APP_KEY and ZTOA_SIGN, "ZTOA_OPENAPI_APP_KEY/ZTOA_OPENAPI_SIGN 都必须有"


# === ztoa 工作表 ===
WS_DELIVERY = "629da7f86f0dcb3b9b7cd603"      # 交付项目
WS_LANGYA = "63e59ab31c09549442d4717f"        # 大区省份表-琅琊榜特殊使用


# === 「交付项目」字段 ===
F_PROJ_DAQU_TXT = "629dc18f6f0dcb3b9b7cd740"   # 大区（汇总文本）
F_PROJ_DAQU_SEL = "62aff5b9182553a4819a42b0"   # 所属大区（单选，返回中文 value）
F_PROJ_QUYU = "629dc18f6f0dcb3b9b7cd741"       # 区域（汇总文本）
F_PROJ_QUYU_TXT = "63744b49b208a0d6f8dda116"   # 所属区域（文本）
F_PROJ_NAME = "629dc18f6f0dcb3b9b7cd742"       # 项目名称
F_PROJ_STATUS = "62cb8536182553a4819d6506"     # 项目状态（单选，返回中文 value：打开/关闭/停工）
F_PROJ_PM = "629dc18f6f0dcb3b9b7cd745"         # 项目经理（user）

PROJ_STATUS_OPEN_VALUE = "打开"


# === 「大区省份表-琅琊榜特殊使用」字段 ===
F_LY_DAQU = "63e59ab31c09549442d47180"
F_LY_PROVINCE = "63e59b056028cc4370625a8f"     # 「省份」实际值=区域名称
F_LY_QUYU_NAME = "63e59b056028cc4370625a91"
F_LY_DAQU_ENG = "63e59b056028cc4370625a92"     # 大区责任人 = 大区工程总
F_LY_PROV_ENG = "63e59b056028cc4370625a93"     # 省份责任人 = 省份工程总
F_LY_DAQU_SALES = "642f748fe96d901c0c2c67a2"   # 大区销售总（不要默认用）
F_LY_PROV_SALES = "642f748fe96d901c0c2c67a3"   # 省份销售总（不要默认用）
F_LY_USABLE = "6486d00e1d46a4779da959cd"
LY_USABLE_TRUE = "是"


# === 大区有效集合（用于过滤异常值不进单选 options） ===
VALID_DAQU_SET = {
    "华北一区", "华北二区", "华中大区", "东南大区",
    "华南大区", "西南大区", "西北大区", "华北大区（测试）",
}
DEFAULT_DAQU_OPTIONS = [
    "华北一区", "华北二区", "华中大区", "东南大区",
    "华南大区", "西南大区", "西北大区",
]


# === ztoa-mcp 源码路径（导入 ZtoaOpenApiClient） ===
ZTOA_MCP_SRC = Path("D:/git/ztoa-mcp/src")
if ZTOA_MCP_SRC.exists() and str(ZTOA_MCP_SRC) not in sys.path:
    sys.path.insert(0, str(ZTOA_MCP_SRC))
