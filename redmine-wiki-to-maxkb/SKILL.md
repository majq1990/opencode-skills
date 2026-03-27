# Redmine Wiki to MaxKB Sync Skill

从 Redmine Wiki 分析提取活跃文档，推送到 MaxKB 知识库。

## 特性

- 自动主备服务器切换（主服务器找不到时自动从备份服务器拉取）
- 灵珑表单详情获取（需求分析、产品设计、研发设计等）
- 案件信息提取（批转记录、代码提交等）
- 产品模块筛选

## 快速开始

```bash
# 完整同步（推荐）
redmine-wiki-to-maxkb --product 麒舰 --full-sync

# 只获取 Wiki
redmine-wiki-to-maxkb --product 麒舰

# 包含案件信息
redmine-wiki-to-maxkb --product 麒舰 --include-issues

# 测试服务器连接
redmine-wiki-to-maxkb --test-connection
```

## 命令行参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--product` | 产品名称（麒舰、灵珑、明镜、市民通等） | 交互选择 |
| `--dataset` | MaxKB 知识库名称 | "{产品名}工程Wiki知识库" |
| `--min-score` | 最低活跃度得分 | 60 |
| `--days` | 活跃时间阈值（天） | 365 |
| `--include-issues` | 包含关联案件信息 | False |
| `--full-sync` | 完整同步（Wiki + 案件 + 灵珑） | False |
| `--dry-run` | 只分析不上传 | False |
| `--test-connection` | 测试服务器连接 | False |

## 备份服务器自动切换

```
主服务器: https://faq.egova.com.cn:7787
备份服务器: https://faq.egova.com.cn:7789 (只读)
```

当主服务器返回 404 时，自动切换到备份服务器拉取数据。导出的 Markdown 会标记数据来源。

## 灵珑表单 API

支持的表单类型：

| 表单 ID | 名称 |
|---------|------|
| `form_demand_analysis` | 需求分析 |
| `form_product_design` | 产品设计 |
| `form_develop_design` | 研发设计 |
| `form_develop_finish` | 研发完成 |
| `form_product_verify` | 产品验证 |
| `form_tester_verify` | 测试验证 |
| `form_demand_analysis_audit` | 需求审核 |
| `form_develop_design_audit` | 研发设计审核 |

## 产品映射

| 产品 | 关键词 |
|------|--------|
| 麒舰 | 麒舰、麒舰FAQ |
| 灵珑 | 灵珑 |
| 明镜 | 明镜 |
| 市民通 | 市民通、市民通FAQ |
| 智云 | 智云、智云FAQ |
| GIS | GIS、GIS_FAQ |
| 物联网 | 物联网、IoT |

## 配置

环境变量：

```bash
REDMINE_URL=https://faq.egova.com.cn:7787
REDMINE_API_KEY=your-api-key
REDMINE_BACKUP_URL=https://faq.egova.com.cn:7789
MAXKB_URL=http://111.4.141.154:18080
MAXKB_USERNAME=egova-jszc
MAXKB_PASSWORD=eGova@2026
```

## 输出文件

```
D:/opencode/file/{YYYY-MM-DD}/
├── {product}_wiki_md/      # Wiki Markdown 文件
├── {product}_issues_md/    # 案件 Markdown 文件
└── {product}_issue_ids.txt # 案件编号列表
```

## 使用示例

```bash
# 测试连接
redmine-wiki-to-maxkb --test-connection
# [Redmine] Primary server (https://faq.egova.com.cn:7787): OK
# [Redmine] Backup server (https://faq.egova.com.cn:7789): OK

# 完整同步
redmine-wiki-to-maxkb --product 麒舰 --full-sync
# [1] Fetching Wiki list... Found 15304 pages
# [2] Filtering by product: 麒舰... Found 283 wikis
# [3] Analyzing activity... Active: 196
# [4] Fetching wiki content... Success: 196/196
# [5] Extracting issues... Found 195 unique IDs
# [6] Fetching issue details... Primary: 191, Backup: 4

# 只分析不上传
redmine-wiki-to-maxkb --product 麒舰 --dry-run
```

## 相关链接

- Redmine: https://faq.egova.com.cn:7787
- 备份服务器: https://faq.egova.com.cn:7789
- MaxKB: http://111.4.141.154:18080
- 灵珑表单 API 文档: https://faq.egova.com.cn:7787/changelogs/20260313-001