// 补导出编排器：逐条独立浏览器进程 + 失败重试（批量并发模式必死，勿用 rowsfile 全量跑）
// 用法: node run_missing.mjs --type dur|sus --list <todo.json> [--dir <对账目录，可多个用逗号分隔>] [--script-dir <导出脚本目录>]
//   todo.json schema: [{rowId, projectName, attaches?}]  (filter_since.py 产物)
// env: MAX_TRY(默认5) ZTOA_HEADLESS=1
// 对账逻辑: 按 projectName 统计已存在 docx 数（含 -记录N 后缀），与 list 中同名记录数比对，缺几条补几条
import { spawnSync } from "child_process";
import fs from "fs/promises";
import path from "path";
import os from "os";

const args = process.argv.slice(2);
const get = (k) => { const i = args.indexOf(k); return i > -1 ? args[i + 1] : null; };
const type = get("--type") || "dur";
const listFile = get("--list");
const DIRS = (get("--dir") || "D:/opencode/file/2026-09-02,D:/opencode/file/" + new Date().toISOString().slice(0, 10)).split(",");
const SCRIPT_DIR = get("--script-dir") || path.join(path.dirname(new URL(import.meta.url).pathname.replace(/^\/(\w:)/, "$1")));
const SCRIPT = path.join(SCRIPT_DIR, type === "dur" ? "export_duration_word.mjs" : "export_suspend_word.mjs");
const PREFIX = type === "dur" ? "工期更新" : "挂起导出";
const MAX_TRY = parseInt(process.env.MAX_TRY || "5", 10);
const OUT_DIR = DIRS[DIRS.length - 1];

if (!listFile) { console.error("用法: node run_missing.mjs --type dur|sus --list <todo.json>"); process.exit(2); }

const items = JSON.parse(await fs.readFile(listFile, "utf8"));
const safe = (s) => (s || "未命名").replace(/[\\/:*?"<>|\r\n\t]/g, "_").trim();

// 各目录 docx 清单
const filesByDir = {};
for (const d of DIRS) {
  try { filesByDir[d] = await fs.readdir(d); } catch { filesByDir[d] = []; }
}

// 同项目已有 docx 数（跨目录求和；挂起 -记录N 后缀归一）
function haveCount(name) {
  let n = 0;
  const base = `${PREFIX}-${safe(name)}`;
  for (const d of DIRS) {
    for (const f of filesByDir[d]) {
      if (type === "dur") { if (f === `${base}.docx`) n++; }
      else if (f === `${base}.docx` || f.startsWith(`${base}-记录`)) n++;
    }
  }
  return n;
}

// 同名记录按 ctime 排序，前 have 条视为已导
const byName = {};
for (const it of items) (byName[it.projectName] ||= []).push(it);
for (const k in byName) byName[k].sort((a, b) => String(a.ctime).localeCompare(String(b.ctime)));

const todo = [];
for (const k in byName) {
  const have = haveCount(k);
  byName[k].forEach((it, idx) => { if (idx >= have) todo.push(it); });
}
console.log(`待补 ${todo.length} / ${items.length} (${PREFIX})`);

const still = [];
for (const it of todo) {
  // 补挂起必需 attaches 字段（rowsfile schema）
  const payload = { rowId: it.rowId, projectName: it.projectName };
  if (type === "sus") payload.attaches = it.attaches || [];
  let ok = false;
  for (let t = 1; t <= MAX_TRY && !ok; t++) {
    console.log(`\n>>> ${it.projectName} (第${t}次)`);
    const point = path.join(os.tmpdir(), `tt_point_${it.rowId.slice(0, 8)}.json`);
    await fs.writeFile(point, JSON.stringify([payload], null, 1), "utf8");
    const r = spawnSync("node", [SCRIPT, "rowsfile", point], {
      env: { ...process.env, ZTOA_HEADLESS: "1", CONCURRENCY: "1", ZTOA_PROFILE: process.env.ZTOA_PROFILE || "D:/git/工程实施改造/.edge-profile" },
      encoding: "utf8", timeout: 180000,
    });
    const out = (r.stdout || "") + (r.stderr || "");
    console.log("  " + (out.split("\n").filter(l => /OK|FAIL|PARTIAL/.test(l)).join(" | ").slice(-300) || "无输出"));
    // 生成确认：任一目录出现目标文件（同名第一条）或 -记录N（后续条）
    for (const d of DIRS) {
      const base = `${PREFIX}-${safe(it.projectName)}`;
      try { await fs.access(path.join(d, `${base}.docx`)); ok = true; break; } catch {}
      try {
        const fs2 = await fs.readdir(d);
        if (fs2.some(f => f.startsWith(`${base}-记录`))) { ok = true; break; }
      } catch {}
    }
  }
  if (!ok) still.push(it);
}
console.log(`\n===== 剩余失败 ${still.length}/${todo.length} =====`);
for (const s of still) console.log("  " + s.rowId + " " + s.projectName);
await fs.writeFile(path.join(path.dirname(listFile), `${type}_still_fail.json`), JSON.stringify(still, null, 1), "utf8");
