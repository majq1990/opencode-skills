/**
 * 悟空大屏模板检索器
 * ──────────────────────────────────────────────────────
 * 功能：
 *   1. buildIndex(token)   — 遍历所有分组的所有页面，生成 assets/template-index.json
 *   2. searchTemplates(query, options) — 从索引文件按关键词/业务域/主题检索 top-N 模板
 *
 * 环境变量：
 *   WK_TOKEN — Bearer token（buildIndex 时必须；searchTemplates 只读本地文件不需要）
 *
 * 用法示例（不直接执行，由 skill 主流程调用）：
 *   import { buildIndex, searchTemplates } from './template-retriever.mjs';
 *   await buildIndex(process.env.WK_TOKEN);
 *   const hits = searchTemplates('城管执法态势', { topN: 5 });
 */

import { readFileSync, writeFileSync, mkdirSync, statSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

/** 索引文件输出路径 */
const INDEX_PATH = resolve(__dirname, '..', 'assets', 'template-index.json');

/** 悟空后端基址 */
const WK_BASE = 'http://wk.egova.com.cn:8042/wukong-backend';

// ═══════════════════════════════════════════════════════
//  一、构建索引
// ═══════════════════════════════════════════════════════

/**
 * 调悟空 API，带 Bearer 鉴权
 * @param {string} token
 * @param {string} path  - 相对路径，如 "unity/page-group/list"
 * @param {object} body  - POST body
 * @returns {Promise<object>} 解包后的 result
 */
async function wkPost(token, path, body = {}) {
  const url = `${WK_BASE}/${path}`;
  const resp = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
    },
    body: JSON.stringify(body),
  });
  if (!resp.ok) {
    throw new Error(`悟空 API ${path} 响应 ${resp.status}: ${await resp.text().catch(() => '')}`);
  }
  const data = await resp.json();
  if (data.hasError) {
    throw new Error(`悟空 API ${path} 业务错误: ${data.message || JSON.stringify(data).slice(0, 300)}`);
  }
  return data;
}

/**
 * 获取所有分组列表
 * @param {string} token
 * @returns {Promise<Array<{id:string, name:string}>>}
 */
async function fetchGroups(token) {
  const data = await wkPost(token, 'unity/page-group/list', {});
  // result 通常是分组数组
  const groups = data.result || data;
  if (!Array.isArray(groups)) {
    console.warn('[模板检索] page-group/list 返回非数组，尝试从 result 提取');
    return [];
  }
  return groups.map(g => ({ id: g.id, name: g.name || g.groupName || '' }));
}

/**
 * 获取指定分组下的所有页面（分页兜底，默认每页 1000）
 * @param {string} token
 * @param {string} groupId
 * @returns {Promise<Array<object>>}
 */
async function fetchPagesInGroup(token, groupId) {
  const allPages = [];
  let pageIndex = 1;
  const pageSize = 1000;

  while (true) {
    const body = {
      condition: {
        keyword: '',
        groupId,
        kind: 'PAGE',
        type: '1',        // 1=普通页面
      },
      paging: { pageIndex, pageSize },
    };
    const data = await wkPost(token, 'unity/page/page', body);
    const result = data.result || data;
    // result 可能是 { items: [...], totalCount } 或直接数组
    const items = Array.isArray(result) ? result : (result.items || result.list || []);
    const totalCount = result.totalCount ?? result.total ?? 0;

    allPages.push(...items);

    // 如果本页不满或已达 totalCount，结束翻页
    if (items.length < pageSize || allPages.length >= totalCount) break;
    pageIndex++;
  }

  return allPages;
}

/**
 * 也获取"未分组"的页面（groupId 传空字符串）
 */
async function fetchUngroupedPages(token) {
  return fetchPagesInGroup(token, '');
}

/**
 * 从页面对象中提取索引字段
 * @param {object} page - API 返回的页面对象
 * @param {string} groupId
 * @param {string} groupName
 * @returns {object} 索引条目
 */
function extractEntry(page, groupId, groupName) {
  return {
    id: page.id,
    name: page.name || '',
    product: page.product || '',
    productText: page.productText || '',
    subject: page.subject || '',
    subjectText: page.subjectText || '',
    width: page.width || 0,
    height: page.height || 0,
    templateStyleType: page.templateStyleType || '',
    groupId: groupId || page.groupId || '',
    groupName: groupName || page.groupName || '',
    sourceId: page.sourceId || '',
    // cardCount 需要额外请求 page-detail 才能拿到，索引阶段暂不深入
    // 如果 API 直接返回了 cardCount 就取
    cardCount: page.cardCount ?? null,
    // 辅助检索字段
    kind: page.kind || 'PAGE',
    type: page.type || '',
    createTime: page.createTime || '',
    updateTime: page.updateTime || page.modifyTime || '',
  };
}

