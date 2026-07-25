"""
解析麒舰实操考核 docx 文件。
- 输入：<workdir>/麒舰实操考核-*.docx
- 输出：<workdir>/_extracted/<name>/text_only.txt + media/

用法: python extract_docx.py <workdir>
"""
import os, sys, zipfile, re, json, shutil
from xml.etree import ElementTree as ET

ROOT = sys.argv[1] if len(sys.argv) > 1 else r"D:\backup\user1\majq\Desktop\麒舰"
EXT_DIR = os.path.join(ROOT, "_extracted")

NS = {
    "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "pic": "http://schemas.openxmlformats.org/drawingml/2006/picture",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "rel": "http://schemas.openxmlformats.org/package/2006/relationships",
}
W = "{%s}" % NS["w"]
A = "{%s}" % NS["a"]
REL = "{%s}" % NS["rel"]
R = "{%s}" % NS["r"]


def parse_docx(docx_path, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    media_dir = os.path.join(out_dir, "media")
    os.makedirs(media_dir, exist_ok=True)

    with zipfile.ZipFile(docx_path, "r") as z:
        names = z.namelist()
        for n in names:
            if n.startswith("word/media/") and not n.endswith("/"):
                fname = os.path.basename(n)
                if fname:
                    with open(os.path.join(media_dir, fname), "wb") as f:
                        f.write(z.read(n))
        doc_xml = z.read("word/document.xml").decode("utf-8", errors="ignore")
        rels_xml = (
            z.read("word/_rels/document.xml.rels").decode("utf-8", errors="ignore")
            if "word/_rels/document.xml.rels" in names
            else ""
        )

    rid_map = {}
    if rels_xml:
        rt = ET.fromstring(rels_xml)
        for r in rt.findall(REL + "Relationship"):
            rid = r.get("Id")
            target = r.get("Target") or ""
            if target.startswith("../"):
                target = target[3:]
            rid_map[rid] = os.path.basename(target)

    root = ET.fromstring(doc_xml)
    body = root.find(W + "body")

    events = []  # (type, content)  type: 'text' | 'image'

    for elem in body:
        tag = elem.tag
        if tag == W + "p":
            texts = []
            has_image = False
            for t in elem.iter(W + "t"):
                if t.text:
                    texts.append(t.text)
            for drawing in elem.iter():
                dtag = drawing.tag.split("}")[-1] if "}" in drawing.tag else drawing.tag
                if dtag in ("drawing", "pict", "object"):
                    has_image = True
                    break
            line = "".join(texts).strip()
            if line:
                events.append(("text", line))
            if has_image:
                # 找 rId
                rid = None
                for blip in elem.iter():
                    if blip.tag == A + "blip" or blip.tag.endswith("}blip"):
                        rid = blip.get(R + "embed") or blip.get("embed")
                        break
                fname = rid_map.get(rid, f"image_{len(events)}")
                events.append(("image", f"[图:{fname}]"))

        elif tag == W + "tbl":
            # 表格：提取每个单元格文字，用 | 分隔
            for tr in elem.iter(W + "tr"):
                cells = []
                for tc in tr.iter(W + "tc"):
                    cell_text = "".join(t.text or "" for t in tc.iter(W + "t")).strip()
                    cells.append(cell_text)
                events.append(("text", " | ".join(cells)))

    # 写 text_only.txt
    with open(os.path.join(out_dir, "text_only.txt"), "w", encoding="utf-8") as f:
        for etype, content in events:
            f.write(content + "\n")

    # 统计
    img_dir_count = len([n for n in os.listdir(media_dir) if not n.startswith(".")])
    return {"text_lines": sum(1 for t, _ in events if t == "text"),
            "images": sum(1 for t, _ in events if t == "image"),
            "media_files": img_dir_count}


def main():
    docx_files = sorted([
        f for f in os.listdir(ROOT)
        if f.endswith(".docx") and f.startswith("麒舰实操考核-")
    ])
    if not docx_files:
        print(f"[✗] 在 {ROOT} 下未找到 麒舰实操考核-*.docx 文件")
        sys.exit(1)

    print(f"[✓] 发现 {len(docx_files)} 份答卷")
    for fname in docx_files:
        name = fname.replace("麒舰实操考核-", "").replace(".docx", "")
        out_dir = os.path.join(EXT_DIR, name)
        print(f"  → 解析 {fname} ...")
        stats = parse_docx(os.path.join(ROOT, fname), out_dir)
        print(f"     {stats['text_lines']} 文字段落, {stats['images']} 图片占位, {stats['media_files']} 媒体文件")
    print(f"[✓] 全部解析完毕 → {EXT_DIR}/")


if __name__ == "__main__":
    main()
