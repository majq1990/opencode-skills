// 悟空自动登录：读本机凭证 → SM2 加密密码 → OAuth token → 缓存
// 凭证: ~/.wukong-cli/credentials.json  (不进 git, chmod 600)
// 缓存: ~/.wukong-cli/token-cache.json
//
// 用法:
//   node wk-login.mjs            # 登录拿 token（优先用未过期缓存）
//   node wk-login.mjs --force    # 强制重新登录
//   node wk-login.mjs --selftest # 本地 SM2 加密自检（不发网络，零风险）
//   node wk-login.mjs --print    # 只输出当前有效 token（供其他脚本 eval）
//
// 供其他脚本 import: getToken() 返回有效 token（自动刷新）

import { createHmac } from 'node:crypto';
import { readFileSync, writeFileSync, mkdirSync, existsSync, chmodSync } from 'node:fs';
import { homedir } from 'node:os';
import { join } from 'node:path';
import { sm2 } from 'sm-crypto';

const CFG_DIR = join(homedir(), '.wukong-cli');
// 可用环境变量覆盖凭证/缓存路径（只读探索账号走独立文件）
const CRED_FILE = process.env.WK_CRED || join(CFG_DIR, 'credentials.json');
const CACHE_FILE = process.env.WK_TOKEN_CACHE || join(CFG_DIR, 'token-cache.json');

const DEFAULTS = {
  baseUrl: 'http://wk.egova.com.cn:8042/wukong-backend',
  ak: 'ad13dec6216acac85e91562821bf8dda',
  appId: 'wukong',
};

function loadCreds() {
  if (!existsSync(CRED_FILE)) {
    throw new Error(`凭证文件不存在: ${CRED_FILE}\n请先创建（参考 wk-login.mjs 顶部说明），填 username/password`);
  }
  const c = JSON.parse(readFileSync(CRED_FILE, 'utf-8'));
  return { ...DEFAULTS, ...c };
}

function randomStr(n) { return Math.random().toString(32).substring(2, 2 + n); }
function encodeParam(v) {
  return encodeURIComponent(String(v)).replace(/%40/g, '@').replace(/\+/g, '%2B');
}

function sign(ak, method, pathname, params, body) {
  const timestamp = String(Math.floor(Date.now() / 1000));
  const nonce = 'node_' + randomStr(10);
  const all = { ...params, timestamp, nonce };
  const paramStr = Object.keys(all).sort().map(k => `${k}=${encodeParam(all[k])}`).join('&');
  let signStr = `${pathname}?${paramStr}`;
  if (method === 'POST' && body && body.length < 128 * 1024) signStr += encodeURIComponent(body);
  const signature = createHmac('sha1', ak).update(signStr).digest('hex');
  return { timestamp, nonce, signature };
}

async function signedFetch(cfg, method, apiPath, body) {
  const pathname = `/wukong-backend/${apiPath}`;
  const bodyStr = body ? JSON.stringify(body) : '';
  const { timestamp, nonce, signature } = sign(cfg.ak, method, pathname, {}, bodyStr);
  const qs = new URLSearchParams({ timestamp, nonce, signature }).toString();
  const url = `${cfg.baseUrl}/${apiPath}?${qs}`;
  const opts = {
    method,
    headers: { 'Content-Type': 'application/json;charset=UTF-8', 'App-Id': cfg.appId },
    signal: AbortSignal.timeout(15000),
  };
  if (method === 'POST' && bodyStr) opts.body = bodyStr;
  const r = await fetch(url, opts);
  const text = await r.text();
  let json; try { json = JSON.parse(text); } catch { json = null; }
  return { status: r.status, json, text };
}

// SM2 加密密码（不带 04 前缀，C1C3C2，匹配悟空前端）
function encryptPassword(plain, publicKeyHex) {
  // sm-crypto doEncrypt 默认 cipherMode=1 (C1C3C2)，输出不带 04
  // 公钥若带 04 前缀也接受
  return sm2.doEncrypt(plain, publicKeyHex, 1);
}