/**
 * 构建模板索引：遍历全部分组 + 未分组，提取页面元信息，写入 JSON
 *
 * @param {string} token - Bearer token（来自环境变量 WK_TOKEN）
 * @returns {Promise<{total:number, groups:number, path:string}>} 统计信息
 */
export async function buildIndex(token) {
  if (!token) {
    throw new Error('token 为空，请通过环境变量 WK_TOKEN 传入悟空 Bearer token');
  }

  console.log('[模板检索] 开始构建索引...');

  // 1. 拉取所有分组
  const groups = await fetchGroups(token);
  console.log(`[模板检索] 发现 ${groups.length} 个分组`);

  const entries = [];
  const seenIds = new Set(); // 去重

  // 2. 遍历每个分组拉页面
  for (const group of groups) {
    try {
      const pages = await fetchPagesInGroup(token, group.id);
      console.log(`[模板检索]   分组 "${group.name}" (${group.id}): ${pages.length} 个页面`);
      for (const page of pages) {
        if (!seenIds.has(page.id)) {
          seenIds.add(page.id);
          entries.push(extractEntry(page, group.id, group.name));
        }
      }
    } catch (err) {
      console.warn(`[模板检索]   分组 "${group.name}" 拉取失败: ${err.message}`);
    }
  }

  // 3. 拉取未分组页面
  try {
    const ungrouped = await fetchUngroupedPages(token);
    console.log(`[模板检索]   未分组: ${ungrouped.length} 个页面`);
    for (const page of ungrouped) {
      if (!seenIds.has(page.id)) {
        seenIds.add(page.id);
        entries.push(extractEntry(page, '', '未分组'));
      }
    }
  } catch (err) {
    console.warn(`[模板检索]   未分组拉取失败: ${err.message}`);
  }

  // 4. 写入索引文件
  const index = {
    version: '1.0',
    buildTime: new Date().toISOString(),
    total: entries.length,
    groupCount: groups.length,
    entries,
  };

  // 确保 assets 目录存在
  mkdirSync(dirname(INDEX_PATH), { recursive: true });
  writeFileSync(INDEX_PATH, JSON.stringify(index, null, 2), 'utf-8');
  console.log(`[模板检索] 索引构建完成: ${entries.length} 个页面 → ${INDEX_PATH}`);

  return { total: entries.length, groups: groups.length, path: INDEX_PATH };
}

// ═══════════════════════════════════════════════════════
//  二、检索模板
// ═══════════════════════════════════════════════════════

/**
 * 加载索引（带内存缓存）
 * @returns {{ version:string, entries:object[] }}
 */
let _cachedIndex = null;
let _cachedMtime = 0;

function loadIndex() {
  try {
    // 简单 mtime 缓存：同一进程内如果文件没变就不重新 parse
    const { mtimeMs } = statSync(INDEX_PATH);
    if (_cachedIndex && mtimeMs === _cachedMtime) return _cachedIndex;
    const raw = readFileSync(INDEX_PATH, 'utf-8');
    _cachedIndex = JSON.parse(raw);
    _cachedMtime = mtimeMs;
    return _cachedIndex;
  } catch {
    throw new Error(`索引文件不存在或不可读: ${INDEX_PATH}\n请先执行 buildIndex(token) 构建索引。`);
  }
}

// ─── 分词工具 ───

/**
 * 中文分词：简单的字符级 n-gram + 按常见分隔符切割
 * 不依赖第三方分词库，对大屏场景够用
 * @param {string} text
 * @returns {string[]} 词项数组（已去重、小写化）
 */
function tokenize(text) {
  if (!text) return [];
  const s = text.toLowerCase();
  const terms = new Set();

  // 1. 按非中文/英文/数字字符切割得到「词块」
  const chunks = s.split(/[^a-z0-9一-鿿]+/).filter(Boolean);
  for (const chunk of chunks) {
    terms.add(chunk);
    // 2. 中文部分：2-gram 和 3-gram（短语匹配）
    const chineseOnly = chunk.replace(/[a-z0-9]/g, '');
    if (chineseOnly.length >= 2) {
      for (let i = 0; i < chineseOnly.length - 1; i++) {
        terms.add(chineseOnly.slice(i, i + 2));
      }
    }
    if (chineseOnly.length >= 3) {
      for (let i = 0; i < chineseOnly.length - 2; i++) {
        terms.add(chineseOnly.slice(i, i + 3));
      }
    }
  }
  return [...terms];
}

