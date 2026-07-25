"""
从 Moodle quiz responses 报告页抓取所有 attempt 列表 + 附件，下载到 <workdir>/<attempt>_<name>/Q<n>_*.docx
用法: python download_attachments.py <quiz_id> <workdir>
环境变量: MOODLE_COOKIE  (MoodleSession=xxx; MOODLEID1_=xxx)
"""
import os, sys, re, json, urllib.parse, urllib.request

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

if len(sys.argv) < 3:
    print("用法: python download_attachments.py <quiz_id> <workdir>", file=sys.stderr)
    sys.exit(1)

QUIZ_ID = sys.argv[1]
WORKDIR = sys.argv[2]
COOKIE = os.environ.get("MOODLE_COOKIE", "")
BASE = os.environ.get("MOODLE_BASE", "http://onekey.egova.com.cn:8888")

if not COOKIE:
    print("ERR: 必须设置环境变量 MOODLE_COOKIE", file=sys.stderr)
    sys.exit(2)

os.makedirs(WORKDIR, exist_ok=True)

# WAF（雷池/lua_waf）会拦默认 Python-urllib UA，pluginfile 下载必须伪装浏览器 UA
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"


def fetch(url):
    req = urllib.request.Request(url, headers={"Cookie": COOKIE, "User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", errors="ignore")


def download(url, out_path, referer=None, retries=3):
    # 多附件/弱网下载会瞬时失败（如同名多 slot 提交时某个 slot 偶发丢失），
    # 必须重试，否则会静默漏掉考生的部分作答（如全业务流转 slot-10）。
    headers = {"Cookie": COOKIE, "User-Agent": UA, "Referer": referer or (BASE + "/")}
    last_err = None
    for attempt in range(1, retries + 1):
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=300) as r:
                data = r.read()
            if not data:
                raise IOError("空响应")
            with open(out_path, "wb") as f:
                f.write(data)
            return len(data)
        except Exception as e:
            last_err = e
            if attempt < retries:
                print(f"   重试 {attempt}/{retries - 1} ({e})", flush=True)
    raise last_err


def slug(s):
    return re.sub(r"[<>:\"/\\|?*]", "_", s).strip()


def main():
    print(f"[*] 抓取 quiz {QUIZ_ID} 的所有 attempt...")
    # 用大 pagesize 一次抓全
    url = f"{BASE}/mod/quiz/report.php?id={QUIZ_ID}&mode=responses&pagesize=100"
    html = fetch(url)

    # 提取每行 attempt：review.php?attempt=XXX → 学员名 / email
    # 表格 id=responses，每行 td 含学员信息
    rows = re.findall(
        r'<tr[^>]*>(.*?)</tr>',
        html.split('id="responses"')[1].split('</table>')[0] if 'id="responses"' in html else html,
        re.DOTALL,
    )

    attempts = []
    for r in rows:
        m = re.search(r'review\.php\?attempt=(\d+)', r)
        if not m:
            continue
        attempt = int(m.group(1))
        # 提取学员名（先看 <td> 列）
        cells = re.findall(r'<td[^>]*>(.*?)</td>', r, re.DOTALL)
        name = ""
        email = ""
        if len(cells) >= 3:
            name = re.sub(r'<[^>]+>', '', cells[2]).strip()
            name = re.sub(r'\s+', ' ', name).replace('回顾试答', '').strip()
        if len(cells) >= 4:
            email = re.sub(r'<[^>]+>', '', cells[3]).strip()
        attempts.append({"attempt": attempt, "name": name, "email": email})

    # 去重 attempt
    seen = set()
    uniq = []
    for a in attempts:
        if a["attempt"] not in seen:
            seen.add(a["attempt"])
            uniq.append(a)
    attempts = uniq

    print(f"[*] 找到 {len(attempts)} 个 attempt")

    # 对每个 attempt 访问 review.php 拿附件 URL
    all_attempts = []
    for ai, a in enumerate(attempts, 1):
        print(f"[{ai}/{len(attempts)}] attempt={a['attempt']} {a['name']}", flush=True)
        rev = fetch(f"{BASE}/mod/quiz/review.php?attempt={a['attempt']}")
        # 找所有 pluginfile URL，按 slot 分组（URL 里有 response_attachments/X/SLOT/）
        files = []
        for m in re.finditer(
            r'<a\s+href="(https?://[^"]*pluginfile\.php/[^"]*response_attachments/(\d+)/(\d+)/(\d+)/([^"?]+)[^"]*)"',
            rev,
        ):
            url2, quba, slot, fid, fname = m.groups()
            fname = urllib.parse.unquote(fname)
            files.append({"slot": int(slot), "url": url2, "fname": fname, "quba": int(quba)})

        a["files"] = files
        all_attempts.append(a)

        if not files:
            continue
        # 下载到 <workdir>/<attempt>_<name>/Q<slot>_<fname>
        dir_name = f"{a['attempt']}_{slug(a['name']) or 'unknown'}"
        # 处理重复提交：同一名字多次 attempt 加 _v1/_v2 后缀
        existing_dirs = [d for d in os.listdir(WORKDIR) if d.startswith(f"{a['attempt']}_")]
        out_dir = os.path.join(WORKDIR, dir_name)
        os.makedirs(out_dir, exist_ok=True)
        if len({fl["slot"] for fl in files}) > 1:
            # 同一考生分多个 slot 提交（如 slot-1 主文档 + slot-10 全业务流转补充），
            # 解析/判分时必须把该考生所有 Q*_ 文件合并看，否则会漏判整段采分点。
            print(f"   ⚠ 多附件考生：{len(files)} 个文件分布在 slot "
                  f"{sorted({fl['slot'] for fl in files})}，判分需合并所有 Q*_ 目录")
        for f in files:
            out_path = os.path.join(out_dir, f"Q{f['slot']}_{f['fname']}")
            try:
                size = download(f["url"], out_path, referer=f"{BASE}/mod/quiz/review.php?attempt={a['attempt']}")
                print(f"   OK Q{f['slot']} {f['fname']} ({size} bytes)")
            except Exception as e:
                print(f"   FAIL Q{f['slot']} {f['fname']}: {e}")

    # 落档 attempts 元数据
    with open(os.path.join(WORKDIR, "_attempts.json"), "w", encoding="utf-8") as f:
        json.dump(all_attempts, f, ensure_ascii=False, indent=2)
    print(f"\n[✓] 全部 attempt 元数据已存 {WORKDIR}\\_attempts.json")


if __name__ == "__main__":
    main()
