# 星桥高级一期认证评分规则（quiz 263 / v3）

总分 100 分，5 个场景各 20 分。自动评分是初评，不替代对截图的最终视觉复核。

## 一、ddcat 数据模型与接口（20 分）

| 代码 | 采分点 | 分值 | 核心证据 |
|---|---|---:|---|
| S1-01 | 连接 exam 数据源/查看数据源 | 2 | exam、exam_accident、数据源连接和表数据 |
| S1-02 | 检查事故表字段 | 1 | roadName、reportTime 等字段/样例数据 |
| S1-03 | 创建正确查询模型 | 4 | 按 roadName 分组、count、时间条件、倒序、LIMIT 5 |
| S1-04 | 调试/查看查询结果 | 2 | 运行结果含道路和统计数量 |
| S1-05 | 配置数据转换脚本 | 3 | 输出 name/text/value，name 自增 |
| S1-06 | 生成目标接口 | 2 | `/api/data-model/exam/top5` 或等价代理路径 |
| S1-07 | 应用审核/授权申请 | 2 | 应用审核或接口授权状态 |
| S1-08 | 配置 OAuth 前置脚本 | 2 | tokenStore、clientId/clientSecret、Bearer 请求头 |
| S1-09 | 用时间范围验证接口 | 2 | Postman/星桥 API 调用、指定起止时间、返回符合格式 |

## 二、MIS 统计接口代理（20 分）

| 代码 | 采分点 | 分值 | 核心证据 |
|---|---|---:|---|
| S2-01 | 注册 MIS 统计接口及 query 参数 | 2 | getgeneraldata、dateType、dateValue、token |
| S2-02 | 认证前置脚本获取 token | 3 | gettokenbyhumanid、humanID 100433、tokenStore |
| S2-03 | 解析原始响应 | 4 | `resultInfo.data.generaldata` 及字段读取 |
| S2-04 | 转换四项统计结果 | 4 | 立案数、上报数、结案数、结案率；name/text/value |
| S2-05 | 配置接口代理 | 2 | proxy/upstream 配置及目标代理地址 |
| S2-06 | 应用授权 | 2 | client/app 授权申请或授权成功 |
| S2-07 | 验证代理接口 | 3 | 获取 token 后调用、HTTP 返回和四项结果 |

## 三、第三方案卷上报与调度（20 分）

| 代码 | 采分点 | 分值 | 核心证据 |
|---|---|---:|---|
| S3-01 | 注册城管上报接口/平台编码 | 2 | uprecreport、senderCode、actionType |
| S3-02 | 案卷字段映射 | 4 | task_num、event_desc、坐标、区域、类型、等级、时间等 |
| S3-03 | 查询并封装多媒体 | 4 | exam_media、relationId、mediaURL、mediaType、mediaUsage |
| S3-04 | 前置脚本转换请求 | 4 | 读取 data、组装新 data、查询媒体、form-urlencoded 请求体 |
| S3-05 | 调试并验证案件生成 | 2 | 上报成功响应、recID/taskNum 或 MIS 综合查询可见 |
| S3-06 | 配置增量查询任务 | 2 | exam_rec 查询及增量/定时取数配置 |
| S3-07 | 配置 5 分钟调度 | 2 | 调度周期、任务运行日志、多次推送 |

## 四、多媒体增量同步（20 分）

| 代码 | 采分点 | 分值 | 核心证据 |
|---|---|---:|---|
| S4-01 | 源/目标任务与增量 SQL | 3 | exam_mis_media、目标表、SYSTEM_LAST_VALUE/CURRENT_VALUE |
| S4-02 | 基础字段映射 | 2 | mediaId/relationId/mediaName/mediaUsage/createTime/updateTime |
| S4-03 | URL 拼接转换 | 3 | mediaServer + mediaPath + mediaName 写入 URL |
| S4-04 | 媒体类型转换 | 3 | IMAGE/空→1，VIDEO→2 |
| S4-05 | server 与端口拆分 | 3 | `http://egova.top:18014` 拆成 server/18014 |
| S4-06 | status 状态转换 | 2 | mediaUsage 非空→1，否则→0 |
| S4-07 | 配置 2 分钟调度 | 2 | 调度周期和增量日志 |
| S4-08 | 验证目标端结果 | 2 | 多次调度、目标表新增/更新记录 |

## 五、binlog 多表实时同步（20 分）

| 代码 | 采分点 | 分值 | 核心证据 |
|---|---|---:|---|
| S5-01 | 人口表 CDC 监听 | 3 | exam_sg_resident_cdc、mysql-cdc、主键 |
| S5-02 | 分析目标表/JDBC 维表 | 2 | exam_sg_analysis、JDBC、字段结构 |
| S5-03 | 人口变更写入分析表 | 3 | resident CDC + house/building 维表 join |
| S5-04 | 房屋表实时关联 | 3 | exam_sg_house_cdc、与 resident/building 关联 |
| S5-05 | 楼栋表实时关联 | 3 | exam_sg_building_cdc、与 resident/house 关联 |
| S5-06 | 字段类型和目标映射 | 2 | floorNum/houseNum 等 String→INT、目标字段顺序 |
| S5-07 | 修改源数据验证实时更新 | 2 | 修改源表后目标表同步结果 |
| S5-08 | 作业部署和运行状态 | 2 | 作业提交、运行状态、日志或验证截图 |

评分说明：完成一张人口 CDC 可得基础分；人口与房屋或人口与楼栋两表实时关联覆盖完整时，场景可得满分；三表均完成时记录“额外完成”，但场景分不超过 20 分。

## 自动初评分档

- 关键文字/脚本命中 + 达到参考最低截图数：100%。
- 关键文字/脚本命中 + 有截图但低于参考最低数：按证据覆盖度给 60%～90%。
- 只有文字/脚本、没有截图：最多 30%，并标记人工复核。
- 只有截图占位、没有可定位文字：0 分初评，标记人工视觉复核。
- 题干中的关键词不计入证据；优先使用“答/答案”标记后的内容。
