#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""05_gen_artifacts.py — 实施交付物生成（SQL 四件套 / Linux 部署脚本 / 中间件配置）。

设计约束：
  - 纯标准库生成，不连数据库、不执行任何 SQL。产出的是**待人工评审后执行**的交付文件。
  - 所有表名/字段名/索引名先过 db_rules.json 命名闸门，任一 P0 违规直接 GapError 停止，
    不生成「看着对但会被 DBA 打回」的脚本。
  - 升级脚本必须自带回滚脚本；缺一不成套（fail fast，不产出半套）。
  - 只写 --outdir，不联网、不执行系统命令。

输入模型（--model <模型.json>）字段说明见 docstring 末尾或 references/model_sample.json。

用法:
  python 05_gen_artifacts.py --model <模型.json> --outdir <输出目录> \
      [--only sql deploy middleware] [--validate-only] [--rules db_rules.json]
"""
import argparse
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from daa_common import (  # noqa: E402
    GapError, emit, envelope, exit_gap, load_json, safe_path, setup_io, skill_root,
    today_str, write_text,
)

PKGS = ("sql", "deploy", "middleware")


# ------------------------------------------------------------------ 命名闸门
class NameGate:
    """按 db_rules.json 校验表/列/索引命名。任一 P0 违规即阻断。"""

    def __init__(self, rules):
        t = rules["table"]
        self.max_tbl = int(t.get("max_length") or 48)
        self.max_col = int(rules["column"].get("max_length") or 32)
        self.allowed_prefix = tuple(t.get("allowed_prefixes") or ())
        self.deprecated_prefix = tuple(t.get("deprecated_prefixes") or ())
        self.lv = rules.get("naming_violation_levels") or {}
        self.reserved = set((rules.get("mysql_reserved_words") or "").split())
        self.soft = set((rules.get("soft_keywords") or "").split())
        self.abbrev = set((rules.get("abbreviation_whitelist") or "").split())
        self.uk = rules.get("index", {}).get("unique_prefix", "uk_")
        self.idx = rules.get("index", {}).get("normal_prefix", "idx_")

    def _p0(self, kind):
        return self.lv.get(kind, "P2")

    def check_table(self, name):
        probs = []
        if len(name) > self.max_tbl:
            probs.append(("too_long", "表名 %d 字符 > %d" % (len(name), self.max_tbl)))
        # 允许前缀优先：t_biz_ 命中时不能再被废弃前缀 t_ 判死
        hit_allowed = next((p for p in self.allowed_prefix if name.startswith(p)), None)
        if not hit_allowed:
            hit_bad = next((p for p in self.deprecated_prefix if name.startswith(p)), None)
            if hit_bad:
                probs.append(("deprecated_prefix", "使用了废弃前缀 %s" % hit_bad))
            probs.append(("semantic_not_matched",
                          "表名不以约定前缀开头（允许：%s）"
                          % "/".join(self.allowed_prefix)))
        if re.search(r"[A-Z]", name):
            probs.append(("camel_or_upper", "表名含大写字母，应为 snake_case"))
        if name.startswith("_") or name.endswith("_") or "__" in name:
            probs.append(("leading_or_trailing_underscore" if "__" not in name
                          else "double_underscore", "表名含异常下划线"))
        if name[:1].isdigit():
            probs.append(("digit_first", "表名不能以数字开头"))
        if name in self.reserved:
            probs.append(("mysql_reserved_word", "表名命中 MySQL 保留字"))
        return probs

    def check_column(self, name):
        probs = []
        if len(name) > self.max_col:
            probs.append(("too_long", "字段名 %d 字符 > %d" % (len(name), self.max_col)))
        if re.search(r"[A-Z]", name):
            probs.append(("camel_or_upper", "字段名含大写字母，应为 snake_case"))
        if name.startswith("_") or name.endswith("_") or "__" in name:
            probs.append(("leading_or_trailing_underscore" if "__" not in name
                          else "double_underscore", "字段名含异常下划线"))
        if name[:1].isdigit():
            probs.append(("digit_first", "字段名不能以数字开头"))
        if name in self.reserved:
            probs.append(("mysql_reserved_word", "字段名命中 MySQL 保留字，需加反引号或改名"))
        elif name in self.soft:
            probs.append(("soft_keyword", "字段名使用了通用词 %s，建议加业务前缀" % name))
        return probs

    def check_index(self, name, unique):
        probs = []
        want = self.uk if unique else self.idx
        if not name.startswith(want):
            probs.append(("semantic_not_matched",
                          "索引名应以 %s 开头（实际 %s）" % (want, name)))
        if len(name) > self.max_col + 6:
            probs.append(("too_long", "索引名过长（%d 字符）" % len(name)))
        if re.search(r"[A-Z]", name):
            probs.append(("camel_or_upper", "索引名含大写字母"))
        return probs


# ------------------------------------------------------------------ SQL 生成
def _q(ident):
    return "`%s`" % ident


def gen_create_table(tbl, rules):
    t = rules["table"]
    c = rules["column"]
    name = tbl["name"]
    lines = ["CREATE TABLE IF NOT EXISTS %s (" % _q(name)]
    body = ["  %s bigint(20) unsigned NOT NULL AUTO_INCREMENT COMMENT '主键ID'" % _q("id")]
    # 索引去重：同一列只保留最合适的一个。
    #  - unique=true 的列：唯一约束走命名唯一索引 uk_xxx，不再写列内 UNIQUE；
    #  - 另有 indexes[] 显式声明该列时，以显式声明为准。
    declared = {}
    for idx in tbl.get("indexes") or []:
        for cn in idx.get("columns") or []:
            declared.setdefault(cn, []).append(idx)
    inline_unique = []
    for col in tbl.get("columns", []):
        cn = col["name"]
        seg = "  %s %s" % (_q(cn), col.get("type") or "varchar(64)")
        seg += " NOT NULL" if col.get("null") is False else " NULL"
        if col.get("default") is not None:
            seg += " DEFAULT %s" % col["default"]
        seg += " COMMENT '%s'" % str(col.get("comment") or cn).replace("'", "''")
        if col.get("unique") and cn not in declared:
            seg += " UNIQUE"
            inline_unique.append(cn)
        body.append(seg)
    for col in c.get("audit_columns", []):
        seg = "  %s %s" % (_q(col["name"]), col.get("type"))
        seg += " NOT NULL" if col.get("null") is False else " NULL"
        if col.get("default") is not None:
            seg += " DEFAULT %s" % col["default"]
        seg += " COMMENT '%s'" % col.get("comment", col["name"])
        body.append(seg)
    sd = c.get("soft_delete")
    if sd:
        body.append("  %s %s NOT NULL DEFAULT %s COMMENT '%s'"
                    % (_q(sd["name"]), sd["type"], sd.get("default", "0"),
                       sd.get("comment", "删除标记")))
    body.append("  PRIMARY KEY (%s)" % _q("id"))
    for col in tbl.get("columns", []):
        cn = col["name"]
        if col.get("index") and cn not in declared and cn not in inline_unique:
            body.append("  KEY %s (%s)" % (_q("idx_%s" % cn), _q(cn)))
    for idx in tbl.get("indexes", []):
        cols = ", ".join(_q(x) for x in idx.get("columns", []))
        if not cols:
            continue
        kw = "UNIQUE KEY" if idx.get("unique") else "KEY"
        body.append("  %s %s (%s)" % (kw, _q(idx["name"]), cols))
    lines.append(",\n".join(body))
    lines.append(") ENGINE=%s DEFAULT CHARSET=%s COLLATE=%s COMMENT='%s';"
                 % (t.get("default_engine", "InnoDB"),
                    t.get("default_charset", "utf8mb4"),
                    t.get("default_collate", "utf8mb4_general_ci"),
                    str(tbl.get("comment") or name).replace("'", "''")))
    return "\n".join(lines)


def gen_sql_package(model, rules):
    """返回 {相对路径: 内容}：建表 / 初始化数据 / 升级 / 回滚 四件套。"""
    db = model.get("db_name") or model.get("project") or "app_db"
    ver = model.get("changelog_version") or "v1.0.0"
    tables = model.get("tables") or []
    if not tables:
        raise GapError("模型中 tables 为空，拒绝生成空 SQL 包")
    out = {}

    head = ("-- ===========================================================\n"
            "-- 项目：%s\n-- 数据库：%s\n-- 版本：%s\n"
            "-- 生成时间：%s\n"
            "-- 说明：由 delivery-acceptance-assistant 按工程中心现行数据库设计约定生成，\n"
            "--       执行前请经 DBA / 架构评审。\n"
            "-- ===========================================================\n"
            % (model.get("project", ""), db, ver, today_str()))
    creates = [head, "USE `%s`;\n" % db]
    for tbl in tables:
        creates.append("\n-- %s" % tbl.get("comment", tbl["name"]))
        creates.append(gen_create_table(tbl, rules))
    out["sql/01_create_%s.sql" % ver] = "\n".join(creates) + "\n"

    seeds = []
    for tbl in tables:
        rows = tbl.get("seed") or []
        if not rows:
            continue
        keys = sorted({k for r in rows for k in r})
        seeds.append("INSERT INTO %s (%s) VALUES"
                     % (_q(tbl["name"]), ", ".join(_q(k) for k in keys)))
        for i, r in enumerate(rows):
            vals = ", ".join("'%s'" % str(r.get(k, "")).replace("'", "''") for k in keys)
            seeds.append("  (%s)%s" % (vals, ";" if i == len(rows) - 1 else ","))
    if seeds:
        out["sql/02_init_data_%s.sql" % ver] = (
            head + "USE `%s`;\n\n" % db + "\n".join(seeds) + "\n")
    else:
        out["sql/02_init_data_%s.sql" % ver] = head + "-- 本版本无初始化数据。\n"

    up = model.get("upgrade") or {}
    ups = up.get("statements") or []
    if ups:
        frm = up.get("from_version") or "上一版本"
        out["sql/03_upgrade_%s_from_%s.sql" % (ver, frm.replace(".", ""))] = (
            head + "-- 升级自：%s\nUSE `%s`;\n\n" % (frm, db)
            + "\n".join(s.rstrip().rstrip(";") + ";" for s in ups) + "\n")
    else:
        out["sql/03_upgrade_%s.sql" % ver] = head + "-- 本版本无库表结构变更。\n"

    downs = up.get("rollback") or []
    if ups and not downs:
        raise GapError("模型提供了 upgrade.statements 但未提供 upgrade.rollback，"
                       "升级/回滚必须成对，拒绝产出半套 SQL")
    if downs:
        frm = up.get("from_version") or "上一版本"
        out["sql/04_rollback_%s_to_%s.sql" % (ver, frm.replace(".", ""))] = (
            head + "-- 回滚 %s → %s\nUSE `%s`;\n\n" % (ver, frm, db)
            + "\n".join(s.rstrip().rstrip(";") + ";" for s in downs) + "\n")
    elif ups:
        out["sql/04_rollback_%s.sql" % ver] = (
            head + "-- 警告：未提供回滚语句，本脚本不可用于生产回退。\n")
    else:
        out["sql/04_rollback_%s.sql" % ver] = head + "-- 本版本无结构变更，无需回滚。\n"
    return out


# ------------------------------------------------------------------ 部署脚本
def gen_deploy_package(model):
    d = model.get("deploy") or {}
    app = d.get("app_name") or "app"
    jar = d.get("package") or "%s.jar" % app
    port = int(d.get("port") or 8080)
    user = d.get("service_user") or app
    home = d.get("deploy_dir") or "/opt/%s" % app
    logs = d.get("log_dir") or "%s/logs" % home
    java = d.get("java_home") or "/usr/lib/jvm/java-8-openjdk"
    out = {}

    out["deploy/deploy.sh"] = _deploy_sh(app, jar, port, home, logs, java)
    out["deploy/rollback.sh"] = _rollback_sh(app, jar, port, home, logs, java)
    out["deploy/stop.sh"] = """#!/bin/bash