// ─── 匹配打分 ───

/**
 * 计算查询与单个模板条目的相关性得分
 *
 * 策略：
 *   - name 分词匹配：2 分/命中词
 *   - productText 精确包含：5 分
 *   - subjectText 精确包含：5 分
 *   - groupName 包含：3 分
 *   - templateStyleType == "专题模板"：2 分加成（优质骨架优先）
 *   - 分辨率匹配（如指定）：1 分
 *
 * @param {object} entry - 索引条目
 * @param {object} parsed - 解析后的查询上下文
 * @returns {number} 得分
 */
function scoreEntry(entry, parsed) {
  let score = 0;

  // ── name 分词匹配 ──
  const nameTokens = tokenize(entry.name);
  for (const qt of parsed.queryTokens) {
    if (nameTokens.includes(qt)) {
      score += 2;
    }
  }
  // 全名子串匹配额外加分
  const nameLower = (entry.name || '').toLowerCase();
  if (parsed.queryLower && nameLower.includes(parsed.queryLower)) {
    score += 6;
  }
  // 反向：查询包含页面名（短页名被长查询命中）
  if (parsed.queryLower && nameLower && parsed.queryLower.includes(nameLower)) {
    score += 4;
  }

  // ── productText 精确匹配 ──
  const pt = (entry.productText || '').toLowerCase();
  if (parsed.product && pt === parsed.product) {
    score += 5;
  } else if (parsed.queryLower && pt && parsed.queryLower.includes(pt)) {
    score += 3;
  }
  // 查询词在 productText 中出现
  for (const qt of parsed.queryTokens) {
    if (pt.includes(qt)) {
      score += 1;
    }
  }

  // ── subjectText 精确匹配 ──
  const st = (entry.subjectText || '').toLowerCase();
  if (parsed.subject && st === parsed.subject) {
    score += 5;
  } else if (parsed.queryLower && st && parsed.queryLower.includes(st)) {
    score += 3;
  }
  for (const qt of parsed.queryTokens) {
    if (st.includes(qt)) {
      score += 1;
    }
  }

  // ── groupName 模糊匹配 ──
  const gn = (entry.groupName || '').toLowerCase();
  for (const qt of parsed.queryTokens) {
    if (gn.includes(qt)) {
      score += 1.5;
    }
  }

  // ── 专题模板加成（优质骨架优先） ──
  if (entry.templateStyleType === '专题模板') {
    score += 2;
  }

  // ── 分辨率匹配 ──
  if (parsed.width && entry.width === parsed.width && parsed.height && entry.height === parsed.height) {
    score += 1;
  }

  return score;
}

/**
 * 从索引中检索最相似的模板
 *
 * @param {string} query - 自然语言查询（如 "城管执法态势大屏"、"智慧交通"）
 * @param {object} [options]
 * @param {number} [options.topN=10] - 返回前 N 个结果
 * @param {string} [options.product] - 精确过滤业务线（productText，如 "城市管理"）
 * @param {string} [options.subject] - 精确过滤主题（subjectText，如 "态势感知"）
 * @param {string} [options.templateStyleType] - 只保留指定模板类型（如 "专题模板"）
 * @param {number} [options.width] - 画布宽度过滤
 * @param {number} [options.height] - 画布高度过滤
 * @param {string} [options.groupName] - 分组名过滤（模糊包含）
 * @param {number} [options.minScore=0.5] - 最低得分阈值
 * @returns {Array<{entry:object, score:number}>} 按得分降序排列
 */