export async function login(force = false) {
  const cfg = loadCreds();
  if (!cfg.username || !cfg.password) {
    throw new Error(`凭证 ${CRED_FILE} 缺 username/password`);
  }
  // 1) 公钥
  const pk = await signedFetch(cfg, 'GET', 'oauth/extras/public-key');
  if (pk.json?.hasError || !pk.json?.result) throw new Error(`取公钥失败: ${pk.text.slice(0, 200)}`);
  const publicKey = pk.json.result;
  // 2) 算法（确认 sm2）
  const alg = await signedFetch(cfg, 'GET', 'oauth/extras/alg');
  const algName = alg.json?.result || 'sm2';
  if (algName !== 'sm2') console.error(`⚠️ 算法非 sm2: ${algName}（当前脚本只实现 sm2）`);
  // 3) 加密密码 + 换 token
  const encPwd = encryptPassword(cfg.password, publicKey);
  const tok = await signedFetch(cfg, 'POST', 'oauth/extras/token', {
    grant_type: 'password', username: cfg.username, password: encPwd,
  });
  // OAuth 标准返回 {access_token, expires_in, ...} 或 {hasError,result}
  const body = tok.json || {};
  const accessToken = body.access_token || body.accessToken || body.result?.access_token || body.result;
  if (!accessToken || typeof accessToken !== 'string') {
    const err = body.error_description || body.error || body.message || tok.text.slice(0, 300);
    throw new Error(`登录失败: ${err}`);
  }
  const expiresIn = Number(body.expires_in || body.expiresIn || 7200);
  const cache = {
    token: accessToken,
    username: cfg.username,
    fetchedAt: Date.now(),
    expiresAt: Date.now() + Math.max(60, expiresIn - 120) * 1000, // 提前 2 分钟视为过期
  };
  mkdirSync(CFG_DIR, { recursive: true });
  writeFileSync(CACHE_FILE, JSON.stringify(cache, null, 2), 'utf-8');
  try { chmodSync(CACHE_FILE, 0o600); } catch {}
  return cache;
}

// 对外：拿有效 token（缓存优先，过期或 force 时重登）
export async function getToken(force = false) {
  if (!force && existsSync(CACHE_FILE)) {
    try {
      const c = JSON.parse(readFileSync(CACHE_FILE, 'utf-8'));
      if (c.token && c.expiresAt > Date.now()) return c.token;
    } catch {}
  }
  const c = await login(force);
  return c.token;
}

// 本地加密自检：不发网络，验证 SM2 加密格式（用真实抓包公钥）
function selftest() {
  const SAMPLE_PK = '04ffa798f0fb5c717e765c6dacf8cacb5002b3eefb3277eee1d6eb3ab8c0352e94337c9556204f5abc95ab4a18c4de5b1d3daad438095e27c7208de7f4dc946b63';
  const plain = 'Egova@123';
  const enc = encryptPassword(plain, SAMPLE_PK);
  const expectLen = 2 * (64 + 32 + plain.length); // C1(64B)+C3(32B)+C2(明文长度)
  console.log('明文:', plain, `(${plain.length} 字节)`);
  console.log('密文:', enc);
  console.log('密文长度:', enc.length, 'hex, 期望:', expectLen, enc.length === expectLen ? '✅ 格式匹配' : '❌ 不匹配');
  console.log('开头 04?:', enc.startsWith('04') ? '是(异常)' : '否 ✅ 与悟空抓包一致');
  // 回环：用临时密钥对验证 encrypt/decrypt 逻辑通
  const kp = sm2.generateKeyPairHex();
  const e2 = sm2.doEncrypt(plain, kp.publicKey, 1);
  const d2 = sm2.doDecrypt(e2, kp.privateKey, 1);
  console.log('SM2 加解密回环:', d2 === plain ? '✅' : '❌', d2);
}

// CLI
if (process.argv[1]?.endsWith('wk-login.mjs')) {
  const arg = process.argv[2];
  if (arg === '--selftest') {
    selftest();
  } else if (arg === '--print') {
    try { console.log(await getToken(false)); }
    catch (e) { console.error(e.message); process.exit(1); }
  } else {
    try {
      const c = await login(arg === '--force');
      console.log('✅ 登录成功');
      console.log('token:', c.token.slice(0, 12) + '...');
      console.log('有效至:', new Date(c.expiresAt).toLocaleString());
      console.log('缓存:', CACHE_FILE);
    } catch (e) {
      console.error('❌', e.message);
      process.exit(1);
    }
  }
}
