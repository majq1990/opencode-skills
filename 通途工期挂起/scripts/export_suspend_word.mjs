/**
 * 项目工期挂起记录 → 「挂起导出」word 文档批量导出 + 工期挂起说明附件批量下载
 *
 * 输出落 D:/opencode/file/<日期>/：
 *   挂起导出-{项目名}.docx
 *   挂起导出-{项目名}-{原文件名}.{ext}            （单附件）
 *   挂起导出-{项目名}-{i}-{原文件名}.{ext}        （多附件，i 从 1 起编号）
 *
 * 用法：
 *   node export_suspend_word.mjs all              拉全表，按顺序导出全部
 *   node export_suspend_word.mjs all --dry        只打印将处理的内容，不下载
 *   node export_suspend_word.mjs row <rowId>      单条
 *   node export_suspend_word.mjs rowsfile <path>  从 JSON 文件读取（schema 兼容 sus_rowids.json）
 *
 * 登录态复用 C:\Users\majq1\.playwright-mcp-profile/（与 export_duration_word.mjs 共用）。
 */
import pw from "file:///C:/Users/majq1/node_modules/playwright/index.js";
const { chromium } = pw;
import path from "path";
import fs from "fs/promises";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const USER_DATA_DIR =
  process.env.ZTOA_PROFILE ||
  path.join(__dirname, ".edge-profile"); // 用 Edge 独立 profile，不抢 chrome MCP
const BROWSER_CHANNEL = process.env.ZTOA_CHANNEL || "msedge";
const today = new Date().toISOString().slice(0, 10);
const OUTPUT_DIR = path.join("D:/opencode/file", today);

const APP_ID = "6987622c-c4c5-4d23-8ce4-0fd6887250a5";
const WORKSHEET_ID = "69fc30c1111e45dac897c658";
const TEMPLATE_NAME = "挂起导出";
const TEMPLATE_ID = "6a38b4f5416b923955e664e4";
const PROJECT_ID = "9a60927f-0d37-4164-9a87-856bfd01771c";
const PROJECT_NAME_CID = "6a1808ba964e268c28697ebe"; // 公式回填的项目名
const RELATED_PROJECT_CID = "6a0aa776964e268c286826fa"; // 关联交付项目（兜底）
const ATTACH_CID = "6a27a90e964e268c286ae204"; // 工期挂起说明附件
const FILE_PREFIX = "挂起导出";

const recordUrl = (rowId) =>
  `https://ztoa.egova.com.cn/worksheet/${WORKSHEET_ID}/row/${rowId}`;

function safeName(s) {
  return (s || "未命名").replace(/[\\/:*?"<>|\r\n\t]/g, "_").trim();
}

// 去掉「S3级-」「A1级-」「E2级-」「B1级-」等等评级前缀
function stripLevelPrefix(s) {
  return (s || "").replace(/^[SABCDE]\d+级[-—]\s*/, "");
}

async function fetchAllRows(page) {
  const rows = await page.evaluate(
    async ({ wsid, appId }) => {
      const r = await fetch(
        "https://ztoa.egova.com.cn/wwwapi/Worksheet/GetFilterRows",
        {
          method: "POST",
          credentials: "include",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            worksheetId: wsid,
            pageIndex: 1,
            pageSize: 1000,
            getType: 0,
            appId,
          }),
        },
      );
      const j = await r.json();
      return j?.data?.data || [];
    },
    { wsid: WORKSHEET_ID, appId: APP_ID },
  );

  return rows.map((rw) => {
    let projectName = rw[PROJECT_NAME_CID] || "";
    if (!projectName) {
      const rel = rw[RELATED_PROJECT_CID];
      if (rel) {
        try {
          const arr = JSON.parse(rel);
          projectName = stripLevelPrefix(arr?.[0]?.name || "");
        } catch {}
      }
    }
    let attaches = [];
    const a = rw[ATTACH_CID];
    if (a && a !== "[]") {
      try {
        const arr = JSON.parse(a);
        attaches = arr.map((f) => ({
          fileId: f.fileId,
          name: f.originalFilename,
          ext: f.ext,
          url: f.fileUrl,
          size: f.filesize,
        }));
      } catch {}
    }
    return { rowId: rw.rowid, projectName, attaches };
  });
}

