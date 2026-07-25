import sharp from "sharp";
import { readFileSync, writeFileSync } from "node:fs";
import { chromium } from "playwright";
// 一条命令对比: 识别目标图 + 截图识别实际大屏 + 对齐对比 → 逐块报告+还原度%
// 用法: node review.mjs <目标图> <pageId> [报告路径]
const tgtImg = process.argv[2];
const pageId = process.argv[3];
const out = process.argv[4] || "/opt/wk-kg-mcp/verify/review-report.md";
if (!tgtImg || !pageId) { console.error("用法: node review.mjs <目标图> <pageId> [报告路径]"); process.exit(1); }
const env = readFileSync("/opt/wk-kg-mcp/.env", "utf8");
const SF = (env.match(/SILICONFLOW_API_KEY=(.+)/) || [])[1].trim();
const VIEW = "http://wk.egova.com.cn:8042/wukong/index.html#/view?id=" + pageId;

async function describe(imgPath) {
  await sharp(imgPath).resize(1400).jpeg({ quality: 78 }).toFile("/tmp/_rv_" + (Math.floor(process.hrtime()[1] % 99999)) + ".jpg");
  const tmp = "/tmp/_rv_desc.jpg";
  await sharp(imgPath).resize(1400).jpeg({ quality: 78 }).toFile(tmp);
  const b64 = readFileSync(tmp).toString("base64");
  const prompt = "客观拆解这张数据大屏截图,把画面分成所有独立区块,逐块输出一行,格式: 块号|位置|标题|组件类型|该块所有具体数字文字(完整读出,绝不编造)。不遗漏区块。中文。";
  const r = await fetch("https://api.siliconflow.cn/v1/chat/completions", { method: "POST", headers: { Authorization: "Bearer " + SF, "Content-Type": "application/json" }, body: JSON.stringify({ model: "Qwen/Qwen3-VL-30B-A3B-Instruct", messages: [{ role: "user", content: [{ type: "text", text: prompt }, { type: "image_url", image_url: { url: "data:image/jpeg;base64," + b64 } }] }], max_tokens: 2500 }) });
  const j = await r.json();
  return j.choices && j.choices[0] ? j.choices[0].message.content : "ERR:" + JSON.stringify(j).slice(0, 200);
}

async function shotActual() {
  const browser = await chromium.launch({ headless: true, args: ["--no-sandbox", "--disable-gpu"] });
  const page = await browser.newPage({ viewport: { width: 1920, height: 1080 } });
  await page.goto(VIEW, { waitUntil: "networkidle", timeout: 60000 }).catch(() => {});
  await page.waitForTimeout(9000);
  const png = "/tmp/_review_actual.png";
  await page.screenshot({ path: png });
  await browser.close();
  return png;
}

console.log("[1/3] 识别目标图...");
const tgtDoc = await describe(tgtImg);
console.log("[2/3] 截图+识别实际大屏...");
const actPng = await shotActual();
const actDoc = await describe(actPng);
console.log("[3/3] 对齐对比...");
const cmpPrompt = "下面是【目标图】和【我的复刻】各自的区块清单。请按区块语义对齐,逐块对比,输出markdown表格(列: 区块|目标图内容|我的复刻内容|状态|缺什么/差距),状态用 一致/部分/缺失。表格后给一行统计: 一致X块 部分Y块 缺失Z块, 整体还原度约N%。\n\n【目标图】:\n" + tgtDoc + "\n\n【我的复刻】:\n" + actDoc;
const cr = await fetch("https://api.siliconflow.cn/v1/chat/completions", { method: "POST", headers: { Authorization: "Bearer " + SF, "Content-Type": "application/json" }, body: JSON.stringify({ model: "Qwen/Qwen2.5-72B-Instruct", messages: [{ role: "user", content: cmpPrompt }], max_tokens: 3000 }) });
const cj = await cr.json();
const report = cj.choices && cj.choices[0] ? cj.choices[0].message.content : "ERR:" + JSON.stringify(cj).slice(0, 200);
const full = "# 大屏复刻对比报告\n\n- 目标图: " + tgtImg + "\n- 实际大屏: page " + pageId + "\n- 生成: review.mjs\n\n" + report + "\n\n---\n## 附:目标图识别原文\n" + tgtDoc + "\n\n## 附:实际图识别原文\n" + actDoc + "\n";
writeFileSync(out, full, "utf8");
console.log("\n报告已写: " + out + "\n\n" + report);
