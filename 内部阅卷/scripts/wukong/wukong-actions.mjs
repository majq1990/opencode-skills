// 通用动作脚本: node wukong-actions.mjs <action> [arg]
// action: login <user> | open <url> | shot <file> | evaljs <jsFile>
import pw from 'file:///C:/Users/majq1/AppData/Roaming/npm/node_modules/@playwright/mcp/node_modules/playwright-core/index.js';
import fs from 'node:fs';
const [,, action, arg] = process.argv;
const browser = await pw.chromium.connectOverCDP('http://127.0.0.1:9333');
const ctx = browser.contexts()[0];
let page = ctx.pages()[0] || await ctx.newPage();
await page.setViewportSize({width: 1920, height: 1080}).catch(()=>{});

if (action === 'login') {
  await page.goto('http://8.130.127.28:8080/wukong/index.html#/login', {waitUntil: 'domcontentloaded', timeout: 30000});
  await page.waitForTimeout(2500);
  if (!page.url().includes('#/login')) { console.log('already: ' + page.url()); }
  else {
    await page.locator('input[placeholder="请输入账号"]').fill(arg);
    await page.locator('input[placeholder="密码"]').fill('eGova@123');
    await page.locator("form .login-btn:not(.ukey)").first().click();
    await page.waitForTimeout(3000);
    console.log('after login: ' + page.url());
  }
} else if (action === 'open') {
  await page.goto(arg, {waitUntil: 'domcontentloaded', timeout: 30000}).catch(e => console.error('goto:', e.message));
  await page.waitForTimeout(6000);
  console.log('url: ' + page.url() + ' | title: ' + await page.title());
} else if (action === 'shot') {
  await page.screenshot({path: arg, fullPage: false, timeout: 20000});
  console.log('saved ' + arg);
} else if (action === 'evaljs') {
  const result = await page.evaluate(fs.readFileSync(arg, 'utf8'));
  console.log(typeof result === 'string' ? result : JSON.stringify(result, null, 1));
}
process.exit(0);