// 调 GetPrint 取附件控件的 signed downloadUrl（mdoc 原始 URL token check fail，必须走 wwwapi/file/downDocument）
async function fetchSignedAttachments(page, rowId) {
  return await page.evaluate(
    async ({ rowId, wsid, appId, tplId, projId, attCid }) => {
      const r = await fetch(
        "https://ztoa.egova.com.cn/wwwapi/Worksheet/GetPrint",
        {
          method: "POST",
          credentials: "include",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            id: tplId,
            projectId: projId,
            worksheetId: wsid,
            rowId,
            pageIndex: 1,
            pageSize: 100000,
            getType: 1,
            appId,
          }),
        },
      );
      const j = await r.json();
      const ctrls = j?.data?.receiveControls || [];
      const att = Array.isArray(ctrls)
        ? ctrls.find((c) => c.controlId === attCid)
        : null;
      if (!att?.value) return [];
      try {
        const arr = JSON.parse(att.value);
        return arr.map((a) => ({
          name: a.originalFilename,
          ext: a.ext,
          downloadUrl: a.downloadUrl,
          size: a.filesize,
        }));
      } catch {
        return [];
      }
    },
    {
      rowId,
      wsid: WORKSHEET_ID,
      appId: APP_ID,
      tplId: TEMPLATE_ID,
      projId: PROJECT_ID,
      attCid: ATTACH_CID,
    },
  );
}

async function downloadAttachments(page, projectName, attaches) {
  if (!attaches.length) return { saved: [], failed: [] };
  const safe = safeName(projectName);
  const multi = attaches.length > 1;
  const saved = [];
  const failed = [];
  for (let i = 0; i < attaches.length; i++) {
    const a = attaches[i];
    const prefix = multi ? `-${i + 1}` : "";
    const fileName = `${FILE_PREFIX}-${safe}${prefix}-${safeName(a.name)}${a.ext}`;
    const target = path.join(OUTPUT_DIR, fileName);
    try {
      const b64 = await page.evaluate(async (url) => {
        const r = await fetch(url, { credentials: "include" });
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        const buf = await r.arrayBuffer();
        const u8 = new Uint8Array(buf);
        let bin = "";
        for (let i = 0; i < u8.length; i++) bin += String.fromCharCode(u8[i]);
        return btoa(bin);
      }, a.downloadUrl);
      const buf = Buffer.from(b64, "base64");
      await fs.writeFile(target, buf);
      saved.push({ name: fileName, size: buf.length });
    } catch (e) {
      failed.push({ name: fileName, error: e.message.split("\n")[0] });
    }
  }
  return { saved, failed };
}

async function exportWord(page, rowId, projectName) {
  await page.goto(recordUrl(rowId), { waitUntil: "load" });
  await page
    .waitForLoadState("networkidle", { timeout: 30000 })
    .catch(() => {});
  await page.waitForTimeout(3000);

  // 个别 rowId 服务器直接重定向到 print preview 页
  if (page.url().includes("/printForm/")) {
    await page.waitForSelector(".exportForWord", { timeout: 30000 });
    await page.waitForTimeout(1500);
    const [download] = await Promise.all([
      page.waitForEvent("download", { timeout: 60000 }),
      page.click(".exportForWord"),
    ]);
    const target = path.join(
      OUTPUT_DIR,
      `${FILE_PREFIX}-${safeName(projectName)}.docx`,
    );
    await download.saveAs(target);
    return target;
  }

  await page.waitForSelector(".icon-task-point-more", { timeout: 45000 });
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

  let menuOk = false;
  for (let attempt = 0; attempt < 3 && !menuOk; attempt++) {
    try {
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
        await page.waitForSelector(`li:has-text("${TEMPLATE_NAME}")`, {
          timeout: 15000,
        });
      }
      menuOk = true;
    } catch (e) {
      if (attempt === 2) throw e;
      await page.waitForTimeout(2000);
      await page.keyboard.press("Escape").catch(() => {});
      await page.keyboard.press("Escape").catch(() => {});
    }
  }
  if (!page.url().includes("/printForm/")) {
    await Promise.all([
      page.waitForURL(/\/printForm\//, { timeout: 30000 }),
      page.click(`li:has-text("${TEMPLATE_NAME}")`),
    ]);
  }

  await page.waitForSelector(".exportForWord", { timeout: 30000 });
  await page.waitForTimeout(1500);
  const [download] = await Promise.all([
    page.waitForEvent("download", { timeout: 60000 }),
    page.click(".exportForWord"),
  ]);
  const target = path.join(
    OUTPUT_DIR,
    `${FILE_PREFIX}-${safeName(projectName)}.docx`,
  );
  await download.saveAs(target);
  return target;
}

