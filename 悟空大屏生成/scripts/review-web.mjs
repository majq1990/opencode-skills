import { createServer } from "node:http";
import { writeFileSync, readFileSync, existsSync } from "node:fs";
import { execFile } from "node:child_process";
const PORT = 3200;
const HTML = `<!doctype html><html lang="zh"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>大屏复刻对比工具</title>
<style>body{font-family:system-ui,sans-serif;max-width:900px;margin:30px auto;padding:0 16px;color:#222}h1{font-size:22px}.box{border:1px solid #ddd;border-radius:8px;padding:18px;margin:14px 0}label{display:block;margin:10px 0 4px;font-weight:600}input[type=text]{width:100%;padding:8px;border:1px solid #ccc;border-radius:6px}button{background:#1761b0;color:#fff;border:0;padding:10px 22px;border-radius:6px;font-size:15px;cursor:pointer;margin-top:12px}button:disabled{background:#999}pre{white-space:pre-wrap;background:#f6f8fa;padding:14px;border-radius:8px;overflow:auto;font-size:13px}.tip{color:#666;font-size:13px}</style></head>
<body><h1>悟空大屏复刻对比工具</h1><p class="tip">上传目标设计图 + 填写你复刻的悟空大屏 pageId，自动逐块对比，输出"目标/复刻/状态/缺什么"报告。处理约 1-2 分钟。</p>
<div class="box"><label>① 目标设计图（png/jpg）</label><input type="file" id="img" accept="image/*">
<label>② 悟空大屏 pageId</label><input type="text" id="pid" placeholder="如 59dd90b8-bb0a-4151-bd79-720ac4aebfdb">
<button id="go" onclick="run()">开始对比</button></div>
<div class="box"><b>对比报告</b><pre id="out">（等待开始）</pre></div>
<script>
async function run(){
  const f=document.getElementById("img").files[0], pid=document.getElementById("pid").value.trim();
  if(!f){alert("请选择目标图");return}
  if(!pid){alert("请填写 pageId");return}
  const b=document.getElementById("go"); b.disabled=true; b.textContent="处理中...";
  document.getElementById("out").textContent="正在识别目标图、截取并识别实际大屏、对齐对比……约1-2分钟";
  const rd=new FileReader();
  rd.onload=async()=>{
    try{
      const r=await fetch("/api/review",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({imageBase64:rd.result,pageId:pid})});
      document.getElementById("out").textContent=await r.text();
    }catch(e){document.getElementById("out").textContent="出错: "+e.message}
    b.disabled=false; b.textContent="开始对比";
  };
  rd.readAsDataURL(f);
}
</script></body></html>`;
const server = createServer((req, res) => {
  if (req.method === "GET" && (req.url === "/" || req.url === "/index.html")) {
    res.writeHead(200, { "Content-Type": "text/html;charset=utf-8" }); res.end(HTML); return;
  }
  if (req.method === "POST" && req.url === "/api/review") {
    const chunks = [];
    req.on("data", c => chunks.push(c));
    req.on("end", () => {
      try {
        const body = JSON.parse(Buffer.concat(chunks).toString());
        const { imageBase64, pageId } = body;
        if (!imageBase64 || !pageId) { res.writeHead(400, { "Content-Type": "text/plain;charset=utf-8" }); res.end("缺少图片或 pageId"); return; }
        const ts = Date.now();
        const imgPath = "/tmp/web_target_" + ts + ".png";
        writeFileSync(imgPath, Buffer.from(imageBase64.replace(/^data:image\/\w+;base64,/, ""), "base64"));
        const repPath = "/tmp/web_rep_" + ts + ".md";
        execFile("node", ["/opt/wk-kg-mcp/scripts/review.mjs", imgPath, pageId, repPath], { timeout: 180000 }, (err, stdout, stderr) => {
          if (existsSync(repPath)) { res.writeHead(200, { "Content-Type": "text/plain;charset=utf-8" }); res.end(readFileSync(repPath, "utf8")); }
          else { res.writeHead(500, { "Content-Type": "text/plain;charset=utf-8" }); res.end("生成失败: " + (stderr || (err && err.message) || "未知")); }
        });
      } catch (e) { res.writeHead(400, { "Content-Type": "text/plain;charset=utf-8" }); res.end("请求错误: " + e.message); }
    });
    return;
  }
  res.writeHead(404); res.end("Not Found");
});
server.listen(PORT, "127.0.0.1", () => console.log("review-web listening 127.0.0.1:" + PORT));