export function searchTemplates(query, options = {}) {
  const {
    topN = 10,
    product = '',
    subject = '',
    templateStyleType = '',
    width = 0,
    height = 0,
    groupName = '',
    minScore = 0.5,
  } = options;

  const index = loadIndex();
  let entries = index.entries || [];

  // ── 硬过滤（精确条件，提前缩小范围） ──
  if (templateStyleType) {
    entries = entries.filter(e => e.templateStyleType === templateStyleType);
  }
  if (width && height) {
    entries = entries.filter(e => e.width === width && e.height === height);
  }
  if (groupName) {
    const gnLower = groupName.toLowerCase();
    entries = entries.filter(e => (e.groupName || '').toLowerCase().includes(gnLower));
  }

  // ── 解析查询 ──
  const queryLower = (query || '').toLowerCase().trim();
  const queryTokens = tokenize(query);
  const parsed = {
    queryLower,
    queryTokens,
    product: product.toLowerCase(),
    subject: subject.toLowerCase(),
    width,
    height,
  };

  // ── 打分 ──
  const scored = [];
  for (const entry of entries) {
    const s = scoreEntry(entry, parsed);
    if (s >= minScore) {
      scored.push({ entry, score: s });
    }
  }

  // ── 排序 + 截断 ──
  scored.sort((a, b) => b.score - a.score);
  return scored.slice(0, topN);
}

// ═══════════════════════════════════════════════════════
//  三、CLI 入口（可选，直接 node 执行时用）
// ═══════════════════════════════════════════════════════

/**
 * 命令行模式：
 *   node template-retriever.mjs build          — 构建索引（需 WK_TOKEN 环境变量）
 *   node template-retriever.mjs search "关键词" — 检索模板
 *   node template-retriever.mjs search "关键词" --product "城市管理" --topN 5
 */
async function main() {
  const args = process.argv.slice(2);
  const cmd = args[0];

  if (cmd === 'build') {
    const token = process.env.WK_TOKEN;
    if (!token) {
      console.error('错误: 请设置环境变量 WK_TOKEN');
      process.exit(1);
    }
    const result = await buildIndex(token);
    console.log(`\n构建完成: ${result.total} 个页面, ${result.groups} 个分组`);
    console.log(`索引文件: ${result.path}`);

  } else if (cmd === 'search') {
    const query = args[1];
    if (!query) {
      console.error('用法: node template-retriever.mjs search "查询关键词" [--topN N] [--product X] [--subject X] [--type X]');
      process.exit(1);
    }
    // 解析可选参数
    const opts = {};
    for (let i = 2; i < args.length; i += 2) {
      const key = args[i]?.replace(/^--/, '');
      const val = args[i + 1];
      if (key === 'topN') opts.topN = parseInt(val, 10);
      else if (key === 'product') opts.product = val;
      else if (key === 'subject') opts.subject = val;
      else if (key === 'type') opts.templateStyleType = val;
      else if (key === 'group') opts.groupName = val;
      else if (key === 'width') opts.width = parseInt(val, 10);
      else if (key === 'height') opts.height = parseInt(val, 10);
      else if (key === 'minScore') opts.minScore = parseFloat(val);
    }

    const hits = searchTemplates(query, opts);
    if (hits.length === 0) {
      console.log('未找到匹配的模板。尝试放宽关键词或使用 --minScore 0 查看全部。');
    } else {
      console.log(`\n找到 ${hits.length} 个匹配模板（按相关性降序）:\n`);
      for (let i = 0; i < hits.length; i++) {
        const { entry, score } = hits[i];
        console.log(`  ${i + 1}. [${score.toFixed(1)}分] ${entry.name}`);
        console.log(`     ID: ${entry.id}`);
        console.log(`     业务线: ${entry.productText || '-'}  主题: ${entry.subjectText || '-'}`);
        console.log(`     分组: ${entry.groupName || '-'}  尺寸: ${entry.width}x${entry.height}`);
        console.log(`     类型: ${entry.templateStyleType || '-'}  组件数: ${entry.cardCount ?? '未知'}`);
        console.log('');
      }
    }

  } else {
    console.log('悟空大屏模板检索器');
    console.log('─────────────────');
    console.log('用法:');
    console.log('  node template-retriever.mjs build                     构建索引（需 WK_TOKEN）');
    console.log('  node template-retriever.mjs search "关键词"            检索模板');
    console.log('  node template-retriever.mjs search "关键词" --topN 5   指定返回数量');
    console.log('  node template-retriever.mjs search "关键词" --product "城市管理"');
    console.log('  node template-retriever.mjs search "关键词" --type "专题模板"');
  }
}

// 仅在直接执行时运行 CLI
const isMain = process.argv[1] && (
  process.argv[1].endsWith('template-retriever.mjs') ||
  process.argv[1].endsWith('template-retriever')
);
if (isMain) {
  main().catch(err => {
    console.error('致命错误:', err.message);
    process.exit(1);
  });
}