# 停止 {app}
set -euo pipefail
APP_HOME={home}
PID_FILE="$APP_HOME/app.pid"
if [ ! -f "$PID_FILE" ]; then
  echo "未找到 PID 文件，进程可能未启动"
  exit 0
fi
PID=$(cat "$PID_FILE")
if kill -0 "$PID" 2>/dev/null; then
  echo "停止进程 $PID ..."
  kill "$PID"
  for i in $(seq 1 30); do
    kill -0 "$PID" 2>/dev/null || {{ echo "已停止"; rm -f "$PID_FILE"; exit 0; }}
    sleep 1
  done
  echo "优雅停止超时，强制结束"
  kill -9 "$PID" || true
  rm -f "$PID_FILE"
else
  echo "进程 $PID 不存在，清理 PID 文件"
  rm -f "$PID_FILE"
fi
""".format(app=app, home=home)

    out["deploy/health_check.sh"] = """#!/bin/bash
# {app} 健康检查
set -euo pipefail
PORT={port}
URL="http://127.0.0.1:${{PORT}}/actuator/health"
for i in $(seq 1 10); do
  CODE=$(curl -s -o /dev/null -w '%{{http_code}}' "$URL" || true)
  if [ "$CODE" = "200" ]; then
    echo "健康检查通过"
    exit 0
  fi
  echo "第 $i 次检查返回 ${{CODE:-无响应}}，3 秒后重试"
  sleep 3
