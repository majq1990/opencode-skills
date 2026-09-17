**V22市区对接标准文档**

|  |  |  |  |
| --- | --- | --- | --- |
| 编辑人 | 编辑时间 | 说明 | 备注 |
| 数字政通研发-刘浪 | 2023-10-09 | V22市区对接标准文档V1.0 |  |
| 数字政通研发-刘浪 | 2023-10-27 | 新增办理经过同步接口 |  |
| 数字政通研发-刘浪 | 2023-10-30 | 新增反馈接口 |  |
| 数字政通研发-刘浪 | 2023-10-31 | 新增申请授权接口 |  |
| 数字政通研发-刘浪 | 2023-11-08 | 新增通知查询接口 |  |
| 数字政通研发-刘浪 | 2023-11-20 | 调整工单评价接口 |  |
| 数字政通研发-刘浪 | 2023-11-22 | 新增工单督办接口 |  |
| 数字政通研发-刘浪 | 2023-12-18 | 新增申请作废接口 |  |
| 数字政通研发-符培伦 | 2024-08-01 | 目录格式调整。接口整体自测，核对请求参数和响应参数，删除不可用的接口。新增通知查询、通知签收、工单催办、下派通知查询、工单签收、工单告知、工单办理经过查询、更新工单对接信息、上传多媒体、基础字典表接口。新增错误码说明，新增部分通知名称字典。 |  |

目录

