/**
 * 悟空大屏包补丁器 —— 可复用 ES module
 * -----------------------------------------------
 * 落地路径 A（包补丁）的完整实现：
 *   export zip -> 解包 -> 改 pageJson -> 重打包 -> import
 *
 * 所有 token 通过参数传入，不硬编码。
 * 临时文件使用 os.tmpdir()。
 * Windows 环境，打包/解包走 PowerShell Compress-Archive / Expand-Archive。
 *
 * 用法：
 *   import { roundtrip, exportTemplate, unpackZip, patchPageJson, repackZip, importPackage } from './package-patcher.mjs';
 *   const result = await roundtrip(pageId, patches, groupId, token);
 */

import { readFileSync, writeFileSync, mkdirSync, readdirSync, rmSync, existsSync, statSync } from 'node:fs';
import { join, resolve } from 'node:path';
import { tmpdir } from 'node:os';
import { randomUUID } from 'node:crypto';
import { execSync } from 'node:child_process';

// ============================================================
// 常量
// ============================================================

const BASE_URL = 'http://wk.egova.com.cn:8042/wukong-backend/';

// ============================================================
// 1. exportTemplate — 调 batch-export 下载模板 zip
// ============================================================

/**
 * 从悟空后端导出指定页面的 zip 包。
 * @param {string|string[]} pageId  单个页面 id 或 id 数组
 * @param {string} token            Bearer token（不含 "Bearer " 前缀）
 * @param {object} [options]
 * @param {string} [options.baseUrl] 自定义后端地址，默认 BASE_URL
 * @returns {Promise<Buffer>} zip 文件的 Buffer
 */
export async function exportTemplate(pageId, token, options = {}) {
  const base = options.baseUrl || BASE_URL;
  const ids = Array.isArray(pageId) ? pageId : [pageId];

  // 第一步：触发导出，拿到 relativePath
  const exportUrl = base + 'unity/page/batch-export';
  const exportResp = await fetch(exportUrl, {
    method: 'POST',
    headers: {
      'Authorization': 'Bearer ' + token,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ ids }),
  });
  if (!exportResp.ok) {
    throw new Error(`batch-export 请求失败: HTTP ${exportResp.status} ${await exportResp.text()}`);
  }
  const exportJson = await exportResp.json();
  if (exportJson.hasError) {
    throw new Error(`batch-export 后端报错: ${exportJson.message || JSON.stringify(exportJson)}`);
  }
  const relativePath = exportJson.result?.relativePath;
  if (!relativePath) {
    throw new Error(`batch-export 未返回 relativePath: ${JSON.stringify(exportJson)}`);
  }

  // 第二步：下载 zip
  const downloadUrl = base + relativePath.replace(/^\//, '');
  const dlResp = await fetch(downloadUrl, {
    headers: { 'Authorization': 'Bearer ' + token },
  });
  if (!dlResp.ok) {
    throw new Error(`zip 下载失败: HTTP ${dlResp.status} ${downloadUrl}`);
  }
  const arrayBuf = await dlResp.arrayBuffer();
  return Buffer.from(arrayBuf);
}

// ============================================================
// 2. unpackZip — 解包 zip 到目录
// ============================================================

/**
 * 将 zip Buffer 解包到指定目录。如果 destDir 不传，自动在 tmpdir 下创建。
 * @param {Buffer} zipBuffer  zip 文件内容
 * @param {string} [destDir]  目标目录，默认 os.tmpdir()/wk-patcher-{uuid}
 * @returns {string} 解包后的目录路径
 */
export function unpackZip(zipBuffer, destDir) {
  if (!destDir) {
    destDir = join(tmpdir(), 'wk-patcher-' + randomUUID().slice(0, 8));
  }
  // 确保目标目录干净
  if (existsSync(destDir)) {
    rmSync(destDir, { recursive: true, force: true });
  }
  mkdirSync(destDir, { recursive: true });

  // 先把 zip 写到临时文件
  const zipPath = join(tmpdir(), 'wk-tmp-' + randomUUID().slice(0, 8) + '.zip');
  writeFileSync(zipPath, zipBuffer);

  try {
    // 用 PowerShell Expand-Archive 解包
    execSync(
      `powershell -NoProfile -Command "Expand-Archive -Path '${zipPath}' -DestinationPath '${destDir}' -Force"`,
      { stdio: 'pipe', timeout: 120000 }
    );
  } finally {
    // 清理临时 zip 文件
    try { rmSync(zipPath); } catch {}
  }

  return destDir;
}

