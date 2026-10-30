// 页面配置拉取（在浏览器页面内执行: byurl.mjs <urlKey> evaljs pull_page_config.js）
// 前置：把下方 PAGE_KEY 改成目标 pageId 前 8 位；auth 头从该页最近一次 page/detail 请求头抄
// 输出：接口分类统计 / 星桥&视频流是否存在 / 各组件 extractor（含热词过滤、实时告警 id）
(async () => {
  const PAGE_KEY = 'f1e30a60'; // TODO 改成目标 pageId 前缀
  const AUTH = {
    'authorization': 'bearer lUBCVW5QfTHA-85TssKqvfXZlGQ',
    'encryptkey': 'c799b4b8825c96823a58030f0792b487',
    'encryptiv': '207b5da967c28637c3a1d0485965dffb',
    'app-id': 'wukong'
  };
  const out = {};
  const entry = performance.getEntriesByType('resource').find(r => r.name.includes('/free/page/detail/' + PAGE_KEY));
  if (!entry) { out.detailErr = 'no entry (先刷新页面)'; return out; }
  const resp = await fetch(entry.name, { headers: AUTH }).catch(() => null);
  if (!resp || !resp.ok) { out.detailErr = 'fetch fail'; return out; }
  const s = JSON.stringify(await resp.json());
  if (s.includes('未登录')) { out.detailErr = 'signature expired (刷新页面重试)'; return out; }
  out.detailLen = s.length;
  const cats = [...s.matchAll(/"categoryName":"([^"]{1,50})"/g)].map(m => m[1]);
  const catCount = {};
  cats.forEach(c => { catCount[c] = (catCount[c] || 0) + 1; });
  out.apiCategories = catCount;
  out.hasStarbridge = s.includes('接口合并') || s.includes('星桥');
  out.hasVideoStream = s.includes('视频流') || s.includes('获取视频');
  const extractors = [...s.matchAll(/"extractor":"((?:[^"\\]|\\.)*)"/g)].map(m => m[1].replace(/\\n/g, ' ').replace(/\\"/g, '"'));
  out.extractors = extractors.map(e => e.replace(/\s+/g, ' ').slice(0, 180));
  const hot = extractors.find(e => e.includes('!== 0') || e.includes('!==0') || e.includes('report'));
  out.hotwordFilter = hot ? hot.slice(0, 220) : 'none';
  const alert = extractors.find(e => e.includes('attachments'));
  out.alertHasId = alert ? /["']id["']\s*:/.test(alert) : 'no-alert-ext';
  return out;
})()
