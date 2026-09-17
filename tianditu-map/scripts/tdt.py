#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""天地图 API 命令行工具：地理编码 / 逆地理编码 / POI搜索 / 批量编码

零第三方依赖（仅标准库）。key 池来自同目录上级 keys.json，
只启用 type=server 的 key；TIANDITU_MAP_KEYS（逗号分隔）可追加临时 key。
"""
import argparse
import csv
import io
import json
import os
import re
import sys
import threading
import time
import urllib.parse
import urllib.request

BASE = "http://api.tianditu.gov.cn"
HERE = os.path.dirname(os.path.abspath(__file__))
KEYS_FILE = os.path.join(HERE, "..", "keys.json")                  # 公开范本（环境变量引用名）
KEYS_LOCAL = os.path.join(HERE, "..", "config", "keys.local.json")  # 本机私有（真实 key，.gitignore）

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


# ---------------- key 池 ----------------

class KeyPool:
    """多 key 轮询，每 key 独立最小间隔限速（线程安全）。"""

    def __init__(self, tps_per_key=15.0):
        self.tps = tps_per_key
        self.keys = []          # [(key, min_interval, last_ts)]
        self._idx = 0
        self._lock = threading.Lock()
        self._load()
        if not self.keys:
            sys.exit("错误：keys.json 无 type=server 的 key，且未设置 TIANDITU_MAP_KEYS/TIANDITU_API_KEY")

    def _load(self):
        # 加载顺序（本机私有优先，其次环境变量，最后公开范本）：
        # 1) config/keys.local.json（真实 key，不入库）  2) TIANDITU_MAP_KEYS/TIANDITU_API_KEY
        # 3) keys.json（公开范本，仅环境变量引用名，无明文 key）
        extra = []
        env_multi = os.getenv("TIANDITU_MAP_KEYS")
        if env_multi:
            extra += [k.strip() for k in env_multi.split(",") if k.strip()]
        env_single = os.getenv("TIANDITU_API_KEY")
        if env_single:
            extra.append(env_single.strip())
        conf = {"keys": []}
        for path in (KEYS_LOCAL, KEYS_FILE):
            try:
                with open(path, encoding="utf-8") as f:
                    conf = json.load(f)
                    if conf.get("keys"):
                        break
            except (FileNotFoundError, json.JSONDecodeError):
                continue
        self.tps = float(conf.get("default_tps_per_key", self.tps))
        for item in conf.get("keys", []):
            if item.get("type") == "server":
                self.keys.append([item["key"], 1.0 / self.tps, 0.0])
        for k in extra:
            if not any(k == row[0] for row in self.keys):
                self.keys.append([k, 1.0 / self.tps, 0.0])

    def acquire(self):
        """轮询取一个 key，必要时按该 key 的限速等待。"""
        with self._lock:
            row = self.keys[self._idx % len(self.keys)]
            self._idx += 1
            wait = row[2] + row[1] - time.monotonic()
            row[2] = max(row[2], time.monotonic()) + (0 if wait > 0 else 0)
            if wait > 0:
                row[2] = time.monotonic() + wait
                return row[0], wait
            row[2] = time.monotonic()
            return row[0], 0.0

    def disable(self, key, reason=""):
        """摘除坏 key（权限错误/403），防止拖累批量任务。"""
        with self._lock:
            before = len(self.keys)
            self.keys = [r for r in self.keys if r[0] != key]
            if len(self.keys) < before:
                print(f"⚠️ key {key[:8]}… 已从池中摘除：{reason}", file=sys.stderr, flush=True)
            if not self.keys:
                sys.exit("错误：key 池已空（所有 key 均无效）")

    def __len__(self):
        return len(self.keys)


POOL = None


def get_pool(tps=None):
    global POOL
    if POOL is None:
        POOL = KeyPool(tps) if tps else KeyPool()
    return POOL


# ---------------- HTTP ----------------

def _get(url, timeout=15):
    req = urllib.request.Request(url, headers={"User-Agent": "tianditu-map-skill/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:          # 403 等也带 JSON body
        body = e.read().decode("utf-8", errors="replace")
        if body:
            return body
        raise


def api_get(path, params, retries=4):
    """带 key 轮询 + 429/瞬时错误指数退避 + 坏key自动摘除的 GET。返回解析后的 dict。"""
    pool = get_pool()
    last = None
    for attempt in range(retries):
        key, wait = pool.acquire()
        if wait > 0:
            time.sleep(wait)
        qs = urllib.parse.urlencode(params)
        url = f"{BASE}{path}?{qs}&tk={key}"
        try:
            data = json.loads(_get(url))
        except Exception as e:                     # 网络瞬时错误
            last = f"network: {e}"
            time.sleep(min(2 ** attempt, 8))
            continue
        if isinstance(data, dict):
            code = str(data.get("code", ""))
            msg = str(data.get("msg", ""))
            if code == "301012" or "权限" in msg:   # key 类型不匹配
                pool.disable(key, f"{code} {msg}")
                continue
            if str(data.get("status")) in ("429",) or "fast" in msg:
                last = "429 rate limited"
                time.sleep(min(2 ** attempt * 1.5, 10))
                continue
        return data
    return {"status": "error", "error": last or "unknown"}


# ---------------- 业务接口 ----------------

def geocode(addr):
    """地址 → {lon, lat, score, level}；无命中返回 None。"""
    ds = json.dumps({"keyWord": addr}, ensure_ascii=False)
    r = api_get("/geocoder", {"ds": ds})
    if r.get("status") == "0" and r.get("location"):
        loc = r["location"]
        return {"lon": float(loc["lon"]), "lat": float(loc["lat"]),
                "score": loc.get("score"), "level": loc.get("level")}
    return None


def reverse(lon, lat):
    """坐标 → {formatted_address, province, city, county, town, road, poi...}"""
    post = json.dumps({"lon": lon, "lat": lat, "ver": "1"}, ensure_ascii=False)
    r = api_get("/geocoder", {"postStr": post, "type": "geocode"})
    res = r.get("result")
    if not res:
        return None
    comp = res.get("addressComponent", {})
    return {"formatted_address": res.get("formatted_address"),
            "province": comp.get("province"), "city": comp.get("city"),
            "county": comp.get("county"), "town": comp.get("town"),
            "road": comp.get("road"), "address": comp.get("address"),
            "poi": comp.get("poi")}


def search(keyword, query_type="2", map_bound=None, level="15",
           point_lonlat=None, radius=None, specify=None, polygon=None,
           count=10, start=0):
    """v2/search 地名搜索。queryType: 2视野内/3周边/10多边形/12行政区划区域"""
    post = {"keyWord": keyword, "queryType": str(query_type),
            "count": str(count), "start": str(start)}
    if query_type in ("2", "1"):
        post["level"] = str(level)
        post["mapBound"] = map_bound or "73.0,3.0,136.0,54.0"
    if query_type == "3":
        post["pointLonlat"] = point_lonlat
        post["queryRadius"] = str(radius)
    if query_type == "10":
        post["polygon"] = polygon
    if query_type == "12":
        post["specify"] = str(specify)
    r = api_get("/v2/search", {"postStr": json.dumps(post, ensure_ascii=False), "type": "query"})
    if isinstance(r.get("pois"), list):
        out = []
        for p in r["pois"]:
            lonlat = (p.get("lonlat") or "").split(",")
            out.append({"name": p.get("name"), "address": p.get("address"),
                        "lon": float(lonlat[0]) if len(lonlat) == 2 else None,
                        "lat": float(lonlat[1]) if len(lonlat) == 2 else None,
                        "phone": p.get("phone"), "poiType": p.get("poiType")})
        return {"count": r.get("count"), "pois": out}
    return r


# ---------------- 批量地理编码 ----------------

B_NUM = re.compile(r"^\d+$")


def building_key(addr):
    """楼栋级去重 key：仅去掉末尾一段纯数字房号，保留楼号/单元号。"""
    parts = re.split(r"[_\-]", addr)
    if len(parts) > 1 and B_NUM.match(parts[-1]):
        parts.pop()
    return "-".join(parts)


def _geocode_shard(items, prefix, ckpt_file, out, stats, stop_flag):
    """单 key 顺序处理一个分片；items: [(key, addr), ...]"""
    done = {}
    if ckpt_file and os.path.exists(ckpt_file):
        try:
            with open(ckpt_file, encoding="utf-8") as f:
                done = json.load(f)
        except Exception:
            done = {}
    n = len(items)
    for i, (bkey, addr) in enumerate(items):
        if bkey in done and done[bkey]:
            continue
        if stop_flag.get("stop"):
            break
        full = prefix + addr if prefix else addr
        res = geocode(full)
        done[bkey] = res
        with stats["lock"]:
            stats["done"] += 1
            if res:
                stats["hit"] += 1
            cur = stats["done"]
            if cur % 50 == 0 or cur == stats["total"]:
                print(f"  进度 {cur}/{stats['total']}  命中 {stats['hit']}", flush=True)
        if ckpt_file and (i % 100 == 99 or i == n - 1):
            _save_ckpt(ckpt_file, done)
    if ckpt_file:
        _save_ckpt(ckpt_file, done)
    out.update(done)


def _save_ckpt(path, data):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)
    os.replace(tmp, path)


def merge_ckpts(prefix):
    """合并所有 prefix 开头的 ckpt：有坐标的值优先覆盖 None。"""
    merged = {}
    d = os.path.dirname(os.path.abspath(prefix)) or "."
    base = os.path.basename(prefix)
    for fn in os.listdir(d):
        if fn.startswith(base) and fn.endswith(".json"):
            with open(os.path.join(d, fn), encoding="utf-8") as f:
                for k, v in json.load(f).items():
                    if v is not None or k not in merged:
                        merged[k] = v
    return merged


def batch_geocode(input_file, addr_col, output, prefix="", workers=None,
                  ckpt_prefix=None, encoding="utf-8-sig", dedup=True):
    rows = list(csv.DictReader(open(input_file, encoding=encoding)))
    addrs = [(r[addr_col] or "").strip() for r in rows]
    keys = []
    seen = set()
    for a in addrs:
        if not a:
            continue
        k = building_key(a) if dedup else a
        if k not in seen:
            seen.add(k)
            keys.append((k, a))
    print(f"输入 {len(rows)} 行，唯一{'楼栋' if dedup else '地址'} key {len(keys)} 个", flush=True)

    pool = get_pool()
    nk = len(pool)
    workers = workers or nk
    shards = [keys[i::nk] for i in range(nk)]
    ckpt_prefix = ckpt_prefix or os.path.join(
        os.path.dirname(os.path.abspath(output)) or ".", "tdt_batch_ckpt")
    stats = {"done": 0, "hit": 0, "total": len(keys), "lock": threading.Lock()}
    stop = {}
    threads = []
    results = {}
    for i, shard in enumerate(shards):
        if not shard:
            continue
        t = threading.Thread(target=_geocode_shard, daemon=True,
                              args=(shard, prefix, f"{ckpt_prefix}_s{i}.json",
                                    results, stats, stop))
        t.start()
        threads.append(t)
    for t in threads:
        t.join()

    miss = [k for k, _ in keys if results.get(k) is None]
    # 写回
    fieldnames = list(rows[0].keys()) if rows else []
    for col in ("lon", "lat", "score", "level"):
        if col not in fieldnames:
            fieldnames.append(col)
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=fieldnames)
    w.writeheader()
    for r, a in zip(rows, addrs):
        row = dict(r)
        res = results.get(building_key(a) if dedup else a)
        if res:
            row["lon"], row["lat"] = res["lon"], res["lat"]
            row["score"], row["level"] = res.get("score"), res.get("level")
        elif row.get("lon") in (None, ""):
            row["lon"] = row["lat"] = ""
        w.writerow(row)
    with open(output, "w", encoding=encoding, newline="") as f:
        f.write(buf.getvalue())
    print(f"完成：{stats['hit']}/{len(keys)} 命中；未命中 {len(miss)}；输出 {output}", flush=True)
    # 生成【待复核】复核清单：坐标产物默认需人工核验后才可对外回写（认证红线：AI输出未核验即发送）
    review = output + ".review.md"
    with open(review, "w", encoding="utf-8") as f:
        f.write(f"# 地理编码产物复核清单（【待复核】）\n\n"
                f"- 生成时间：{time.strftime('%Y-%m-%d %H:%M:%S')}\n"
                f"- 输入行数：{len(rows)}，唯一 key：{len(keys)}，命中：{stats['hit']}，未命中：{len(miss)}\n"
                f"- 坐标精度：小区/楼栋级（天地图能力边界），非入户级\n"
                f"- 复核项：\n"
                f"  1. 随机抽 10 条，与天地图 geocode 单条复测比对\n"
                f"  2. 确认经纬度在目标城市合理范围（如银川 106.0~107.0 / 38.0~39.0）\n"
                f"  3. 未命中地址确认是否需人工补地址\n"
                f"  - 复核后如需写库，使用 `apply-db --confirm \"确认写入\"`\n")
    print(f"⚠️【待复核】产物已生成，复核清单：{review}", flush=True)
    if miss:
        mf = output + ".miss.txt"
        open(mf, "w", encoding="utf-8").write("\n".join(dict(keys)[k] for k in miss))
        print(f"未命中地址已写入 {mf}", flush=True)
    return results


# ---------------- 小区爬取 ----------------

DEFAULT_KW = ["小区", "花园", "家园", "苑", "公寓", "住宅", "宿舍", "里", "园", "府"]


def _grid_cells(bbox, size):
    """把 bbox [x1,y1,x2,y2] 切成 size°×size° 网格，返回每个格的 bounds 字符串。"""
    x1, y1, x2, y2 = bbox
    cols = max(1, int((x2 - x1) / size) + 1)
    rows = max(1, int((y2 - y1) / size) + 1)
    cells = []
    for r in range(rows):
        for c in range(cols):
            bx1 = x1 + c * size
            by1 = y1 + r * size
            bx2 = min(bx1 + size, x2)
            by2 = min(by1 + size, y2)
            cells.append(f"{bx1},{by1},{bx2},{by2}")
    return cells


def _search_cell(keyword, cell_bound, count=300, start=0, level="18"):
    """视野内搜索一格；level=18 接近小区级。返回 (count, pois_raw)。"""
    r = search(keyword, query_type="2", map_bound=cell_bound, level=level,
               count=count, start=start)
    if isinstance(r, dict) and isinstance(r.get("pois"), list):
        return int(r.get("count", 0)), r["pois"]
    return 0, []


def crawl_communities(bbox, out_prefix, keywords=None, grid_size=0.05,
                      level="18", count=300, max_depth=2):
    """遍历 bbox 网格爬小区 POI；输出 CSV + GeoJSON Point。
    bbox: 'x1,y1,x2,y2'。单格命中>=count 时递归切细（最多 max_depth 层）。"""
    bbox = [float(v) for v in bbox.split(",")]
    keywords = keywords or DEFAULT_KW
    seen = {}          # key -> poi
    stats = {"req": 0, "hit_cells": 0}

    def _dedup_key(p):
        if p.get("lon") is not None and p.get("lat") is not None:
            return (p.get("name"), round(p["lon"], 4), round(p["lat"], 4))
        return None

    def _scan(cell, depth):
        for kw in keywords:
            start = 0
            while True:
                cnt, pois = _search_cell(kw, cell, count, start, level)
                stats["req"] += 1
                with stats_lock:
                    if stats["req"] % 20 == 0:
                        print(f"  已发 {stats['req']} 请求，小区 {len(seen)}", flush=True)
                new = 0
                for p in pois:
                    k = _dedup_key(p)
                    if k and k not in seen:
                        seen[k] = p
                        new += 1
                if cnt < count or len(pois) < count:
                    break
                start += count
                if start >= 300:          # v2 start 上限
                    break
            # 单格单关键词满载(>=count)且未到底 → 递归切细
            if cnt >= count and depth < max_depth and len(pois) >= count:
                x1, y1, x2, y2 = [float(v) for v in cell.split(",")]
                mx, my = (x1 + x2) / 2, (y1 + y2) / 2
                for sub in [f"{x1},{y1},{mx},{my}", f"{mx},{y1},{x2},{my}",
                            f"{x1},{my},{mx},{y2}", f"{mx},{my},{x2},{y2}"]:
                    _scan(sub, depth + 1)

    stats_lock = threading.Lock()
    cells = _grid_cells(bbox, grid_size)
    print(f"网格 {grid_size}° → {len(cells)} 格 × {len(keywords)} 关键词", flush=True)
    for cell in cells:
        before = len(seen)
        _scan(cell, 0)
        if len(seen) > before:
            stats["hit_cells"] += 1

    # 写 CSV + GeoJSON
    csv_path = out_prefix + ".csv"
    geo_path = out_prefix + ".geojson"
    with open(csv_path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["name", "address", "lon", "lat", "poiType", "phone"])
        for p in seen.values():
            w.writerow([p.get("name"), p.get("address"),
                        p.get("lon", ""), p.get("lat", ""),
                        p.get("poiType"), p.get("phone", "")])
    feats = []
    for p in seen.values():
        if p.get("lon") is None or p.get("lat") is None:
            continue
        feats.append({"type": "Feature",
                      "geometry": {"type": "Point", "coordinates": [p["lon"], p["lat"]]},
                      "properties": {"name": p.get("name"), "address": p.get("address"),
                                      "poiType": p.get("poiType")}})
    with open(geo_path, "w", encoding="utf-8") as f:
        json.dump({"type": "FeatureCollection", "features": feats}, f, ensure_ascii=False)
    print(f"完成：{len(seen)} 个小区，{stats['req']} 次请求，命中格 {stats['hit_cells']}", flush=True)
    print(f"CSV: {csv_path}\nGeoJSON: {geo_path}", flush=True)
    return csv_path, geo_path


# ---------------- 地图可视化 ----------------

def make_map(input_file, output_html, encoding="utf-8-sig", title="小区地图"):
    """读 CSV/GeoJSON → 生成 Leaflet HTML（天地图瓦片底图+markercluster聚合打点）。"""
    feats = []
    if input_file.lower().endswith(".geojson"):
        data = json.load(open(input_file, encoding="utf-8"))
        feats = data.get("features", [])
    else:
        rows = list(csv.DictReader(open(input_file, encoding=encoding)))
        for r in rows:
            try:
                lon, lat = float(r["lon"]), float(r["lat"])
            except (KeyError, ValueError):
                continue
            feats.append({"type": "Feature", "geometry": {"type": "Point", "coordinates": [lon, lat]},
                          "properties": {"name": r.get("name", ""), "address": r.get("address", "")}})
    pool = get_pool()
    tk = pool.keys[0][0] if pool.keys else ""
    geojson = json.dumps({"type": "FeatureCollection", "features": feats}, ensure_ascii=False)

    html = f"""<!DOCTYPE html><html lang="zh"><head><meta charset="utf-8">