// ============================================================
// 3. patchPageJson — 应用补丁到 pageJson
// ============================================================

/**
 * 对解包目录中的 pageJson 应用补丁。
 *
 * @param {string} unpackedDir 解包后的根目录（含 pageJson/ cardListJson/ card/ images/）
 * @param {object} patches 补丁描述对象
 * @param {string}  [patches.name]      新页面名称
 * @param {string}  [patches.groupId]   目标分组 id
 * @param {number}  [patches.width]     画布宽度
 * @param {number}  [patches.height]    画布高度
 * @param {string}  [patches.newPageId] 自定义新 page.id（不传则自动生成 UUID）
 * @param {Array}   [patches.dataPatches]  数据绑定补丁数组
 *   每项：{ cardDataId, request?, extractor?, extractorEnable?, refreshInterval?, ... }
 *   cardDataId 用于匹配 cardDataList 中的 id，匹配到则合并其余字段
 * @param {Array}   [patches.cardPatches]  组件实例补丁数组
 *   每项：{ pageCardId, x?, y?, w?, h?, name?, beHidden?, beLocked?, ... }
 *   pageCardId 用于匹配 pageCardList 中的 id，匹配到则合并其余字段
 * @param {object}  [patches.pageOverrides] page 段的任意字段覆盖（高级用法）
 * @returns {{ pj: object, pjFilePath: string, oldPageId: string, newPageId: string }}
 */
export function patchPageJson(unpackedDir, patches = {}) {
  const pjDir = join(unpackedDir, 'pageJson');
  if (!existsSync(pjDir)) {
    throw new Error(`pageJson 目录不存在: ${pjDir}`);
  }

  const pjFiles = readdirSync(pjDir).filter(f => f.endsWith('.json'));
  if (pjFiles.length === 0) {
    throw new Error('pageJson 目录为空，无 json 文件');
  }
  if (pjFiles.length > 1) {
    // 多页导出场景：当前仅支持单页补丁
    console.warn(`[package-patcher] pageJson 下有 ${pjFiles.length} 个文件，仅处理第一个`);
  }

  const origFile = pjFiles[0];
  const pj = JSON.parse(readFileSync(join(pjDir, origFile), 'utf8'));

  const oldPageId = pj.page.id;
  const newPageId = patches.newPageId || randomUUID();

  // --- 3a. 替换 page.id ---
  pj.page.id = newPageId;

  // --- 3b. 替换 name / groupId / 尺寸 ---
  if (patches.name !== undefined)    pj.page.name    = patches.name;
  if (patches.groupId !== undefined) pj.page.groupId = patches.groupId;
  if (patches.width !== undefined)   pj.page.width   = patches.width;
  if (patches.height !== undefined)  pj.page.height  = patches.height;

  // --- 3c. page 段任意字段覆盖 ---
  if (patches.pageOverrides) {
    Object.assign(pj.page, patches.pageOverrides);
  }

  // --- 3d. 递归替换所有引用旧 pageId 的子实体 ---
  const _patchId = (obj) => {
    if (!obj || typeof obj !== 'object') return;
    if (Array.isArray(obj)) { obj.forEach(_patchId); return; }
    for (const [k, v] of Object.entries(obj)) {
      if (typeof v === 'string' && v === oldPageId) {
        obj[k] = newPageId;
      } else if (typeof v === 'object') {
        _patchId(v);
      }
    }
  };

  // pageJson 12 段中所有可能引用 pageId 的子实体
  const refSegments = [
    'pageCardList', 'cardList', 'cardDataList',
    'interactionList', 'pageLayerList',
    'layerMenuList', 'layerMenuRelationList',
    'labelList', 'pageAiConfigList', 'pageAiCustomInteractList',
  ];
  for (const seg of refSegments) {
    if (pj[seg]) _patchId(pj[seg]);
  }
  // pageHook 也可能引用 pageId
  if (pj.pageHook) _patchId(pj.pageHook);

  // --- 3e. 应用 dataPatches（数据绑定补丁）---
  if (patches.dataPatches && Array.isArray(patches.dataPatches) && pj.cardDataList) {
    for (const dp of patches.dataPatches) {
      const target = pj.cardDataList.find(cd => cd.id === dp.cardDataId);
      if (!target) {
        console.warn(`[package-patcher] dataPatches: 未找到 cardDataId=${dp.cardDataId}，跳过`);
        continue;
      }
      // 合并补丁字段（cardDataId 仅用于匹配，不写入）
      const { cardDataId, ...rest } = dp;
      // request 是嵌套对象，做深合并
      if (rest.request && target.request) {
        Object.assign(target.request, rest.request);
        delete rest.request;
      }
      Object.assign(target, rest);
    }
  }

  // --- 3f. 应用 cardPatches（组件实例补丁）---
  if (patches.cardPatches && Array.isArray(patches.cardPatches) && pj.pageCardList) {
    for (const cp of patches.cardPatches) {
      const target = pj.pageCardList.find(pc => pc.id === cp.pageCardId);
      if (!target) {
        console.warn(`[package-patcher] cardPatches: 未找到 pageCardId=${cp.pageCardId}，跳过`);
        continue;
      }
      const { pageCardId, ...rest } = cp;
      // 把 w/h 映射为 width/height
      if (rest.w !== undefined) { rest.width  = rest.w; delete rest.w; }
      if (rest.h !== undefined) { rest.height = rest.h; delete rest.h; }
      Object.assign(target, rest);
    }
  }

  // --- 3g. 写回 pageJson ---
  // 文件名格式：{页面名}_{pageId}.json
  const finalName = (patches.name || pj.page.name || 'patched') + '_' + newPageId + '.json';
  const newPjPath = join(pjDir, finalName);
  writeFileSync(newPjPath, JSON.stringify(pj, null, 2), 'utf8');

  // 删除原始文件（如果文件名变了）
  if (finalName !== origFile) {
    try { rmSync(join(pjDir, origFile)); } catch {}
  }

  return {
    pj,
    pjFilePath: newPjPath,
    oldPageId,
    newPageId,
  };
}

