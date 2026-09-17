---
name: doc-generator-skill
description: Generate enterprise technical documents from structured JSON system metadata with the bundled script. Use when producing design docs, database docs, interface docs, user manuals, or test reports in Markdown or DOCX.
---

# 智能文档生成器

使用 `scripts/generate-document.py` 作为唯一入口，不要手写整套文档框架。

## 当前实际能力

- 支持 7 类文档模板：
  - `概要设计说明书`
  - `数据库设计说明书`
  - `详细设计说明书`
  - `接口设计说明书`
  - `产品交互设计说明书`
  - `用户操作手册`
  - `软件测试报告`
- 支持两种输出：
  - `docx`，默认格式
  - `md`
- 支持把现有 Markdown 转成 DOCX：
  - `--convert <file.md>`
- 模板与字段定义来自：
  - `config/document-types.json`
  - `config/template-structure.json`
- 示例输入在：
  - `examples/camunda-input.json`

说明：

- 这份 skill 当前 **不支持 PPTX 生成**。
- 如果不确定某类文档需要哪些输入字段，先读 `config/document-types.json` 里对应条目的 `requiredInput` 和 `optionalInput`。

## 工作流

1. 准备输入 JSON。
2. 先运行 `--list-types` 确认文档类型名称。
3. 生成目标文档。
4. 如果已经有 Markdown，再按需转成 DOCX。

## 常用命令

```bash
python scripts/generate-document.py --list-types
python scripts/generate-document.py --type "概要设计说明书" --input examples/camunda-input.json --output output.docx
python scripts/generate-document.py --type "接口设计说明书" --input input.json --format md --output api.md
python scripts/generate-document.py --convert api.md --output api.docx
```

## 输入建议

通用字段通常包括：

- `systemName`
- `systemUrl`
- `description`
- `version`
- `author`

不同文档类型还会额外要求：

- `features`
- `techStack`
- `tables`
- `apiDocs`
- `userRoles`
- `testResults`

先按文档类型读取配置，再补齐最少必需字段。

## 生成约束

- 文档章节顺序以 `config/document-types.json` 为准。
- 生成 Markdown 时，脚本会输出基础标题、文档信息表、修订历史、目录和章节骨架。
- 生成 DOCX 时，脚本会把同一套结构写入 Word 文档。
- 生成结果仍需要人工复核，尤其是接口示例、数据库细节、测试结论等事实性内容。
