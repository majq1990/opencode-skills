import sharp from "sharp";
import { readFileSync, writeFileSync } from "node:fs";
import { chromium } from "playwright";
// 截图实际大屏 + Qwen-VL识别 + 对照固定target-spec → 验收报告
// 用法: node verify.mjs <pageId> [spec路径] [报告路径]
const pageId = process.argv[2];
const specPath = process.argv[3] || "/opt/wk-kg-mcp/verify/target-spec.txt";
const out = process.argv[4] || "/opt/wk-kg-mcp/verify/verify-report.md";
if (!pageId) { console.error("用法: node verify.mjs <pageId> [spec路径] [报告路径]"); process.exit(1); }
const env = readFileSync("/opt/wk-kg-mcp/.env", "utf8");
const SF = (env.match(/SILICONFLOW_API_KEY=(.+)/) || [])[1].trim();
let spec = ""; try { spec = readFileSync(specPath, "utf8"); } catch { spec = "(无 target-spec, 仅描述实际画面)"; }
const VIEW = "http://wk.egova.com.cn:8042/wukong/index.html#/view?id=" + pageId;
const browser = await chromium.launch({ headless: true, args: ["--no-sandbox", "--disable-gpu"] });
const page = await browser.newPage({ viewport: { width: 1920, height: 1080 } });
await page.goto(VIEW, { waitUntil: "networkidle", timeout: 60000 }).catch(() => {});
await page.waitForTimeout(9000);
await page.screenshot({ path: "/tmp/_verify.png" });
await browser.close();
await sharp("/tmp/_verify.png").resize(1400).jpeg({ quality: 78 }).toFile("/tmp/_verify.jpg");
const b64 = readFileSync("/tmp/_verify.jpg").toString("base64");
const prompt = "这是实际大屏截图。对照下面的目标标准逐条核对,输出每条: 满足/部分/不满足 + 实际看到什么。最后给还原度%。\n目标标准:\n" + spec;
const r = await fetch("https://api.siliconflow.cn/v1/chat/completions", { method: "POST", headers: { Authorization: "Bearer " + SF, "Content-Type": "application/json" }, body: JSON.stringify({ model: "Qwen/Qwen3-VL-30B-A3B-Instruct", messages: [{ role: "user", content: [{ type: "text", text: prompt }, { type: "image_url", image_url: { url: "data:image/jpeg;base64," + b64 } }] }], max_tokens: 2500 }) });
const j = await r.json();
const rep = j.choices && j.choices[0] ? j.choices[0].message.content : "ERR:" + JSON.stringify(j).slice(0, 200);
writeFileSync(out, "# 验收报告 page " + pageId + "\n\n" + rep + "\n", "utf8");
console.log(rep);