done
echo "健康检查失败"
exit 1
""".format(app=app, port=port)

    out["deploy/install_service.sh"] = _service_sh(app, user, home, logs, java)
    out["deploy/README.md"] = _deploy_readme(app, jar, port, user, home, logs, java)
    return out


def _deploy_sh(app, jar, port, home, logs, java):
    return """#!/bin/bash
# ===========================================================
# {app} 部署脚本
# 用法： sudo bash deploy.sh <包文件路径>
# ===========================================================
set -euo pipefail

APP_NAME="{app}"
JAR_NAME="{jar}"
PORT={port}
APP_HOME={home}
LOG_DIR={logs}
JAVA_HOME={java}
JAVA_BIN="$JAVA_HOME/bin/java"
JAR_PATH="$APP_HOME/app.jar"
BACKUP_DIR="$APP_HOME/backup"
STAMP=$(date +%Y%m%d%H%M%S)

PKG="${{1:-}}"
if [ -z "$PKG" ] || [ ! -f "$PKG" ]; then
  echo "用法：bash deploy.sh <包文件路径>"; exit 1
fi
if [ ! -x "$JAVA_BIN" ]; then
  echo "未找到 Java：$JAVA_BIN，请检查 deploy.java_home"; exit 1
fi

mkdir -p "$APP_HOME" "$LOG_DIR" "$BACKUP_DIR"

