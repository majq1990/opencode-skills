// 拉取通途三张表全量行 JSON：工期表 / 挂起表 / 交付项目主数据表
// 用法: node probe_tables.mjs [--out D:/opencode/file/<日期>]
// env: ZTOA_PROFILE(默认 D:/git/工程实施改造/.edge-profile 已登录态) ZTOA_CHANNEL(默认 msedge)
import pw from "file:///C:/Users/majq1/node_modules/playwright/index.js";
const { chromium } = pw;
import fs from "fs/promises";
import path from "path";

const PROFILE = process.env.ZTOA_PROFILE || "D:/git/工程实施改造/.edge-profile";
const CHANNEL = process.env.ZTOA_CHANNEL || "msedge";

const argOut = (() => {
  const i = process.argv.indexOf("--out");
  return i > -1 ? process.argv[i + 1] : null;
})();
const OUT = argOut || path.join("D:/opencode/file", new Date().toISOString().slice(0, 10));
await fs.mkdir(OUT, { recursive: true });

const TABLES = [
  { name: "duration", id: "69fc30b91e6716810741b4a7" },  // 工期表
  { name: "suspend", id: "69fc30c1111e45dac897c658" },   // 挂起表
  { name: "projects", id: "629da7f86f0dcb3b9b7cd603" },  // 交付项目主数据表
];

const ctx = await chromium.launchPersistentContext(PROFILE, {
  headless: true, channel: CHANNEL, viewport: { width: 1400, height: 900 },
});
const page = ctx.pages()[0] || (await ctx.newPage());
await page.goto("https://ztoa.egova.com.cn/", { waitUntil: "load", timeout: 60000 });
await page.waitForTimeout(3000);

for (const t of TABLES) {
  // 注意: searchType 必须 0 才是全量; searchType:1 只回部分行!
  const res = await page.evaluate(async (wsid) => {
    const r = await fetch("https://ztoa.egova.com.cn/wwwapi/Worksheet/GetFilterRows", {
      method: "POST", credentials: "include",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ worksheetId: wsid, pageIndex: 1, pageSize: 1000, getType: 0, searchType: 0 }),
    });
    const j = await r.json();
    return { rows: j?.data?.data || j?.data?.rows || [], err: j?.error ?? null };
  }, t.id);
  const out = path.join(OUT, `probe_${t.name}.json`);
  await fs.writeFile(out, JSON.stringify(res.rows, null, 1), "utf8");
  console.log(`${t.name}: ${res.rows.length} 行 → ${out}${res.err ? "  ERR=" + JSON.stringify(res.err) : ""}`);
}
await ctx.close();
console.log("done.");
