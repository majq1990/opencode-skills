import sharp from "sharp";
import { readFileSync, writeFileSync } from "node:fs";
// 任意图 → Qwen-VL 识别成区块清单(第1层拆解目标图用)
// 用法: node describe.mjs <图路径> [输出txt] [.env路径]
const img = process.argv[2];
const out = process.argv[3] || "/tmp/describe-out.txt";
const envPath = process.argv[4] || "/opt/wk-kg-mcp/.env";
if (!img) { console.error("用法: node describe.mjs <图路径> [输出txt] [.env路径]"); process.exit(1); }
const env = readFileSync(envPath, "utf8");
const SF = (env.match(/SILICONFLOW_API_KEY=(.+)/) || [])[1].trim();
await sharp(img).resize(1400).jpeg({ quality: 78 }).toFile("/tmp/_desc.jpg");
const b64 = readFileSync("/tmp/_desc.jpg").toString("base64");
const prompt = "客观拆解这张数据大屏截图,把画面分成所有独立区块,逐块输出一行,格式: 块号|位置|标题|组件类型(表格/折线图/柱状图/桑基流图/翻牌数字/地图/切换/边框/图例/滚动播报等)|该块显示的所有具体数字和文字(完整读出,看不清写不清,绝不编造)。不遗漏任何区块。中文。";
const r = await fetch("https://api.siliconflow.cn/v1/chat/completions", { method: "POST", headers: { Authorization: "Bearer " + SF, "Content-Type": "application/json" }, body: JSON.stringify({ model: "Qwen/Qwen3-VL-30B-A3B-Instruct", messages: [{ role: "user", content: [{ type: "text", text: prompt }, { type: "image_url", image_url: { url: "data:image/jpeg;base64," + b64 } }] }], max_tokens: 2500 }) });
const j = await r.json();
const txt = j.choices && j.choices[0] ? j.choices[0].message.content : "ERR:" + JSON.stringify(j).slice(0, 200);
writeFileSync(out, txt, "utf8");
console.log(txt);