echo "[1/5] 停止旧进程"
bash "$(dirname "$0")/stop.sh" || true

echo "[2/5] 备份当前版本"
if [ -f "$JAR_PATH" ]; then
  cp -p "$JAR_PATH" "$BACKUP_DIR/${{JAR_NAME}}.${{STAMP}}"
  echo "已备份到 $BACKUP_DIR/${{JAR_NAME}}.${{STAMP}}"
fi

echo "[3/5] 释放新版本"
cp -f "$PKG" "$JAR_PATH"
chmod 644 "$JAR_PATH"

echo "[4/5] 启动"
cd "$APP_HOME"
nohup "$JAVA_BIN" -server \\
  -Dfile.encoding=UTF-8 \\
  -Dspring.profiles.active=prod \\
  -Dserver.port=${{PORT}} \\
  -jar "$JAR_PATH" > "$LOG_DIR/stdout.log" 2>&1 &
echo $! > "$APP_HOME/app.pid"
echo "PID $(cat "$APP_HOME/app.pid")"

echo "[5/5] 健康检查"
if bash "$(dirname "$0")/health_check.sh"; then
  echo "部署成功"
  exit 0
fi
echo "健康检查未通过，请查看 $LOG_DIR/ 下日志；可执行 rollback.sh $STAMP 回退"
exit 1
""".format(app=app, jar=jar, port=port, home=home, logs=logs, java=java)


def _rollback_sh(app, jar, port, home, logs, java):
    return """#!/bin/bash
# ===========================================================
# {app} 回滚脚本
# 用法： sudo bash rollback.sh [备份时间戳]；不带参数时自动选用最新备份
# ===========================================================
set -euo pipefail

APP_NAME="{app}"
JAR_NAME="{jar}"
APP_HOME={home}
LOG_DIR={logs}
JAVA_HOME={java}
BACKUP_DIR="$APP_HOME/backup"
JAR_PATH="$APP_HOME/app.jar"

[ -d "$BACKUP_DIR" ] || {{ echo "备份目录不存在：$BACKUP_DIR"; exit 1; }}

if [ -n "${{1:-}}" ]; then
  TARGET="$BACKUP_DIR/${{JAR_NAME}}.$1"
else
  TARGET=$(ls -1t "$BACKUP_DIR/${{JAR_NAME}}."* 2>/dev/null | head -1 || true)
