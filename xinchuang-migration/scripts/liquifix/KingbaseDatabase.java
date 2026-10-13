package com.egova.liquibase.database;

import liquibase.database.DatabaseConnection;
import liquibase.exception.DatabaseException;

/**
 * 金仓 KingbaseES 的 liquibase Database 认领类。
 * 背景：eGova fork 的 liquibase-core 内置 DMDatabase（达梦）与
 * PgSupportedHgDatabase（瀚高），但没有认领 "KingbaseES" 产品名，
 * DatabaseFactory 兜底到 UnsupportedDatabase（发出 Oracle 风格
 * `call current_schema`），应用启动即 LiquibaseDatabaseInitException。
 * 本类继承 fork 的 PostgresDatabase（shortName 保持 postgresql，
 * 使 changelog 的 dbms="postgresql" 分支生效），仅认领 KingbaseES。
 */
public class KingbaseDatabase extends PostgresDatabase {

    @Override
    public boolean isCorrectDatabaseImplementation(DatabaseConnection conn)
            throws DatabaseException {
        String name = conn.getDatabaseProductName();
        return name != null && name.toLowerCase().contains("kingbase");
    }

    @Override
    public int getPriority() {
        return PRIORITY_DATABASE + 5;
    }
}
