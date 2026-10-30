// 刷新页面并抓取图层接口响应: node reload_layers.mjs <urlKey> <outJson>
import pw from 'file:///C:/Users/majq1/AppData/Roaming/npm/node_modules/@playwright/mcp/node_modules/playwright-core/index.js';
import fs from 'node:fs';
const [,, key, outPath] = process.argv;
const browser = await pw.chromium.connectOverCDP('http://127.0.0.1:9333');
const page = browser.contexts()[0].pages().find(p => p.url().includes(key));
if (!page) { console.error('no page'); process.exit(1); }

const layerData = { layers: null, menu: null };
page.on('response', async (resp) => {
  try {
    const u = resp.url();
    if (u.includes('page-layer/list')) layerData.layers = await resp.json();
    if (u.includes('layer-menu/tree/list')) layerData.menu = await resp.json();
  } catch {}
});
await page.reload({ waitUntil: 'domcontentloaded', timeout: 30000 });
await page.waitForTimeout(10000);
fs.writeFileSync(outPath, JSON.stringify(layerData, null, 1), 'utf8');
const layers = (layerData.layers && layerData.layers.result) || [];
const summary = layers.map(l => ({
  name: l.name,
  enable: l.enable,
  extractor: l.data && l.data.extractor ? l.data.extractor.replace(/\s+/g, ' ').slice(0, 400) : null,
  src: l.data && l.data.request ? (l.data.request.categoryName || '') + ' | ' + (l.data.request.url || '') : null,
  hasInfoWindow: !!l.infoWindowDataId
}));
const menu = (layerData.menu && layerData.menu.result) || [];
const menuSummary = menu.map(m => ({ name: m.name, menuType: m.menuType, subLayers: (m.subLayers || []).map(s => ({ name: s.name, creator: s.creator })) }));
console.log(JSON.stringify({ layerCount: layers.length, summary, menuSummary }, null, 1));
process.exit(0);
