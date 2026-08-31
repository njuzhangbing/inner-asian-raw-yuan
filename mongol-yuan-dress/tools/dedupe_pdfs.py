#!/usr/bin/env python3
"""按内容哈希去重 PDF，保留页数最多/体积最大的一份，其余移入 _dupes/。"""
import hashlib, os, re, shutil, sys, glob, collections
root = sys.argv[1]
dup = os.path.join(root, "_dupes"); os.makedirs(dup, exist_ok=True)
by_hash = collections.defaultdict(list)
for p in glob.glob(os.path.join(root, "**", "*.pdf"), recursive=True):
    if "/_dupes/" in p: continue
    h = hashlib.sha256(open(p,"rb").read()).hexdigest()
    by_hash[h].append(p)
moved = 0
for h, ps in by_hash.items():
    if len(ps) < 2: continue
    ps.sort(key=lambda p: -os.path.getsize(p))
    keep = ps[0]
    for p in ps[1:]:
        shutil.move(p, os.path.join(dup, os.path.basename(p)))
        moved += 1
        print(f"  dup -> {os.path.basename(p)[:66]}\n      keep {os.path.relpath(keep, root)[:66]}")
# 再按“同题不同体积”找近似重复（同一篇的不同版本）
norm = lambda s: re.sub(r"[^a-z0-9]+","", re.sub(r"^\d{4}_","", os.path.basename(s).lower()))[:55]
by_title = collections.defaultdict(list)
for p in glob.glob(os.path.join(root, "**", "*.pdf"), recursive=True):
    if "/_dupes/" in p: continue
    by_title[norm(p)].append(p)
for t, ps in by_title.items():
    if len(ps) < 2: continue
    ps.sort(key=lambda p: -os.path.getsize(p))
    for p in ps[1:]:
        shutil.move(p, os.path.join(dup, os.path.basename(p))); moved += 1
        print(f"  近似重复 -> {os.path.basename(p)[:60]}")
rest = [p for p in glob.glob(os.path.join(root,"**","*.pdf"), recursive=True) if "/_dupes/" not in p]
print(f"\n移走 {moved} 份重复；剩余 {len(rest)} 篇，"
      f"{sum(os.path.getsize(p) for p in rest)/1048576:.1f} MB")
