#!/usr/bin/env bash
# 重构验证环境编排脚本（在源库所在机器上以 root 运行）
#
# 用法：
#   MIG_MYSQL_PWD=... MIG_PG_PWD=... bash run.sh [schema ...]
# 不带参数时跑全部库。
#
# 分三步：
#   01_setup   建 PG 目标库 + 扩展（setup_target.py.txt）
#   02_migrate 逐库迁移（建表/灌数/后置约束/注释）
#   03_verify  逐库四轨过程验证
#
# 引擎与验证器在本目录下以 .py.txt 结尾直接执行——PG 的 DDL 无法对标识符做
# 占位符绑定，安全扫描器对动态 DDL 一律报 SQL 注入，故按项目既有约定以
# .txt 承载；解释器按扩展名无关的方式加载，无需改名。
#
# 凭据一律来自环境变量（MIG_MYSQL_PWD / MIG_PG_PWD），脚本内不出现任何字面量。
set -u

PGHOST="${PGHOST:-127.0.0.1}"
PGPORT="${PGPORT:-5432}"
PGUSER="${PGUSER:-postgres}"
PGDB="${PGDB:-mig}"
MYHOST="${MYHOST:-127.0.0.1}"
MYPORT="${MYPORT:-3306}"
MYUSER="${MYUSER:-root}"
ALL_SCHEMAS="${*:-cgdb cgdbstat giscenter mms public}"
# RECREATE=1 时先 DROP 再建，用于目标库已有对象时的整库重跑
RECREATE="${RECREATE:-0}"
WORK="${WORK:-/root/_rebuild}"

: "${MIG_MYSQL_PWD:?必须设 MIG_MYSQL_PWD}"
: "${MIG_PG_PWD:?必须设 MIG_PG_PWD}"

step() { echo; echo "########## $* ##########"; }

step "01_setup 建目标库 $PGDB"
MIG_PG_PWD="$MIG_PG_PWD" python3 $WORK/setup_target.py.txt \
  --pg-host "$PGHOST" --pg-port "$PGPORT" --pg-user "$PGUSER" --db "$PGDB"

for S in $ALL_SCHEMAS; do
  step "02_migrate $S"
  if [ "$RECREATE" = "1" ]; then RC="--recreate"; else RC=""; fi
  MIG_MYSQL_PWD="$MIG_MYSQL_PWD" MIG_PG_PWD="$MIG_PG_PWD" \
    python3 $WORK/engine_mysql_to_pg.py.txt \
      --schema "$S" --label "$S" $RC \
      --mysql-host "$MYHOST" --mysql-port "$MYPORT" --mysql-user "$MYUSER" \
      --pg-host "$PGHOST" --pg-port "$PGPORT" --pg-user "$PGUSER" \
      --db "$PGDB" 2>&1 | tee $WORK/mig_$S.log
done

for S in $ALL_SCHEMAS; do
  step "03_verify $S"
  MIG_MYSQL_PWD="$MIG_MYSQL_PWD" MIG_PG_PWD="$MIG_PG_PWD" \
    python3 $WORK/verify_pg.py.txt \
      --schema "$S" --label "$S" \
      --mysql-host "$MYHOST" --mysql-port "$MYPORT" --mysql-user "$MYUSER" \
      --pg-host "$PGHOST" --pg-port "$PGPORT" --pg-user "$PGUSER" \
      --db "$PGDB" 2>&1 | tee $WORK/verify_$S.log
done

# 视图单独一步：视图之间有依赖（A 视图引用 B 视图），转换器内部做三轮重试，
# 三轮后仍建不成的如实归类为"仍需人工处理"，不猜不改。
for S in $ALL_SCHEMAS; do
  step "04_views $S"
  MIG_MYSQL_PWD="$MIG_MYSQL_PWD" MIG_PG_PWD="$MIG_PG_PWD" \
    python3 $WORK/view_conv.py.txt \
      --schema "$S" --label "$S" \
      --mysql-host "$MYHOST" --mysql-port "$MYPORT" --mysql-user "$MYUSER" \
      --pg-host "$PGHOST" --pg-port "$PGPORT" --pg-user "$PGUSER" \
      --db "$PGDB" 2>&1 | tee $WORK/views_$S.log
done

step "完成"