async function openContext({ headless }) {
  headless = process.env.ZTOA_HEADLESS
    ? process.env.ZTOA_HEADLESS !== "0"
    : headless;
  await fs.mkdir(USER_DATA_DIR, { recursive: true });
  const ctx = await chromium.launchPersistentContext(USER_DATA_DIR, {
    headless,
    channel: BROWSER_CHANNEL,
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

async function processItems(items, dry) {
  await fs.mkdir(OUTPUT_DIR, { recursive: true });
  const { ctx, page } = await openContext({ headless: false });
  await page.goto("https://ztoa.egova.com.cn/", {
    waitUntil: "load",
    timeout: 60000,
  });
  await page.waitForTimeout(6000);

  const results = [];
  for (let i = 0; i < items.length; i++) {
    const it = items[i];
    const tag = `[${i + 1}/${items.length}] ${it.rowId}`;
    if (dry) {
      console.log(
        `${tag} dry → ${it.projectName || "(空项目名)"} / 附件 ${it.attaches.length}`,
      );
      results.push({ ...it, ok: true, dry: true });
      continue;
    }
    process.stdout.write(`${tag} … `);
    let docTarget = null;
    let attResult = { saved: [], failed: [] };
    let mainErr = null;
    try {
      docTarget = await exportWord(page, it.rowId, it.projectName);
    } catch (e) {
      mainErr = e.message.split("\n")[0];
      // 截图便于排查
      const dbg = path.join(__dirname, "debug-suspend-fail");
      await fs.mkdir(dbg, { recursive: true });
      await page
        .screenshot({
          path: path.join(dbg, `${it.rowId}.png`),
          fullPage: true,
        })
        .catch(() => {});
    }
    // 附件独立处理：每条记录现拉一次 signed downloadUrl，再下载
    if (it.attaches.length > 0) {
      try {
        const signed = await fetchSignedAttachments(page, it.rowId);
        attResult = await downloadAttachments(page, it.projectName, signed);
      } catch (e) {
        attResult.failed = it.attaches.map((a) => ({
          name: a.name,
          error: e.message.split("\n")[0],
        }));
      }
    }
    if (mainErr && attResult.failed.length === it.attaches.length) {
      console.log(`FAIL: ${mainErr}`);
      results.push({ ...it, ok: false, error: mainErr });
    } else {
      const note =
        attResult.failed.length > 0
          ? ` (附件 ${attResult.saved.length}/${it.attaches.length}, 失败 ${attResult.failed.length})`
          : ` (附件 ${attResult.saved.length})`;
      console.log(
        `${mainErr ? "PARTIAL" : "OK"} ${it.projectName} → ${docTarget ? "docx" : "(无 docx)"}${note}`,
      );
      results.push({
        ...it,
        ok: !mainErr,
        partial: !!mainErr,
        doc: docTarget ? path.basename(docTarget) : null,
        saved: attResult.saved,
        attFailed: attResult.failed,
        error: mainErr || undefined,
      });
    }
  }
  console.log("\n===== 汇总 =====");
  const okN = results.filter((x) => x.ok).length;
  console.log(`成功 ${okN} / ${results.length}`);
  for (const r of results.filter((x) => !x.ok)) {
    console.log(`  失败 ${r.rowId} (${r.projectName}): ${r.error}`);
  }
  // 失败项落 retry.json
  const retries = results
    .filter((x) => !x.ok)
    .map(({ rowId, projectName, attaches }) => ({
      rowId,
      projectName,
      attaches,
    }));
  if (retries.length) {
    const p = path.join(__dirname, "sus_retry.json");
    await fs.writeFile(p, JSON.stringify(retries, null, 2), "utf8");
    console.log(`  失败 rowId 已落 ${p}`);
  }
  await ctx.close();
}

async function cmdAll(dry) {
  const { ctx, page } = await openContext({ headless: false });
  await page.goto("https://ztoa.egova.com.cn/");
  await page.waitForTimeout(3000);
  const items = await fetchAllRows(page);
  console.log(`[all] 共 ${items.length} 条挂起记录`);
  const itemsFile = path.join(__dirname, "sus_rowids.json");
  await fs.writeFile(itemsFile, JSON.stringify(items, null, 2), "utf8");
  console.log(`  已落 ${itemsFile}`);
  await ctx.close();
  await processItems(items, dry);
}

async function cmdRowsFile(p, dry) {
  const items = JSON.parse(await fs.readFile(p, "utf8"));
  await processItems(items, dry);
}

async function cmdRow(rowIds) {
  // 单条没有 projectName / attaches 信息，先拉全表再过滤
  const { ctx, page } = await openContext({ headless: false });
  await page.goto("https://ztoa.egova.com.cn/");
  await page.waitForTimeout(3000);
  const all = await fetchAllRows(page);
  await ctx.close();
  const items = all.filter((x) => rowIds.includes(x.rowId));
  if (!items.length) throw new Error("rowId 在挂起表里找不到");
  await processItems(items, false);
}

async function cmdLogin() {
  const { ctx, page } = await openContext({ headless: false });
  await page.goto("https://ztoa.egova.com.cn/");
  console.log(
    `[login] Edge 窗口已打开（profile=${USER_DATA_DIR}）。登录完成后按 Ctrl+C 退出，cookies 已落地，下次免登。`,
  );
  await new Promise(() => {});
}

const [cmd, ...rest] = process.argv.slice(2);
try {
  if (cmd === "login") await cmdLogin();
  else if (cmd === "all") await cmdAll(rest.includes("--dry"));
  else if (cmd === "row") await cmdRow(rest);
  else if (cmd === "rowsfile") await cmdRowsFile(rest[0], rest.includes("--dry"));
  else {
    console.error("用法见脚本头注释");
    process.exit(2);
  }
} catch (e) {
  console.error(e);
  process.exit(1);
}