// ============================================================
// 4. repackZip — 重打包为 zip Buffer
// ============================================================

/**
 * 将补丁后的目录重新打包为 zip。
 * @param {string} patchedDir 补丁后的根目录（含 pageJson/ cardListJson/ card/ images/）
 * @returns {Buffer} zip 文件的 Buffer
 */
export function repackZip(patchedDir) {
  const zipPath = join(tmpdir(), 'wk-patched-' + randomUUID().slice(0, 8) + '.zip');

  // 如果已存在先删除（Compress-Archive -Force 不能覆盖已有文件在某些 PS 版本）
  try { rmSync(zipPath); } catch {}

  try {
    execSync(
      `powershell -NoProfile -Command "Compress-Archive -Path '${patchedDir}\\*' -DestinationPath '${zipPath}' -Force"`,
      { stdio: 'pipe', timeout: 120000 }
    );
  } catch (e) {
    throw new Error(`重打包 zip 失败: ${e.message}`);
  }

  const buf = readFileSync(zipPath);

  // 清理临时 zip
  try { rmSync(zipPath); } catch {}

  return buf;
}

// ============================================================
// 5. importPackage — POST import 到悟空后端
// ============================================================

/**
 * 将 zip 包导入悟空后端。
 * @param {Buffer} zipBuffer        zip 文件 Buffer
 * @param {string} groupId          目标分组 id
 * @param {string} token            Bearer token
 * @param {object} [options]
 * @param {string}   [options.baseUrl]       自定义后端地址
 * @param {boolean}  [options.setStaticData] 是否设为静态数据（默认 false）
 * @param {string}   [options.filename]      上传文件名（默认 patched.zip）
 * @returns {Promise<object>} 后端响应 JSON
 */
