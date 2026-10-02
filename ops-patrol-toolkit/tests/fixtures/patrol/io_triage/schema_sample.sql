-- 说明：本文件为「合成测试样例」（fixtures），仅用于验证 02_mysql_io_triage 的 DDL 解析链路。
-- 表名/字段名均为虚构，不含任何真实业务库结构或数据。
-- 覆盖点：大字段（text/mediumtext/longtext）、大 varchar、有主键、无主键、索引偏少。

CREATE TABLE `biz_event_log` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `event_time` datetime DEFAULT NULL COMMENT '事件时间',
  `operator_name` varchar(64) DEFAULT NULL,
  `account_id` bigint(20) DEFAULT NULL,
  `event_type` varchar(32) DEFAULT NULL,
  `region_code` varchar(32) DEFAULT NULL,
  `status` tinyint(4) DEFAULT '0',
  `detail` text COMMENT '事件明细，大字段',
  `ext_data` mediumtext COMMENT '扩展数据，大字段',
  `remark` varchar(256) DEFAULT NULL,
  `create_time` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 ROW_FORMAT=DYNAMIC;

CREATE TABLE `sys_account` (
  `id` bigint(20) NOT NULL,
  `account_name` varchar(64) DEFAULT NULL,
  `dept_id` bigint(20) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 ROW_FORMAT=DYNAMIC;

CREATE TABLE `biz_event_attach` (
  `id` bigint(20) NOT NULL,
  `event_id` bigint(20) DEFAULT NULL,
  `payload` longtext COMMENT '附件原文，大字段'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 ROW_FORMAT=DYNAMIC;