fi
[ -n "$TARGET" ] && [ -f "$TARGET" ] || {{ echo "未找到可回退的备份"; exit 1; }}
echo "将回滚到：$TARGET"

bash "$(dirname "$0")/stop.sh" || true
cp -f "$TARGET" "$JAR_PATH"
cd "$APP_HOME"
nohup "$JAVA_HOME/bin/java" -server -Dfile.encoding=UTF-8 \\
  -Dspring.profiles.active=prod -Dserver.port={port} \\
  -jar "$JAR_PATH" > "$LOG_DIR/stdout.log" 2>&1 &
echo $! > "$APP_HOME/app.pid"
echo "回滚完成，PID $(cat "$APP_HOME/app.pid")"
""".format(app=app, jar=jar, port=port, home=home, logs=logs, java=java)


def _service_sh(app, user, home, logs, java):
    return """#!/bin/bash
# 注册 systemd 服务（{app}）
# 用法： sudo bash install_service.sh
set -euo pipefail

APP_NAME="{app}"
APP_HOME={home}
LOG_DIR={logs}
JAVA_HOME={java}
SERVICE_FILE=/etc/systemd/system/${{APP_NAME}}.service

cat > "$SERVICE_FILE" <<EOF
[Unit]
Description=${{APP_NAME}} service
After=network.target

[Service]
Type=simple
User=${{APP_USER:-{user}}}
WorkingDirectory=${{APP_HOME}}
Environment="JAVA_HOME=${{JAVA_HOME}}"
ExecStart=${{JAVA_HOME}}/bin/java -server \\
  -Dfile.encoding=UTF-8 \\
  -Dspring.profiles.active=prod \\
  -jar ${{APP_HOME}}/app.jar
SuccessExitStatus=143
Restart=on-failure
RestartSec=10
StandardOutput=append:${{LOG_DIR}}/service.log
StandardError=append:${{LOG_DIR}}/error.log

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable ${{APP_NAME}}
systemctl restart ${{APP_NAME}}
systemctl status ${{APP_NAME}} --no-pager
echo "已注册并启动服务：${{APP_NAME}}"
""".format(app=app, user=user, home=home, logs=logs, java=java)


def _deploy_readme(app, jar, port, user, home, logs, java):
    return """# {app} 部署说明

## 环境

| 项 | 值 |
| --- | --- |
| 应用名 | {app} |
| 包文件 | {jar} |
| 端口 | {port} |
| 安装目录 | {home} |
| 日志目录 | {logs} |
| JAVA_HOME | {java} |
| 运行用户 | {user} |

## 首次部署

```bash
sudo useradd -r -s /sbin/nologin {user} 2>/dev/null || true
sudo mkdir -p {home} {logs}
sudo chown -R {user} {home}
sudo bash install_service.sh
```

## 常规发布

```bash
sudo bash deploy.sh /path/to/{jar}
```

脚本会依次：停旧进程 → 备份当前 jar → 释放新版本 → 启动 → 健康检查。
健康检查 30 秒未通过时不会自动回退，需人工确认后执行 `rollback.sh`。

## 回滚

```bash
sudo bash rollback.sh                 # 回滚到最新备份
sudo bash rollback.sh 20260925120000  # 回滚到指定时间戳
```

## 常用运维命令

