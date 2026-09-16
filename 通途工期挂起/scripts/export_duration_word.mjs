/**
 * 工期记录 → 「工期调整申请」word 文档批量导出 + 自动重命名为「工期更新-{项目名}.docx」
 *
 * 用法：
 *   node export_duration_word.mjs login                     首次启动并手动登录 ztoa
 *   node export_duration_word.mjs row <rowId> [<rowId>...]  指定 rowId 导出
 *   node export_duration_word.mjs all                       拉全表，对每条工期记录导出
 *   node export_duration_word.mjs all --dry                 仅打印将处理的 rowId+项目名，不真正导出
 *
 * 登录态保存在脚本同目录 .ztoa-pw-profile/，第一次跑 `login` 之后可长期复用。
 */
import pw from "file:///C:/Users/majq1/node_modules/playwright/index.js";
const { chromium } = pw;
import path from "path";
import fs from "fs/promises";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const USER_DATA_DIR =
  process.env.ZTOA_PROFILE ||
  path.join(__dirname, ".ztoa-pw-profile"); // 独立 profile，避开 playwright MCP 抢占
const today = new Date().toISOString().slice(0, 10);
const OUTPUT_DIR = path.join("D:/opencode/file", today);

const APP_ID = "6987622c-c4c5-4d23-8ce4-0fd6887250a5";
const WORKSHEET_ID = "69fc30b91e6716810741b4a7";
const PROJECT_NAME_CID = "69fc40831e6716810741b843";
const APPLY_NO_CID = "69fc3daa1e6716810741b7ce";

const recordUrl = (rowId) =>
  `https://ztoa.egova.com.cn/worksheet/${WORKSHEET_ID}/row/${rowId}`;

function safeName(s) {
  return (s || "未命名").replace(/[\\/:*?"<>|\r\n\t]/g, "_").trim();
}

async function fetchAllRows(page) {
  return page.evaluate(async ({ wsid }) => {
    const r = await fetch(
      "https://ztoa.egova.com.cn/wwwapi/Worksheet/GetFilterRows",
      {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          worksheetId: wsid,
          viewId: "",
          pageIndex: 1,
          pageSize: 1000,
          getType: 0,
          searchType: 1,
        }),
      },
    );
    const j = await r.json();
    const list = j?.data?.data || j?.data?.rows || [];
    return list.map((row) => ({
      rowId: row.rowid,
      applyNo: row["69fc3daa1e6716810741b7ce"] || "",
      projectName: row["69fc40831e6716810741b843"] || "",
    }));
  }, { wsid: WORKSHEET_ID });
}

