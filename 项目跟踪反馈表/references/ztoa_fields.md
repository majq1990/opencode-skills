# ztoa 关键 worksheet / 字段速查

## 应用 / 凭据

| Key | Value |
|---|---|
| ztoa base URL | `https://ztoa.egova.com.cn`（公网；内网 `https://172.16.5.27` 大数据量更快但需 verify=False） |
| OpenAPI app_key | `8f88361d723b7e6c` |
| OpenAPI sign | 见 `D:\git\ztoa-mcp\.env` `ZTOA_OPENAPI_SIGN`，含 base64 `==` padding |
| projectId | `9a60927f-0d37-4164-9a87-856bfd01771c`（工程实施） |
| appId | `6987622c-c4c5-4d23-8ce4-0fd6887250a5` |

## 工作表

| 名称 | worksheetId | 用途 |
|---|---|---|
| 交付项目 | `629da7f86f0dcb3b9b7cd603` | 拉项目清单（1851 条全量） |
| 大区省份表-琅琊榜特殊使用 | `63e59ab31c09549442d4717f` | 拉 (大区,区域) → 责任人 映射（32 条，过滤 是否可用=否 后 31 条） |

## 「交付项目」表关键字段（控制 ID 不变）

| 字段 | controlId | type | 说明 |
|---|---|---|---|
| 大区（汇总） | `629dc18f6f0dcb3b9b7cd740` | 30 | 文本聚合 |
| 所属大区 | `62aff5b9182553a4819a42b0` | 11 | 单选，返回中文值 |
| 区域（汇总） | `629dc18f6f0dcb3b9b7cd741` | 30 | 文本聚合 |
| 所属区域 | `63744b49b208a0d6f8dda116` | 2 | 文本 |
| 项目名称 | `629dc18f6f0dcb3b9b7cd742` | 30 | 主键 |
| 项目状态 | `62cb8536182553a4819d6506` | 11 | 单选，返回 `打开`/`关闭`/`停工`（不是 key） |
| 项目经理 | `629dc18f6f0dcb3b9b7cd745` | 26 | 用户字段，JSON 字符串数组 `[{accountId,fullname,status,avatar}]` |

**过滤条件铁律：**
- 项目状态 == "打开"（按中文 value 比，**不是** key）
- 项目经理 status == 1（在职；离职会显示 status=2 或不返回）

## 「大区省份表-琅琊榜特殊使用」表关键字段

| 字段 | controlId | type | 说明 |
|---|---|---|---|
| 大区 | `63e59ab31c09549442d47180` | 2 | 文本，如 `华北二区` |
| 省份 | `63e59b056028cc4370625a8f` | 2 | 文本，值实际是「区域名称」如 `天津区域` |
| 区域名称 | `63e59b056028cc4370625a91` | 2 | 同上 |
| 大区责任人 (= 大区工程总) | `63e59b056028cc4370625a92` | 26 | 工程线总监 |
| 省份责任人 (= 省份工程总) | `63e59b056028cc4370625a93` | 26 | 工程线总监 |
| 大区销售总 | `642f748fe96d901c0c2c67a2` | 26 | 销售线，**别误用** |
| 省份销售总 | `642f748fe96d901c0c2c67a3` | 26 | 销售线，**别误用** |
| 是否可用 | `6486d00e1d46a4779da959cd` | 11 | 单选，过滤掉 `是否可用 == "否"` 的测试行 |

**用户语境约定：**
- 「大区总 / 省份总」—— 默认指 **工程总**（大区责任人/省份责任人），不是销售总
- 想要销售总的话用户会明确说「销售总」

## ztoa OpenAPI 路径

| 接口 | path | 方法 |
|---|---|---|
| 应用信息 | `/api/v1/open/app/get` | GET |
| 工作表 schema | `/api/v2/open/worksheet/getWorksheetInfo` | POST `{worksheetId}` |
| 翻页查行 | `/api/v2/open/worksheet/getFilterRows` | POST `{worksheetId,filters,pageSize,pageIndex,viewId?}` |
| 新增行 | `/api/v2/open/worksheet/addRow` | POST `{worksheetId,controls,ownerMobile?}` |
| 改行 | `/api/v2/open/worksheet/editRow` | POST |
| 取行 | `/api/v2/open/worksheet/getRowById` | GET |
| 删行 | `/api/v2/open/worksheet/deleteRow` | POST |

## 已确认 **关闭** 的接口（不要再尝试）

ztoa 私有部署阉割了所有用户/部门相关 OpenAPI（返回 404 或 405）：

- `/api/v1/open/user/getUser`
- `/api/v2/open/user/getUser`
- `/api/v2/open/user/listUsers`
- `/api/v1/open/user/getList`
- `/api/v1/open/department/*`
- `/api/v2/open/department/*`

**结论**：从 ztoa 拿不到工号/手机号，姓名 → 钉钉 userId 映射必须走 `dws contact user search`。

## ztoa OpenAPI 协议要点

- POST 接口的 appKey/sign 必须放 **body**，不能放 query
- 所有写接口必须带 `Origin/Referer` header（CSRF 保护）
- 明道云反直觉：`success=true, error_code=1` 是成功
- ztoa OpenAPI 是应用身份调用，`user-self`/filterType=21 等"当前用户"占位符全部失效
- viewId 现在可空（`""` = 全表，绕开视图过滤）

## 客户端

`D:\git\ztoa-mcp\src\ztoa_mcp\auth\ztoa_openapi.py`

```python
from ztoa_mcp.auth.ztoa_openapi import ZtoaOpenApiClient
c = ZtoaOpenApiClient(BASE_URL, APP_KEY, SIGN, verify=True)
app = await c.get_app()                                # /app/get
info = await c.get_worksheet_info(worksheet_id)        # schema
r = await c.query_records(ws_id, page_size=200, page_index=1)  # rows
```
