# 公钥接口 404 排查

这个问题属于**故障排查**场景，不在本 skill 的处理范围内。

本 skill（egova-eurbanpro-thirdparty-api-reference）只负责 API 文档检索与示例生成，**不承担故障归因与排查**。

## 可以告诉你的 API 信息

公钥接口的路径是 `/oauth/extras/openapi/pubkey`，请求方式为 GET。如果你在调这个地址时返回 404，可以先用以下信息做初步确认：

- 接口路径是否拼写正确：`/oauth/extras/openapi/pubkey`
- 是否多拼或少拼了路径前缀（如 `/api/`、`/v2/` 等）
- 网络层是否能 ping 通目标服务器

## 建议下一步

请切换到 **troubleshooting** 技能（`egova-eurbanpro-thirdparty-troubleshooting`），它可以提供：

1. 404 问题的默认前置核查清单（网络、地址、网关等）
2. 公钥/token 相关的定向诊断步骤
3. 关键配置表与 SQL 验证方法
