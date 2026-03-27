# 智能文档生成器 (Smart Document Generator)

## 简介

智能文档生成器是一个自动化的软件开发文档生成工具,能够根据系统信息自动生成符合企业标准的7种技术文档。

## 功能特点

- ✅ **支持7种文档类型**: 概要设计、数据库设计、详细设计、接口设计、交互设计、用户手册、测试报告
- ✅ **模板化生成**: 基于标准模板自动生成文档
- ✅ **智能填充**: 根据系统信息自动填充内容
- ✅ **格式统一**: 确保所有文档符合企业规范
- ✅ **快速生成**: 大幅提升文档编写效率
- ✅ **易于扩展**: 支持自定义模板和文档类型

## 支持的文档类型

| 文档编号 | 文档名称 | 描述 |
|---------|---------|------|
| RD-002 | 概要设计说明书 | 描述系统总体架构、功能模块划分、技术选型等 |
| RD-001 | 数据库设计说明书 | 详细说明数据库的表结构设计、索引设计等 |
| RD-003 | 详细设计说明书 | 描述系统各模块的详细设计,包括类设计、算法设计等 |
| RD-004 | 接口设计说明书 | 详细说明系统对外提供的API接口 |
| PM-006 | 产品交互设计说明书 | 描述系统的用户交互设计和UI设计 |
| RM-002 | 用户操作手册 | 指导最终用户如何使用系统 |
| TD-002 | 软件测试报告 | 记录软件测试的过程和结果 |

## 快速开始

### 1. 查看支持的文档类型

```bash
python scripts/generate-document.py --list-types
```

### 2. 准备输入数据

创建JSON格式的输入数据文件,参考 `examples/camunda-input.json`。

**必需字段**:
- `systemName`: 系统名称
- `systemUrl`: 系统地址
- `description`: 系统描述
- `version`: 版本号
- `author`: 编写人

**可选字段**:
- `features`: 功能列表
- `techStack`: 技术栈
- `databaseType`: 数据库类型
- `tables`: 数据库表信息
- `apiDocs`: API接口文档
- `userRoles`: 用户角色

### 3. 生成文档

```bash
python scripts/generate-document.py --type "概要设计说明书" --input examples/camunda-input.json --output output.md
```

### 4. 批量生成文档

```bash
# 生成概要设计文档
python scripts/generate-document.py --type "概要设计说明书" --input examples/camunda-input.json -o 概要设计.md

# 生成数据库设计文档
python scripts/generate-document.py --type "数据库设计说明书" --input examples/camunda-input.json -o 数据库设计.md

# 生成接口设计文档
python scripts/generate-document.py --type "接口设计说明书" --input examples/camunda-input.json -o 接口设计.md

# 生成用户操作手册
python scripts/generate-document.py --type "用户操作手册" --input examples/camunda-input.json -o 用户手册.md

# 生成软件测试报告
python scripts/generate-document.py --type "软件测试报告" --input examples/camunda-input.json -o 测试报告.md
```

## 使用示例

### 示例1: 生成Camunda概要设计文档

**输入文件** (`camunda-input.json`):

```json
{
  "systemName": "Camunda工作流引擎平台",
  "description": "基于BPMN 2.0标准的开源工作流和业务流程管理平台",
  "version": "v1.0",
  "author": "开发团队",
  "systemUrl": "http://47.110.57.11:8080/camunda",
  "features": [
    "流程设计与管理",
    "流程执行与监控",
    "任务分配与处理",
    "决策管理(DMN)"
  ],
  "techStack": {
    "语言": "Java (JDK 11+)",
    "流程引擎": "Camunda BPM Platform 7.x",
    "数据库": "MySQL"
  }
}
```

**生成命令**:

```bash
python scripts/generate-document.py --type "概要设计说明书" --input camunda-input.json
```

### 示例2: 生成接口设计文档

```json
{
  "systemName": "订单管理系统",
  "baseUrl": "http://api.example.com/v1",
  "apiDocs": [
    {
      "name": "创建订单",
      "method": "POST",
      "path": "/orders",
      "description": "创建新的订单"
    },
    {
      "name": "查询订单",
      "method": "GET",
      "path": "/orders/{id}",
      "description": "根据ID查询订单"
    }
  ]
}
```

## 目录结构

```
doc-generator-skill/
├── skill.md                    # Skill主文件
├── README.md                   # 使用说明
├── config/                     # 配置文件目录
│   ├── document-types.json      # 文档类型配置
│   └── template-structure.json # 模板结构配置
├── scripts/                    # 脚本目录
│   └── generate-document.py    # 文档生成脚本
└── examples/                   # 示例目录
    └── camunda-input.json     # Camunda输入数据示例
```

## 配置说明

### 文档类型配置 (config/document-types.json)

定义支持的文档类型及其章节结构。

### 模板结构配置 (config/template-structure.json)

定义每种文档的模板结构和章节说明。

## 自定义扩展

### 添加新的文档类型

1. 在 `config/document-types.json` 中添加新的文档类型配置
2. 在 `config/template-structure.json` 中添加模板结构
3. 在 `scripts/generate-document.py` 中添加生成逻辑

### 自定义模板

修改 `template-structure.json` 中的模板定义,调整章节结构和内容格式。

## 最佳实践

1. **输入数据要完整**: 提供尽可能多的系统信息,生成更完整的文档
2. **分步完善**: 先生成基础文档,再人工补充细节
3. **定期更新**: 系统变更后及时更新文档
4. **版本管理**: 对文档进行版本控制
5. **团队协作**: 团队成员共同维护文档

## 输出格式

当前版本支持 **Markdown** 格式输出,可以:

- 直接查看和编辑
- 转换为Word、PDF等格式
- 发布到文档网站
- 导入到Git仓库

## 技术支持

如有问题或建议,请联系技术支持团队。

## 许可证

本工具为内部使用工具,请遵守企业相关规定。

## 更新日志

### v1.0 (2026-03-26)
- 初始版本发布
- 支持7种文档类型
- 提供Camunda示例
- 完善文档结构

---

**智能文档生成器 - 让文档编写更高效!**