async function exportOne(page, rowId, knownProjectName) {
  await page.goto(recordUrl(rowId), { waitUntil: "load" });
  // 等待页面 settle（navigation 可能后续触发跳到 preview）
  await page.waitForLoadState("networkidle", { timeout: 30000 }).catch(() => {});
  await page.waitForTimeout(3000);

  // 个别 rowId 服务器直接重定向到 print preview 页
  if (page.url().includes("/printForm/")) {
    await page.waitForSelector(".exportForWord", { timeout: 30000 });
    await page.waitForTimeout(1500);
    const projectName =
      knownProjectName ||
      (await page.title()).replace(/^系统打印[-—]/, "").trim();
    const [download] = await Promise.all([
      page.waitForEvent("download", { timeout: 60000 }),
      page.click(".exportForWord"),
    ]);
    const target = path.join(
      OUTPUT_DIR,
      `工期更新-${safeName(projectName)}.docx`,
    );
    await download.saveAs(target);
    return { projectName, target };
  }

  // 三点菜单出现 = record 详情加载完
  await page.waitForSelector(".icon-task-point-more", { timeout: 45000 });
  // 等 React 列表完整渲染（数据/控件 lazy load），并等"加载中"消失
  await page
    .waitForFunction(
      () =>
        document.title &&
        !document.title.includes("加载中") &&
        document.querySelector(".icon-task-point-more"),
      null,
      { timeout: 30000 },
    )
    .catch(() => {});
  await page.waitForTimeout(4500);
  await page
    .locator(".icon-task-point-more")
    .first()
    .scrollIntoViewIfNeeded()
    .catch(() => {});

  let projectName = knownProjectName || "";
  if (!projectName) {
    // 兜底：从 record API 字段提取（GetRowDetail 返回结构跟 query_records 不一样，要单字段读）
    projectName = await page.evaluate(
      async ({ wsid, rowId, nameCid }) => {
        const r = await fetch(
          "https://ztoa.egova.com.cn/wwwapi/Worksheet/GetRowDetail",
          {
            method: "POST",
            credentials: "include",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ worksheetId: wsid, rowId, getType: 1 }),
          },
        );
        const j = await r.json();
        const ctrls = j?.data?.receiveControls;
        if (Array.isArray(ctrls)) {
          const f = ctrls.find((c) => c.controlId === nameCid);
          if (f?.value) return f.value;
        }
        return j?.data?.[nameCid] || "";
      },
      { wsid: WORKSHEET_ID, rowId, nameCid: PROJECT_NAME_CID },
    );
  }

  // 点 三点 → 打印/导出 → 工期调整申请（菜单偶尔卡死，第 2 轮 reload 兜底）
  let menuOk = false;
  for (let attempt = 0; attempt < 4 && !menuOk; attempt++) {
    try {
      // attempt 2 时 reload 整个页面（山西临汾经验：reload 后立即就好）
      if (attempt === 2) {
        await page.reload({ waitUntil: "domcontentloaded" });
        await page
          .waitForLoadState("networkidle", { timeout: 30000 })
          .catch(() => {});
        await page.waitForSelector(".icon-task-point-more", { timeout: 45000 });
        await page.waitForTimeout(5000);
        await page
          .locator(".icon-task-point-more")
          .first()
          .scrollIntoViewIfNeeded()
          .catch(() => {});
      }
      await page
        .locator(".icon-task-point-more")
        .first()
        .click({ timeout: 15000, force: true });
      await page.waitForSelector(".printItem", { timeout: 15000 });
      await page.click(".printItem");
      // 新流程：点打印后直接跳 preview 页；旧流程才有二级菜单
      const direct = await page
        .waitForURL(/\/printForm\//, { timeout: 8000 })
        .then(() => true)
        .catch(() => false);
      if (!direct) {
        await page.waitForSelector('li:has-text("工期调整申请")', {
          timeout: 15000,
        });
      }
      menuOk = true;
    } catch (e) {
      if (attempt === 3) throw e;
      await page.waitForTimeout(2000);
      // 关弹层避免堆积
      await page.keyboard.press("Escape").catch(() => {});
      await page.keyboard.press("Escape").catch(() => {});
    }
  }
  if (!page.url().includes("/printForm/")) {
    await Promise.all([
      page.waitForURL(/\/printForm\//, { timeout: 30000 }),
      page.click('li:has-text("工期调整申请")'),
    ]);
  }

  // preview 渲染完
  await page.waitForSelector(".exportForWord", { timeout: 30000 });
  await page.waitForTimeout(1500);

  // 监听下载
  const [download] = await Promise.all([
    page.waitForEvent("download", { timeout: 60000 }),
    page.click(".exportForWord"),
  ]);

  const target = path.join(
    OUTPUT_DIR,
    `工期更新-${safeName(projectName)}.docx`,
  );
  await download.saveAs(target);
  return { projectName, target };
}

async function openContext({ headless }) {
  headless = process.env.ZTOA_HEADLESS
    ? process.env.ZTOA_HEADLESS !== "0"
    : headless;
  await fs.mkdir(USER_DATA_DIR, { recursive: true });
  const ctx = await chromium.launchPersistentContext(USER_DATA_DIR, {
    headless,
    channel: "chrome",
    acceptDownloads: true,
    viewport: { width: 1400, height: 900 },
  });
  // ztoa 打印预览在触发导出后 ~4s 会 window.close()，会掐死尚未完成的 blob 下载 → saveAs 报 browser closed
  await ctx.addInitScript(() => {
    window.close = () => {};
  });
  const page = ctx.pages()[0] || (await ctx.newPage());
  return { ctx, page };
}

async function cmdLogin() {
  const { ctx, page } = await openContext({ headless: false });
  await page.goto("https://ztoa.egova.com.cn/");
  console.log(
    "[login] 浏览器已打开。请在窗口里完成登录，登录成功后按 Ctrl+C 退出（cookies 已落地，下次免登）。",
  );
  await new Promise(() => {});
}

async function cmdRows(items) {
  // items: string[] (rowId) or {rowId, projectName}[]
  // 环境变量 CONCURRENCY=N 控制并发 tab 数（默认 2）
  await fs.mkdir(OUTPUT_DIR, { recursive: true });
  const norm = items.map((x) =>
    typeof x === "string" ? { rowId: x } : x,
  );
  const concurrency = Math.max(
    1,
    parseInt(process.env.CONCURRENCY || "2", 10) || 2,
  );

  const { ctx, page: page0 } = await openContext({ headless: false });
  // warmup 主 page
  await page0.goto("https://ztoa.egova.com.cn/", {
    waitUntil: "load",
    timeout: 60000,
  });
  // 启额外 tab
  const pages = [page0];
  for (let i = 1; i < concurrency; i++) {
    const p = await ctx.newPage();
    await p.goto("https://ztoa.egova.com.cn/", {
      waitUntil: "load",
      timeout: 60000,
    });
    pages.push(p);
  }
  await page0.waitForTimeout(6000);
  console.log(`[batch] ${norm.length} 条 × ${concurrency} 并发\n`);

  const total = norm.length;
  const queue = [...norm.map((it, idx) => ({ ...it, _seq: idx + 1 }))];
  const results = [];
  let done = 0;

  async function worker(workerId, page) {
    while (queue.length > 0) {
      const item = queue.shift();
      if (!item) break;
      const tag = `[w${workerId} ${item._seq}/${total}]`;
      try {
        const r = await exportOne(page, item.rowId, item.projectName);
        done++;
        console.log(`${tag} OK ${r.projectName} → ${path.basename(r.target)}`);
        results.push({ rowId: item.rowId, ok: true, ...r });
      } catch (e) {
        done++;
        const msg = e.message.split("\n")[0];
        console.log(`${tag} FAIL: ${msg}`);
        results.push({ rowId: item.rowId, ok: false, error: msg });
        // 关弹层避免污染下一轮
        await page.keyboard.press("Escape").catch(() => {});
        await page.keyboard.press("Escape").catch(() => {});
      }
    }
  }

  await Promise.all(pages.map((p, i) => worker(i + 1, p)));

  console.log("\n===== 汇总 =====");
  console.log(`成功 ${results.filter((x) => x.ok).length} / ${results.length}`);
  const fails = results.filter((x) => !x.ok);
  for (const r of fails) {
    console.log(`  失败 ${r.rowId}: ${r.error}`);
  }
  const retryPath = path.join(__dirname, "retry.json");
  if (fails.length) {
    const retryItems = fails.map((r) => {
      const orig = norm.find((x) => x.rowId === r.rowId);
      return orig ? orig : { rowId: r.rowId };
    });
    await fs.writeFile(retryPath, JSON.stringify(retryItems, null, 2));
    console.log(`  失败 rowId 已落 ${retryPath}（重跑：node export_duration_word.mjs rowsfile retry.json）`);
  } else {
    await fs.rm(retryPath, { force: true }).catch(() => {});
  }
  await ctx.close();
}

async function cmdAll(dry) {
  const { ctx, page } = await openContext({ headless: false });
  // 必须先到 ztoa 域名才能用 fetch
  await page.goto("https://ztoa.egova.com.cn/");
  await page.waitForTimeout(1500);
  const rows = await fetchAllRows(page);
  console.log(`[all] 共 ${rows.length} 条工期记录`);
  if (dry) {
    for (const r of rows.slice(0, 5)) {
      console.log("  ", r.applyNo, "→", r.projectName, "(", r.rowId, ")");
    }
    console.log("  …");
    await ctx.close();
    return;
  }
  await ctx.close();
  await cmdRows(rows.map((r) => r.rowId));
}

const [cmd, ...rest] = process.argv.slice(2);
try {
  if (cmd === "login") await cmdLogin();
  else if (cmd === "row") await cmdRows(rest);
  else if (cmd === "all") await cmdAll(rest.includes("--dry"));
  else if (cmd === "rowsfile") {
    const raw = JSON.parse(await fs.readFile(rest[0], "utf8"));
    await cmdRows(raw);
  }
  else {
    console.error("用法见脚本头注释");
    process.exit(2);
  }
} catch (e) {
  console.error(e);
  process.exit(1);
}
