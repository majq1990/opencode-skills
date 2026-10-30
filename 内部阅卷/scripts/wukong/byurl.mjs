// 按 URL 匹配 tab 执行: node byurl.mjs <url关键词> <shot|click|evaljs> <arg>
import pw from 'file:///C:/Users/majq1/AppData/Roaming/npm/node_modules/@playwright/mcp/node_modules/playwright-core/index.js';
import fs from 'node:fs';
const [,, key, action, arg] = process.argv;
const browser = await pw.chromium.connectOverCDP('http://127.0.0.1:9333');
const page = browser.contexts()[0].pages().find(p => p.url().includes(key));
if (!page) { console.error('no page with ' + key); process.exit(1); }
console.error('matched: ' + page.url().slice(0, 90));
if (action === 'shot') {
  await page.screenshot({path: arg, fullPage: false, timeout: 20000});
  console.log('saved ' + arg);
} else if (action === 'click') {
  await page.locator('text=' + arg).first().click({timeout: 5000});
  await page.waitForTimeout(1500);
  console.log('clicked ' + arg);
} else if (action === 'evaljs') {
  const result = await page.evaluate(fs.readFileSync(arg, 'utf8'));
  console.log(typeof result === 'string' ? result : JSON.stringify(result, null, 1));
}
process.exit(0);
