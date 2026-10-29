import java.sql.Connection;
import java.sql.DriverManager;
import java.util.List;

import liquibase.ChecksumVersion;
import liquibase.LabelExpression;
import liquibase.Contexts;
import liquibase.database.Database;
import liquibase.database.DatabaseFactory;
import liquibase.database.jvm.JdbcConnection;
import liquibase.change.CheckSum;
import liquibase.changelog.ChangeLogHistoryService;
import liquibase.changelog.ChangeLogHistoryServiceFactory;
import liquibase.changelog.ChangeLogParameters;
import liquibase.changelog.ChangeSet;
import liquibase.changelog.DatabaseChangeLog;
import liquibase.changelog.RanChangeSet;
import liquibase.parser.ChangeLogParser;
import liquibase.parser.ChangeLogParserFactory;
import liquibase.resource.ClassLoaderResourceAccessor;
import liquibase.resource.ResourceAccessor;

/**
 * B1Fix：A1Fix 的金仓变体（同一规程，换驱动与 URL）。
 * 处置：已登记(EXECUTED/RERAN)且校验值≠当前(V9) → replaceChecksum；
 *       未登记且 dbms 适用于 postgresql → setExecType(EXECUTED)；其余不动。
 *
 * 用法（cg156，classpath=eUrbanGIS/WEB-INF/lib/*）：
 *   java -cp "LIB/*:/root/_b1fix" B1Fix <changelogFile> [more...]
 *   口令经 -Dkb.pass= 传入。
 */
public class B1Fix {
    public static void main(String[] args) throws Exception {
        if (args.length < 1) {
            System.err.println("usage: B1Fix <changelog> [changelog...]");
            System.exit(2);
        }
        String pass = System.getProperty("kb.pass", "");
        Class.forName("com.kingbase8.Driver");
        Connection conn = DriverManager.getConnection(
                "jdbc:kingbase8://127.0.0.1:54321/test?currentSchema=cgdb", "mig", pass);
        try {
            Database db = DatabaseFactory.getInstance()
                    .findCorrectDatabaseImplementation(new JdbcConnection(conn));
            System.out.println("[DB] " + db.getDatabaseProductName()
                    + " " + db.getDatabaseProductVersion());
            ResourceAccessor ra = new ClassLoaderResourceAccessor();
            ChangeLogHistoryService svc =
                    ChangeLogHistoryServiceFactory.getInstance().getChangeLogService(db);
            svc.reset();
            svc.init();

            int fixed = 0, marked = 0, same = 0, skipped = 0, missing = 0;
            for (String file : args) {
                ChangeLogParser parser =
                        ChangeLogParserFactory.getInstance().getParser(file, ra);
                DatabaseChangeLog log = parser.parse(file, new ChangeLogParameters(db), ra);
                List<ChangeSet> sets = log.getChangeSets();
                System.out.println("[FILE] " + file + " changesets=" + sets.size());
                for (ChangeSet cs : sets) {
                    java.util.Set<String> dbms = cs.getDbmsSet();
                    boolean applies = (dbms == null || dbms.isEmpty()
                            || dbms.contains("postgresql"));
                    RanChangeSet ran = svc.getRanChangeSet(cs);
                    if (ran == null) {
                        if (applies) {
                            svc.setExecType(cs, ChangeSet.ExecType.EXECUTED);
                            marked++;
                        } else {
                            skipped++;
                        }
                        continue;
                    }
                    ChangeSet.ExecType et = ran.getExecType();
                    if (et != ChangeSet.ExecType.EXECUTED && et != ChangeSet.ExecType.RERAN) {
                        skipped++;
                        continue;
                    }
                    CheckSum stored = ran.getLastCheckSum();
                    CheckSum cur = cs.generateCheckSum(ChecksumVersion.V9);
                    if (cur == null) {
                        missing++;
                    } else if (stored == null || !stored.toString().equals(cur.toString())) {
                        svc.replaceChecksum(cs);
                        fixed++;
                    } else {
                        same++;
                    }
                }
            }
            System.out.println("[DONE] replaceChecksum=" + fixed
                    + " setExecType=" + marked
                    + " checksumSame=" + same
                    + " skipped(filtered/markran)=" + skipped
                    + " nullChecksum=" + missing);
            System.out.println("[NOTE] 复验必须另起进程");
            new Contexts();
            new LabelExpression();
        } finally {
            conn.close();
        }
    }
}
