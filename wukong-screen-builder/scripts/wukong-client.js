/* ============================================================
 * 悟空大屏落地引擎 —— 浏览器内注入脚本（IIFE，挂 window.WK）
 * ------------------------------------------------------------
 * 用法：在已登录的悟空编辑器页面（含 webpackJsonp 的页面）里，
 *       用 playwright browser_evaluate / javascript_tool 注入本文件全文，
 *       然后调用 window.WK.* 方法。
 *
 * 原理：复用页面里"带签名拦截器"的 axios 实例（webpack 模块 54fa.axios），
 *       签名 / JSESSIONID+token Cookie / nonce / timestamp 全部由该实例自动处理，
 *       无需自己实现 HMAC-SHA1。
 *
 * 安全：所有"写端点"默认 dryRun=true —— 只回显将要发送的请求，不真正落库。
 *       真正落地必须显式传 {dryRun:false}，且应在用户确认后调用。
 * ============================================================ */
(function () {
  'use strict';

  var WK = (window.WK = window.WK || {});
  var _axios = null;

  /* ---------- 1. 取签名 axios 实例 ---------- */
  WK.getAxios = function () {
    if (_axios) return _axios;
    // webpackJsonp hack 拿 __webpack_require__
    if (!window.__wreq) {
      try {
        window.webpackJsonp.push([
          ['wk-probe'],
          { 'wk-probe': function (m, e, r) { window.__wreq = r; } },
          [['wk-probe']],
        ]);
      } catch (e) { /* 某些构建用 webpackChunk，下面回退 */ }
    }
    var req = window.__wreq;
    // 首选已知模块 id 54fa
    if (req) {
      try {
        var mod = req('54fa');
        if (mod && (mod.axios || mod.default)) { _axios = mod.axios || mod.default; return _axios; }
      } catch (e) { /* 模块 id 可能随构建变化，回退扫缓存 */ }
    }
    // 回退：扫 require.c 模块缓存，找带签名拦截器（拦截器源码含 App-Id/signature/nonce）的 axios 实例
    if (req && req.c) {
      for (var k in req.c) {
        try {
          var ex = req.c[k] && req.c[k].exports;
          var cand = ex && (ex.axios || ex.default || ex);
          if (cand && cand.interceptors && cand.interceptors.request) {
            var handlers = cand.interceptors.request.handlers || [];
            for (var i = 0; i < handlers.length; i++) {
              var src = (handlers[i].fulfilled || '').toString();
              if (/App-Id|signature|nonce/.test(src)) { _axios = cand; return _axios; }
            }
          }
        } catch (e) {}
      }
    }
    throw new Error('未找到带签名拦截器的 axios 实例；确认在悟空编辑器页面且页面已加载 webpack 模块。');
  };

  /* ---------- 2. 请求封装 ----------
   * 54fa 实例的 response 拦截器已把响应解包为 {hasError,result,message,tag,totalCount}。
   * baseURL = /wukong-backend，所以 path 传 "unity/xxx" 即可（前面不加 /wukong-backend）。 */
  function unwrap(r) {
    // 拦截器通常直接返回解包后的对象；个别返回 axios response，做兼容
    var d = (r && r.data && ('hasError' in r.data)) ? r.data : r;
    if (d && d.hasError) throw new Error('悟空后端报错: ' + (d.message || JSON.stringify(d).slice(0, 200)));
    return d;
  }
  WK.get = function (path, params) {
    return WK.getAxios().get(path, { params: params || {} }).then(unwrap);
  };
  WK.post = function (path, body) {
    return WK.getAxios().post(path, body).then(unwrap);
  };
  WK.put = function (path, body) {
    return WK.getAxios().put(path, body).then(unwrap);
  };

  /* ---------- 3. 读端点（侦察已验证形状，可放心调） ---------- */
  WK.read = {
    pageDetail:   function (pageId) { return WK.get('unity/page/detail/' + pageId); },
    cardTree:     function (pageId) { return WK.get('unity/page-card/level-tree/' + pageId); },
    cardData:     function (dataId) { return WK.get('unity/card-data/' + dataId); },
    pageHook:     function (pageId) { return WK.get('unity/page-hook/pageId/' + pageId); },
    interactions: function (pageId) { return WK.post('unity/interaction/chain', { pageId: pageId }); },
    componentLib: function ()       { return WK.get('unity/page/category/card-tree'); },
    dataTemplates:function (groupId){ return WK.post('unity/data-template/page', { condition: { groupId: groupId, type: '1', status: 1 }, paging: { pageIndex: 1, pageSize: 100 }, sorts: [] }); },
  };

  /* ---------- 4. 写端点（★ body 形状需首次落地时用真实抓包校准 ★）
   * 侦察阶段遵守"只读不写"安全约束，未实际触发保存，故下列 body 字段名以
   * page-detail/level-tree 的读结构反推，首次真落地前务必：
   *   (a) 在编辑器里手工做一次对应操作，开 network 抓真实请求 body；
   *   (b) 用抓到的形状校正这里的字段，再去掉 dryRun。 */
  function maybeSend(label, method, path, body, opts) {
    opts = opts || {};
    var dryRun = opts.dryRun !== false; // 默认 true
    if (dryRun) {
      console.log('[WK dryRun] ' + label + ' -> ' + method + ' ' + path, body);
      return Promise.resolve({ dryRun: true, label: label, method: method, path: path, body: body });
    }
    return WK[method.toLowerCase()](path, body);
  }
  WK.write = {
    // 1. 新建页面：meta = {name,width,height,groupId,type:'PAGE',kind:'PAGE',...}
    newPage:     function (meta, opts)        { return maybeSend('newPage', 'POST', 'unity/page/', meta, opts); },
    editCheck:   function (pageId, opts)      { return maybeSend('editCheck', 'POST', 'unity/page/edit-check', { pageId: pageId }, opts); },
    // 2. 加单个组件：card = 单个 pageCard（base.code + x/y/width/height + style + data）
    addCard:     function (card, opts)        { return maybeSend('addCard', 'POST', 'unity/page-card', card, opts); },
    // 2b. autosave 单卡全量
    saveCard:    function (cardId, card, opts){ return maybeSend('saveCard', 'POST', 'unity/page-card/' + cardId, card, opts); },
    // 2c. 批量改：cards = pageCard 对象数组（验证：updateModuleLayers 调此端点传卡片数组）
    batchModify: function (cards, opts)       { return maybeSend('batchModify', 'POST', 'unity/page-card/batch-modify', cards, opts); },
    // 3. 数据绑定：data = {request,extractor,dataMapping,refresh,cardData,...}（现有数据对接能力产出）
    saveCardData:  function (data, opts)         { return maybeSend('saveCardData', 'POST', 'unity/card-data', data, opts); },
    updateCardData:function (dataId, data, opts) { return maybeSend('updateCardData', 'PUT', 'unity/card-data/' + dataId, data, opts); },
    // 3b. 测试运行：跑一次接口取真数据
    directServe:   function (dataId, opts)       { return maybeSend('directServe', 'POST', 'unity/card-data/' + dataId + '/direct/serve', {}, opts); },
    // 5. 交互链：chain = 页面级交互对象（见 references/交互与脚本.md）
    saveInteraction: function (chain, opts)      { return maybeSend('saveInteraction', 'POST', 'unity/interaction/chain', chain, opts); },
    // 6. 页面脚本：hook = {pageId,preScript,afterScript,globalScript,globalScriptJson}
    savePageHook:    function (hook, opts)       { return maybeSend('savePageHook', 'POST', 'unity/page-hook', hook, opts); },
  };

  /* ---------- 5. 高层编排：按"增量分层"顺序落地一份大屏草案 ----------
   * draft = { page:{meta}, cards:[...], cardData:[...], interactions:[...], pageHook:{...} }
   * 默认 dryRun，会按顺序回显每一步将发的请求；确认后传 {dryRun:false} 真落地。
   * 真落地时各步依赖前序返回的 id（pageId / cardId / dataId），故串行 await。 */
  WK.land = async function (draft, opts) {
    opts = opts || {};
    var log = [];
    var step = function (name, p) { return p.then(function (r) { log.push({ step: name, ok: true, r: r }); return r; }); };

    // step1 新建页面
    var pageRes = await step('newPage', WK.write.newPage(draft.page && draft.page.meta, opts));
    var pageId = (pageRes && pageRes.result && pageRes.result.id) || (draft.page && draft.page.meta && draft.page.meta.id);

    // step2 组件：优先批量
    if (draft.cards && draft.cards.length) {
      var cards = draft.cards.map(function (c) { return Object.assign({ pageId: pageId }, c); });
      await step('batchModify', WK.write.batchModify(cards, opts));
    }
    // step3 数据绑定
    for (var i = 0; draft.cardData && i < draft.cardData.length; i++) {
      await step('saveCardData#' + i, WK.write.saveCardData(draft.cardData[i], opts));
    }
    // step5 交互
    for (var j = 0; draft.interactions && j < draft.interactions.length; j++) {
      var inter = Object.assign({ pageId: pageId }, draft.interactions[j]);
      await step('saveInteraction#' + j, WK.write.saveInteraction(inter, opts));
    }
    // step6 页面脚本
    if (draft.pageHook) {
      await step('savePageHook', WK.write.savePageHook(Object.assign({ pageId: pageId }, draft.pageHook), opts));
    }
    return { pageId: pageId, dryRun: opts.dryRun !== false, log: log };
  };

  console.log('[WK] 落地引擎已就绪。读: WK.read.* / 写(默认dryRun): WK.write.* / 编排: WK.land(draft,{dryRun:false})');
  return WK;
})();
