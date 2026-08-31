#!/usr/bin/env python3
"""极简正文抽取：剥离 script/style/nav 等，按文本密度选主块。"""
import re, sys, html, os

DROP = r"script|style|nav|header|footer|aside|form|noscript|svg|iframe|button|select"

def strip_tags(h):
    h = re.sub(rf"<({DROP})\b.*?</\1>", " ", h, flags=re.S|re.I)
    h = re.sub(r"<!--.*?-->", " ", h, flags=re.S)
    h = re.sub(r"<br\s*/?>", "\n", h, flags=re.I)
    h = re.sub(r"</(p|div|li|h[1-6]|tr|blockquote)>", "\n\n", h, flags=re.I)
    h = re.sub(r"<li\b[^>]*>", "\n- ", h, flags=re.I)
    h = re.sub(r"<h([1-6])\b[^>]*>", lambda m: "\n\n" + "#"*int(m.group(1)) + " ", h, flags=re.I)
    h = re.sub(r"<[^>]+>", " ", h)
    h = html.unescape(h)
    h = re.sub(r"[ \t\xa0]+", " ", h)
    h = re.sub(r"\n\s*\n\s*\n+", "\n\n", h)
    return "\n".join(l.strip() for l in h.split("\n")).strip()

def best_block(hsrc):
    """在 <div>/<article>/<section>/<main> 中挑文本量最大的一块。"""
    best, bl = "", 0
    for m in re.finditer(r"<(article|main|div|section)\b[^>]*>", hsrc, re.I):
        start = m.start()
        tag = m.group(1).lower()
        depth, pos = 1, m.end()
        pat = re.compile(rf"</?{tag}\b[^>]*>", re.I)
        while depth and pos < len(hsrc):
            mm = pat.search(hsrc, pos)
            if not mm: break
            depth += -1 if mm.group(0).startswith("</") else 1
            pos = mm.end()
        chunk = hsrc[start:pos]
        if len(chunk) > 400000: continue
        txt = strip_tags(chunk)
        # 惩罚链接密度高的块（导航）
        links = len(re.findall(r"<a\b", chunk, re.I))
        score = len(txt) - links * 60
        if score > bl: best, bl = txt, score
    return best

if __name__ == "__main__":
    src, dst = sys.argv[1], sys.argv[2]
    hsrc = open(src, encoding="utf-8", errors="ignore").read()
    body = best_block(hsrc)
    full = strip_tags(hsrc)
    out = body if len(body) > 600 else full
    # 掐掉明显的导航尾巴
    out = re.sub(r"\n(- \S.*\n){12,}", "\n", out)
    title = re.search(r"<title[^>]*>(.*?)</title>", hsrc, re.S|re.I)
    hdr = f"# {html.unescape(title.group(1)).strip()}\n\n> 源文件: {os.path.basename(src)}\n\n---\n\n" if title else ""
    open(dst, "w").write(hdr + out)
    print(f"  {os.path.basename(dst):<44} {len(out):>7} chars")