export async function importPackage(zipBuffer, groupId, token, options = {}) {
  const base = options.baseUrl || BASE_URL;
  const setStaticData = options.setStaticData ?? false;
  const filename = options.filename || 'patched.zip';

  // 手工构建 multipart/form-data（避免引入第三方依赖）
  const boundary = '----WukongPatcher' + Date.now();
  const CRLF = '\r\n';

  // part 1: file
  const fileHeader = [
    `--${boundary}${CRLF}`,
    `Content-Disposition: form-data; name="file"; filename="${filename}"${CRLF}`,
    `Content-Type: application/zip${CRLF}${CRLF}`,
  ].join('');

  // part 2: setStaticData
  const staticPart = [
    `${CRLF}--${boundary}${CRLF}`,
    `Content-Disposition: form-data; name="setStaticData"${CRLF}${CRLF}`,
    `${setStaticData}`,
  ].join('');

  // part 3: groupId
  const groupPart = [
    `${CRLF}--${boundary}${CRLF}`,
    `Content-Disposition: form-data; name="groupId"${CRLF}${CRLF}`,
    `${groupId}`,
  ].join('');

  // 尾部
  const tail = `${CRLF}--${boundary}--${CRLF}`;

  const headerBuf = Buffer.from(fileHeader, 'utf8');
  const tailBuf   = Buffer.from(staticPart + groupPart + tail, 'utf8');
  const body      = Buffer.concat([headerBuf, zipBuffer, tailBuf]);

  const importUrl = base + 'unity/page/batch-import';
  const resp = await fetch(importUrl, {
    method: 'POST',
    headers: {
      'Authorization': 'Bearer ' + token,
      'Content-Type': `multipart/form-data; boundary=${boundary}`,
    },
    body,
  });

  const respText = await resp.text();
  let result;
  try {
    result = JSON.parse(respText);
  } catch {
    result = { raw: respText, status: resp.status };
  }

  if (!resp.ok) {
    throw new Error(`import 请求失败: HTTP ${resp.status} ${respText.slice(0, 500)}`);
  }
  if (result.hasError) {
    throw new Error(`import 后端报错: ${result.message || respText.slice(0, 500)}`);
  }

  return result;
}

// ============================================================
// 6. roundtrip — 串联全流程
// ============================================================

/**
 * 一键完成：导出模板 -> 解包 -> 打补丁 -> 重打包 -> 导入。
 *
 * @param {string} pageId   源模板页面 id
 * @param {object} patches  补丁描述（同 patchPageJson 的 patches 参数）
 * @param {string} groupId  目标分组 id
 * @param {string} token    Bearer token
 * @param {object} [options]
 * @param {string}   [options.baseUrl]       自定义后端地址
 * @param {boolean}  [options.setStaticData] 是否设为静态数据
 * @param {boolean}  [options.keepTempDir]   是否保留临时解包目录（调试用，默认 false）
 * @returns {Promise<object>} { importResult, newPageId, oldPageId, tempDir? }
 */
export async function roundtrip(pageId, patches, groupId, token, options = {}) {
  const fetchOpts = { baseUrl: options.baseUrl };

  // 1. 导出
  console.log('[package-patcher] 导出模板:', pageId);
  const zipBuffer = await exportTemplate(pageId, token, fetchOpts);
  console.log('[package-patcher] zip 大小:', zipBuffer.length, 'bytes');

  // 2. 解包
  const tempDir = join(tmpdir(), 'wk-roundtrip-' + randomUUID().slice(0, 8));
  console.log('[package-patcher] 解包到:', tempDir);
  unpackZip(zipBuffer, tempDir);

  try {
    // 3. 打补丁（groupId 写入 patches 以确保 pageJson 里也更新）
    const mergedPatches = { ...patches, groupId };
    const { oldPageId, newPageId } = patchPageJson(tempDir, mergedPatches);
    console.log('[package-patcher] 旧 pageId:', oldPageId, '-> 新 pageId:', newPageId);

    // 4. 重打包
    const patchedZip = repackZip(tempDir);
    console.log('[package-patcher] 重打包 zip:', patchedZip.length, 'bytes');

    // 5. 导入
    console.log('[package-patcher] 开始导入到分组:', groupId);
    const importResult = await importPackage(patchedZip, groupId, token, {
      baseUrl: options.baseUrl,
      setStaticData: options.setStaticData,
      filename: `patched_${newPageId}.zip`,
    });
    console.log('[package-patcher] 导入完成:', JSON.stringify(importResult).slice(0, 500));

    const result = { importResult, newPageId, oldPageId };
    if (options.keepTempDir) {
      result.tempDir = tempDir;
    }
    return result;
  } finally {
    // 清理临时目录（除非调试模式保留）
    if (!options.keepTempDir) {
      try { rmSync(tempDir, { recursive: true, force: true }); } catch {}
    }
  }
}
