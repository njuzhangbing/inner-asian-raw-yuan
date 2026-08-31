#!/usr/bin/env python3
"""校验 PDF：魔数、页数、是否有文本层。"""
import os, re, sys, glob
rows=[]
for p in sorted(glob.glob(os.path.join(sys.argv[1], "**", "*.pdf"), recursive=True)):
    raw = open(p,"rb").read()
    ok  = raw[:5].startswith(b"%PDF")
    pages = len(re.findall(rb"/Type\s*/Page[^s]", raw)) or len(re.findall(rb"/Count\s+(\d+)", raw[:4000]) or [b"0"])
    if isinstance(pages, list): pages = 0
    text = b"/Font" in raw
    rows.append((os.path.relpath(p, sys.argv[1]), ok, pages, text, len(raw)))
bad=[r for r in rows if not r[1] or r[4]<20000]
print(f"{'文件':<74}{'页':>5}{'文本层':>7}{'KB':>8}")
print("-"*96)
for name,ok,pg,tx,sz in rows:
    print(f"{name[:72]:<74}{pg:>5}{'有' if tx else '无':>7}{sz//1024:>8}")
print("-"*96)
print(f"合计 {len(rows)} 个 PDF，{sum(r[4] for r in rows)/1048576:.1f} MB；异常 {len(bad)} 个")
