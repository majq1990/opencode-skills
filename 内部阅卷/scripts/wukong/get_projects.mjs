// 读项目列表 + 拦截 window.open 拿项目页 URL（不真开新页）
import pw from 'file:///C:/Users/majq1/AppData/Roaming/npm/node_modules/@playwright/mcp/node_modules/playwright-core/index.js';
const browser = await pw.chromium.connectOverCDP('http://127.0.0.1:9333');
const page = browser.contexts()[0].pages().find(p => p.url().includes('/space/project'));
if (!page) { console.error('no project list page'); process.exit(1); }
const out = {};
out.projects = await page.evaluate(() => {
  const txt = document.body.innerText;
  const i = txt.indexOf('项目分组');
  return txt.slice(i >= 0 ? i : 0, (i >= 0 ? i : 0) + 600).replace(/\n+/g, ' | ');
});
// 拦截 open 拿页面 URL
out.pages = await page.evaluate(async () => {
  const opened = [];
  const orig = window.open;
  window.open = (u) => { opened.push(String(u)); return null; };
  const names = [...document.querySelectorAll('*')].filter(e => e.children.length === 0 && /1920\*1080/.test('') === false);
  // 点所有卡片上的眼睛图标
  const eyes = [...document.querySelectorAll('.icon-yanjing-kai')].filter(e => e.getBoundingClientRect().width > 0);
  for (const eye of eyes) {
    const r = eye.getBoundingClientRect();
    const x = r.x + r.width / 2, y = r.y + r.height / 2;
    const opts = { bubbles: true, cancelable: true, view: window, clientX: x, clientY: y };
    const t = document.elementFromPoint(x, y) || eye;
    ['pointerdown', 'mousedown', 'pointerup', 'mouseup', 'click'].forEach(tt => t.dispatchEvent(new (tt.startsWith('pointer') ? PointerEvent : MouseEvent)(tt, opts)));
    await new Promise(rr => setTimeout(rr, 400));
  }
  window.open = orig;
  return opened;
});
console.log(JSON.stringify(out, null, 1));
process.exit(0);
