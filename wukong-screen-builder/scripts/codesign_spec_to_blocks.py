#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# codesign get_artboard_spec 输出文件 → 区块清单
# 策略: 顶层group(area>=min)=区块候选; 文字层按"中心点落在哪个最小区块内"空间归属
# 用法: python codesign_spec_to_blocks.py <spec_file.json> [out.json] [--min-area=20000]
import sys, json
try: sys.stdout.reconfigure(encoding='utf-8')
except: pass

args = [a for a in sys.argv[1:] if not a.startswith('--')]
opts = dict(a[2:].split('=',1) for a in sys.argv[1:] if a.startswith('--') and '=' in a)
spec_file = args[0]; out_file = args[1] if len(args) > 1 else None
min_area = float(opts.get('min-area', 20000))

d = json.load(open(spec_file, encoding='utf-8'))
spec = d.get('spec', d); ab = spec.get('artboard', {})
layers = spec.get('layers', []); groups = spec.get('groups', [])
root = ab.get('objectId')

def area(r): return (r.get('width') or 0) * (r.get('height') or 0)
def center(r): return (r.get('x',0)+ (r.get('width') or 0)/2, r.get('y',0)+(r.get('height') or 0)/2)
def inside(r, x, y): return r.get('x',0) <= x <= r.get('x',0)+(r.get('width') or 0) and r.get('y',0) <= y <= r.get('y',0)+(r.get('height') or 0)

# 区块候选 = 顶层节点(parent=artboard) 且 面积达标
top = [n for n in (layers + groups) if n.get('parent_id') == root]
cands = [{'object_id': t.get('object_id'), 'name': t.get('name'), 'type': t.get('type'),
          'rect': t.get('rect') or {}, '_texts': []} for t in top if area(t.get('rect') or {}) >= min_area]

# 所有文字层(全局) → 按中心点归属到最小的包含区块
all_texts = [n for n in layers if n.get('type') == 'text' and n.get('content')]
unassigned = []
for t in all_texts:
    cx, cy = center(t.get('rect') or {})
    box = [b for b in cands if inside(b['rect'], cx, cy)]
    if box:
        min(box, key=lambda b: area(b['rect']))['_texts'].append(t)
    else:
        unassigned.append(t)

cands.sort(key=lambda b: (b['rect'].get('y', 0), b['rect'].get('x', 0)))
def texts_of(b): return [t['content'] for t in b['_texts']]

result = {'screen': d.get('screen'),
          'artboard': {'name': ab.get('name'), 'width': ab.get('width'), 'height': ab.get('height'), 'rect': ab.get('rect')},
          'blockCount': len(cands),
          'blocks': [{'name': b['name'], 'rect': b['rect'], 'textCount': len(b['_texts']),
                      'texts': texts_of(b),
                      'textDetail': [{'text': t['content'], 'rect': t.get('rect'), 'color': t.get('color'), 'fontSize': t.get('fontSize')} for t in b['_texts']]} for b in cands],
          'unassignedTexts': [t['content'] for t in unassigned]}

print(f"画板: {ab.get('name')} {ab.get('width')}x{ab.get('height')}  区块: {len(cands)}  游离文字: {len(unassigned)}")
print("=" * 64)
for i, b in enumerate(cands, 1):
    r = b['rect']
    print(f"[{i}] {b['name']} | x{int(r.get('x',0))},y{int(r.get('y',0))} {int(r.get('width',0))}x{int(r.get('height',0))} | 文字{len(b['_texts'])}")
    tx = texts_of(b)
    if tx: print("    " + ' / '.join(tx[:12])[:150])
if unassigned:
    print(f"\n游离文字(未归属任何区块): " + ' / '.join(t['content'] for t in unassigned[:15])[:150])
if out_file:
    json.dump(result, open(out_file, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(f"\n区块清单JSON → {out_file}")