<title>{title}</title>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
<link rel="stylesheet" href="https://unpkg.com/leaflet.markercluster@1.5.3/dist/MarkerCluster.css"/>
<style>html,body,#map{{height:100%;margin:0}}.info{{position:absolute;z-index:1000;top:10px;left:55px;background:#fff;padding:6px 10px;border-radius:4px;font:14px sans-serif;box-shadow:0 1px 5px rgba(0,0,0,.3)}}</style>
</head><body>
<div id="map"></div>
<div class="info">{title} · {len(feats)} 个点位 · 滚轮缩放/点击聚合展开</div>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script src="https://unpkg.com/leaflet.markercluster@1.5.3/dist/leaflet.markercluster.js"></script>
<script>
const tk="{tk}";
const map=L.map('map').setView([38.48,106.23],12);
L.tileLayer('http://t{{s}}.tianditu.gov.cn/vec_w/wmts?SERVICE=WMTS&REQUEST=GetTile&VERSION=1.0.0&LAYER=vec&STYLE=default&TILEMATRIXSET=w&FORMAT=tiles&TILEMATRIX={{z}}&TILEROW={{y}}&TILECOL={{x}}&tk='+tk,{{subdomains:'01234567',maxZoom:18,attribution:'天地图'}}).addTo(map);
L.tileLayer('http://t{{s}}.tianditu.gov.cn/cva_w/wmts?SERVICE=WMTS&REQUEST=GetTile&VERSION=1.0.0&LAYER=cva&STYLE=default&TILEMATRIXSET=w&FORMAT=tiles&TILEMATRIX={{z}}&TILEROW={{y}}&TILECOL={{x}}&tk='+tk,{{subdomains:'01234567',maxZoom:18}}).addTo(map);
const data={geojson};
const cluster=L.markerClusterGroup();
const bounds=[];
const polygons=[];
data.features.forEach(f=>{{
  const geom=f.geometry;
  const p=f.properties||{{}};
  if(geom.type==='Polygon'&&geom.coordinates?.length){{
    const pts=geom.coordinates[0].map(c=>[c[1],c[0]]);
    const poly=L.polygon(pts,{{color:'#f06',weight:2,fillColor:'#f06',fillOpacity:0.15}}).bindPopup('<b>'+(p.name||'')+'</b><br>'+p.level||'');
    polygons.push(poly);bounds.push(pts);
  }}else{{
    const[lon,lat]=geom.coordinates;const m=L.marker([lat,lon]).bindPopup('<b>'+(p.name||'')+'</b><br>'+(p.address||''));
    cluster.addLayer(m);bounds.push([lat,lon]);
  }}
}});
if(polygons.length)polygons.forEach(p=>p.addTo(map));
map.addLayer(cluster);
if(bounds.length)map.fitBounds(bounds,{{maxZoom:14}});
else if(polygons.length)map.fitBounds(bounds,{{maxZoom:14}});
</script></body></html>"""
    with open(output_html, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"地图已生成：{output_html}（{len(feats)} 点位）", flush=True)
    return output_html


# ---------------- 写库人工门禁（apply-db） ----------------

_IDENT = r"^[A-Za-z0-9_\.\"]+$"


def apply_db(csv_file, table, key_cols, coord_cols, db_dsn=None,
             confirm=None, encoding="utf-8-sig", limit=50):
    """把 batch 产物（CSV 坐标）回写数据库表。
    - 默认【预览】：只打印将执行的 UPDATE 语句样例与匹配统计，不写库；
    - --confirm "确认写入" 才在事务中执行。
    数据库连接串只从 --db-dsn 或环境变量 TIANDITU_DB_DSN 读取，不写入任何文件。"""
    dsn = db_dsn or os.getenv("TIANDITU_DB_DSN")
    for ident in [table] + key_cols + coord_cols:
        if not re.match(_IDENT, ident):
            print(json.dumps({"ok": False, "gap": f"非法标识符：{ident}"}, ensure_ascii=False)); return
    if not dsn:
        print(json.dumps({"ok": False, "gap": "未提供数据库连接串：--db-dsn 或环境变量 TIANDITU_DB_DSN"}, ensure_ascii=False)); return
    try:
        import psycopg2
    except ImportError:
        print(json.dumps({"ok": False, "gap": "缺少 psycopg2，安装后重试"}, ensure_ascii=False)); return

    rows = [r for r in csv.DictReader(open(csv_file, encoding=encoding))
            if r.get(coord_cols[0]) and r.get(coord_cols[1])]
    if not rows:
        print(json.dumps({"ok": False, "gap": "CSV 无有效坐标行"}, ensure_ascii=False)); return
    k1, k2 = key_cols[0], key_cols[1] if len(key_cols) > 1 else key_cols[0]
    c1, c2 = coord_cols[0], coord_cols[1]
    sql_head = (f"UPDATE {table} t SET {c1}=v.c1, {c2}=v.c2 "
                f"FROM (VALUES ...) v(k1,k2,c1,c2) WHERE t.{k1}=v.k1 AND t.{k2}=v.k2")
    try:
        conn = psycopg2.connect(dsn, connect_timeout=10)
        cur = conn.cursor()
    except Exception as e:
        print(json.dumps({"ok": False, "gap": f"数据库连接失败：{e}"}, ensure_ascii=False)); return

    print(f"【预览】匹配键 {k1},{k2} → 坐标列 {c1},{c2}", flush=True)
    print(f"    将更新 {len(rows)} 行（CSV 有效坐标行），示例语句：", flush=True)
    for r in rows[:3]:
        sample = sql_head.replace("...", f"('{r[k1]}','{r[k2]}',{r[c1]},{r[c2]}),...")
        print("    " + sample, flush=True)

    if confirm != "确认写入":
        conn.close()
        print(json.dumps({"ok": False, "preview": True, "rows": len(rows),
                          "msg": "预览模式：加 --confirm \"确认写入\" 才实际写库"}, ensure_ascii=False)); return

    # 执行：分批更新（VALUES 用临时表 join，避免表达式注入）
    updated, failed = 0, 0
    try:
        B, n = 1000, len(rows)
        for i in range(0, n, B):
            chunk = rows[i:i + B]
            vals = [(r[k1], r[k2], float(r[c1]), float(r[c2])) for r in chunk]
            cur.execute("CREATE TEMP TABLE _tdt_apply(k1 text, k2 text, c1 double precision, c2 double precision)")
            cur.executemany("INSERT INTO _tdt_apply VALUES (%s,%s,%s,%s)", vals)
            cur.execute(f"UPDATE {table} t SET {c1}=t2.c1, {c2}=t2.c2 FROM _tdt_apply t2 "
                        f"WHERE t.{k1}=t2.k1 AND t.{k2}=t2.k2")
            updated += cur.rowcount
            cur.execute("DROP TABLE _tdt_apply")
        conn.commit()
    except Exception as e:
        conn.rollback()
        print(json.dumps({"ok": False, "gap": f"写库失败已回滚：{e}"}, ensure_ascii=False)); return
    finally:
        conn.close()
    print(json.dumps({"ok": True, "updated": updated, "rows": len(rows),
                      "msg": f"已确认写入 {updated} 行（未匹配行未更新）"}, ensure_ascii=False))


# ---------------- CLI ----------------

def main():
    ap = argparse.ArgumentParser(description="天地图 API CLI（key池轮询/并发/断点）")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("geocode", help="地址 → 坐标")
    p.add_argument("address")
    p.add_argument("--raw", action="store_true", help="输出原始响应")

    p = sub.add_parser("reverse", help="坐标 → 地址")
    p.add_argument("lon", type=float)
    p.add_argument("lat", type=float)

    p = sub.add_parser("search", help="v2 地名/POI 搜索")
    p.add_argument("keyword")
    p.add_argument("--query-type", default="2", help="2视野内/3周边/10多边形/12行政区")
    p.add_argument("--map-bound", default=None, help='"x1,y1,x2,y2"')
    p.add_argument("--level", default="15")
    p.add_argument("--point-lonlat", default=None, help='"lon,lat"')
    p.add_argument("--radius", default=None, help="米")
    p.add_argument("--specify", default=None, help="9位行政区码(queryType=12)")
    p.add_argument("--polygon", default=None)
    p.add_argument("--count", type=int, default=10)
    p.add_argument("--start", type=int, default=0)

    p = sub.add_parser("batch", help="CSV/TXT 批量地理编码")
    p.add_argument("input")
    p.add_argument("--col", default="address", help="地址列名")
    p.add_argument("--out", required=True)
    p.add_argument("--prefix", default="", help='地址前缀，如 "宁夏银川市"')
    p.add_argument("--workers", type=int, default=None, help="默认=key数")
    p.add_argument("--ckpt-prefix", default=None)
    p.add_argument("--encoding", default="utf-8-sig", help="输入/输出编码，GBK 文件用 gbk")
    p.add_argument("--no-dedup", action="store_true", help="关闭楼栋级去重")

    p = sub.add_parser("crawl-communities", help="网格切分遍历爬城市小区POI")
    p.add_argument("bbox", help='"x1,y1,x2,y2"')
    p.add_argument("--out-prefix", required=True, help="输出 CSV/GeoJSON 前缀")
    p.add_argument("--keywords", default=None, help='逗号分隔，默认 "小区,花园,家园,苑,公寓,住宅,宿舍,里,园,府"')
    p.add_argument("--grid-size", type=float, default=0.05, help="网格边长(度)，默认0.05≈5km")
    p.add_argument("--level", default="18", help="搜索级别(zoom)，默认18接近小区级")
    p.add_argument("--count", type=int, default=300, help="每格每词上限(<=300)")
    p.add_argument("--max-depth", type=int, default=2, help="满载格递归切细深度")

    p = sub.add_parser("map", help="CSV/GeoJSON → Leaflet 地图HTML")
    p.add_argument("input", help="输入 CSV 或 GeoJSON")
    p.add_argument("--out", required=True, help="输出 HTML")
    p.add_argument("--title", default="小区地图")
    p.add_argument("--encoding", default="utf-8-sig")

    p = sub.add_parser("apply-db", help="【人工门禁】CSV坐标回写数据库")
    p.add_argument("csv", help="batch 产物 CSV")
    p.add_argument("--table", required=True, help="目标表，如 iotbase.iot_equip_info")
    p.add_argument("--key-cols", default="equip_name,address", help="匹配列，逗号分隔")
    p.add_argument("--coord-cols", default="lon,lat", help="坐标列，逗号分隔")
    p.add_argument("--db-dsn", default=None, help='连接串，默认读环境变量 TIANDITU_DB_DSN')
    p.add_argument("--encoding", default="utf-8-sig")
    p.add_argument("--confirm", default=None, help='写库前必须输入 "确认写入"')

    p = sub.add_parser("keys", help="显示 key 池状态")
    p.add_argument("--tps", type=float, default=None)

    args = ap.parse_args()

    if args.cmd == "geocode":
        if args.raw:
            ds = json.dumps({"keyWord": args.address}, ensure_ascii=False)
            print(json.dumps(api_get("/geocoder", {"ds": ds}), ensure_ascii=False, indent=2))
        else:
            r = geocode(args.address)
            print(json.dumps(r, ensure_ascii=False, indent=2))
    elif args.cmd == "reverse":
        print(json.dumps(reverse(args.lon, args.lat), ensure_ascii=False, indent=2))
    elif args.cmd == "search":
        r = search(args.keyword, args.query_type, args.map_bound, args.level,
                   args.point_lonlat, args.radius, args.specify, args.polygon,
                   args.count, args.start)
        print(json.dumps(r, ensure_ascii=False, indent=2))
    elif args.cmd == "batch":
        batch_geocode(args.input, args.col, args.out, args.prefix,
                      args.workers, args.ckpt_prefix, args.encoding,
                      dedup=not args.no_dedup)
    elif args.cmd == "crawl-communities":
        crawl_communities(
            args.bbox, args.out_prefix,
            keywords=args.keywords.split(",") if args.keywords else None,
            grid_size=args.grid_size, level=args.level,
            count=args.count, max_depth=args.max_depth)
    elif args.cmd == "map":
        make_map(args.input, args.out, args.encoding, args.title)
    elif args.cmd == "apply-db":
        apply_db(args.csv, args.table, [c.strip() for c in args.key_cols.split(",")],
                 [c.strip() for c in args.coord_cols.split(",")],
                 db_dsn=args.db_dsn, confirm=args.confirm, encoding=args.encoding)
    elif args.cmd == "keys":
        pool = get_pool(args.tps)
        print(f"key 池（server，轮询）：{len(pool)} 个，每 key {pool.tps} TPS")
        conf = None
        for path in (KEYS_LOCAL, KEYS_FILE):
            try:
                with open(path, encoding="utf-8") as f:
                    conf = json.load(f)
                if conf.get("keys"):
                    break
            except (FileNotFoundError, json.JSONDecodeError):
                continue
        if conf:
            for it in conf.get("keys", []):
                mark = "✅启用" if it.get("type") == "server" else "⏸跳过(browser)"
                print(f"  {it['key'][:8]}…  {mark}  {it.get('note','')}")


if __name__ == "__main__":
    main()
