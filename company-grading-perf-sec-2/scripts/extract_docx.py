"""
解析 docx，按顺序导出 文字段落 / 图片插入位置 / 图片文件清单
为评分做准备。
"""
import os, sys, zipfile, re, json, shutil
from xml.etree import ElementTree as ET

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# 用法: python extract_docx.py <workdir>
ROOT = sys.argv[1] if len(sys.argv) > 1 else r"D:\backup\user1\majq\Desktop\阅卷"
EXT_DIR = os.path.join(ROOT, "_extracted")

NS = {
    "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "pic": "http://schemas.openxmlformats.org/drawingml/2006/picture",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "rel": "http://schemas.openxmlformats.org/package/2006/relationships",
    "v": "urn:schemas-microsoft-com:vml",
}
W = "{%s}" % NS["w"]
A = "{%s}" % NS["a"]
REL = "{%s}" % NS["rel"]
R = "{%s}" % NS["r"]
V = "{%s}" % NS["v"]


def parse_docx(docx_path, out_dir):
    """解压并解析 docx → 返回 [{type:'text'|'image', ...}, ...]"""
    os.makedirs(out_dir, exist_ok=True)
    media_dir = os.path.join(out_dir, "media")
    os.makedirs(media_dir, exist_ok=True)

    try:
        with zipfile.ZipFile(docx_path, "r") as z:
            names = z.namelist()
            # 提取媒体
            for n in names:
                if n.startswith("word/media/") and not n.endswith("/"):
                    fname = os.path.basename(n)
                    if not fname:
                        continue
                    with open(os.path.join(media_dir, fname), "wb") as f:
                        f.write(z.read(n))
            # 读 document.xml + rels
            doc_xml = z.read("word/document.xml").decode("utf-8", errors="ignore")
            rels_xml = (
                z.read("word/_rels/document.xml.rels").decode("utf-8", errors="ignore")
                if "word/_rels/document.xml.rels" in names
                else ""
            )
    except Exception as e:
        return [{"type": "error", "msg": str(e)}]

    # rels: rId -> media/imageN
    rid_map = {}
    if rels_xml:
        rt = ET.fromstring(rels_xml)
        for r in rt.findall(REL + "Relationship"):
            rid = r.get("Id")
            target = r.get("Target") or ""
            if "media/" in target:
                rid_map[rid] = os.path.basename(target)

    # 解析 document.xml: 按段落顺序，每段提文字+图片
    root = ET.fromstring(doc_xml)
    body = root.find(W + "body")
    items = []
    for p in body.iter(W + "p"):
        # 提文字
        texts = [t.text or "" for t in p.iter(W + "t")]
        text = "".join(texts).strip()
        # 提图片：新式 <a:blip r:embed> + 老式 <v:imagedata r:id>
        imgs = []
        for blip in p.iter(A + "blip"):
            rid = blip.get(R + "embed") or blip.get(R + "link")
            if rid and rid in rid_map:
                imgs.append(rid_map[rid])
        for vimg in p.iter(V + "imagedata"):
            rid = vimg.get(R + "id") or vimg.get(R + "href")
            if rid and rid in rid_map:
                imgs.append(rid_map[rid])
        if text:
            items.append({"type": "text", "val": text})
        for img in imgs:
            items.append({"type": "image", "file": img})

    return items


def slug(s):
    return re.sub(r"[<>:\"/\\|?*]", "_", s).strip()


def main():
    if os.path.exists(EXT_DIR):
        shutil.rmtree(EXT_DIR, ignore_errors=True)
    os.makedirs(EXT_DIR, exist_ok=True)

    manifest = []
    for entry in sorted(os.listdir(ROOT)):
        sub = os.path.join(ROOT, entry)
        if not os.path.isdir(sub) or entry.startswith("_") or entry.startswith("."):
            continue
        for fname in sorted(os.listdir(sub)):
            if not (fname.lower().endswith(".docx") or fname.lower().endswith(".doc")):
                continue
            docx = os.path.join(sub, fname)
            stub = slug(entry + "__" + fname.rsplit(".", 1)[0])
            out = os.path.join(EXT_DIR, stub)
            print(f"[*] {entry}/{fname}")
            if fname.lower().endswith(".doc"):
                # .doc 老格式无法用 zipfile，跳过先标记
                manifest.append(
                    {
                        "src": docx,
                        "out": out,
                        "fmt": "doc",
                        "err": "需 libreoffice 转换",
                        "items": [],
                    }
                )
                continue
            items = parse_docx(docx, out)
            # 写 items.json
            with open(os.path.join(out, "items.json"), "w", encoding="utf-8") as f:
                json.dump(items, f, ensure_ascii=False, indent=2)
            # 写文字纯文本，方便快速浏览
            with open(os.path.join(out, "text_only.txt"), "w", encoding="utf-8") as f:
                for it in items:
                    if it["type"] == "text":
                        f.write(it["val"] + "\n")
                    elif it["type"] == "image":
                        f.write(f"[图: {it['file']}]\n")
                    else:
                        f.write(f"[err: {it.get('msg','')}]\n")
            img_count = sum(1 for it in items if it["type"] == "image")
            txt_count = sum(1 for it in items if it["type"] == "text")
            manifest.append(
                {
                    "src": docx,
                    "out": out,
                    "fmt": "docx",
                    "img_count": img_count,
                    "txt_count": txt_count,
                }
            )
            print(f"    -> {txt_count} 段文字 / {img_count} 张图")

    with open(os.path.join(EXT_DIR, "_manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
    print(f"\n[✓] 解析完成，{len(manifest)} 份输出在 {EXT_DIR}")


if __name__ == "__main__":
    main()