[1. 概述 9](#_Toc173423188)

[2. 缩略语 9](#_Toc173423189)

[2.1. HTTP 协议 9](#_Toc173423190)

[2.2. JSON (数据交换格式) 9](#_Toc173423191)

[2.3. Header(请求头) 9](#_Toc173423192)

[2.3.1. Content-Type(内容编码类型) 10](#_Toc173423193)

[2.3.2. Authorization(用户凭证) 10](#_Toc173423194)

[2.4. body(报文体) 10](#_Toc173423195)

[2.5. UTF-8(字符编码) 10](#_Toc173423196)

[3. 系统对接技术要求 10](#_Toc173423197)

[3.1. 接口对接方式 10](#_Toc173423198)

[3.2. 请求规范 10](#_Toc173423199)

[3.3. 请求频率 11](#_Toc173423200)

[3.4. 接口对接流程 11](#_Toc173423201)

[3.4.1. 制定业务规范 11](#_Toc173423202)

[3.4.2. 制定接口标准 11](#_Toc173423203)

[3.4.3. 准备运行环境 11](#_Toc173423204)

[3.4.4. 开发及联调测试 12](#_Toc173423205)

[3.4.5. 上线运行 12](#_Toc173423206)

[4. 业务办理接口详情 12](#_Toc173423207)

[4.1. 工单上报 12](#_Toc173423208)

[4.1.1. 接口描述 12](#_Toc173423209)

[4.1.2. 接口请求参数 12](#_Toc173423210)

[4.1.3. 请求样例 16](#_Toc173423211)

[4.1.4. 接口返回参数 17](#_Toc173423212)

[4.1.5. 返回样例 17](#_Toc173423213)

[4.2. 工单信息查询 17](#_Toc173423214)

[4.2.1. 接口描述 17](#_Toc173423215)

[4.2.2. 接口请求参数 18](#_Toc173423216)

[4.2.3. 接口返回参数 18](#_Toc173423217)

[4.2.4. 请求样例 20](#_Toc173423218)

[4.2.5. 返回样例 21](#_Toc173423219)

[4.3. 工单办理经过同步 22](#_Toc173423220)

[4.3.1. 接口描述 22](#_Toc173423221)

[4.3.2. 接口请求参数 22](#_Toc173423222)

[4.3.3. 请求样例 24](#_Toc173423223)

[4.3.4. 接口返回参数 24](#_Toc173423224)

[4.3.5. 返回样例 25](#_Toc173423225)

[4.4. 工单处置反馈 26](#_Toc173423226)

[4.4.1. 接口描述 26](#_Toc173423227)

[4.4.2. 接口请求参数 26](#_Toc173423228)

[4.4.3. 请求样例 27](#_Toc173423229)

[4.4.4. 接口返回参数 27](#_Toc173423230)

[4.4.5. 返回样例 28](#_Toc173423231)

[4.5. 工单申请回退 29](#_Toc173423232)

[4.5.1. 接口描述 29](#_Toc173423233)

[4.5.2. 接口请求参数 29](#_Toc173423234)

[4.5.3. 请求样例 30](#_Toc173423235)

[4.5.4. 接口返回参数 31](#_Toc173423236)

[4.5.5. 返回样例 31](#_Toc173423237)

[4.6. 工单答复回退 32](#_Toc173423238)

[4.6.1. 接口描述 32](#_Toc173423239)

[4.6.2. 接口请求参数 32](#_Toc173423240)

[4.6.3. 请求样例 34](#_Toc173423241)

[4.6.4. 接口返回参数 34](#_Toc173423242)

[4.6.5. 返回样例 35](#_Toc173423243)

[4.7. 工单申请延期 36](#_Toc173423244)

[4.7.1. 接口描述 36](#_Toc173423245)

[4.7.2. 接口请求参数 37](#_Toc173423246)

[4.7.3. 请求样例 38](#_Toc173423247)

[4.7.4. 接口返回参数 39](#_Toc173423248)

[4.7.5. 返回样例 39](#_Toc173423249)

[4.8. 工单答复延期 40](#_Toc173423250)

[4.8.1. 接口描述 40](#_Toc173423251)

[4.8.2. 接口请求参数 41](#_Toc173423252)

[4.8.3. 请求样例 42](#_Toc173423253)

[4.8.4. 接口返回参数 42](#_Toc173423254)

[4.8.5. 返回样例 43](#_Toc173423255)

[4.9. 工单申请作废 43](#_Toc173423256)

[4.9.1. 接口描述 43](#_Toc173423257)

[4.9.2. 接口请求参数 43](#_Toc173423258)

[4.9.3. 请求样例 44](#_Toc173423259)

[4.9.4. 接口返回参数 45](#_Toc173423260)

[4.9.5. 返回样例 45](#_Toc173423261)

[4.10. 工单答复作废 46](#_Toc173423262)

[4.10.1. 接口描述 46](#_Toc173423263)

[4.10.2. 接口请求参数 46](#_Toc173423264)

[4.10.3. 请求样例 47](#_Toc173423265)

[4.10.4. 接口返回参数 48](#_Toc173423266)

[4.10.5. 返回样例 48](#_Toc173423267)

[4.11. 工单核查反馈 50](#_Toc173423268)

[4.11.1. 接口描述 50](#_Toc173423269)

[4.11.2. 接口请求参数 50](#_Toc173423270)

[4.11.3. 请求样例 51](#_Toc173423271)

[4.11.4. 接口返回参数 52](#_Toc173423272)

[4.11.5. 返回样例 52](#_Toc173423273)

[4.12. 工单办结 53](#_Toc173423274)

[4.12.1. 接口描述 53](#_Toc173423275)

[4.12.2. 接口请求参数 53](#_Toc173423276)

[4.12.3. 请求样例 54](#_Toc173423277)

[4.12.4. 接口返回参数 55](#_Toc173423278)

[4.12.5. 返回样例 55](#_Toc173423279)

[4.13. 工单评价 56](#_Toc173423280)

[4.13.1. 接口描述 56](#_Toc173423281)

[4.13.2. 接口请求参数 56](#_Toc173423282)

[4.13.3. 请求样例 58](#_Toc173423283)

[4.13.4. 接口返回参数 59](#_Toc173423284)

[4.13.5. 返回样例 59](#_Toc173423285)

[4.14. 通知查询 59](#_Toc173423286)

[4.14.1. 接口描述 59](#_Toc173423287)

[4.14.2. 接口请求参数 59](#_Toc173423288)

[4.14.3. 请求样例 60](#_Toc173423289)

[4.14.4. 接口返回参数 60](#_Toc173423290)

[4.14.5. 返回样例 61](#_Toc173423291)

[4.15. 通知签收 62](#_Toc173423292)

[4.15.1. 接口描述 62](#_Toc173423293)

[4.15.2. 接口请求参数 62](#_Toc173423294)

[4.15.3. 请求样例 62](#_Toc173423295)

[4.15.4. 接口返回参数 63](#_Toc173423296)

[4.15.5. 返回样例 63](#_Toc173423297)

[4.16. 工单督办 63](#_Toc173423298)

[4.16.1. 接口描述 63](#_Toc173423299)

[4.16.2. 接口请求参数 63](#_Toc173423300)

[4.16.3. 请求样例 64](#_Toc173423301)

[4.16.4. 接口返回参数 64](#_Toc173423302)

[4.16.5. 返回样例 65](#_Toc173423303)

[4.17. 工单催办 66](#_Toc173423304)

[4.17.1. 接口描述 66](#_Toc173423305)

[4.17.2. 接口请求参数 66](#_Toc173423306)

[4.17.3. 请求样例 66](#_Toc173423307)

[4.17.4. 接口返回参数 67](#_Toc173423308)

[4.17.5. 返回样例 67](#_Toc173423309)

[4.18. 下派通知查询 68](#_Toc173423310)

[4.18.1. 接口描述 68](#_Toc173423311)

[4.18.2. 接口请求参数 68](#_Toc173423312)

[4.18.3. 请求样例 69](#_Toc173423313)

[4.18.4. 接口返回参数 69](#_Toc173423314)

[4.18.5. 返回样例 71](#_Toc173423315)

[4.19. 工单签收 72](#_Toc173423316)

[4.19.1. 接口描述 72](#_Toc173423317)

[4.19.2. 接口请求参数 72](#_Toc173423318)

[4.19.3. 请求样例 73](#_Toc173423319)

[4.19.4. 接口返回参数 73](#_Toc173423320)

[4.19.5. 返回样例 74](#_Toc173423321)

[4.20. 工单告知 75](#_Toc173423322)

[4.20.1. 接口描述 75](#_Toc173423323)

[4.20.2. 接口请求参数 75](#_Toc173423324)

[4.20.3. 请求样例 76](#_Toc173423325)

[4.20.4. 接口返回参数 76](#_Toc173423326)

[4.20.5. 返回样例 76](#_Toc173423327)

[4.21. 工单办理经过查询 77](#_Toc173423328)

[4.21.1. 接口描述 77](#_Toc173423329)

[4.21.2. 接口请求参数 77](#_Toc173423330)

[4.21.3. 请求样例 78](#_Toc173423331)

[4.21.4. 接口返回参数 78](#_Toc173423332)

[4.21.5. 返回样例 79](#_Toc173423333)

[4.22. 更新工单对接信息 81](#_Toc173423334)

[4.22.1. 接口描述 81](#_Toc173423335)

[4.22.2. 接口请求参数 82](#_Toc173423336)

[4.22.3. 请求样例 83](#_Toc173423337)

[4.22.4. 接口返回参数 83](#_Toc173423338)

[4.22.5. 返回样例 83](#_Toc173423339)

[4.23. 上传工单多媒体 85](#_Toc173423340)

[4.23.1. 接口描述 85](#_Toc173423341)

[4.23.2. 接口请求参数 85](#_Toc173423342)

[4.23.3. 请求样例 85](#_Toc173423343)

[4.23.4. 接口返回参数 86](#_Toc173423344)

[4.23.5. 返回样例 86](#_Toc173423345)

[5. 用户凭证接口详情 86](#_Toc173423346)

[5.1. 获取公钥接口 87](#_Toc173423347)

[5.1.1. 接口描述 87](#_Toc173423348)

[5.1.2. 接口请求参数 87](#_Toc173423349)

[5.1.3. 接口返回参数 87](#_Toc173423350)

[5.1.4. 返回样例 88](#_Toc173423351)

[5.2. 获取token接口 88](#_Toc173423352)

[5.2.1. 接口描述 88](#_Toc173423353)

[5.2.2. 接口请求参数 88](#_Toc173423354)

[5.2.3. 接口返回参数 88](#_Toc173423355)

[5.2.4. 返回样例 89](#_Toc173423356)

[6. 基础字典表接口详细 89](#_Toc173423357)

[6.1. 工单字典表接口 89](#_Toc173423358)

[6.1.1. 接口描述 89](#_Toc173423359)

[6.1.2. 接口请求参数 90](#_Toc173423360)

[6.1.3. 请求样例 90](#_Toc173423361)

[6.1.4. 接口返回参数 90](#_Toc173423362)

[6.1.5. 返回样例 91](#_Toc173423363)

[7. 附录 92](#_Toc173423364)

[7.1. SM2加密算法 92](#_Toc173423365)

[7.2. 通知名称字典 93](#_Toc173423366)

[7.3. 常见错误码 94](#_Toc173423367)

# 概述

本手册为V22市区对接区级接口标准说明，用于与市级平台与各区分中心数据交互的参考。内容主要包括：接口缩略语、系统对接技术要求和业务员接口详解等。

区分中心数据接口提供的功能包括：工单上报、答复退单、答复延期、答复结案、工单督办、工单催办、满意度评价、工单更新、工单回收和工单重办等。

# 缩略语

下列缩略语适用本文件。

## HTTP 协议

超文本传输协议(HTTP，HyperTextTransfer Protocol)是互联网上应用最为广泛的一种网络协议。HTTP 请求信息由请求方法 URI 协议/版本、请求头(Request Header) 以及请求正文三部分组成。

## JSON (数据交换格式)

JSON(JavaScript Object Notation, JS 对象标记) 是一种轻量级的数据交换格式。它基于 ECMAScript (w3c 制定的js 规范)的一个子集，采用完全独立于编程语言的文本格式来存储和表示数据。简洁和清晰的层次结构使得 JSON成为理想的数据交换语言。易于人阅读和编写，同时也易于机器解析和生成，并有效地提升网络传输效率。

## Header(请求头)

header 是指请求或者响应报文的头部信息。

### Content-Type(内容编码类型)

是指 http 发送信息至服务器时的内容编码类型，Content-Type 用于表明发送数据 流的类型，服务器根据编码类型使用特定的解析方式，获取数据流中的数据。该参数为 Header(请求头)必填参数。

### Authorization(用户凭证)

根据用户提供的身份凭证，生成权限实体，并为之授予相应的权限。该参数为 Header(请求头)必填参数。

## body(报文体)

报文体是指请求或者响应报文的 body 信息。本文档中的报文体都是 JSON 数据。

## UTF-8(字符编码)

Unicode 的可变长度字符编码(8-bit Unicode Transformation Format)。

# 系统对接技术要求

## 接口对接方式

本系统接口协议用于分中心应用通过 HTTP 请求方式， Content-type：application/json。

## 请求规范

接口交互统一采用 UTF-8 编码。

请求参数必须统一包含用户凭证，参考 5 章节

请求方法为 GET 或 POST，使用方式参考接口说明-请求路径及方法。

## 请求频率

处理工单时，建议由人工提交工单；除新工单列表、通知等定时请求(时间间隔 5- 10 分钟)；其他避免系统定时调用接口。

## 接口对接流程

### 制定业务规范

明确接口交互内容、接口对接方式、接口操作流程、接口详情。

### 制定接口标准

接口标准应约定以下内容

A、接口对接方式

B 、请求规范

C 、请求频率

D 、接口操作流程

E 、业务详情描述

F、 接口描述

G 、接口请求参数说明

H 、接口返回参数说明

详情查阅此文档。

### 准备运行环境

#### 网络

接口部署在政务外网，对外提供政务外网访问地址。

接口地址防火墙限制源请求 IP，需分中心提供请求 IP ，开通防火墙安全策略。

#### 接口互联互通用户

申请接口用户，配置接口请求权限。

#### 运行环境检查

系统联调测试及上线前， 应检查运行环境是否满足网络、安全、账户配置要求。

### 开发及联调测试

双方技术人员根据技术规范进行开发工作。

存在争议或变更的内容，由各方业务管理人员沟通后，变更规范文档。 按需搭建各自系统测试环境，避免联调测试数据流入生产环境。

### 上线运行

经过联调测试无异常，符合业务要求，向业务管理单位申请功能上线。系统运行期间，定期进行巡检和校对。

# 业务办理接口详情

## 工单上报

### 接口描述

平台上报接口。

### 接口请求参数

|  |  |  |  |
| --- | --- | --- | --- |
| 请求路径：http://{ip}:{port}/v22-api/openapi/v1/action POST请求  星桥请求路径：http://{ip}:{port}/星桥服务名称/api/exchange/eurbanpro/openapi/v1/report POST请求 | | | |
| 参数名称 | 参数类型 | 参数说明 | 备注 |
| data | Object | 下派信息json对象 | 必传 |
| senderCode | string | 发送方标识，参见第三方平台编码 | 必传 |
| action | String | REPORT | 必传 |
| uid | String | 请求唯一标识 | 必传，可以通过UUID.randomUUID().toString()获取 |
| data参数详情 | | | |
| 参数名称 | 参数类型 | 参数说明 | 备注 |
| caseId | string | 工单标识 | 必传 |
| caseHandleId | string | 派单唯一标识 | 非必传 |
| casNum | string | 工单编号 | 非必传 |
| openId | string | 微信OpenId | 非必传 |
| registerTime | string | 登记时间 | 必传，格式为“yyyy-MM-dd HH:mm:ss” |
| dispatchTime | String | 派单时间 | 非必传，格式为“yyyy-MM-dd HH:mm:ss” |
| signTime | string | 签收时间 | 非必传，格式为“yyyy-MM-dd HH:mm:ss” |
| signDeadline | string | 签收截止时间 | 非必传，格式为“yyyy-MM-dd HH:mm:ss” |
| rollbackDeadline | string | 回退截止时间 | 非必传，格式为“yyyy-MM-dd HH:mm:ss” |
| disposeDeadlineTime | string | 处置截止时间 | 非必传，工单处置时限（天/小时） |
| title | string | 工单标题 | 非必传 |
| eventDesc | string | 工单内容 | 必传 |
| recTypeId | integer | 工单类型 | 必传，参考6.1 工单类型字典表 |
| recTypeName | String | 工单类型名称 | 必传，参考6.1 工单类型字典表 |
| eventTypeId | integer | 问题类型标识 | 非必传 |
| eventTypeName | string | 问题类型 | 非必传 |
| mainTypeId | Integer | 大类标识 | 非必传 |
| mainTypeName | string | 大类名称 | 非必传 |
| subTypeId | Integer | 小类标识 | 非必传 |
| subTypeName | string | 小类名称 | 非必传 |
| thirdTypeId | Integer | 细类标识 | 非必传 |
| thirdTypeName | string | 细类名称 | 非必传 |
| eventSrcId | Integer | 工单来源标识 | 必传，参考6.1 工单来源字典表 |
| eventSrcName | string | 工单来源名称 | 必传，参考6.1 工单来源字典表 |
| coordinateX | double | 工单X坐标 | 非必传 |
| coordinateY | double | 工单Y坐标 | 非必传 |
| address | string | 诉求详细地址 | 必传 |
| districtId | Integer | 问题所属区县编码 | 非必传 |
| districtName | string | 问题所属区县名称 | 非必传 |
| streetId | Integer | 街道标识 | 非必传 |
| streetName | String | 街道名称 | 非必传 |
| communityId | Integer | 社区标识 | 非必传 |
| communityName | String | 社区名称 | 非必传 |
| cellId | Integer | 网格标识 | 非必传 |
| cellName | String | 网格名称 | 非必传 |
| dispatchOpinion | longtext | 派单意见 | 非必传 |
| signState | int | 签收状态 | 非必传 |
| sendTypeCode | string | 交办类型 | 非必传 |
| sendTypeName | string | 交办类型名称 | 非必传 |
| handleOrgCode | String | 待处置部门编号 | 非必传 |
| handleOrgName | String | 待处置部门名称 | 非必传 |
| caseStatus | Integer | 工单状态 | 非必传 |
| urgentLevelId | int | 紧急程度 | 非必传 |
| keyword | string | 关键词 | 非必传 |
| caseMark | string | 工单标签 | 非必传 |
| evaluateContent | String | 评价内容 | 非必传 |
| accidentFlag | int | 是否突发事件 | 非必传 |
| instableFlag | int | 是否不稳定因素 | 非必传 |
| repeatCallFlag | int | 是否重复来电 | 非必传 |
| returnVisitFlag | int | 是否回访 | 非必传，默认0，不回访 |
| publicFlag | int | 是否允许对外公开 | 非必传，默认0，不对外公开 |
| rollbackFlag | Int | 是否允许回退 | 非必传，默认1，允许回退 |
| postponeFlag | Int | 是否允许延期 | 非必传，默认1，允许延期 |
| reHandleFlag | Int | 是否重办 | 非必传，默认0 |
| callSubjectId | Integer | 来电主体标识 | 非必传 |
| callSubjectName | string | 来电人主体名称 | 非必传 |
| contact | string | 来电号码 | 非必传 |
| IdCardNo | string | 证件号 | 非必传 |
| callTime | date | 来电时间 | 非必传 |
| reporterName | string | 来电人姓名 | 非必传 |
| reporterAddress | string | 来电人详细地址 | 非必传 |
| reporterPublicFlag | int | 是否公开举报人标识 | 非必传 |
| genderId | Integer | 来电人性别 | 非必传 |
| ageRangeId | int | 来电人年龄范围标识 | 非必传 |
| telReply | String | 答复号码 | 非必传，多个用因为逗号分隔 |
| medias | List | 多媒体列表 | 必传 |
| mediaName | String | 多媒体名称 | 必传 |
| mediaPath | String | 多媒体完整地址 | 二选一必传 |
| content | String | Base64内容 |
| mediaUsage | String | 文件类型 | 必传，上报/核查/核实/处置/自处置 |
| mediaTypeId | Integer | 多媒体关联类型 | 必传，参见字典表接口，默认传1 |

### 请求样例

|  |
| --- |
| {      "uid": "oNbld0TohzzqNlWYZCjb5bevvIQ8",      "data": {          "eventPropertyName": "求助",          "publicFlag": 1,          "reporterName": "匿名",          "eventLevelId": 1,          "eventDesc": "标题： 反映拖欠工资的问题\n工作领域:非工程建设领域\n行业类型:其他\n拖欠工资单位名称:宠物馆\n拖欠工资单位电话:132\*\*\*\*\n实际工作地址:xx区xx街道宠物馆\n是否有签订劳动合同:否\n欠薪时间段:xxx到xxx\n欠薪金额（元）:xx元\n是否曾经通过以下途径反映上述问题（可多选）:未曾通过以上途径反映欠薪问题\n欠薪基本情况摘要:本人于xx年xx月xx日开始进入宠物馆 从事给喂粮喂水换猫砂的工作 目前拖欠本人xx日到xx日的工资 共计xx元\n反映人姓名:xxx\n反映人身份证号码:xxxxxxxx\n反映人性别:x\n",          "caseId": "20240731104001",          "contact": "13211112222",          "reporterAddress": "xx路xx宠物馆",          "eventPropertyId": 13,          "registerTime": "2024-07-18 09:04:36",          "eventSrcId": 104,          "recTypeId": 23,          "medias": [              {                  "mediaName": "618cf8c4e1d935754.jpg",                  "mediaPath": "https://pic.616pic.com/photoone/00/03/16/618cf8c4e1d935754.jpg",                  "mediaUsage": "上报",                  "mediaTypeId": 1              }          ],          "rollbackRedispatchRec": false,          "eventSrcName": "链接下单",          "altpsRec": false,          "disposeDeadlineTime": "2024-08-01 23:59:59",          "title": "反映拖欠工资的问题",          "streetName": "xx街道",          "telReply": "13211112222",          "sendTypeName": "",          "recTypeName": "市一体化平台",          "caseMark": "综治信访维稳/劳动纠纷/用人单位欠薪、辞退问题",          "caseHandleId": "0964e3fa46a94f2783c8846acbd7c87a",          "address": "xx路xx宠物馆",          "districtName": "xx区",          "genderId": 0,          "rollbackNotApproveRec": false,          "dispatchOpinion": "请贵单位尽快处理，按处理期限答复市民并将处理结果反馈给我单位。(注:请勿将来电人资料泄露给被投诉单位，做好市民信息保密工作）",          "dispatchTime": "2024-07-18 09:04:42",          "coordinateY": "22.63333",          "coordinateX": "114.33333",          "archiveNotApproveRec": false,          "reporterPublicFlag": 1,          "callTime": "2024-07-18 09:04:36"      },      "action": "REPORT",      "senderCode": "mssq"  } |

### 接口返回参数

|  |  |  |  |
| --- | --- | --- | --- |
| 参数名称 | 参数类型 | 参数说明 | 备注 |
| success | boolean | 接口是否成功返回标识 | true: 成功 false: 失败 |
| code | int | 错误编码 | 0:成功 -1: 失败 |
| message | string | 返回结果消息 |  |
| result | Json | 返回数据内容 |  |
| recId | int | 区级平台方案卷标识 |  |
| taskNum | string | 区级平台案件号 |  |

### 返回样例

|  |
| --- |
| {      "success": true,      "code": 0,      "message": "工单上报成功",      "result": {          "recId": 1251239,          "taskNum": "202407310001"      },      "uid": "oNbld0TohzzqNlWYZCjb5bevvIQ8",      "hasError": false  } |

## 工单信息查询

### 接口描述

获取工单详情，包括案件基础信息，来电记录（评价信息）、多媒体信息、举报人信息等。

### 接口请求参数

|  |  |  |  |
| --- | --- | --- | --- |
| 请求路径：http://{ip}:{port}/v22-api/openapi/v1/action POST请求  星桥请求路径：http://{ip}:{port}/星桥服务名称/api/exchange/eurbanpro/openapi/v1/getrecinfo POST请求 | | | |
| 参数名称 | 参数类型 | 参数说明 | 备注 |
| data | Object | 上报信息json对象 | 必传 |
| senderCode | string | 发送方标识，参见第三方平台编码 | 必传 |
| action | String | GET\_REC\_INFO | 必传 |
| uid | String | 请求唯一标识 | 必传，可以通过UUID.randomUUID().toString()获取 |
| data参数详情 | | | |
| 参数名称 | 参数类型 | 参数说明 | 备注 |
| caseId | string | 工单标识 | 必传（没有可以传工单编号） |

### 接口返回参数

|  |  |  |  |
| --- | --- | --- | --- |
| 参数名称 | 参数类型 | 参数说明 | 备注 |
| success | boolean | 接口是否成功返回标识 | true: 成功 false: 失败 |
| code | int | 错误编码 | 0:成功 -1: 失败 |
| message | string | 返回结果消息 |  |
| result | json | 返回数据内容 |  |
| result参数详情 | | | |
| recInfo | Json | 工单详情 |  |
| recInfo参数详情 | | | |
| reporterName | String | 举报人名称 |  |
| title | string | 工单标题 |  |
| eventDesc | string | 工单内容 |  |
| recTypeId | integer | 工单类型 |  |
| recTypeName | String | 工单类型名称 |  |
| eventTypeId | integer | 问题类型标识 |  |
| eventTypeName | string | 问题类型 |  |
| mainTypeId | Integer | 大类标识 |  |
| mainTypeName | string | 大类名称 |  |
| subTypeId | Integer | 小类标识 |  |
| subTypeName | string | 小类名称 |  |
| maxTypeId | Integer | 细类标识 |  |
| maxTypeName | string | 细类名称 |  |
| eventSrcId | Integer | 工单来源标识 |  |
| eventSrcName | string | 工单来源名称 |  |
| coordinateX | double | 工单X坐标 |  |
| coordinateY | double | 工单Y坐标 |  |
| address | string | 诉求详细地址 |  |
| districtId | Integer | 问题所属区县编码 |  |
| districtName | string | 问题所属区县名称 |  |
| streetId | Integer | 街道标识 |  |
| streetName | String | 街道名称 |  |
| communityId | Integer | 社区标识 |  |
| communityName | String | 社区名称 |  |
| partId | Integer | 参与者标识 |  |
| partType | String | 参与者类型 |  |
| partName | String | 参与者名称 |  |
| roleId | Integer | 岗位标识 |  |
| roleName | string | 岗位名称 |  |
| unitId | Integer | 部门标识 |  |
| unitName | String | 部门名称 |  |
| actCreateTime | String | 当前阶段开始时间 |  |
| actDeadline | String | 当前阶段截止时间 |  |
| recCreateTime | String | 案件创建时间 |  |
| actEndTime | string | 当前阶段结束时间 |  |
| eventLevelId | Integer | 问题级别标识 |  |
| eventLevelName | String | 问题级别名称 |  |
| actDefName | String | 阶段名称 |  |
| dealSatisfactionId | Integer | 处置满意度标识 |  |
| returnSatisfactionId | Integer | 回访满意度标识 |  |
| recId | Integer | 案件标识 |  |
| medias | array | 多媒体信息 |  |
| medias参数详情 | | | |
| uid | String | 多媒体唯一标识 |  |
| mediaName | String | 多媒体名称 |  |
| mediaPath | String | 多媒体完整地址 |  |
| mediaUsage | String | 文件类型 |  |
| mediaTypeId | Integer | 多媒体关联类型 |  |
| createTime | string | 多媒体创建时间 |  |

### 请求样例

|  |
| --- |
| {      "uid": "oNbld0TohzzqNlWYZCjb5bevvIQ8",      "data": {          "caseId": "20240731001"      },      "action": "GET\_REC\_INFO",      "senderCode": "mssq"  }  - |

### 返回样例

|  |
| --- |
| {      "success": true,      "code": 0,      "message": null,      "result": {          "recInfo": {              "eventPropertyName": "求助",              "partId": 13138,              "title": "反映拖欠工资的问题",              "reporterName": "匿名",              "eventLevelId": 1,              "partName": "区中心操作员",              "streetName": "马峦街道",              "eventDesc": "标题： 反映拖欠工资的问题\n工作领域:非工程建设领域\n行业类型:其他\n拖欠工资单位名称:宠物馆\n拖欠工资单位电话:132\*\*\*\*\n实际工作地址:xx区xx街道宠物馆\n是否有签订劳动合同:否\n欠薪时间段:xxx到xxx\n欠薪金额（元）:xx元\n是否曾经通过以下途径反映上述问题（可多选）:未曾通过以上途径反映欠薪问题\n欠薪基本情况摘要:本人于xx年xx月xx日开始进入宠物馆 从事给喂粮喂水换猫砂的工作 目前拖欠本人xx日到xx日的工资 共计xx元\n反映人姓名:xxx\n反映人身份证号码:xxxxxxxx\n反映人性别:x\n",              "recCreateTime": "2024-07-31T14:59:09.000",              "eventPropertyId": 13,              "unitId": 36500,              "recTypeName": "市一体化平台",              "communityName": "马峦社区",              "actPropertyId": 2,              "replyContent": null,              "communityId": 10000,              "taskNum": "202407310001",              "partType": "role",              "address": "xx路xx宠物馆",              "districtName": "坪山区",              "roleId": 13138,              "eventSrcId": 104,              "recTypeId": 23,              "replyUnit": "民生诉求服务中心",              "actDefName": "民生诉求服务中心受理分拨",              "dealSatisfactionId": 0,              "medias": [                  {                      "uid": "1-d83d5fe925864856a9dc8c5e1ff96eb3",                      "recId": 1251239,                      "mediaName": "7e0b477499a641ec9db4f19f935ac850.jpg",                      "mediaPath": "/free/media/getdata/Local/rec/1251239/7e0b477499a641ec9db4f19f935ac850.jpg",                      "mediaTypeId": 1,                      "mediaUsage": "上报",                      "createTime": "2024-07-31 14:59:12",                      "fileType": "IMAGE"                  }              ],              "coordinateY": 22.633330,              "coordinateX": 114.333330,              "districtId": 1,              "roleName": "区中心操作员",              "eventSrcName": "链接下单",              "actDeadline": "2024-08-01T14:59:09.000",              "actCreateTime": "2024-07-31T14:59:09.000",              "recId": 1251239,              "streetId": 102,              "returnSatisfactionId": 0          }      },      "uid": "b4fe314a-b3b8-4fad-a5df-a9113b3f92b6",      "hasError": false  } |

## 工单办理经过同步

### 接口描述

将工单办理经过信息同步至我方平台。

### 接口请求参数

|  |  |  |  |
| --- | --- | --- | --- |
| 请求路径：http://{ip}:{port}/v22-api/openapi/v1/action POST请求  星桥请求路径：[http://{ip}:{port}/星桥服务名称/api/exchange/eurbanpro/openapi/v1/iteminstsync](http://{ip}:{port}/%E6%98%9F%E6%A1%A5%E6%9C%8D%E5%8A%A1%E5%90%8D%E7%A7%B0/api/exchange/eurbanpro/openapi/v1/iteminstsync) POST请求 | | | |
| 参数名称 | 参数类型 | 参数说明 | 备注 |
| data | Object | 信息json对象 | 必传 |
| senderCode | string | 发送方标识，参见第三方平台编码 | 必传 |
| action | String | ITEM\_INST\_SYNC | 必传 |
| uid | String | 请求唯一标识 | 必传，可以通过UUID.randomUUID().toString()获取 |
| data参数详情 | | | |
| 参数名称 | 参数类型 | 参数说明 | 备注 |
| caseId | String | 工单标识 | 必传 |
| caseHandleId | String | 派单唯一标识 | 非必传 |
| caseNum | String | 工单编号 | 非必传 |
| taskDefineId | String | 当前阶段标识 |  |
| taskDefineName | String | 当前阶段名称 |  |
| action | String | 操作标识 | 必传 |
| actionName | String | 操作名称 | 必传 |
| actionTime | String | 操作时间 | 必传 |
| humanId | String | 办理人标识 |  |
| humanName | String | 办理人名称 |  |
| partUid | Integer | 参与者唯一标识 |  |
| partId | String | 参与者标识 |  |
| partTypeId | Integer | 参与者类型标识 |  |
| partName | String | 参与者名称 | 必传 |
| roleId | String | 岗位标识 |  |
| roleName | String | 岗位名称 |  |
| unitId | String | 部门标识 |  |
| unitName | String | 部门名称 |  |
| itemContent | String | 办理项内容，意见 | 必传 |
| nextTaskDefineId | String | 下阶段标识 |  |
| nextTaskDefineName | String | 下阶段名称 |  |
| nextHumanId | String | 下阶段办理人标识 |  |
| nextHumanName | String | 下阶段办理人名称 |  |
| nextPartId | String | 下阶段参与者标识 |  |
| nextPartTypeId | Integer | 下阶参与者类型标识 |  |
| nextPartName | String | 下阶参与者名称 |  |
| nextPartUid | Integer | 下阶段参与者标识 |  |
| nextRoleId | String | 下阶岗位标识 |  |
| nextRoleName | String | 下阶岗位名称 |  |
| nextUnitId | String | 下阶部门标识 |  |
| nextUnitName | String | 下阶部门名称 |  |

### 请求样例

|  |
| --- |
| {      "data": {          "taskDefineId": "artificial\_357c3b17-bbba-468b-b592-9bb1a22c52b4",          "taskDefineName": "市信息中心（受理）",          "action": "transit",          "actionName": "批转",          "actionTime": "2023-09-22 14:05:38",          "humanId": "1673529228661366784",          "humanName": "ls20230627777",          "partId": "wizdom:130072",          "partUid": 50455,          "partName": "拱墅区采集公司",          "partTypeId": 1,          "roleId": "wizdom:130072",          "roleName": "拱墅区采集公司",          "unitId": "wizdom:662",          "unitName": "采集公司",          "itemContent": "新增办理经过测试",          "nextTaskDefineId": "artificial\_357c3b17-bbba-468b-b592-9bb1a22c52b5",          "nextTaskDefineName": "市信息中心（派遣）",          "nextHumanId": "dbadf436-513d-4a8b-8d47-5c8c911fe90b",          "nextHumanName": "egova",          "nextPartId": "wizdom:131512",          "nextPartUid": 50595,          "nextPartName": "仓前街道派遣员",          "nextPartTypeId": 1,          "nextRoleId": "wizdom:131512",          "nextRoleName": "仓前街道派遣员",          "nextUnitId": "wizdom:3024",          "nextUnitName": "北干街道分派遣",          "caseId": "20240731001"      },      "senderCode": "mssq",      "uid": "836b6f0b-f83d-49e5-a4a1-7fc543d19402",      "action": "ITEM\_INST\_SYNC"  } |

### 接口返回参数

|  |  |  |  |
| --- | --- | --- | --- |
| 参数名称 | 参数类型 | 参数说明 | 备注 |
| success | boolean | 接口是否成功返回标识 | true: 成功 false: 失败 |
| code | int | 错误编码 | 0:成功 -1: 失败 |
| message | string | 返回结果消息 |  |
| result | Json | 返回数据内容 |  |
| recId | int | 区级平台方案卷标识 |  |
| taskNum | string | 区级平台案件号 |  |

### 返回样例

|  |
| --- |
| {      "success": true,      "code": 0,      "message": "工单办理经过同步成功",      "result": {          "wfActList": [              {                  "actId": "ebd7a070-cc0b-4c76-a7f0-df3d76916e73",                  "actDefId": "artificial\_385fe827-01de-46e4-9b3e-0aafaece4c44",                  "actDefName": "民生诉求服务中心受理分拨",                  "procDefId": "35059528ed4bf4449ef7e7",                  "procVersion": 10,                  "preActDef": null,                  "transItemTypeId": 231,                  "transItemTypeName": "wf\_inst\_create",                  "actStateId": 11110,                  "actStateName": "正常移交",                  "actPropertyId": 2,                  "actPropertyName": null,                  "startTime": "2024-07-31 14:59:09",                  "endTime": null,                  "updateTime": "2024-07-31 14:59:10",                  "bizEntryId": 1251239,                  "procInstId": "120cf6d0-fe64-4b64-8c44-ea909fd6a4c7",                  "partId": 13138,                  "partUid": "wizdom:716",                  "partName": "区中心操作员",                  "partType": "role",                  "humanId": 0,                  "humanUid": null,                  "humanName": null,                  "roleId": 13138,                  "roleUid": "wizdom:716",                  "roleName": "区中心操作员",                  "unitId": 36500,                  "unitUid": "wizdom:684",                  "unitName": "民生诉求服务中心",                  "menuSet": ",postpone,finish,cancel,suspend,transit\_end,transit,transit\_phase,apply\_cancel,accredit,transit\_any,",                  "priSubTypeId": 0,                  "engineTypeId": 2,                  "applyInfo": null,                  "parallelId": null,                  "initTaskId": "ebd7a070-cc0b-4c76-a7f0-df3d76916e73",                  "ardTypeId": 0,                  "ardStateId": 0,                  "assignTime": null,                  "id": 51570              }          ],          "recId": 1251239,          "taskNum": "202407310001"      },      "uid": "836b6f0b-f83d-49e5-a4a1-7fc543d19402",      "hasError": false  } |

## 工单处置反馈

### 接口描述

工单处置完后反馈处置信息，调用成功后工单在我方系统中的阶段会流转至下个核查/结案阶段。

### 接口请求参数

|  |  |  |  |
| --- | --- | --- | --- |
| 请求路径：http://{ip}:{port}/v22-api/openapi/v1/action POST请求  星桥请求路径：http://{ip}:{port}/星桥服务名称/api/exchange/eurbanpro/openapi/v1/disposefeedback POST请求 | | | |
| 参数名称 | 参数类型 | 参数说明 | 备注 |
| data | Object | 信息json对象 | 必传 |
| senderCode | String | 发送方标识，参见第三方平台编码 | 必传 |
| action | String | DISPOSE\_FEEDBACK | 必传 |
| uid | String | 请求唯一标识 | 必传，可以通过UUID.randomUUID().toString()获取 |
| data参数详情 | | | |
| 参数名称 | 参数类型 | 参数说明 | 备注 |
| caseId | String | 工单标识 | 必传 |
| caseHandleId | String | 派单唯一标识 | 非必传 |
| caseNum | String | 工单编号 | 非必传 |
| disposeOpinion | String | 处置意见 | 必传 |
| disposeTime | String | 处置时间 | 非必传，格式为“yyyy-MM-dd HH:mm:ss” |
| medias | List | 多媒体列表 | 非必传 |
| medias详情 | | | |
| mediaName | String | 多媒体名称 | 必传 |
| mediaPath | String | 多媒体完整地址 | 必传 |
| mediaUsage | String | 文件类型 | 处置 |
| mediaTypeId | Integer | 多媒体关联类型 | 必传，参见字典表接口，默认传1 |

### 请求样例

|  |
| --- |
| {      "data": {          "disposeTime": "2023-10-28 11:00:00",          "disposeOpinion": "处置反馈",          "disposeState": 1,          "disposeHumanName": "ls20230627",          "disposeRoleName": "市园文局绿化处",          "disposeUnitName": "市园文局绿化处",          "caseId": "20240731001",          "medias": [{              "mediaName": "618cf8c4e1d935754.jpg",              "mediaPath": "https://pic.616pic.com/photoone/00/03/16/618cf8c4e1d935754.jpg",              "mediaUsage": "处置",              "mediaTypeId":1            }]      },      "senderCode": "mssq",      "uid": "836b6f0b-f83d-49e5-a4a1-7fc543d19402",      "action": "DISPOSE\_FEEDBACK"  } |

### 接口返回参数

|  |  |  |  |
| --- | --- | --- | --- |
| 参数名称 | 参数类型 | 参数说明 | 备注 |
| success | boolean | 接口是否成功返回标识 | true: 成功 false: 失败 |
| code | int | 错误编码 | 0:成功 -1: 失败 |
| message | string | 返回结果消息 |  |
| result | Json | 返回数据内容 |  |
| recId | int | 区级平台方案卷标识 |  |
| taskNum | string | 区级平台案件号 |  |

### 返回样例

|  |
| --- |
| {      "success": true,      "code": 0,      "message": "工单处置反馈成功",      "result": {          "wfActList": [              {                  "actId": "ebd7a070-cc0b-4c76-a7f0-df3d76916e73",                  "actDefId": "artificial\_385fe827-01de-46e4-9b3e-0aafaece4c44",                  "actDefName": "民生诉求服务中心受理分拨",                  "procDefId": "35059528ed4bf4449ef7e7",                  "procVersion": 10,                  "preActDef": null,                  "transItemTypeId": 231,                  "transItemTypeName": "wf\_inst\_create",                  "actStateId": 11110,                  "actStateName": "正常移交",                  "actPropertyId": 2,                  "actPropertyName": null,                  "startTime": "2024-07-31 14:59:09",                  "endTime": null,                  "updateTime": "2024-07-31 14:59:10",                  "bizEntryId": 1251239,                  "procInstId": "120cf6d0-fe64-4b64-8c44-ea909fd6a4c7",                  "partId": 13138,                  "partUid": "wizdom:716",                  "partName": "区中心操作员",                  "partType": "role",                  "humanId": 0,                  "humanUid": null,                  "humanName": null,                  "roleId": 13138,                  "roleUid": "wizdom:716",                  "roleName": "区中心操作员",                  "unitId": 36500,                  "unitUid": "wizdom:684",                  "unitName": "民生诉求服务中心",                  "menuSet": ",postpone,finish,cancel,suspend,transit\_end,transit,transit\_phase,apply\_cancel,accredit,transit\_any,",                  "priSubTypeId": 0,                  "engineTypeId": 2,                  "applyInfo": null,                  "parallelId": null,                  "initTaskId": "ebd7a070-cc0b-4c76-a7f0-df3d76916e73",                  "ardTypeId": 0,                  "ardStateId": 0,                  "assignTime": null,                  "id": 51570              }          ],          "recId": 1251239,          "taskNum": "202407310001"      },      "uid": "836b6f0b-f83d-49e5-a4a1-7fc543d19402",      "hasError": false  } |

## 工单申请回退

### 接口描述

外部系统作为工单接受方时，外部系统使用此接口向我方系统申请已下派工单的回退。

### 接口请求参数

|  |  |  |  |
| --- | --- | --- | --- |
| 请求路径：http://{ip}:{port}/v22-api/openapi/v1/action POST请求  星桥请求路径：[http://{ip}:{port}/星桥服务名称//api/exchange/eurbanpro/openapi/v1/applyrollback](http://{ip}:{port}/%E6%98%9F%E6%A1%A5%E6%9C%8D%E5%8A%A1%E5%90%8D%E7%A7%B0/api/exchange/eurbanpro/openapi/v1/applyrollback) POST请求 | | | |
| 参数名称 | 参数类型 | 参数说明 | 备注 |
| data | Object | 信息json对象 | 必传 |
| senderCode | String | 发送方标识，参见第三方平台编码 | 必传 |
| action | String | APPLY\_ ROLLBACK | 必传 |
| uid | String | 请求唯一标识 | 必传，可以通过UUID.randomUUID().toString()获取 |
| data参数详情 | | | |
| 参数名称 | 参数类型 | 参数说明 | 备注 |
| caseId | String | 工单标识 | 必传 |
| caseHandleId | String | 派单唯一标识 | 非必传 |
| caseNum | String | 工单编号 | 非必传 |
| applyTypeId | Integer | 申请类型标识 | 必传，0：不需要审核，直接回退；1：需要答复回退 |
| applyReason | String | 申请原因 | 必传 |
| applyHumanId | String | 申请人标识 | 非必传 |
| applyHumanName | String | 申请人名称 | 非必传 |
| applyUnitId | String | 申请部门标识 | 非必传 |
| applyUnitName | String | 申请部门 | 非必传 |
| applyTime | String | 申请时间 | 必传，格式为“yyyy-MM-dd HH:mm:ss” |
| medias | List | 多媒体列表 | 非必传 |
| medias详情 | | | |
| mediaName | String | 多媒体名称 | 必传 |
| mediaPath | String | 多媒体完整地址 | 必传 |
| mediaUsage | String | 文件类型 | 申请回退/回退 |
| mediaTypeId | Integer | 多媒体关联类型 | 必传，参见字典表接口，默认传1 |

### 请求样例

|  |
| --- |
| {      "data": {          "applyTime": "2023-10-30 11:00:00",          "applyHumanName": "ls20230627",          "applyHumanId": "1673529228661366784",          "applyUnitId": "wizdom:132429",          "applyUnitName": "专业部门A",          "caseId": "20240731001",          "applyTypeId": 1,          "applyReason": "非本部门案件，申请回退",          "medias": [{              "mediaName": "618cf8c4e1d9357545.jpg",              "mediaPath": "https://pic.616pic.com/photoone/00/03/16/618cf8c4e1d935754.jpg",              "mediaUsage": "申请回退",              "mediaTypeId": 1          }]      },      "senderCode": "mssq",      "uid": "836b6f0b-f83d-49e5-a4a1-7fc543d19402",      "action": "APPLY\_ROLLBACK"  } |

### 接口返回参数

|  |  |  |  |
| --- | --- | --- | --- |
| 参数名称 | 参数类型 | 参数说明 | 备注 |
| success | boolean | 接口是否成功返回标识 | true: 成功 false: 失败 |
| code | int | 错误编码 | 0:成功 -1: 失败 |
| message | string | 返回结果消息 |  |
| result | Json | 返回数据内容 |  |
| recId | int | 区级平台方案卷标识 |  |
| taskNum | string | 区级平台案件号 |  |

### 返回样例

|  |
| --- |
| {      "success": true,      "code": 0,      "message": "工单申请回退成功",      "result": {          "wfActList": [              {                  "actId": "a3a6eacf-cc8b-0a0c-8024-ea8ef5ee1ba6",                  "actDefId": "artificial\_d899d2dd-397f-4400-b830-bcedb5250134",                  "actDefName": "街道分中心派遣",                  "procDefId": "35059528ed4bf4449ef7e7",                  "procVersion": 10,                  "preActDef": "artificial\_385fe827-01de-46e4-9b3e-0aafaece4c44",                  "transItemTypeId": 610,                  "transItemTypeName": "transit",                  "actStateId": 11110,                  "actStateName": "正常移交",                  "actPropertyId": 26,                  "actPropertyName": null,                  "startTime": "2024-07-31 15:35:20",                  "endTime": null,                  "updateTime": "2024-07-31 15:35:20",                  "bizEntryId": 1251239,                  "procInstId": "120cf6d0-fe64-4b64-8c44-ea909fd6a4c7",                  "partId": 13138,                  "partUid": "wizdom:716",                  "partName": "区中心操作员",                  "partType": "role",                  "humanId": 0,                  "humanUid": null,                  "humanName": null,                  "roleId": 13138,                  "roleUid": "wizdom:716",                  "roleName": "区中心操作员",                  "unitId": 36500,                  "unitUid": "wizdom:684",                  "unitName": "民生诉求服务中心",                  "menuSet": ",postpone,finish,cancel,suspend,transit\_end,untransit,rollback,transit,transit\_phase,apply\_rollback,accredit,transit\_any,ForceCancelRedirect,",                  "priSubTypeId": 0,                  "engineTypeId": 2,                  "applyInfo": null,                  "parallelId": null,                  "initTaskId": "a3a6eacf-cc8b-0a0c-8024-ea8ef5ee1ba6",                  "ardTypeId": 0,                  "ardStateId": 0,                  "assignTime": null,                  "id": 51572              }          ],          "recId": 1251239,          "taskNum": "202407310001"      },      "uid": "836b6f0b-f83d-49e5-a4a1-7fc543d19402",      "hasError": false  } |

## 工单答复回退

### 接口描述

我方系统作为工单接受方时，我方系统向外部系统申请工单回退，外部系统可使用该接口答复回退申请。

### 接口请求参数

|  |  |  |  |
| --- | --- | --- | --- |
| 请求路径：http://{ip}:{port}/v22-api/openapi/v1/action POST请求  星桥请求路径：[http://{ip}:{port}/星桥服务名称/api/exchange/eurbanpro/openapi/v1/replyrollback](http://{ip}:{port}/%E6%98%9F%E6%A1%A5%E6%9C%8D%E5%8A%A1%E5%90%8D%E7%A7%B0/api/exchange/eurbanpro/openapi/v1/replyrollback) POST请求 | | | |
| 参数名称 | 参数类型 | 参数说明 | 备注 |
| data | Object | 信息json对象 | 必传 |
| senderCode | String | 发送方标识，参见第三方平台编码 | 必传 |
| action | String | REPLY\_ROLLBACK | 必传 |
| uid | String | 请求唯一标识 | 必传，可以通过UUID.randomUUID().toString()获取 |
| data参数详情 | | | |
| 参数名称 | 参数类型 | 参数说明 | 备注 |
| caseId | String | 工单标识 | 必传 |
| caseHandleId | String | 派单唯一标识 | 非必传 |
| caseNum | String | 工单编号 | 非必传 |
| replyResult | Integer | 答复结果标识 | 必传，0：不同意；1：同意 |
| replyOpinion | String | 答复意见 | 必传 |
| replyHumanId | String | 答复人标识 | 非必传 |
| replyHumanName | String | 答复人名称 | 非必传 |
| replyUnitId | String | 答复部门标识 | 非必传 |
| replyUnitName | String | 答复部门 | 非必传 |
| replyTime | String | 答复时间 | 必传，格式为“yyyy-MM-dd HH:mm:ss” |
| thirdDeadlineTime | String | 第三方处置截止时间 | 非必传 |
| medias | List | 多媒体列表 | 非必传 |
| medias详情 | | | |
| mediaName | String | 多媒体名称 | 必传 |
| mediaPath | String | 多媒体完整地址 | 必传 |
| mediaUsage | String | 文件类型 | 答复回退 |
| mediaTypeId | Integer | 多媒体关联类型 | 必传，参见字典表接口，默认传1 |

### 请求样例

|  |
| --- |
| {      "data": {          "replyTime": "2023-10-30 11:00:00",          "replyHumanName": "ls20230627",          "replyHumanId": "1673529228661366784",          "replyUnitId": "wizdom:132429",          "replyUnitName": "市园文局绿化处",          "caseId": "20240731001",          "thirdDeadlineTime": "2023-11-01 00:00:00",          "replyResult": 1,          "replyOpinion": "案件同意回退",          "medias": [{              "mediaName": "618cf8c4e1d9357545.jpg",              "mediaPath": "https://pic.616pic.com/photoone/00/03/16/618cf8c4e1d935754.jpg",              "mediaUsage": "答复回退",              "mediaTypeId": 1          }]      },      "senderCode": "mssq",      "uid": "836b6f0b-f83d-49e5-a4a1-7fc543d19402",      "action": "REPLY\_ROLLBACK"  } |

### 接口返回参数

|  |  |  |  |
| --- | --- | --- | --- |
| 参数名称 | 参数类型 | 参数说明 | 备注 |
| success | boolean | 接口是否成功返回标识 | true: 成功 false: 失败 |
| code | int | 错误编码 | 0:成功 -1: 失败 |
| message | string | 返回结果消息 |  |
| result | Json | 返回数据内容 |  |
| recId | int | 区级平台方案卷标识 |  |
| taskNum | string | 区级平台案件号 |  |

### 返回样例

|  |
| --- |
| {      "success": true,      "code": 0,      "message": "工单答复回退成功",      "result": {          "wfActList": [              {                  "actId": "a3a6eacf-cc8b-0a0c-8024-ea8ef5ee1ba6",                  "actDefId": "artificial\_d899d2dd-397f-4400-b830-bcedb5250134",                  "actDefName": "街道分中心派遣",                  "procDefId": "35059528ed4bf4449ef7e7",                  "procVersion": 10,                  "preActDef": "artificial\_385fe827-01de-46e4-9b3e-0aafaece4c44",                  "transItemTypeId": 610,                  "transItemTypeName": "transit",                  "actStateId": 11310,                  "actStateName": "申请授权",                  "actPropertyId": 26,                  "actPropertyName": null,                  "startTime": "2024-07-31 15:35:20",                  "endTime": null,                  "updateTime": "2024-07-31 17:39:00",                  "bizEntryId": 1251239,                  "procInstId": "120cf6d0-fe64-4b64-8c44-ea909fd6a4c7",                  "partId": 13138,                  "partUid": "wizdom:716",                  "partName": "区中心操作员",                  "partType": "role",                  "humanId": 88052,                  "humanUid": "1748263346799611904",                  "humanName": "duijie",                  "roleId": 13138,                  "roleUid": "wizdom:716",                  "roleName": "区中心操作员",                  "unitId": 36500,                  "unitUid": "wizdom:684",                  "unitName": "民生诉求服务中心",                  "menuSet": ",postpone,finish,cancel,suspend,transit\_end,untransit,rollback,transit,transit\_phase,apply\_rollback,accredit,transit\_any,ForceCancelRedirect,unaccredit,",                  "priSubTypeId": 0,                  "engineTypeId": 2,                  "applyInfo": null,                  "parallelId": null,                  "initTaskId": "a3a6eacf-cc8b-0a0c-8024-ea8ef5ee1ba6",                  "ardTypeId": 626,                  "ardStateId": 1,                  "assignTime": "2024-07-31 17:39:00",                  "id": 51572              },              {                  "actId": "9d76d0f2-30fc-40f9-9823-2aae5685ffdf",                  "actDefId": "artificial\_53a18d27-9584-4882-b170-171268f530ad",                  "actDefName": "回退",                  "procDefId": "bb9491cbec96bcdeb0691a",                  "procVersion": 10,                  "preActDef": "artificial\_d899d2dd-397f-4400-b830-bcedb5250134",                  "transItemTypeId": 640,                  "transItemTypeName": "accredit",                  "actStateId": 11310,                  "actStateName": "申请授权",                  "actPropertyId": 104,                  "actPropertyName": null,                  "startTime": "2024-07-31 17:39:00",                  "endTime": null,                  "updateTime": "2024-07-31 17:39:00",                  "bizEntryId": 1251239,                  "procInstId": "d9f11545-0dcf-4e72-b570-8ba5255865de",                  "partId": 13138,                  "partUid": "wizdom:716",                  "partName": "区中心操作员",                  "partType": "role",                  "humanId": 0,                  "humanUid": null,                  "humanName": null,                  "roleId": 13138,                  "roleUid": "wizdom:716",                  "roleName": "区中心操作员",                  "unitId": 36500,                  "unitUid": "wizdom:684",                  "unitName": "民生诉求服务中心",                  "menuSet": ",reply\_accredit,",                  "priSubTypeId": 0,                  "engineTypeId": 2,                  "applyInfo": null,                  "parallelId": null,                  "initTaskId": "9d76d0f2-30fc-40f9-9823-2aae5685ffdf",                  "ardTypeId": 626,                  "ardStateId": 1,                  "assignTime": null,                  "id": 51573              }          ],          "recId": 1251239,          "taskNum": "202407310001"      },      "uid": "836b6f0b-f83d-49e5-a4a1-7fc543d19402",      "hasError": false  } |

## 工单申请延期

### 接口描述

外部系统作为工单接受方时，外部系统使用此接口向我方系统申请已下派工单的延期。

### 接口请求参数

|  |  |  |  |
| --- | --- | --- | --- |
| 请求路径：http://{ip}:{port}/v22-api/openapi/v1/action POST请求  星桥请求路径：[http://{ip}:{port}/星桥服务名称/api/exchange/eurbanpro/openapi/v1/applypostpone](http://{ip}:{port}/%E6%98%9F%E6%A1%A5%E6%9C%8D%E5%8A%A1%E5%90%8D%E7%A7%B0/api/exchange/eurbanpro/openapi/v1/applypostpone) POST请求 | | | |
| 参数名称 | 参数类型 | 参数说明 | 备注 |
| data | Object | 信息json对象 | 必传 |
| senderCode | String | 发送方标识，参见第三方平台编码 | 必传 |
| action | String | APPLY\_POSTPONE | 必传 |
| uid | String | 请求唯一标识 | 必传，可以通过UUID.randomUUID().toString()获取 |
| data参数详情 | | | |
| 参数名称 | 参数类型 | 参数说明 | 备注 |
| caseId | String | 工单标识 | 必传 |
| caseHandleId | String | 派单唯一标识 | 非必传 |
| caseNum | String | 工单编号 | 非必传 |
| applyTypeId | Integer | 申请类型标识 | 必传，0：不需要审核，直接延期；1：需要答复延期 |
| applyReason | String | 申请原因 | 必传 |
| applyHumanId | String | 申请人标识 | 非必传 |
| applyHumanName | String | 申请人名称 | 非必传 |
| applyUnitId | String | 申请部门标识 | 非必传 |
| applyUnitName | String | 申请部门 | 非必传 |
| postponeType | Integer | 延期单位 | 必传，0：延期时间；1：小时；2：天。 |
| postponeTime | Double | 延期数量 | 必传，延期XX小时或者XX天 |
| postponeDeadline | String | 延期时间 | 非必传，延期至XX时间，格式为“yyyy-MM-dd HH:mm:ss。（延期单位等于0时，必传） |
| applyTime | String | 申请时间 | 必传，格式为“yyyy-MM-dd HH:mm:ss” |
| medias | List | 多媒体列表 | 非必传 |
| medias详情 | | | |
| mediaName | String | 多媒体名称 | 必传 |
| mediaPath | String | 多媒体完整地址 | 必传 |
| mediaUsage | String | 文件类型 | 申请回退 |
| mediaTypeId | Integer | 多媒体关联类型 | 必传，参见字典表接口，默认传1 |

### 请求样例

|  |
| --- |
| **采用申请延期XX小时或者XX天的方式**  {      "data": {          "applyTime": "2023-10-30 11:00:00",          "applyHumanName": "ls20230627",          "applyHumanId": "1673529228661366784",          "applyUnitId": "wizdom:132429",          "applyUnitName": "专业部门A",          "caseId": "20240731001",          "postponeType": 2,          "postponeTime": 2.5,          "applyTypeId": 1,          "applyReason": "案件即将超期，工作压力大，申请延期",          "medias": [{              "mediaName": "618cf8c4e1d9357545.jpg",              "mediaPath": "https://pic.616pic.com/photoone/00/03/16/618cf8c4e1d935754.jpg",              "mediaUsage": "申请延期",              "mediaTypeId": 1          }]      },      "senderCode": "mssq",      "uid": "836b6f0b-f83d-49e5-a4a1-7fc543d19402",      "action": "APPLY\_POSTPONE"  }  **采用申请延期至XXX的方式**  {      "data": {          "applyTime": "2023-10-30 11:00:00",          "applyHumanName": "ls20230627",          "applyHumanId": "1673529228661366784",          "applyUnitId": "wizdom:132429",          "applyUnitName": "专业部门A",          "caseId": "20240731001",          "postponeDeadline": "2024-08-05 11:00:00",          "applyTypeId": 1,          "applyReason": "案件即将超期，工作压力大，申请延期",          "medias": [              {                  "mediaName": "618cf8c4e1d9357545.jpg",                  "mediaPath": "https://pic.616pic.com/photoone/00/03/16/618cf8c4e1d935754.jpg",                  "mediaUsage": "申请延期",                  "mediaTypeId": 1              }          ]      },      "senderCode": "mssq",      "uid": "836b6f0b-f83d-49e5-a4a1-7fc543d19402",      "action": "APPLY\_POSTPONE"  } |

### 接口返回参数

|  |  |  |  |
| --- | --- | --- | --- |
| 参数名称 | 参数类型 | 参数说明 | 备注 |
| success | boolean | 接口是否成功返回标识 | true: 成功 false: 失败 |
| code | int | 错误编码 | 0:成功 -1: 失败 |
| message | string | 返回结果消息 |  |
| result | Json | 返回数据内容 |  |
| recId | int | 区级平台方案卷标识 |  |
| taskNum | string | 区级平台案件号 |  |

### 返回样例

|  |
| --- |
| {      "success": true,      "code": 0,      "message": "工单申请延期成功",      "result": {          "wfActList": [              {                  "actId": "8f5b66e2-c117-e859-c188-5382df209712",                  "actDefId": "artificial\_4014f54e-f714-472f-9e15-f01e6f3a7b80",                  "actDefName": "区责任单位处置",                  "procDefId": "35059528ed4bf4449ef7e7",                  "procVersion": 10,                  "preActDef": "artificial\_385fe827-01de-46e4-9b3e-0aafaece4c44",                  "transItemTypeId": 610,                  "transItemTypeName": "transit",                  "actStateId": 11110,                  "actStateName": "正常移交",                  "actPropertyId": 7,                  "actPropertyName": null,                  "startTime": "2024-07-31 17:48:45",                  "endTime": null,                  "updateTime": "2024-07-31 17:48:45",                  "bizEntryId": 1251239,                  "procInstId": "120cf6d0-fe64-4b64-8c44-ea909fd6a4c7",                  "partId": 14114,                  "partUid": "wizdom:10403",                  "partName": "水务局",                  "partType": "role",                  "humanId": 0,                  "humanUid": null,                  "humanName": null,                  "roleId": 14114,                  "roleUid": "wizdom:10403",                  "roleName": "水务局",                  "unitId": 37472,                  "unitUid": "wizdom:10401",                  "unitName": "区水务局",                  "menuSet": ",postpone,finish,cancel,suspend,transit\_end,untransit,rollback,transit,transit\_phase,apply\_rollback,apply\_transit,apply\_reset\_notify,apply\_stage\_archive,apply\_viewreporter,apply\_postpone,accredit,transit\_any,ForceCancelRedirect,",                  "priSubTypeId": 0,                  "engineTypeId": 2,                  "applyInfo": null,                  "parallelId": null,                  "initTaskId": "8f5b66e2-c117-e859-c188-5382df209712",                  "ardTypeId": 0,                  "ardStateId": 0,                  "assignTime": null,                  "id": 51575              }          ],          "recId": 1251239,          "taskNum": "202407310001"      },      "uid": "836b6f0b-f83d-49e5-a4a1-7fc543d19402",      "hasError": false  } |

## 工单答复延期

### 接口描述

我方系统作为工单接受方时，我方系统向外部系统申请工单延期，外部系统可使用该接口答复延期申请。

### 接口请求参数

|  |  |  |  |
| --- | --- | --- | --- |
| 请求路径：http://{ip}:{port}/v22-api/openapi/v1/action POST请求  星桥请求路径：[http://{ip}:{port}/星桥服务名称/api/exchange/eurbanpro/openapi/v1/replypostpone](http://{ip}:{port}/%E6%98%9F%E6%A1%A5%E6%9C%8D%E5%8A%A1%E5%90%8D%E7%A7%B0/api/exchange/eurbanpro/openapi/v1/replypostpone) POST请求 | | | |
| 参数名称 | 参数类型 | 参数说明 | 备注 |
| data | Object | 信息json对象 | 必传 |
| senderCode | String | 发送方标识，参见第三方平台编码 | 必传 |
| action | String | REPLY\_POSTPONE | 必传 |
| Uid | String | 请求唯一标识 | 必传，可以通过UUID.randomUUID().toString()获取 |
| data参数详情 | | | |
| 参数名称 | 参数类型 | 参数说明 | 备注 |
| caseId | String | 工单标识 | 必传 |
| caseHandleId | String | 派单唯一标识 | 非必传 |
| caseNum | String | 工单编号 | 非必传 |
| replyResult | Integer | 答复结果标识 | 必传，0：不同意；1：同意 |
| replyOpinion | String | 答复意见 | 必传 |
| replyHumanId | String | 答复人标识 | 非必传 |
| replyHumanName | String | 答复人名称 | 非必传 |
| replyUnitId | String | 答复部门标识 | 非必传 |
| replyUnitName | String | 答复部门 | 非必传 |
| replyTime | String | 答复时间 | 必传，格式为“yyyy-MM-dd HH:mm:ss” |
| medias | List | 多媒体列表 | 非必传 |
| medias详情 | | | |
| mediaName | String | 多媒体名称 | 必传 |
| mediaPath | String | 多媒体完整地址 | 必传 |
| mediaUsage | String | 文件类型 | 答复回退 |
| mediaTypeId | Integer | 多媒体关联类型 | 必传，参见字典表接口，默认传1 |

### 请求样例

|  |
| --- |
| {      "data": {          "replyTime": "2023-10-30 11:00:00",          "replyHumanName": "ls20230627",          "replyHumanId": "1673529228661366784",          "replyUnitId": "wizdom:132429",          "replyUnitName": "市值班长",          "caseId": "20240731001",          "replyResult": 1,          "replyOpinion": "案件同意延期",          "medias": [{              "mediaName": "618cf8c4e1d9357545.jpg",              "mediaPath": "https://pic.616pic.com/photoone/00/03/16/618cf8c4e1d935754.jpg",              "mediaUsage": "答复延期",              "mediaTypeId": 1          }]      },      "senderCode": "mssq",      "uid": "836b6f0b-f83d-49e5-a4a1-7fc543d19402",      "action": "REPLY\_POSTPONE"  } |

### 接口返回参数

|  |  |  |  |
| --- | --- | --- | --- |
| 参数名称 | 参数类型 | 参数说明 | 备注 |
| success | boolean | 接口是否成功返回标识 | true: 成功 false: 失败 |
| code | int | 错误编码 | 0:成功 -1: 失败 |
| message | string | 返回结果消息 |  |
| result | Json | 返回数据内容 |  |
| recId | int | 区级平台方案卷标识 |  |
| taskNum | string | 区级平台案件号 |  |

### 返回样例

|  |
| --- |
| {      "success": true,      "code": 0,      "message": "成功",      "result": {},      "uid": "836b6f0b-f83d-49e5-a4a1-7fc543d19402",      "hasError": false  } |

## 工单申请作废

### 接口描述

外部系统作为工单接受方时，外部系统使用此接口向我方系统申请已下派工单的作废。

### 接口请求参数

|  |  |  |  |
| --- | --- | --- | --- |
| 请求路径：http://{ip}:{port}/v22-api/openapi/v1/action POST请求  星桥请求路径：[http://{ip}:{port}/星桥服务名称/api/exchange/eurbanpro/openapi/v1/applycancel](http://{ip}:{port}/%E6%98%9F%E6%A1%A5%E6%9C%8D%E5%8A%A1%E5%90%8D%E7%A7%B0/api/exchange/eurbanpro/openapi/v1/applycancel) POST请求 | | | |
| 参数名称 | 参数类型 | 参数说明 | 备注 |
| data | Object | 信息json对象 | 必传 |
| senderCode | String | 发送方标识，参见第三方平台编码 | 必传 |
| action | String | APPLY\_CANCEL | 必传 |
| uid | String | 请求唯一标识 | 必传，可以通过UUID.randomUUID().toString()获取 |
| data参数详情 | | | |
| 参数名称 | 参数类型 | 参数说明 | 备注 |
| caseId | String | 工单标识 | 必传 |
| caseHandleId | String | 派单唯一标识 | 非必传 |
| caseNum | String | 工单编号 | 非必传 |
| applyTypeId | Integer | 申请类型标识 | 必传，0：不需要审核，直接回退；1：需要答复回退 |
| applyReason | String | 申请原因 | 必传 |
| applyHumanId | String | 申请人标识 | 非必传 |
| applyHumanName | String | 申请人名称 | 非必传 |
| applyUnitId | String | 申请部门标识 | 非必传 |
| applyUnitName | String | 申请部门 | 非必传 |
| applyTime | String | 申请时间 | 必传，格式为“yyyy-MM-dd HH:mm:ss” |
| medias | List | 多媒体列表 | 非必传 |
| medias详情 | | | |
| mediaName | String | 多媒体名称 | 必传 |
| mediaPath | String | 多媒体完整地址 | 必传 |
| mediaUsage | String | 文件类型 | 申请回退/回退 |
| mediaTypeId | Integer | 多媒体关联类型 | 必传，参见字典表接口，默认传1 |

### 请求样例

|  |
| --- |
| {      "data": {          "applyTime": "2023-10-30 11:00:00",          "applyHumanName": "ls20230627",          "applyUnitName": "专业部门A",          "caseId": "20240731001",          "applyTypeId": 1,          "applyReason": "非部门案件，申请作废",          "medias": [              {                  "mediaName": "618cf8c4e1d9357545.jpg",                  "mediaPath": "https://pic.616pic.com/photoone/00/03/16/618cf8c4e1d935754.jpg",                  "mediaUsage": "申请作废",                  "mediaTypeId": 1              }          ]      },      "senderCode": "mssq",      "uid": "836b6f0b-f83d-49e5-a4a1-7fc543d19402",      "action": "APPLY\_CANCEL"  } |

### 接口返回参数

|  |  |  |  |
| --- | --- | --- | --- |
| 参数名称 | 参数类型 | 参数说明 | 备注 |
| success | boolean | 接口是否成功返回标识 | true: 成功 false: 失败 |
| code | int | 错误编码 | 0:成功 -1: 失败 |
| message | string | 返回结果消息 |  |
| result | Json | 返回数据内容 |  |
| recId | int | 区级平台方案卷标识 |  |
| taskNum | string | 区级平台案件号 |  |

### 返回样例

|  |
| --- |
| {      "success": true,      "code": 0,      "message": "工单申请作废成功",      "result": {          "wfActList": [              {                  "actId": "8f5b66e2-c117-e859-c188-5382df209712",                  "actDefId": "artificial\_4014f54e-f714-472f-9e15-f01e6f3a7b80",                  "actDefName": "区责任单位处置",                  "procDefId": "35059528ed4bf4449ef7e7",                  "procVersion": 10,                  "preActDef": "artificial\_385fe827-01de-46e4-9b3e-0aafaece4c44",                  "transItemTypeId": 610,                  "transItemTypeName": "transit",                  "actStateId": 11110,                  "actStateName": "正常移交",                  "actPropertyId": 7,                  "actPropertyName": null,                  "startTime": "2024-07-31 17:48:45",                  "endTime": null,                  "updateTime": "2024-07-31 17:49:06",                  "bizEntryId": 1251239,                  "procInstId": "120cf6d0-fe64-4b64-8c44-ea909fd6a4c7",                  "partId": 14114,                  "partUid": "wizdom:10403",                  "partName": "水务局",                  "partType": "role",                  "humanId": 88052,                  "humanUid": "1748263346799611904",                  "humanName": "duijie",                  "roleId": 14114,                  "roleUid": "wizdom:10403",                  "roleName": "水务局",                  "unitId": 37472,                  "unitUid": "wizdom:10401",                  "unitName": "区水务局",                  "menuSet": ",postpone,finish,cancel,suspend,transit\_end,untransit,rollback,transit,transit\_phase,apply\_rollback,apply\_transit,apply\_reset\_notify,apply\_stage\_archive,apply\_viewreporter,apply\_postpone,accredit,transit\_any,ForceCancelRedirect,",                  "priSubTypeId": 0,                  "engineTypeId": 2,                  "applyInfo": null,                  "parallelId": null,                  "initTaskId": "8f5b66e2-c117-e859-c188-5382df209712",                  "ardTypeId": 606,                  "ardStateId": 4,                  "assignTime": "2024-07-31 17:49:06",                  "id": 51575              }          ],          "recId": 1251239,          "taskNum": "202407310001"      },      "uid": "836b6f0b-f83d-49e5-a4a1-7fc543d19402",      "hasError": false  } |

## 工单答复作废

### 接口描述

我方系统作为工单接受方时，我方系统向外部系统申请工单作废，外部系统可使用该接口答复作废申请。

### 接口请求参数

|  |  |  |  |
| --- | --- | --- | --- |
| 请求路径：http://{ip}:{port}/v22-api/openapi/v1/action POST请求  星桥请求路径：[http://{ip}:{port}/星桥服务名称/api/exchange/eurbanpro/openapi/v1/replycancel](http://{ip}:{port}/%E6%98%9F%E6%A1%A5%E6%9C%8D%E5%8A%A1%E5%90%8D%E7%A7%B0/api/exchange/eurbanpro/openapi/v1/replycancel) POST请求 | | | |
| 参数名称 | 参数类型 | 参数说明 | 备注 |
| data | Object | 信息json对象 | 必传 |
| senderCode | String | 发送方标识，参见第三方平台编码 | 必传 |
| action | String | REPLY\_CANCEL | 必传 |
| uid | String | 请求唯一标识 | 必传，可以通过UUID.randomUUID().toString()获取 |
| data参数详情 | | | |
| 参数名称 | 参数类型 | 参数说明 | 备注 |
| caseId | String | 工单标识 | 必传 |
| caseHandleId | String | 派单唯一标识 | 非必传 |
| caseNum | String | 工单编号 | 非必传 |
| replyResult | Integer | 答复结果标识 | 必传，0：不同意；1：同意 |
| replyOpinion | String | 答复意见 | 必传 |
| replyHumanId | String | 答复人标识 | 非必传 |
| replyHumanName | String | 答复人名称 | 非必传 |
| replyUnitId | String | 答复部门标识 | 非必传 |
| replyUnitName | String | 答复部门 | 非必传 |
| replyTime | String | 答复时间 | 必传，格式为“yyyy-MM-dd HH:mm:ss” |
| thirdDeadlineTime | String | 第三方处置截止时间 | 非必传 |
| medias | List | 多媒体列表 | 非必传 |
| medias详情 | | | |
| mediaName | String | 多媒体名称 | 必传 |
| mediaPath | String | 多媒体完整地址 | 必传 |
| mediaUsage | String | 文件类型 | 答复作废 |
| mediaTypeId | Integer | 多媒体关联类型 | 必传，参见字典表接口，默认传1 |

### 请求样例

|  |
| --- |
| {      "data": {          "replyTime": "2023-10-30 11:00:00",          "replyHumanName": "ls20230627",          "replyHumanId": "1673529228661366784",          "replyUnitId": "wizdom:132429",          "replyUnitName": "市园文局绿化处",          "caseId": "20240731001",          "thirdDeadlineTime": "2023-11-01 00:00:00",          "replyResult": 0,          "replyOpinion": "案件不同意作废",          "medias": [              {                  "mediaName": "618cf8c4e1d9357545.jpg",                  "mediaPath": "https://pic.616pic.com/photoone/00/03/16/618cf8c4e1d935754.jpg",                  "mediaUsage": "答复作废",                  "mediaTypeId": 1              }          ]      },      "senderCode": "mssq",      "uid": "836b6f0b-f83d-49e5-a4a1-7fc543d19402",      "action": "REPLY\_CANCEL"  } |

### 接口返回参数

|  |  |  |  |
| --- | --- | --- | --- |
| 参数名称 | 参数类型 | 参数说明 | 备注 |
| success | boolean | 接口是否成功返回标识 | true: 成功 false: 失败 |
| code | int | 错误编码 | 0:成功 -1: 失败 |
| message | string | 返回结果消息 |  |
| result | Json | 返回数据内容 |  |
| recId | int | 区级平台方案卷标识 |  |
| taskNum | string | 区级平台案件号 |  |

### 返回样例

|  |
| --- |
| {      "success": true,      "code": 0,      "message": "工单答复作废成功",      "result": {          "wfActList": [              {                  "actId": "8f5b66e2-c117-e859-c188-5382df209712",                  "actDefId": "artificial\_4014f54e-f714-472f-9e15-f01e6f3a7b80",                  "actDefName": "区责任单位处置",                  "procDefId": "35059528ed4bf4449ef7e7",                  "procVersion": 10,                  "preActDef": "artificial\_385fe827-01de-46e4-9b3e-0aafaece4c44",                  "transItemTypeId": 610,                  "transItemTypeName": "transit",                  "actStateId": 11310,                  "actStateName": "申请授权",                  "actPropertyId": 7,                  "actPropertyName": null,                  "startTime": "2024-07-31 17:48:45",                  "endTime": null,                  "updateTime": "2024-07-31 17:49:06",                  "bizEntryId": 1251239,                  "procInstId": "120cf6d0-fe64-4b64-8c44-ea909fd6a4c7",                  "partId": 14114,                  "partUid": "wizdom:10403",                  "partName": "水务局",                  "partType": "role",                  "humanId": 88052,                  "humanUid": "1748263346799611904",                  "humanName": "duijie",                  "roleId": 14114,                  "roleUid": "wizdom:10403",                  "roleName": "水务局",                  "unitId": 37472,                  "unitUid": "wizdom:10401",                  "unitName": "区水务局",                  "menuSet": ",postpone,finish,cancel,suspend,transit\_end,untransit,rollback,transit,transit\_phase,apply\_rollback,apply\_transit,apply\_reset\_notify,apply\_stage\_archive,apply\_viewreporter,apply\_postpone,accredit,transit\_any,ForceCancelRedirect,unaccredit,",                  "priSubTypeId": 0,                  "engineTypeId": 2,                  "applyInfo": null,                  "parallelId": null,                  "initTaskId": "8f5b66e2-c117-e859-c188-5382df209712",                  "ardTypeId": 814,                  "ardStateId": 1,                  "assignTime": "2024-07-31 17:49:06",                  "id": 51575              },              {                  "actId": "b8c8e0a1-f2f4-4a26-b7e3-cca77e8df41e",                  "actDefId": "artificial\_cc06ab7b-91ef-4e9e-b60b-527b663f9d70",                  "actDefName": "市民生诉求平台",                  "procDefId": "4ff28057ccb25456761601",                  "procVersion": 10,                  "preActDef": "artificial\_4014f54e-f714-472f-9e15-f01e6f3a7b80",                  "transItemTypeId": 640,                  "transItemTypeName": "accredit",                  "actStateId": 11310,                  "actStateName": "申请授权",                  "actPropertyId": 104,                  "actPropertyName": null,                  "startTime": "2024-07-31 18:45:41",                  "endTime": null,                  "updateTime": "2024-07-31 18:45:41",                  "bizEntryId": 1251239,                  "procInstId": "55b694bd-1135-4132-91b6-6fc0f8d4083e",                  "partId": 13139,                  "partUid": "wizdom:718",                  "partName": "区中心值班长",                  "partType": "role",                  "humanId": 0,                  "humanUid": null,                  "humanName": null,                  "roleId": 13139,                  "roleUid": "wizdom:718",                  "roleName": "区中心值班长",                  "unitId": 36500,                  "unitUid": "wizdom:684",                  "unitName": "民生诉求服务中心",                  "menuSet": ",reply\_accredit,",                  "priSubTypeId": 0,                  "engineTypeId": 2,                  "applyInfo": null,                  "parallelId": null,                  "initTaskId": "b8c8e0a1-f2f4-4a26-b7e3-cca77e8df41e",                  "ardTypeId": 814,                  "ardStateId": 1,                  "assignTime": null,                  "id": 51578              }          ],          "recId": 1251239,          "taskNum": "202407310001"      },      "uid": "836b6f0b-f83d-49e5-a4a1-7fc543d19402",      "hasError": false  } |

## 工单核查反馈

### 接口描述

我方系统对已处置完成的案件下发核查任务到外部系统，外部系统可通过该接口进行核查结果的反馈。

### 接口请求参数

|  |  |  |  |
| --- | --- | --- | --- |
| 请求路径：http://{ip}:{port}/v22-api/openapi/v1/action POST请求  星桥请求路径：[http://{ip}:{port}/星桥服务名称/api/exchange/eurbanpro/openapi/v1/checkfeedback](http://{ip}:{port}/%E6%98%9F%E6%A1%A5%E6%9C%8D%E5%8A%A1%E5%90%8D%E7%A7%B0/api/exchange/eurbanpro/openapi/v1/checkfeedback) POST请求 | | | |
| 参数名称 | 参数类型 | 参数说明 | 备注 |
| data | Object | 信息json对象 | 必传 |
| senderCode | String | 发送方标识，参见第三方平台编码 | 必传 |
| action | String | CHECK\_FEEDBACK | 必传 |
| uid | String | 请求唯一标识 | 必传，可以通过UUID.randomUUID().toString()获取 |
| data参数详情 | | | |
| 参数名称 | 参数类型 | 参数说明 | 备注 |
| caseId | String | 工单标识 | 必传 |
| disposeOpinion | String | 处置意见 | 必传 |
| disposeTime | String | 处置时间 | 非必传，格式为“yyyy-MM-dd HH:mm:ss” |
| disposeHumanId | String | 处置人员标识 | 非必传 |
| disposeHumanName | String | 处置人员名称 | 非必传 |
| disposeRoleId | String | 处置岗位标识 | 非必传 |
| disposeRoleName | String | 处置岗位名称 | 非必传 |
| disposeUnitId | String | 处置部门标识 | 非必传 |
| disposeUnitName | Integer | 处置部门名称 | 非必传 |
| disposeState | Integer | 处置结果 | 必传，默认0，0：反馈不通过；1：反馈通过 |
| medias | List | 多媒体列表 | 非必传 |
| medias详情 | | | |
| mediaName | String | 多媒体名称 | 必传 |
| mediaPath | String | 多媒体完整地址 | 必传 |
| mediaUsage | String | 文件类型 | 核查 |
| mediaTypeId | Integer | 多媒体关联类型 | 必传，参见字典表接口，默认传1 |

### 请求样例

|  |
| --- |
| {      "data": {          "disposeTime": "2023-10-28 11:00:00",          "disposeOpinion": "核查反馈",          "disposeState": 1,          "disposeHumanName": "ls20230627",          "disposeRoleName": "市园文局绿化处",          "disposeUnitName": "市园文局绿化处",          "caseId": "20240731001",          "medias": [{              "mediaName": "618cf8c4e1d935754.jpg",              "mediaPath": "https://pic.616pic.com/photoone/00/03/16/618cf8c4e1d935754.jpg",              "mediaUsage": "核查",              "mediaTypeId":1            }]      },      "senderCode": "mssq",      "uid": "836b6f0b-f83d-49e5-a4a1-7fc543d19402",      "action": "CHECK\_FEEDBACK"  } |

### 接口返回参数

|  |  |  |  |
| --- | --- | --- | --- |
| 参数名称 | 参数类型 | 参数说明 | 备注 |
| success | boolean | 接口是否成功返回标识 | true: 成功 false: 失败 |
| code | int | 错误编码 | 0:成功 -1: 失败 |
| message | string | 返回结果消息 |  |
| result | Json | 返回数据内容 |  |
| recId | int | 区级平台方案卷标识 |  |
| taskNum | string | 区级平台案件号 |  |

### 返回样例

|  |
| --- |
| {      "success": true,      "code": 0,      "message": "工单核查反馈成功",      "result": {          "wfActList": [              {                  "actId": "f929df7c-49f7-cc7a-0ac7-3846ec760348",                  "actDefId": "artificial\_597c44be-382c-462d-ad12-f0ffb7ba7407",                  "actDefName": "民生诉求服务中心结案",                  "procDefId": "35059528ed4bf4449ef7e7",                  "procVersion": 10,                  "preActDef": "artificial\_4014f54e-f714-472f-9e15-f01e6f3a7b80",                  "transItemTypeId": 610,                  "transItemTypeName": "transit",                  "actStateId": 11110,                  "actStateName": "正常移交",                  "actPropertyId": 14,                  "actPropertyName": null,                  "startTime": "2024-08-01 10:01:42",                  "endTime": null,                  "updateTime": "2024-08-01 10:01:42",                  "bizEntryId": 1251239,                  "procInstId": "120cf6d0-fe64-4b64-8c44-ea909fd6a4c7",                  "partId": 13138,                  "partUid": "wizdom:716",                  "partName": "区中心操作员",                  "partType": "role",                  "humanId": 0,                  "humanUid": null,                  "humanName": null,                  "roleId": 13138,                  "roleUid": "wizdom:716",                  "roleName": "区中心操作员",                  "unitId": 36500,                  "unitUid": "wizdom:684",                  "unitName": "民生诉求服务中心",                  "menuSet": ",postpone,finish,cancel,suspend,transit\_end,untransit,rollback,transit\_phase,ForceCancelRedirect,",                  "priSubTypeId": 0,                  "engineTypeId": 2,                  "applyInfo": null,                  "parallelId": null,                  "initTaskId": "f929df7c-49f7-cc7a-0ac7-3846ec760348",                  "ardTypeId": 0,                  "ardStateId": 0,                  "assignTime": null,                  "id": 51579              }          ],          "recId": 1251239,          "taskNum": "202407310001"      },      "uid": "836b6f0b-f83d-49e5-a4a1-7fc543d19402",      "hasError": false  } |

## 工单办结

### 接口描述

我方系统作为工单接受方时，外部系统可使用该接口通知我方系统工单已办结。

### 接口请求参数

|  |  |  |  |
| --- | --- | --- | --- |
| 请求路径：http://{ip}:{port}/v22-api/openapi/v1/action POST请求  星桥请求路径：http://{ip}:{port}/星桥服务名称/free/exchange/eurbanpro/openapi/v1/checkfeedback POST请求 | | | |
| 参数名称 | 参数类型 | 参数说明 | 备注 |
| Data | Object | 信息json对象 | 必传 |
| senderCode | String | 发送方标识，参见第三方平台编码 | 必传 |
| action | String | CHECK\_FEEDBACK | 必传 |
| uid | String | 请求唯一标识 | 必传，可以通过UUID.randomUUID().toString()获取 |
| data参数详情 | | | |
| 参数名称 | 参数类型 | 参数说明 | 备注 |
| caseId | String | 工单标识 | 必传 |
| archiveTime | String | 办结时间 | 非必传 |
| archiveOpinion | String | 办结意见 | 非必传 |
| archiveTypeId | Integer | 办结类型 | 必传，参见字典表 |
| archiveTypeName | String | 办结类型名称 | 非必传 |
| archiveHumanName | String | 办结人名称 | 非必传 |
| autoTransitNext | Integer | 办结前是否批转至下个阶段 | 非必传，默认1 |
| medias | list | 多媒体列表 | 非必传 |
| medias详情 | | | |
| mediaName | String | 多媒体名称 | 必传 |
| mediaPath | String | 多媒体完整地址 | 必传 |
| mediaUsage | String | 文件类型 | 结案 |
| mediaTypeId | Integer | 多媒体关联类型 | 必传，参见字典表接口，默认传1 |

### 请求样例

|  |
| --- |
| {      "data": {          "archiveTime": "2023-10-30 11:00:00",          "archiveOpinion": "工单办结",          "archiveTypeId": 1,          "archiveTypeName": "正常结案",          "archiveHumanId": "1673529228661366784",          "archiveHumanName": "ls20230627",          "caseId": "20240731001",          "autoTransitNext" : 0,          "medias": [{              "mediaName": "618cf8c4e1d9357545.jpg",              "mediaPath": "https://pic.616pic.com/photoone/00/03/16/618cf8c4e1d935754.jpg",              "mediaUsage": "结案",              "mediaTypeId":1            }]      },      "senderCode": "mssq",      "uid": "836b6f0b-f83d-49e5-a4a1-7fc543d19402",      "action": "ARCHIVE"  } |

### 接口返回参数

|  |  |  |  |
| --- | --- | --- | --- |
| 参数名称 | 参数类型 | 参数说明 | 备注 |
| success | boolean | 接口是否成功返回标识 | true: 成功 false: 失败 |
| code | int | 错误编码 | 0:成功 -1: 失败 |
| message | string | 返回结果消息 |  |
| result | Json | 返回数据内容 |  |
| recId | int | 我方平台方案卷标识 |  |
| taskNum | string | 我方平台案件号 |  |

### 返回样例

|  |
| --- |
| {      "success": true,      "code": 0,      "message": "工单办结成功",      "result": {          "wfActList": [              {                  "actId": "f929df7c-49f7-cc7a-0ac7-3846ec760348",                  "actDefId": "artificial\_597c44be-382c-462d-ad12-f0ffb7ba7407",                  "actDefName": "民生诉求服务中心结案",                  "procDefId": "35059528ed4bf4449ef7e7",                  "procVersion": 10,                  "preActDef": "artificial\_4014f54e-f714-472f-9e15-f01e6f3a7b80",                  "transItemTypeId": 610,                  "transItemTypeName": "transit",                  "actStateId": 11110,                  "actStateName": "正常移交",                  "actPropertyId": 14,                  "actPropertyName": null,                  "startTime": "2024-08-01 10:01:42",                  "endTime": null,                  "updateTime": "2024-08-01 10:01:42",                  "bizEntryId": 1251239,                  "procInstId": "120cf6d0-fe64-4b64-8c44-ea909fd6a4c7",                  "partId": 13138,                  "partUid": "wizdom:716",                  "partName": "区中心操作员",                  "partType": "role",                  "humanId": 0,                  "humanUid": null,                  "humanName": null,                  "roleId": 13138,                  "roleUid": "wizdom:716",                  "roleName": "区中心操作员",                  "unitId": 36500,                  "unitUid": "wizdom:684",                  "unitName": "民生诉求服务中心",                  "menuSet": ",postpone,finish,cancel,suspend,transit\_end,untransit,rollback,transit\_phase,ForceCancelRedirect,",                  "priSubTypeId": 0,                  "engineTypeId": 2,                  "applyInfo": null,                  "parallelId": null,                  "initTaskId": "f929df7c-49f7-cc7a-0ac7-3846ec760348",                  "ardTypeId": 0,                  "ardStateId": 0,                  "assignTime": null,                  "id": 51579              }          ],          "recId": 1251239,          "taskNum": "202407310001"      },      "uid": "836b6f0b-f83d-49e5-a4a1-7fc543d19402",      "hasError": false  } |

## 工单评价

### 接口描述

工单满意度评价。

### 接口请求参数

|  |  |  |  |
| --- | --- | --- | --- |
| 请求路径：http://{ip}:{port}/v22-api/openapi/v1/action POST请求  星桥请求路径：[http://{ip}:{port}/星桥服务名称/api/exchange/eurbanpro/openapi/v1/evaluate](http://{ip}:{port}/%E6%98%9F%E6%A1%A5%E6%9C%8D%E5%8A%A1%E5%90%8D%E7%A7%B0/api/exchange/eurbanpro/openapi/v1/evaluate) POST请求 | | | |
| 参数名称 | 参数类型 | 参数说明 | 备注 |
| data | Object | 信息json对象 | 必传 |
| senderCode | string | 发送方标识，参见第三方平台编码 | 必传 |
| action | String | EVALUATE | 必传 |
| uid | String | 请求唯一标识 | 必传，可以通过UUID.randomUUID().toString()获取 |
| data参数详情 | | | |
| 参数名称 | 参数类型 | 参数说明 | 备注 |
| caseId | String | 工单标识 | 必传 |
| misRecEvaluation | Object | 评价实体 | 必传 |
| schemeId | Integer | 评价方案 | 必传，联系我方对接人员获取 |
| evaluateTime | String | 评价时间 | 必传 |
| content | String | 评价内容 | 必传 |
| score | Float | 评价整体得分 | 非必传 |
| evaluateState | Integer | 评价状态 | 非必传，0：好评；1:差评，2：多次差评 |
| evaluateType | Integer | 评价类型 | 必传，0：主动评价；1:自动评价 |
| appealType | Integer | 申诉类型 | 非必传，0：允许申诉；1：必须申诉，2：不能申诉 |
| detailList | List | 评价详情 | 非必传 |
| groupId | Integer | 指标分组id | 必传，联系我方对接人员获取 |
| opinion | String | 评价内容 | 非必传 |
| indicatorResult | List | 评价指标 | 非必传 |
| indicatorId | Integer | 评价指标标识 | 必传，联系我方对接人员获取 |
| indicatorCode | String | 评价指标 | 必传，联系我方对接人员获取 |
| score | Float | 评价指标得分 | 必传 |

### 请求样例

|  |
| --- |
| {      "data": {          "misRecEvaluation": {              "schemeId": 1,              "evaluateTime": "2024-08-01 10:11:41",              "content": "好评 服务体验：非常满意；处置速度：非常满意；处置效果：非常满意；反馈质量：非常满意。",              "score": 5,              "evaluateState": 0,              "evaluateType": 0,              "appealType": 1,              "detailList": [                  {                      "groupId": 1,                      "opinion": "好评 服务体验：非常满意；处置速度：非常满意；处置效果：非常满意；反馈质量：非常满意。",                      "indicatorResult": [                          {                              "indicatorId": 1,                              "indicatorCode": "rec\_total\_evaluation",                              "score": 5                          },                          {                              "indicatorId": 2,                              "indicatorCode": "deal\_speed\_metrics",                              "score": "5"                          },                          {                              "indicatorId": 3,                              "indicatorCode": "deal\_effect\_metrics",                              "score": "5"                          },                          {                              "indicatorId": 4,                              "indicatorCode": "feedback\_quality\_metrics",                              "score": "5"                          },                          {                              "indicatorId": 5,                              "indicatorCode": "service\_metrics",                              "score": "5"                          }                      ]                  }              ]          },          "caseId": "20240731001"      },      "action": "EVALUATE",      "senderCode": "mssq",      "uid": "836b6f0b-f83d-49e5-a4a1-7fc543d19402"  } |

### 接口返回参数

|  |  |  |  |
| --- | --- | --- | --- |
| 参数名称 | 参数类型 | 参数说明 | 备注 |
| success | boolean | 接口是否成功返回标识 | true: 成功 false: 失败 |
| Code | int | 错误编码 | 0:成功 -1: 失败 |
| message | string | 返回结果消息 |  |
| result | Json | 返回数据内容 |  |

### 返回样例

|  |
| --- |
| {      "success": true,      "code": 0,      "message": null,      "result": {},      "uid": "836b6f0b-f83d-49e5-a4a1-7fc543d19402",      "hasError": false  } |

## 通知查询

### 接口描述

我方系统作为工单接受方或发出方时，外部系统可通过该接口查询工单各种操作的通知信息，例如工单下派通知、工单完成处置反馈通知、工单申请授权（回退、延期、作废、办结等）通知、工单答复授权（回退、延期、作废、办结等）通知、工单办结通知等。

### 接口请求参数

|  |  |  |  |
| --- | --- | --- | --- |
| 请求路径：http://{ip}:{port}/v22-api/openapi/v1/action POST请求  星桥请求路径：[http://{ip}:{port}/星桥服务名称/api/exchange/eurbanpro/openapi/v1/getnoticeinfo](http://{ip}:{port}/%E6%98%9F%E6%A1%A5%E6%9C%8D%E5%8A%A1%E5%90%8D%E7%A7%B0/api/exchange/eurbanpro/openapi/v1/getnoticeinfo) POST请求 | | | |
| 参数名称 | 参数类型 | 参数说明 | 备注 |
| data | Object | 信息json对象 | 必传 |
| senderCode | string | 发送方标识，参见第三方平台编码 | 必传 |
| action | String | GET\_NOTICE\_INFO | 必传 |
| uid | String | 请求唯一标识 | 必传，可以通过UUID.randomUUID().toString()获取 |
| data参数详情 | | | |
| 参数名称 | 参数类型 | 参数说明 | 备注 |
| noticeName | String | 通知名称 | 必传，详情参见附录7.2 |
| curPage | Integer | 查询页号 | 非必传，默认1 |
| numPerPage | Integer | 查询页最大数量 | 非必传，默认10 |

### 请求样例

|  |
| --- |
| {      "data": {          "noticeName": "REPORT\_NOTICE"      },      "action": "GET\_NOTICE\_INFO",      "senderCode": "mssq",      "uid": "836b6f0b-f83d-49e5-a4a1-7fc543d19402"  } |

### 接口返回参数

|  |  |  |  |
| --- | --- | --- | --- |
| 参数名称 | 参数类型 | 参数说明 | 备注 |
| success | Boolean | 接口是否成功返回标识 | true: 成功 false: 失败 |
| code | Int | 错误编码 | 0:成功 -1: 失败 |
| message | String | 返回结果消息 |  |
| result | Json | 返回数据内容 |  |
| result参数详情 | | | |
| resultList | List | 通知列表 |  |
| resultList参数详情 | | | |
| noticeId | Long | 通知标识 |  |
| noticeData | String | 通知内容 | **数据结构与各接口请求参数基本相同，比如工单下派通知与4.1工单上报接口的请求参数类似，答复延期通知与4.8工单答复延期接口请求参数类似。** |
| pageInfo | Json | 分页信息 |  |

### 返回样例

|  |
| --- |
| {      "success": true,      "code": 0,      "message": "工单通知查询成功",      "result": {          "pageInfo": {              "numPerPage": 10,              "currentPage": 1,              "totalPage": 1,              "totalRecord": 2,              "currentRecord": 2,              "enableCount": true          },          "resultList": [              {                  "noticeId": 6,                  "noticeData": "{\"caseId\":\"2131231\",\"disposeHumanId\": \"123456\",\"disposeHumanName\": \"egova\", \"disposeUnitId\": \"wizdom:662\",\"disposeUnitName\":\"采集公司\", \"medias\":[]}"              },              {                  "noticeId": 17,                  "noticeData": "{\"applyHumanId\":\"1673529228661366784\",\"applyHumanName\":\"ls20230627\",\"applyReason\":\"非部门案件，申请回退\",\"applyTime\":1698920297000,\"applyTypeId\":1,\"applyUnitId\":\"wizdom:4949\",\"applyUnitName\":\"拱墅区河道建设中心\",\"caseHandleId\":\"1232323233323685\",\"caseId\":\"1322360264654\",\"caseNum\":\"pinshan12345\",\"medias\":[]}"              }          ]      },      "uid": "1d04fcb5-9fd2-4dce-81b7-5a885350747c",      "hasError": false  } |

## 通知签收

### 接口描述

获取工单各种操作的通知信息后，需要调用此接口表示某条通知已接收到，避免下次调用通知查询接口查询到已处理的通知。

### 接口请求参数

|  |  |  |  |
| --- | --- | --- | --- |
| 请求路径：http://{ip}:{port}/v22-api/openapi/v1/action POST请求  星桥请求路径：[http://{ip}:{port}/星桥服务名称/api/exchange/eurbanpro/openapi/v1/noticesigning](http://{ip}:{port}/%E6%98%9F%E6%A1%A5%E6%9C%8D%E5%8A%A1%E5%90%8D%E7%A7%B0/api/exchange/eurbanpro/openapi/v1/noticesigning) POST请求 | | | |
| 参数名称 | 参数类型 | 参数说明 | 备注 |
| data | Object | 信息json对象 | 必传 |
| senderCode | string | 发送方标识，参见第三方平台编码 | 必传 |
| action | String | NOTICE\_SIGNING | 必传 |
| uid | String | 请求唯一标识 | 必传，可以通过UUID.randomUUID().toString()获取 |
| data参数详情 | | | |
| 参数名称 | 参数类型 | 参数说明 | 备注 |
| noticeList | List | 通知列表 | 必传 |
| **noticeList参数详情** | | | |
| noticeId | Long | 通知标识 | 必传 |
| caseId | string | 工单标识 | 非必传 |

### 请求样例

|  |
| --- |
| {      "data": {          "noticeList": [              {                  "noticeId": 412              }          ]      },      "action": "NOTICE\_SIGNING",      "senderCode": "mssq",      "uid": "836b6f0b-f83d-49e5-a4a1-7fc543d19402"  } |

### 接口返回参数

|  |  |  |  |
| --- | --- | --- | --- |
| 参数名称 | 参数类型 | 参数说明 | 备注 |
| success | Boolean | 接口是否成功返回标识 | true: 成功 false: 失败 |
| code | Int | 错误编码 | 0:成功 -1: 失败 |
| message | String | 返回结果消息 |  |
| result | Json | 返回数据内容 |  |

### 返回样例

|  |
| --- |
| {      "success": true,      "code": 0,      "message": "通知签收成功",      "result": {},      "uid": "a09239d6-cc24-4cf8-ae8d-bcc34e0c16dc",      "hasError": false  } |

## 工单督办

### 接口描述

可通过该接口对我方系统中的工单发起督办，发起后需要我方系统用户在督办中心确认发布。

### 接口请求参数

|  |  |  |  |
| --- | --- | --- | --- |
| 请求路径：http://{ip}:{port}/v22-api/openapi/v1/action POST请求  请求路径：[http://{ip}:{port}/星桥服务名称/api/exchange/eurbanpro/openapi/v1/supervise](http://{ip}:{port}/%E6%98%9F%E6%A1%A5%E6%9C%8D%E5%8A%A1%E5%90%8D%E7%A7%B0/api/exchange/eurbanpro/openapi/v1/supervise) POST请求 | | | |
| 参数名称 | 参数类型 | 参数说明 | 备注 |
| data | Object | 信息json对象 | 必传 |
| senderCode | string | 发送方标识，参见第三方平台编码 | 必传 |
| action | String | SUPERVISE | 必传 |
| uid | String | 请求唯一标识 | 必传，可以通过UUID.randomUUID().toString()获取 |
| data参数详情 | | | |
| 参数名称 | 参数类型 | 参数说明 | 备注 |
| caseId | string | 工单标识 | 必传 |
| endTime | String | 督办结束时间 | 非必传，格式endTime为“yyyy-MM-dd HH:mm:ss” |
| opinion | String | 督办意见 | 必传 |

### 请求样例

|  |
| --- |
| {      "data": {          "caseId": "20240801002",          "endTime": "2024-08-03 19:16:00",          "opinion": "处理太慢，需要督办"      },      "senderCode": "zhwx",      "uid": "836b6f0b-f83d-49e5-a4a1-7fc543d19403",      "action": "SUPERVISE"  } |

### 接口返回参数

|  |  |  |  |
| --- | --- | --- | --- |
| 参数名称 | 参数类型 | 参数说明 | 备注 |
| success | Boolean | 接口是否成功返回标识 | true: 成功 false: 失败 |
| code | Int | 错误编码 | 0:成功 -1: 失败 |
| message | String | 返回结果消息 |  |
| result | Json | 返回数据内容 |  |

### 返回样例

|  |
| --- |
| {      "success": true,      "code": 0,      "message": "工单督办:成功",      "result": {          "wfActList": [              {                  "actId": "b56cbc51-7b7c-4ae0-b95e-d78823ec9dfe",                  "actDefId": "artificial\_385fe827-01de-46e4-9b3e-0aafaece4c44",                  "actDefName": "民生诉求服务中心受理分拨",                  "procDefId": "35059528ed4bf4449ef7e7",                  "procVersion": 10,                  "preActDef": null,                  "transItemTypeId": 231,                  "transItemTypeName": "wf\_inst\_create",                  "actStateId": 11110,                  "actStateName": "正常移交",                  "actPropertyId": 2,                  "actPropertyName": null,                  "startTime": "2024-08-01 14:01:34",                  "endTime": null,                  "updateTime": "2024-08-01 14:01:35",                  "bizEntryId": 1251241,                  "procInstId": "0dbfdbfc-0d33-4dbb-ac14-47148d50ce6e",                  "partId": 13138,                  "partUid": "wizdom:716",                  "partName": "区中心操作员",                  "partType": "role",                  "humanId": 0,                  "humanUid": null,                  "humanName": null,                  "roleId": 13138,                  "roleUid": "wizdom:716",                  "roleName": "区中心操作员",                  "unitId": 36500,                  "unitUid": "wizdom:684",                  "unitName": "民生诉求服务中心",                  "menuSet": ",postpone,finish,cancel,suspend,transit\_end,transit,transit\_phase,apply\_cancel,accredit,transit\_any,",                  "priSubTypeId": 0,                  "engineTypeId": 2,                  "applyInfo": null,                  "parallelId": null,                  "initTaskId": "b56cbc51-7b7c-4ae0-b95e-d78823ec9dfe",                  "ardTypeId": 0,                  "ardStateId": 0,                  "assignTime": null,                  "id": 51582              }          ],          "recId": 1251241,          "taskNum": "202408010002"      },      "uid": "836b6f0b-f83d-49e5-a4a1-7fc543d19403",      "hasError": false  } |

## 工单催办

### 接口描述

可通过该接口对我方系统中的工单发起催办。

### 接口请求参数

|  |  |  |  |
| --- | --- | --- | --- |
| 请求路径：http://{ip}:{port}/v22-api/openapi/v1/action POST请求  星桥请求路径：[http://{ip}:{port}/星桥服务名称/api/exchange/eurbanpro/openapi/v1/press](http://{ip}:{port}/%E6%98%9F%E6%A1%A5%E6%9C%8D%E5%8A%A1%E5%90%8D%E7%A7%B0/api/exchange/eurbanpro/openapi/v1/press) POST请求 | | | |
| 参数名称 | 参数类型 | 参数说明 | 备注 |
| data | Object | 信息json对象 | 必传 |
| senderCode | string | 发送方标识，参见第三方平台编码 | 必传 |
| action | String | PRESS | 必传 |
| uid | String | 请求唯一标识 | 必传，可以通过UUID.randomUUID().toString()获取 |
| data参数详情 | | | |
| 参数名称 | 参数类型 | 参数说明 | 备注 |
| caseId | string | 工单标识 | 必传 |
| opinion | String | 督办意见 | 必传 |

### 请求样例

|  |
| --- |
| {      "uid": "oNbld0TohzzqNlWYZCjb5bevvIQ8",      "data": {          "caseId": "20240801002",          "opinion": "超期严重，请加快处理。"      },      "action": "PRESS",      "senderCode": "zhwx"  } |

### 接口返回参数

|  |  |  |  |
| --- | --- | --- | --- |
| 参数名称 | 参数类型 | 参数说明 | 备注 |
| success | Boolean | 接口是否成功返回标识 | true: 成功 false: 失败 |
| code | Int | 错误编码 | 0:成功 -1: 失败 |
| message | String | 返回结果消息 |  |
| result | Json | 返回数据内容 |  |

### 返回样例

|  |
| --- |
| {      "success": true,      "code": 0,      "message": null,      "result": {          "wfActList": [              {                  "actId": "44e624dd-18bf-b58e-ca70-b45e6c4cf620",                  "actDefId": "artificial\_4014f54e-f714-472f-9e15-f01e6f3a7b80",                  "actDefName": "区责任单位处置",                  "procDefId": "35059528ed4bf4449ef7e7",                  "procVersion": 10,                  "preActDef": "artificial\_385fe827-01de-46e4-9b3e-0aafaece4c44",                  "transItemTypeId": 610,                  "transItemTypeName": "transit",                  "actStateId": 11110,                  "actStateName": "正常移交",                  "actPropertyId": 7,                  "actPropertyName": null,                  "startTime": "2024-08-01 15:18:55",                  "endTime": null,                  "updateTime": "2024-08-01 15:18:55",                  "bizEntryId": 1251241,                  "procInstId": "0dbfdbfc-0d33-4dbb-ac14-47148d50ce6e",                  "partId": 14114,                  "partUid": "wizdom:10403",                  "partName": "水务局",                  "partType": "role",                  "humanId": 0,                  "humanUid": null,                  "humanName": null,                  "roleId": 14114,                  "roleUid": "wizdom:10403",                  "roleName": "水务局",                  "unitId": 37472,                  "unitUid": "wizdom:10401",                  "unitName": "区水务局",                  "menuSet": ",postpone,finish,cancel,suspend,transit\_end,untransit,rollback,transit,transit\_phase,apply\_rollback,apply\_transit,apply\_reset\_notify,apply\_stage\_archive,apply\_viewreporter,apply\_cancel,apply\_postpone,accredit,transit\_any,ForceCancelRedirect,",                  "priSubTypeId": 0,                  "engineTypeId": 2,                  "applyInfo": null,                  "parallelId": null,                  "initTaskId": "44e624dd-18bf-b58e-ca70-b45e6c4cf620",                  "ardTypeId": 0,                  "ardStateId": 0,                  "assignTime": null,                  "id": 51584              }          ],          "recId": 1251241,          "taskNum": "202408010002"      },      "uid": "oNbld0TohzzqNlWYZCjb5bevvIQ8",      "hasError": false  } |

## 下派通知查询

### 接口描述

外部系统可通过该接口获取我方系统下派的工单信息。

### 接口请求参数

|  |  |  |  |
| --- | --- | --- | --- |
| 请求路径：http://{ip}:{port}/v22-api/openapi/v1/action POST请求  星桥请求路径：[http://{ip}:{port}/星桥服务名称/api/exchange/eurbanpro/openapi/v1/getdispatchnoticeinfo](http://{ip}:{port}/%E6%98%9F%E6%A1%A5%E6%9C%8D%E5%8A%A1%E5%90%8D%E7%A7%B0/api/exchange/eurbanpro/openapi/v1/getdispatchnoticeinfo) POST请求 | | | |
| 参数名称 | 参数类型 | 参数说明 | 备注 |
| data | Object | 信息json对象 | 必传 |
| senderCode | string | 发送方标识，参见第三方平台编码 | 必传 |
| action | String | GET\_NOTICE\_INFO | 必传 |
| uid | String | 请求唯一标识 | 必传，可以通过UUID.randomUUID().toString()获取 |
| data参数详情 | | | |
| 参数名称 | 参数类型 | 参数说明 | 备注 |
| noticeName | String | 通知类型 | 固定值：REPORT\_NOTICE |
| curPage | int | 当前页 |  |
| numPerPage | int | 每页数量 |  |

### 请求样例

|  |
| --- |
| {      "data": {          "noticeName": "REPORT\_NOTICE"      },      "action": "GET\_NOTICE\_INFO",      "senderCode": "mssq",      "uid": "836b6f0b-f83d-49e5-a4a1-7fc543d19402"  } |

### 接口返回参数

|  |  |  |  |
| --- | --- | --- | --- |
| 参数名称 | 参数类型 | 参数说明 | 备注 |
| success | boolean | 接口是否成功返回标识 | true: 成功 false: 失败 |
| code | int | 错误编码 | 0:成功 -1: 失败 |
| message | string | 返回结果消息 |  |
| result | Json | 返回数据内容 |  |
| -pageInfo | Object | 分页信息 |  |
| --numPerPage | int | 每页数量 |  |
| --currentPage | int | 当前页 |  |
| --totalPage | int | 总页数 |  |
| --totalRecord | int | 总记录数 |  |
| --currentRecord | int | 当前页记录数 |  |
| -resultList | List<Object> | 返回数据 |  |
| --noticeId | int | 记录id | 通过4.15接口签收后该记录从本接口中消失 |
| --noticeData | String | 记录内容 | 需要通过JSON反序列化 |
| ---createTime | Date | 事发时间 |  |
| ---eventDesc | String | 事件描述 |  |
| ---address | String | 事件地址 |  |
| ---publicFlag | int | 是否允许对外公开 |  |
| ---eventLevelName | String | 事件等级 |  |
| ---eventLevelId | int | 事件等级 |  |
| ---reporterName | String | 上报人 |  |
| **---caseId** | **String** | **我方系统事件编码** |  |
| ---eventPropertyId | Int | 事件性质 |  |
| ---eventPropertyName | String | 事件性质 |  |
| ---maxEventTypeId | Int | 最小类别 |  |
| ---maxEventTypeName | String | 最小类别 |  |
| ---thirdTypeId | Int | 三级类别 |  |
| ---thirdTypeName | String | 三级类别 |  |
| ---subTypeId | Int | 二级类别 |  |
| ---subTypeName | String | 二级类别 |  |
| ---mainTypeId | Int | 一级类别 |  |
| ---mainTypeName | String | 一级类别 |  |
| ---eventTypeId | Int | 事件类别 |  |
| ---eventTypeName | String | 事件类别 |  |
| ---eventSrcId | Int | 事件来源 |  |
| ---eventSrcName | String | 事件来源 |  |
| ---recTypeId | Int | 事件类型 |  |
| ---recTypeName | String | 事件类型 |  |
| ---planeCoordinateY | Double | 平面坐标Y |  |
| ---planeCoordinateX | Double | 平面坐标X |  |
| ---coordinateY | Double | 纬度 | 具体坐标系请与对接人联系 |
| ---coordinateX | Double | 经度 | 具体坐标系请与对接人联系 |
| ---districtName | String | 区级名 |  |
| ---streetName | String | 街道名 |  |
| ---communityName | String | 社区名 |  |
| ---idCardNo | String | 上报人证件信息 |  |
| ---medias | List<Object> | 多媒体信息 |  |
| ----createTime | Long | 上传时间戳 |  |
| ----mediaName | String | 多媒体名 |  |
| ----mediaPath | String | 多媒体路径 | 路径具体前缀请与对接人确认 |
| ----mediaUsage | String | 多媒体用途 | 上报/处置/核实/核查 |

### 返回样例

|  |
| --- |
| {      "success": true,      "code": 0,      "message": "工单通知查询成功",      "result": {          "pageInfo": {              "numPerPage": 10,              "currentPage": 1,              "totalPage": 2,              "totalRecord": 18,              "currentRecord": 10,              "enableCount": true          },          "resultList": [              {                  "noticeId": 358,                  "noticeData": "{\"occurTime\":\"2024-03-06 11:38:46\",\"publicFlag\":0,\"eventLevelName\":\"快速\",\"maxEventTypeId\":4746,\"eventLevelId\":2,\"eventDesc\":\"推送市平台测试\",\"caseId\":\"SZPS202403061102300001\",\"bizId\":1,\"eventPropertyId\":5,\"entryTypeId\":23,\"maxEventTypeName\":\"黑车拉客\",\"thirdTypeName\":\"\",\"caseNum\":\"SZPS202403061102300001\",\"accidentFlag\":0,\"returnVisitFlag\":0,\"eventSrcId\":110,\"recTypeId\":23,\"sendPubCheckTaskFlag\":0,\"subTypeId\":4746,\"medias\":[],\"reviewMsgStateId\":1,\"eventSrcName\":\"市民上报\",\"postponeFlag\":1,\"instableFlag\":0,\"mainTypeId\":32,\"returnSatisfactionId\":0,\"subTypeName\":\"黑车拉客\",\"extras\":{},\"telReply\":\"13333333333\",\"extra\":{},\"callTypeId\":1,\"recTypeName\":\"市一体化平台\",\"timeAreaId\":0,\"finishRecReHandleGenNewRec\":1,\"reHandleFlag\":0,\"address\":\"312\",\"districtName\":\"市辖区\",\"verifyMsgStateId\":1,\"mainTypeName\":\"街面秩序\",\"dealSatisfactionId\":0,\"genderId\":3,\"repeatCallFlag\":0,\"checkMsgStateId\":1,\"eventTypeId\":4,\"rollbackFlag\":1,\"createTime\":\"2024-03-06 11:38:46\",\"areaTypeId\":0,\"eventTypeName\":\"事件\",\"fromMobile\":0,\"reporterPublicFlag\":0,\"reporterId\":283,\"urgentFlag\":0,\"callTime\":\"2023-10-11 18:11:05\"}"              },              {                  "noticeId": 361,                  "noticeData": "{\"occurTime\":\"2024-03-06 14:34:38\",\"publicFlag\":0,\"eventLevelName\":\"快速\",\"maxEventTypeId\":4746,\"eventLevelId\":2,\"eventDesc\":\"推送市平台测试\",\"caseId\":\"SZPS202403061102300004\",\"bizId\":1,\"eventPropertyId\":5,\"entryTypeId\":23,\"maxEventTypeName\":\"黑车拉客\",\"thirdTypeName\":\"\",\"caseNum\":\"SZPS202403061102300004\",\"accidentFlag\":0,\"returnVisitFlag\":0,\"eventSrcId\":110,\"recTypeId\":23,\"sendPubCheckTaskFlag\":0,\"subTypeId\":4746,\"medias\":[],\"reviewMsgStateId\":1,\"eventSrcName\":\"市民上报\",\"postponeFlag\":1,\"instableFlag\":0,\"mainTypeId\":32,\"returnSatisfactionId\":0,\"subTypeName\":\"黑车拉客\",\"extras\":{},\"telReply\":\"13333333333\",\"extra\":{},\"callTypeId\":1,\"recTypeName\":\"市一体化平台\",\"timeAreaId\":0,\"finishRecReHandleGenNewRec\":1,\"reHandleFlag\":0,\"address\":\"312\",\"districtName\":\"市辖区\",\"verifyMsgStateId\":1,\"mainTypeName\":\"街面秩序\",\"dealSatisfactionId\":0,\"genderId\":3,\"repeatCallFlag\":0,\"checkMsgStateId\":1,\"eventTypeId\":4,\"rollbackFlag\":1,\"createTime\":\"2024-03-06 14:34:38\",\"areaTypeId\":0,\"eventTypeName\":\"事件\",\"fromMobile\":0,\"reporterPublicFlag\":0,\"reporterId\":283,\"urgentFlag\":0,\"callTime\":\"2023-10-11 18:11:05\"}"              }          ]      },      "uid": "6b3708b5-6333-4849-9936-e26f03f2a741",      "hasError": false  } |

## 工单签收

### 接口描述

外部系统的用户通过该接口签收工单，表示处置部门已签收该工单。**签收后的工单才能进行后续告知等操作。**

### 接口请求参数

|  |  |  |  |
| --- | --- | --- | --- |
| 请求路径：http://{ip}:{port}/v22-api/openapi/v1/action POST请求  星桥请求路径：[http://{ip}:{port}/星桥服务名称/api/exchange/eurbanpro/openapi/v1/sign](http://{ip}:{port}/%E6%98%9F%E6%A1%A5%E6%9C%8D%E5%8A%A1%E5%90%8D%E7%A7%B0/api/exchange/eurbanpro/openapi/v1/sign) POST请求 | | | |
| 参数名称 | 参数类型 | 参数说明 | 备注 |
| data | Object | 信息json对象 | 必传 |
| senderCode | string | 发送方标识，参见第三方平台编码 | 必传 |
| action | String | SIGN | 必传 |
| uid | String | 请求唯一标识 | 必传，可以通过UUID.randomUUID().toString()获取 |
| data参数详情 | | | |
| 参数名称 | 参数类型 | 参数说明 | 备注 |
| caseId | String | 我方系统工单编号，详见4.15的响应参数 |  |

### 请求样例

|  |
| --- |
| {      "uid": "oNbld0TohzzqNlWYZCjb5bevvIQ8",      "data": {          "caseId": "202406200007"      },      "action": "SIGN",      "senderCode": "zhwx"  } |

### 接口返回参数

|  |  |  |  |
| --- | --- | --- | --- |
| 参数名称 | 参数类型 | 参数说明 | 备注 |
| success | boolean | 接口是否成功返回标识 | true: 成功 false: 失败 |
| code | int | 错误编码 | 0:成功 -1: 失败 |
| message | string | 返回结果消息 |  |
| result | Json | 返回数据内容 |  |

### 返回样例

|  |
| --- |
| {      "success": true,      "code": 0,      "message": "签收成功！",      "result": {          "wfActList": [              {                  "actId": "cd640380-d86d-d8c3-b602-9c1162a819c4",                  "actDefId": "artificial\_4014f54e-f714-472f-9e15-f01e6f3a7b80",                  "actDefName": "区责任单位处置",                  "procDefId": "35059528ed4bf4449ef7e7",                  "procVersion": 10,                  "preActDef": "artificial\_385fe827-01de-46e4-9b3e-0aafaece4c44",                  "transItemTypeId": 610,                  "transItemTypeName": "transit",                  "actStateId": 11110,                  "actStateName": "正常移交",                  "actPropertyId": 7,                  "actPropertyName": null,                  "startTime": "2024-06-20 16:46:01",                  "endTime": null,                  "updateTime": "2024-06-20 16:46:01",                  "bizEntryId": 1251164,                  "procInstId": "c4d329e3-130b-4ea3-b073-57715e7c2a5a",                  "partId": 14114,                  "partUid": "wizdom:10403",                  "partName": "水务局",                  "partType": "role",                  "humanId": 0,                  "humanUid": null,                  "humanName": null,                  "roleId": 14114,                  "roleUid": "wizdom:10403",                  "roleName": "水务局",                  "unitId": 37472,                  "unitUid": "wizdom:10401",                  "unitName": "区水务局",                  "menuSet": ",postpone,finish,cancel,suspend,transit\_end,untransit,rollback,transit,transit\_phase,apply\_rollback,apply\_transit,apply\_reset\_notify,apply\_stage\_archive,apply\_viewreporter,apply\_postpone,accredit,transit\_any,",                  "priSubTypeId": 0,                  "engineTypeId": 2,                  "applyInfo": null,                  "parallelId": null,                  "initTaskId": "cd640380-d86d-d8c3-b602-9c1162a819c4",                  "ardTypeId": 0,                  "ardStateId": 0,                  "assignTime": null,                  "id": 51419              }          ],          "recId": 1251164,          "taskNum": "202406200007"      },      "uid": "oNbld0TohzzqNlWYZCjb5bevvIQ8",      "hasError": false  } |

## 工单告知

### 接口描述

外部系统的业务部门通过该接口发送告知信息到上报人。

### 接口请求参数

|  |  |  |  |
| --- | --- | --- | --- |
| 请求路径：http://{ip}:{port}/v22-api/openapi/v1/action POST请求  星桥请求路径：[http://{ip}:{port}/星桥服务名称/api/exchange/eurbanpro/openapi/v1/notify](http://{ip}:{port}/%E6%98%9F%E6%A1%A5%E6%9C%8D%E5%8A%A1%E5%90%8D%E7%A7%B0/api/exchange/eurbanpro/openapi/v1/notify) POST请求 | | | |
| 参数名称 | 参数类型 | 参数说明 | 备注 |
| data | Object | 信息json对象 | 必传 |
| senderCode | string | 发送方标识，参见第三方平台编码 | 必传 |
| action | String | NOTIFY | 必传 |
| uid | String | 请求唯一标识 | 必传，可以通过UUID.randomUUID().toString()获取 |
| data参数详情 | | | |
| 参数名称 | 参数类型 | 参数说明 | 备注 |
| caseId | String | 我方系统工单编号，详见4.15的响应参数 |  |
| notifyContent | String | 告知内容 |  |
| notifyTypeId | int | 告知类型 | 1-受理告知 2-办理告知 96-阶段回复，各类型工单处置必要的告知类型请与对接人确认。 |
| notifyMethod | int | 告知方式 | 1-短信 2-仅记录 3-微信4-电话 |
| leaderCheck | int | 是否领导审核 |  |

### 请求样例

|  |
| --- |
| {      "uid": "oNbld0TohzzqNlWYZCjb5bevvIQ8",      "data": {          "caseId": "202406200006",          "notifyContent": "告知内容",          "notifyTypeId": 2,          "notifyMethod": 1,          "leaderCheck": 0      },      "action": "NOTIFY",      "senderCode": "zhwx"  } |

### 接口返回参数

|  |  |  |  |
| --- | --- | --- | --- |
| 参数名称 | 参数类型 | 参数说明 | 备注 |
| success | boolean | 接口是否成功返回标识 | true: 成功 false: 失败 |
| code | int | 错误编码 | 0:成功 -1: 失败 |
| message | string | 返回结果消息 |  |
| result | Json | 返回数据内容 |  |

### 返回样例

|  |
| --- |
| {      "success": true,      "code": 0,      "message": null,      "result": {          "wfActList": [              {                  "actId": "34b0bc28-618f-ada3-eee8-5b0421f16fea",                  "actDefId": "artificial\_4014f54e-f714-472f-9e15-f01e6f3a7b80",                  "actDefName": "区责任单位处置",                  "procDefId": "35059528ed4bf4449ef7e7",                  "procVersion": 10,                  "preActDef": "artificial\_385fe827-01de-46e4-9b3e-0aafaece4c44",                  "transItemTypeId": 610,                  "transItemTypeName": "transit",                  "actStateId": 11110,                  "actStateName": "正常移交",                  "actPropertyId": 7,                  "actPropertyName": null,                  "startTime": "2024-06-20 15:40:19",                  "endTime": null,                  "updateTime": "2024-06-20 15:40:19",                  "bizEntryId": 1251163,                  "procInstId": "8f12c474-b263-48b1-a8b6-1aaa26b70284",                  "partId": 14114,                  "partUid": "wizdom:10403",                  "partName": "水务局",                  "partType": "role",                  "humanId": 0,                  "humanUid": null,                  "humanName": null,                  "roleId": 14114,                  "roleUid": "wizdom:10403",                  "roleName": "水务局",                  "unitId": 37472,                  "unitUid": "wizdom:10401",                  "unitName": "区水务局",                  "menuSet": ",postpone,finish,cancel,suspend,transit\_end,untransit,rollback,transit,transit\_phase,apply\_rollback,apply\_transit,apply\_reset\_notify,apply\_stage\_archive,apply\_viewreporter,apply\_postpone,accredit,transit\_any,",                  "priSubTypeId": 0,                  "engineTypeId": 2,                  "applyInfo": null,                  "parallelId": null,                  "initTaskId": "34b0bc28-618f-ada3-eee8-5b0421f16fea",                  "ardTypeId": 0,                  "ardStateId": 0,                  "assignTime": null,                  "id": 51417              }          ],          "recId": 1251163,          "taskNum": "202406200006"      },      "uid": "oNbld0TohzzqNlWYZCjb5bevvIQ8",      "hasError": false  } |

## 工单办理经过查询

### 接口描述

外部系统可通过该接口查询工单在我方系统的办理经过。

### 接口请求参数

|  |  |  |  |
| --- | --- | --- | --- |
| 请求路径：http://{ip}:{port}/v22-api/openapi/v1/action POST请求  星桥请求路径：[http://{ip}:{port}/星桥服务名称/api/exchange/eurbanpro/openapi/v1/getrecprocessinfo](http://{ip}:{port}/%E6%98%9F%E6%A1%A5%E6%9C%8D%E5%8A%A1%E5%90%8D%E7%A7%B0/api/exchange/eurbanpro/openapi/v1/getrecprocessinfo) POST请求 | | | |
| 参数名称 | 参数类型 | 参数说明 | 备注 |
| data | Object | 信息json对象 | 必传 |
| senderCode | string | 发送方标识，参见第三方平台编码 | 必传 |
| action | String | GET\_REC\_PROCESS\_INFO | 必传 |
| uid | String | 请求唯一标识 | 必传，可以通过UUID.randomUUID().toString()获取 |
| data参数详情 | | | |
| 参数名称 | 参数类型 | 参数说明 | 备注 |
| caseId | String | 我方系统工单编号，详见4.15的响应参数 |  |

### 请求样例

|  |
| --- |
| {      "uid": "oNbld0TohzzqNlWYZCjb5bevvIQ8",      "data": {          "caseId": "20240801002"      },      "action": "GET\_REC\_PROCESS\_INFO",      "senderCode": "zhwx"  } |

### 接口返回参数

|  |  |  |  |
| --- | --- | --- | --- |
| 参数名称 | 参数类型 | 参数说明 | 备注 |
| success | boolean | 接口是否成功返回标识 | true: 成功 false: 失败 |
| code | int | 错误编码 | 0:成功 -1: 失败 |
| message | string | 返回结果消息 |  |
| result | Json | 返回数据内容 |  |
| itemInstList | List | 办理经过列表 |  |
| caseId | string | 工单号 |  |
| taskDefineName | string | 阶段名 |  |
| taskDefineId | string | 阶段标识 |  |
| actionName | string | 操作名 |  |
| actionTime | string | 操作时间 |  |
| humanName | string | 操作人 |  |
| unitName | string | 操作部门 |  |
| roleName | string | 操作岗位 |  |
| partName | string | 操作参与者 |  |
| itemContent | string | 操作内容 |  |
| nextTaskDefineId | string | 下阶段标识 |  |
| nextTaskDefineName | string | 下阶段名 |  |
| nextHumanName | string | 下阶段操作人 |  |
| nextPartName | string | 下阶段参与者 |  |
| nextRoleName | string | 下阶段岗位 |  |
| nextUnitName | string | 下阶段部门 |  |

### 返回样例

|  |
| --- |
| {      "success": true,      "code": 0,      "message": "获取工单办理经过成功",      "result": {          "itemInstList": [              {                  "caseId": "20240801002",                  "caseHandleId": null,                  "caseNum": null,                  "recId": null,                  "taskDefineId": "artificial\_385fe827-01de-46e4-9b3e-0aafaece4c44",                  "taskDefineName": "民生诉求服务中心受理分拨",                  "taskId": "b56cbc51-7b7c-4ae0-b95e-d78823ec9dfe",                  "action": "REPORT",                  "actionName": "工单上报",                  "actionTime": "2024-07-18 09:04:42",                  "humanId": "1748263346799611904",                  "humanName": "duijie",                  "partId": "1748263346799611904",                  "partUid": 88052,                  "partName": "duijie",                  "partTypeId": 0,                  "roleId": null,                  "roleName": null,                  "unitId": null,                  "unitName": null,                  "instanceId": "0dbfdbfc-0d33-4dbb-ac14-47148d50ce6e",                  "itemContent": "请贵单位尽快处理，按处理期限答复市民并将处理结果反馈给我单位。(注:请勿将来电人资料泄露给被投诉单位，做好市民信息保密工作）",                  "nextTaskId": null,                  "nextTaskDefineId": null,                  "nextTaskDefineName": null,                  "nextHumanId": null,                  "nextHumanName": null,                  "nextPartId": null,                  "nextPartUid": null,                  "nextPartName": null,                  "nextPartTypeId": null,                  "nextRoleId": null,                  "nextRoleName": null,                  "nextUnitId": null,                  "nextUnitName": null,                  "actionIndex": 0,                  "pingYinHumanName": null,                  "id": null              },              {                  "caseId": "20240801002",                  "caseHandleId": null,                  "caseNum": null,                  "recId": null,                  "taskDefineId": "artificial\_385fe827-01de-46e4-9b3e-0aafaece4c44",                  "taskDefineName": "民生诉求服务中心受理分拨",                  "taskId": "b56cbc51-7b7c-4ae0-b95e-d78823ec9dfe",                  "action": "Claim",                  "actionName": "办理",                  "actionTime": "2024-08-01 15:18:55",                  "humanId": "1691002223235043328",                  "humanName": "樊考",                  "partId": "wizdom:716",                  "partUid": 13138,                  "partName": "区中心操作员",                  "partTypeId": 1,                  "roleId": "wizdom:716",                  "roleName": "区中心操作员",                  "unitId": "wizdom:684",                  "unitName": "民生诉求服务中心",                  "instanceId": "0dbfdbfc-0d33-4dbb-ac14-47148d50ce6e",                  "itemContent": "执行办理工作项",                  "nextTaskId": "b56cbc51-7b7c-4ae0-b95e-d78823ec9dfe",                  "nextTaskDefineId": "artificial\_385fe827-01de-46e4-9b3e-0aafaece4c44",                  "nextTaskDefineName": "民生诉求服务中心受理分拨",                  "nextHumanId": "1691002223235043328",                  "nextHumanName": "樊考",                  "nextPartId": "wizdom:716",                  "nextPartUid": 13138,                  "nextPartName": "区中心操作员",                  "nextPartTypeId": 1,                  "nextRoleId": "wizdom:716",                  "nextRoleName": "区中心操作员",                  "nextUnitId": "wizdom:684",                  "nextUnitName": "民生诉求服务中心",                  "actionIndex": 0,                  "pingYinHumanName": null,                  "id": null              },              {                  "caseId": "20240801002",                  "caseHandleId": null,                  "caseNum": null,                  "recId": null,                  "taskDefineId": "artificial\_385fe827-01de-46e4-9b3e-0aafaece4c44",                  "taskDefineName": "民生诉求服务中心受理分拨",                  "taskId": "b56cbc51-7b7c-4ae0-b95e-d78823ec9dfe",                  "action": "Redirect",                  "actionName": "批转",                  "actionTime": "2024-08-01 15:18:55",                  "humanId": "1691002223235043328",                  "humanName": "樊考",                  "partId": "wizdom:716",                  "partUid": 13138,                  "partName": "区中心操作员",                  "partTypeId": 1,                  "roleId": "wizdom:716",                  "roleName": "区中心操作员",                  "unitId": "wizdom:684",                  "unitName": "民生诉求服务中心",                  "instanceId": "0dbfdbfc-0d33-4dbb-ac14-47148d50ce6e",                  "itemContent": "请处置",                  "nextTaskId": "44e624dd-18bf-b58e-ca70-b45e6c4cf620",                  "nextTaskDefineId": "artificial\_4014f54e-f714-472f-9e15-f01e6f3a7b80",                  "nextTaskDefineName": "区责任单位处置",                  "nextHumanId": null,                  "nextHumanName": null,                  "nextPartId": "wizdom:10403",                  "nextPartUid": 14114,                  "nextPartName": "水务局",                  "nextPartTypeId": 1,                  "nextRoleId": "wizdom:10403",                  "nextRoleName": "水务局",                  "nextUnitId": "wizdom:10401",                  "nextUnitName": "区水务局",                  "actionIndex": 1,                  "pingYinHumanName": null,                  "id": null              }          ]      },      "uid": "a53e4264-3b10-4f7d-aad3-ce7ab82b39aa",      "hasError": false  } |

## 更新工单对接信息

### 接口描述

外部系统可通过该接口更新我方系统中工单的部分信息。

### 接口请求参数

|  |  |  |  |
| --- | --- | --- | --- |
| 请求路径：http://{ip}:{port}/v22-api/openapi/v1/action POST请求  星桥请求路径：[http://{ip}:{port}/星桥服务名称/api/exchange/eurbanpro/openapi/v1/uploadcaseinfo](http://{ip}:{port}/%E6%98%9F%E6%A1%A5%E6%9C%8D%E5%8A%A1%E5%90%8D%E7%A7%B0/api/exchange/eurbanpro/openapi/v1/uploadcaseinfo) POST请求 | | | |
| 参数名称 | 参数类型 | 参数说明 | 备注 |
| data | Object | 信息json对象 | 必传 |
| senderCode | string | 发送方标识，参见第三方平台编码 | 必传 |
| action | String | UPLOAD\_CASE\_INFO | 必传 |
| uid | String | 请求唯一标识 | 必传，可以通过UUID.randomUUID().toString()获取 |
| data参数详情 | | | |
| 参数名称 | 参数类型 | 参数说明 | 备注 |
| registerTime | string | 登记时间 | 非必传，格式为“yyyy-MM-dd HH:mm:ss” |
| dispatchTime | String | 派单时间 | 非必传，格式为“yyyy-MM-dd HH:mm:ss” |
| signTime | string | 签收时间 | 非必传，格式为“yyyy-MM-dd HH:mm:ss” |
| signDeadline | string | 签收截止时间 | 非必传，格式为“yyyy-MM-dd HH:mm:ss” |
| rollbackDeadline | string | 回退截止时间 | 非必传，格式为“yyyy-MM-dd HH:mm:ss” |
| disposeDeadlineTime | double | 处置截止时间 | 非必传，格式为“yyyy-MM-dd HH:mm:ss” |
| title | string | 工单标题 | 非必传 |
| dispatchOpinion | longtext | 派单意见 | 非必传 |
| signState | int | 签收状态 | 非必传 |
| handleOrgCode | String | 待处置部门编号 | 非必传 |
| handleOrgName | String | 待处置部门名称 | 非必传 |
| keyword | string | 关键词 | 非必传 |
| caseMark | string | 工单标签 | 非必传 |
| accidentFlag | int | 是否突发事件 | 非必传 |
| instableFlag | int | 是否不稳定因素 | 非必传 |
| repeatCallFlag | int | 是否重复来电 | 非必传 |
| returnVisitFlag | int | 是否回访 | 非必传，默认0，不回访 |
| publicFlag | int | 是否允许对外公开 | 非必传，默认0，不对外公开 |
| rollbackFlag | Int | 是否允许回退 | 非必传，默认1，允许回退 |
| postponeFlag | Int | 是否允许延期 | 非必传，默认1，允许延期 |
| reHandleFlag | Int | 是否重办 | 非必传，默认0 |

### 请求样例

|  |
| --- |
| {      "uid": "oNbld0TohzzqNlWYZCjb5bevvIQ8",      "data": {          "caseId": "20240801002",          "disposeDeadlineTime": "2024-08-05 23:59:59"      },      "action": "UPDATE\_CASE\_INFO",      "senderCode": "zhwx"  } |

### 接口返回参数

|  |  |  |  |
| --- | --- | --- | --- |
| 参数名称 | 参数类型 | 参数说明 | 备注 |
| success | boolean | 接口是否成功返回标识 | true: 成功 false: 失败 |
| code | int | 错误编码 | 0:成功 -1: 失败 |
| message | string | 返回结果消息 |  |
| result | Json | 返回数据内容 |  |

### 返回样例

|  |
| --- |
| {      "success": true,      "code": 0,      "message": "更新对接信息:成功",      "result": {          "wfActList": [              {                  "actId": "44e624dd-18bf-b58e-ca70-b45e6c4cf620",                  "actDefId": "artificial\_4014f54e-f714-472f-9e15-f01e6f3a7b80",                  "actDefName": "区责任单位处置",                  "procDefId": "35059528ed4bf4449ef7e7",                  "procVersion": 10,                  "preActDef": "artificial\_385fe827-01de-46e4-9b3e-0aafaece4c44",                  "transItemTypeId": 610,                  "transItemTypeName": "transit",                  "actStateId": 11110,                  "actStateName": "正常移交",                  "actPropertyId": 7,                  "actPropertyName": null,                  "startTime": "2024-08-01 15:18:55",                  "endTime": null,                  "updateTime": "2024-08-01 15:18:55",                  "bizEntryId": 1251241,                  "procInstId": "0dbfdbfc-0d33-4dbb-ac14-47148d50ce6e",                  "partId": 14114,                  "partUid": "wizdom:10403",                  "partName": "水务局",                  "partType": "role",                  "humanId": 0,                  "humanUid": null,                  "humanName": null,                  "roleId": 14114,                  "roleUid": "wizdom:10403",                  "roleName": "水务局",                  "unitId": 37472,                  "unitUid": "wizdom:10401",                  "unitName": "区水务局",                  "menuSet": ",postpone,finish,cancel,suspend,transit\_end,untransit,rollback,transit,transit\_phase,apply\_rollback,apply\_transit,apply\_reset\_notify,apply\_stage\_archive,apply\_viewreporter,apply\_cancel,apply\_postpone,accredit,transit\_any,ForceCancelRedirect,",                  "priSubTypeId": 0,                  "engineTypeId": 2,                  "applyInfo": null,                  "parallelId": null,                  "initTaskId": "44e624dd-18bf-b58e-ca70-b45e6c4cf620",                  "ardTypeId": 0,                  "ardStateId": 0,                  "assignTime": null,                  "id": 51584              }          ],          "recId": 1251241,          "taskNum": "202408010002"      },      "uid": "oNbld0TohzzqNlWYZCjb5bevvIQ8",      "hasError": false  } |

## 上传工单多媒体

### 接口描述

外部系统可通过该接口上传工单的相关多媒体附件。

### 接口请求参数

|  |  |  |  |
| --- | --- | --- | --- |
| 请求路径：http://{ip}:{port}/v22-api/openapi/v1/action POST请求  星桥请求路径：[http://{ip}:{port}/星桥服务名称/api/exchange/eurbanpro/openapi/v1/uploadmedia](http://{ip}:{port}/%E6%98%9F%E6%A1%A5%E6%9C%8D%E5%8A%A1%E5%90%8D%E7%A7%B0/api/exchange/eurbanpro/openapi/v1/uploadmedia) POST请求 | | | |
| 参数名称 | 参数类型 | 参数说明 | 备注 |
| data | Object | 信息json对象 | 必传 |
| senderCode | string | 发送方标识，参见第三方平台编码 | 必传 |
| action | String | UPLOAD\_MEDIA | 必传 |
| uid | String | 请求唯一标识 | 必传，可以通过UUID.randomUUID().toString()获取 |
| data参数详情 | | | |
| 参数名称 | 参数类型 | 参数说明 | 备注 |
| medias | List | 多媒体列表 | 必传 |
| mediaName | String | 多媒体名称 | 必传 |
| mediaPath | String | 多媒体完整地址 | 二选一必传 |
| content | String | Base64内容 | 非必传，格式为“yyyy-MM-dd HH:mm:ss” |
| mediaUsage | String | 文件类型 | 必传，上报/核查/核实/处置/自处置 |
| mediaTypeId | Integer | 多媒体关联类型 | 必传，参见字典表接口，默认传1 |

### 请求样例

|  |
| --- |
| {      "uid": "oNbld0TohzzqNlWYZCjb5bevvIQ8",      "data": {          "caseId": "20240801002",          "medias": [              {                  "mediaName": "618cf8c4e1d9357541.jpg",                  "mediaPath": "https://pic.616pic.com/photoone/00/03/16/618cf8c4e1d935754.jpg",                  "mediaUsage": "处置",                  "mediaTypeId": 1              }          ]      },      "action": "UPLOAD\_MEDIA",      "senderCode": "zhwx"  } |

### 接口返回参数

|  |  |  |  |
| --- | --- | --- | --- |
| 参数名称 | 参数类型 | 参数说明 | 备注 |
| success | boolean | 接口是否成功返回标识 | true: 成功 false: 失败 |
| code | int | 错误编码 | 0:成功 -1: 失败 |
| message | string | 返回结果消息 |  |
| result | Json | 返回数据内容 |  |

### 返回样例

|  |
| --- |
| {      "success": true,      "code": 0,      "message": "附件上传成功",      "result": {},      "uid": "oNbld0TohzzqNlWYZCjb5bevvIQ8",      "hasError": false  } |

# 用户凭证接口详情

第三方直接调用接口需要认证，首先需要在统一用户中心进行注册，生成client\_id和client\_secret，然后调用接口获取公钥，对client\_secret进行加密(加密算法参见附件)，随后调用获取token接口获取client\_token。最后调用其他接口的时候可以采用以下两种方式（推荐使用第二种，Query参数里携带egova\_openapi\_token）。

![](data:image/png;base64...)

## 获取公钥接口

### 接口描述

返回公钥信息

### 接口请求参数

|  |  |  |  |
| --- | --- | --- | --- |
| 请求路径：http://{ip}:{port}/v22-api/oauth/extras/openapi/pubkey GET请求 | | | |
| 参数名称 | 参数类型 | 参数说明 | 备注 |

### 接口返回参数

|  |  |  |  |
| --- | --- | --- | --- |
| 参数名称 | 参数类型 | 参数说明 | 备注 |
| success | boolean | 接口是否成功返回标识 | true: 成功 false: 失败 |
| code | int | 错误编码 | 0:成功 -1: 失败 |
| message | string | 返回结果消息 | 公钥 |
| result | Json | 返回数据内容 |  |

### 返回样例

|  |
| --- |
| {      "success": true,      "code": 0,      "message": "04ffa798f0fb5c717e765c6dacf8cacb5002b3eefb3277eee1d6eb3ab8c0352e94337c9556204f5abc95ab4a18c4de5b1d3daad438095e27c7208de7f4dc946b63",      "result": {},      "uid": "data",      "hasError": false  } |

## 获取token接口

### 接口描述

返回公钥信息

### 接口请求参数

|  |  |  |  |
| --- | --- | --- | --- |
| 请求路径：http://{ip}:{port}/v22-api/oauth/extras/openapi/client Post请求 | | | |
| 参数名称 | 参数类型 | 参数说明 | 备注 |
| client\_id | String | 统一用户中心获取 | 必传 |
| client\_secret | String | 统一用户中心获取后加密 | 必传，SM2加密 详见7.1 |
| grant\_type | String | client\_credentials | 必传 |
| uid | String | 请求唯一标识 | 必传，可以通过UUID.randomUUID().toString()获取 |

### 接口返回参数

|  |  |  |  |
| --- | --- | --- | --- |
| 参数名称 | 参数类型 | 参数说明 | 备注 |
| success | boolean | 接口是否成功返回标识 | true: 成功 false: 失败 |
| code | int | 错误编码 | 0:成功 -1: 失败 |
| message | string | 返回结果消息 | 公钥 |
| result | Json | 返回数据内容 |  |
| result参数详情 | | | |
| token | Json | 返回数据内容 |  |
| token参数详情 | | | |
| access\_token | String | client\_token |  |
| token\_type | String |  |  |
| refresh\_token | String | 刷新token |  |
| expires\_in | Long | 剩余有效时间（秒） |  |
| scope | String | egova |  |

### 返回样例

|  |
| --- |
| {      "success": true,      "code": 0,      "message": null,      "result": {          "token": {              "access\_token": "2gDQDQld28-\_PVXtEFeOTtIMp2E",              "token\_type": "bearer",              "refresh\_token": "iiWU-34sGrVw24bZk8oeX22tp54",              "expires\_in": 24323,              "scope": "egova"          }      },      "uid": "836b6f0b-f83d-49e5-a4a1-7fc543d19402",      "hasError": false  } |

# 基础字典表接口详细

## 工单字典表接口

### 接口描述

工单字典表信息。

### 接口请求参数

|  |  |  |  |
| --- | --- | --- | --- |
| 请求路径： http://{ip}:{port}/v22-api/openapi/v1/dic GET请求 | | | |
| 参数名称 | 参数类型 | 参数说明 | 备注 |
| pageIndex | int | 当前页面，默认1 |  |
| pageSize | int | 分页每页显示的条数，默认10 |  |
| code | String | REC\_TYPE-事件类型  EVENT\_PROPERTY-问题性质  EVENT\_SRC-问题来源 |  |

### 请求样例

|  |
| --- |
| http://localhost:8082/v22-api/openapi/v1/dic?code=REC\_TYPE&pageIndex=1&pageSize =10&egova\_openapi\_token=CzlpEf179mmyOljK3PAFjhvxaLE |

### 接口返回参数

|  |  |  |  |
| --- | --- | --- | --- |
| 参数名称 | 参数类型 | 参数说明 | 备注 |
| success | boolean | 是否成功 |  |
| code | Integer | 响应状态 |  |
| message | String | 提示信息 |  |
| result | Object | 返回结果 |  |
| data | List | 字典项列表 |  |
| id | Integer | 字典项标识 |  |
| name | String | 字典项名 |  |
| pageInfo | Object | 分页信息 |  |

### 返回样例

|  |
| --- |
| {      "success": false,      "code": 0,      "message": null,      "result": {          "data": [              {                  "id": 3,                  "name": "民生诉求受理",                  "ROW\_ID": 1              },              {                  "id": 4,                  "name": "机动中队采集",                  "ROW\_ID": 2              },              {                  "id": 5,                  "name": "综合网格员采集",                  "ROW\_ID": 3              },              {                  "id": 6,                  "name": "专项行动",                  "ROW\_ID": 4              },              {                  "id": 7,                  "name": "市级城管上报",                  "ROW\_ID": 5              },              {                  "id": 8,                  "name": "物联感知",                  "ROW\_ID": 6              },              {                  "id": 9,                  "name": "领导批示",                  "ROW\_ID": 7              },              {                  "id": 10,                  "name": "区城管采集",                  "ROW\_ID": 8              },              {                  "id": 11,                  "name": "区信访登记",                  "ROW\_ID": 9              },              {                  "id": 12,                  "name": "一支队伍上报",                  "ROW\_ID": 10              }          ],          "pageInfo": {              "numPerPage": 10,              "currentPage": 1,              "totalPage": 3,              "totalRecord": 26,              "currentRecord": 10,              "enableCount": true          }      },      "hasError": true  } |

# 附录

## SM2加密算法

import org.bouncycastle.asn1.gm.GMNamedCurves;

import org.bouncycastle.asn1.x9.X9ECParameters;

import org.bouncycastle.crypto.engines.SM2Engine;

import org.bouncycastle.crypto.params.ECDomainParameters;

import org.bouncycastle.crypto.params.ECPublicKeyParameters;

import org.bouncycastle.crypto.params.ParametersWithRandom;

import org.bouncycastle.math.ec.ECPoint;

import org.bouncycastle.util.encoders.Hex;

import java.nio.charset.StandardCharsets;

import java.security.SecureRandom;

public class Sm2Utils {

public static String encrypt(String src, String hexPubKey) {

return Hex.toHexString(encrypt(src.getBytes(StandardCharsets.UTF\_8), hexPubKey));

}

private static byte[] encrypt(byte[] src, String hexPubKey) {

X9ECParameters pubParameters = GMNamedCurves.getByName("sm2p256v1");

ECDomainParameters pubDomainParameters = new ECDomainParameters(pubParameters.getCurve(),

pubParameters.getG(), pubParameters.getN());

ECPoint pubPoint = pubParameters.getCurve().decodePoint(Hex.decode(hexPubKey));

ECPublicKeyParameters encryptPubKey = new ECPublicKeyParameters(pubPoint, pubDomainParameters);

try {

SM2Engine sm2Engine = new SM2Engine(SM2Engine.Mode.C1C3C2);

ParametersWithRandom parametersWithRandom = new ParametersWithRandom(encryptPubKey,new SecureRandom());

sm2Engine.init(true, parametersWithRandom);

return sm2Engine.processBlock(src,0,src.length);

}catch (Exception e) {

throw new RuntimeException("");

}

}

}

## 通知名称字典

|  |  |
| --- | --- |
| 工单上报通知 | REPORT\_NOTICE |
| 工单办结通知 | FINISH\_NOTICE |
| 工单申请回退通知 | APPLY\_ROLLBACK\_NOTICE |
| 工单申请延期通知 | APPLY\_POSTPONE\_NOTICE |
| 工单申请结案通知 | APPLY\_ARCHIVE\_NOTICE |
| 工单申请作废通知 | APPLY\_CANCEL\_NOTICE |
| 工单处置反馈通知 | DISPOSE\_FEEDBACK\_NOTICE |
| 工单核查反馈通知 | CHECK\_FEEDBACK\_NOTICE |
| 工单作废通知 | CANCEL\_NOTICE |
| 工单差评申诉完成通知 | EVALUATE\_APPEAL\_NOTICE |
| 工单差评审批完成通知 | EVALUATE\_AUDIT\_NOTICE |
| 工单完成告知通知 | NOTIFY\_NOTICE |
| 工单签收通知 | NOTICE\_SIGNING |
| 工单答复延期通知 | REPLY\_POSTPONE\_NOTICE |
| 工单答复回退通知 | REPLY\_ROLLBACK\_NOTICE |
| 工单答复作废通知 | REPLY\_CANCEL\_NOTICE |
| 工单答复办结通知 | REPLY\_FINISH\_NOTICE |
| 工单新增办理经过通知 | ITEM\_INST\_SYNC\_NOTICE |

## 常见错误码

|  |  |  |
| --- | --- | --- |
| 错误码 | 错误码描述 | 自查措施 |
| -400001 | 认证错误 | 检查token是否携带，加密方式是否正常 |
| -400002 | 参数错误 | 检查请求体是否合法的JSON字符串，各字段类型是否合规。 |
| -400003 | 禁止操作 | 联系我方系统对接人员排查。 |
| -400004 | 未知操作 | 检查请求体中的action字段是否正确。 |
| -400005 | 客户端认证失败 | 检查token是否携带，加密方式是否正常。 |
| -400006 | 代理账号认证失败 | 联系我方系统对接人员排查。 |
| -500001 | 未知异常 | 联系我方系统对接人员排查。 |
| -500002 | 数据错误 | 联系我方系统对接人员排查。 |
| -500003 | 数据记录异常 | 联系我方系统对接人员排查。 |