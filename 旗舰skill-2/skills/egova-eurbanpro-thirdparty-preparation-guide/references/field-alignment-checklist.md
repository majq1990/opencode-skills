# 字段对齐清单

## 适用信号
- 第三方准备开始上报案件。
- 现场虽然能调通接口，但案件无法流转或字段含义混乱。

## 上报前必须对齐的字段
### 基础业务字段
- `eventSrcId` / `eventSrcName`：案件来源
- `recTypeId` / `recTypeName`：案件类型
- `eventTypeId` / `mainTypeId` / `subTypeId`：大小类
- `address`：详细地址
- `caseId`：第三方侧唯一案件标识

### 现场依赖字段
- `districtId` / `districtName`
- `streetId` / `streetName`
- `communityId` / `communityName`

这些字段在标准文档里不一定都是强必填，但如果现场工作流依赖它们，缺失就会导致：
- 无法流转
- 未找到合适处理人
- 节点匹配失败

### 附件字段
- `medias`：上报时通常必须传
- `mediaName`
- `mediaUsage`
- `mediaTypeId`
- `mediaPath` 或 `content` 二选一

## 结论
字段对齐不是只看接口参数表，还要结合现场流程配置判断哪些“非必填字段”实际上是联调必填项。