```bash
sudo systemctl status {app}
sudo systemctl restart {app}
tail -f {logs}/stdout.log
tail -f {logs}/error.log
```
""".format(app=app, jar=jar, port=port, user=user, home=home, logs=logs, java=java)


# ------------------------------------------------------------------ 中间件配置
def gen_middleware_package(model):
    mw = model.get("middleware") or {}
    if not mw:
        raise GapError("模型中 middleware 为空，拒绝生成空配置")
    app = model.get("project") or "app"
    out = {}

    if "app" in mw:
        a = mw["app"]
        out["middleware/application-%s.yml" % app] = (
            "# %s 应用配置（由 delivery-acceptance-assistant 生成）\n"
            "server:\n"
            "  port: %s\n"
            "  tomcat:\n"
            "    max-threads: 200\n"
            "    min-spare-threads: 20\n"
            "spring:\n"
            "  datasource:\n"
            "    hikari:\n"
            "      maximum-pool-size: %s\n"
            "      minimum-idle: 5\n"
            "      connection-timeout: 30000\n"
            "      idle-timeout: 600000\n"
            "      max-lifetime: 1800000\n"
            "  redis:\n"
            "    host: 127.0.0.1\n"
            "    port: 6379\n"
            "    database: 0\n"
            "    timeout: 3000ms\n"
            "logging:\n"
            "  level:\n"
            "    root: INFO\n"
            % (app, a.get("port", 8080), a.get("max_pool", 20)))
        if a.get("jvm"):
            out["middleware/jvm-%s.env" % app] = (
                "# 追加到 deploy.sh 的 JAVA_OPTS 或 systemd ExecStart\n"
                "JAVA_OPTS=%s\n" % a["jvm"])

    if "redis" in mw:
        r = mw["redis"]
        out["middleware/redis-%s.conf" % app] = (
            "# Redis 配置片段：合并到 redis.conf 末尾或以 include 方式引入\n"
            "port %s\n"
            "maxmemory %s\n"
            "maxmemory-policy allkeys-lru\n"
            "appendonly yes\n"
            "requirepass %s\n"
            "timeout 0\n"
            "tcp-keepalive 300\n"
            % (r.get("port", 6379), r.get("maxmemory", "2gb"),
               r.get("requirepass", "CHANGE_ME")))

    if "mysql" in mw:
        m = mw["mysql"]
        out["middleware/my-%s.cnf" % app] = (
            "# MySQL 配置片段：写入 /etc/my.cnf.d/ 下\n"
            "[mysqld]\n"
            "port = %s\n"
            "character-set-server = %s\n"
            "collation-server = utf8mb4_general_ci\n"
            "max_connections = %s\n"
            "max_allowed_packet = 64M\n"
            "innodb_buffer_pool_size = 4G\n"
            "innodb_file_per_table = 1\n"
            "innodb_flush_log_at_trx_commit = 1\n"
            "slow_query_log = 1\n"
            "long_query_time = 1\n"
            "[client]\n"
            "default-character-set = %s\n"
            % (m.get("port", 3306), m.get("charset", "utf8mb4"),
               m.get("max_connections", 500), m.get("charset", "utf8mb4")))

    if "nginx" in mw:
        n = mw["nginx"]
        out["middleware/nginx-%s.conf" % app] = (
            "# Nginx 配置片段：include 到 nginx.conf 的 http {{}} 中\n"
            "upstream {up} {{\n"
            "    server 127.0.0.1:{port};\n"
            "    keepalive 32;\n"
            "}}\n\n"
            "server {{\n"
            "    listen 80;\n"
            "    server_name {server_name};\n"
            "    root {root};\n"
            "    client_max_body_size 50m;\n"
            "    charset utf-8;\n\n"
            "    location / {{\n"
            "        proxy_pass http://{up};\n"
            "        proxy_set_header Host $host;\n"
            "        proxy_set_header X-Real-IP $remote_addr;\n"
            "        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;\n"
            "        proxy_set_header X-Forwarded-Proto $scheme;\n"
            "        proxy_read_timeout 60s;\n"
            "    }}\n\n"
            "    location /static/ {{\n"
            "        expires 7d;\n"
            "        access_log off;\n"
            "    }}\n"
            "}}\n"
            .format(up=n.get("upstream", "app_upstream"),
                    port=n.get("upstream_port", 8080),
                    server_name=n.get("server_name", "example.com"),
                    root=n.get("root", "/opt/app/web")))

    out["middleware/README.md"] = (
        "# %s 中间件配置说明\n\n"
        "本目录为**配置片段**，不是可直接覆盖的完整配置文件。\n"
        "合并前请确认与目标环境已有配置不冲突。\n\n"
        "## 合并后必做\n\n"
        "```bash\n"
        "redis-cli -a <password> CONFIG GET requirepass   # 确认已改掉 CHANGE_ME\n"
        "mysql -e 'SHOW VARIABLES LIKE \"max_connections\";'\n"
        "nginx -t && systemctl reload nginx\n"
        "```\n" % app)
    return out


# ------------------------------------------------------------------ 主流程
def main():
    setup_io()
    ap = argparse.ArgumentParser(description="实施交付物生成（SQL四件套/部署脚本/中间件配置）")
    ap.add_argument("--model", required=True, help="数据模型 JSON")
    ap.add_argument("--rules", default=None, help="数据库命名规则 JSON，默认取 skill 内置")
    ap.add_argument("--outdir", required=True)
    ap.add_argument("--only", nargs="*", default=None, choices=PKGS,
                    help="只生成指定类别，默认全部")
    ap.add_argument("--validate-only", action="store_true",
                    help="只跑命名校验，不落盘")
    a = ap.parse_args()
    outdir = safe_path(a.outdir)

    try:
        model = load_json(a.model)
        if not isinstance(model, dict) or not model:
            raise GapError("模型必须是非空 JSON 对象")
        rules = load_json(a.rules, required=False) if a.rules else None
        if rules is None:
            rules = load_json(os.path.join(skill_root(), "config", "db_rules.json"))
        for k in ("table", "column", "index"):
            if k not in rules:
                raise GapError("数据库规则缺少 %s 段" % k)
    except GapError as e:
        return exit_gap("gen_artifacts", str(e))

    # ---- 命名闸门：P0 违规立即停止
    gate = NameGate(rules)
    all_probs = []
    for tbl in model.get("tables") or []:
        tname = tbl.get("name") or ""
        if not tname:
            all_probs.append({"scope": "table", "name": "", "level": "P0",
                              "kind": "missing_name", "msg": "表缺少 name"})
            continue
        for kind, msg in gate.check_table(tname):
            all_probs.append({"scope": "table", "name": tname,
                              "level": gate._p0(kind), "kind": kind, "msg": msg})
        cnames = set()
        for col in tbl.get("columns") or []:
            cn = col.get("name") or ""
            if not cn:
                all_probs.append({"scope": "column", "table": tname, "name": "",
                                  "level": "P0", "kind": "missing_name",
                                  "msg": "表 %s 有字段缺少 name" % tname})
                continue
            cnames.add(cn)
            for kind, msg in gate.check_column(cn):
                all_probs.append({"scope": "column", "table": tname, "name": cn,
                                  "level": gate._p0(kind), "kind": kind, "msg": msg})
        for idx in tbl.get("indexes") or []:
            iname = idx.get("name") or ""
            if not iname:
                all_probs.append({"scope": "index", "table": tname, "name": "",
                                  "level": "P0", "kind": "missing_name",
                                  "msg": "表 %s 有索引缺少 name" % tname})
                continue
            for kind, msg in gate.check_index(iname, bool(idx.get("unique"))):
                all_probs.append({"scope": "index", "table": tname, "name": iname,
                                  "level": gate._p0(kind), "kind": kind, "msg": msg})
            for c in idx.get("columns") or []:
                if c not in cnames:
                    all_probs.append({"scope": "index", "table": tname, "name": iname,
                                      "level": "P0", "kind": "semantic_not_matched",
                                      "msg": "索引引用了不存在的字段 %s" % c})

    p0 = [p for p in all_probs if str(p["level"]).startswith("P0")]
    if p0:
        return exit_gap("gen_artifacts",
                        "命名校验未通过（%d 项 P0），已停止生成：\n  - %s"
                        % (len(p0), "\n  - ".join(
                            "[%s] %s %s" % (x["level"], x.get("name", ""), x["msg"])
                            for x in p0[:20])),
                        naming_problems=all_probs)

    if a.validate_only:
        emit(envelope("gen_artifacts", True, validated=True,
                      tables=len(model.get("tables") or []),
                      problems=all_probs, p0=0, generated=0))
        return 0

    only = a.only or list(PKGS)
    written, failed = [], []
    builders = {"sql": lambda m: gen_sql_package(m, rules),
                "deploy": gen_deploy_package,
                "middleware": gen_middleware_package}
    for pkg in only:
        try:
            files = builders[pkg](model)
            for rel, content in sorted(files.items()):
                rel_parts = rel.split("/")
                write_text(outdir, "/".join(rel_parts), content)
                written.append(rel)
        except GapError as e:
            failed.append({"package": pkg, "error": str(e)})

    kw = {"outdir": outdir, "generated": len(written), "files": written,
          "failed": failed, "naming_problems": all_probs,
          "note": "产物为待评审文本，未连接数据库、未执行任何命令"}
    if failed:
        kw["gap"] = "；".join(f.get("error", "") for f in failed)
    emit(envelope("gen_artifacts", not failed, **kw))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
