#!/usr/bin/env python3
"""对 oa_resolution.json 中没拿到全文的条目再攻一次：
   pdf_url -> 落地页 citation_pdf_url -> DOI 解析 -> 常见仓储直链改写"""
import json, os, re, subprocess, sys, time, urllib.parse

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")

def curl(url, out=None, timeout=120):
    cmd = ["curl","-sL","--compressed","--max-time",str(timeout),"--connect-timeout","20",
           "-A",UA,"-H","Accept-Language: en-US,en;q=0.9",
           "-H","Sec-Fetch-Dest: document","-H","Sec-Fetch-Mode: navigate",
           "-o", out or "-", "-w","%{http_code}\t%{content_type}\t%{url_effective}"]
    cmd.append(url)
    try: r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout+30)
    except subprocess.TimeoutExpired: return "000","",url,b""
    tail = r.stdout.rsplit("\n",1)[-1] if out else r.stdout[-300:]
    parts = (tail.split("\t")+["","",""])[:3]
    body = b"" if out else r.stdout.encode("utf-8","replace")
    return parts[0], parts[1], parts[2], body

def is_pdf(p):
    return os.path.exists(p) and open(p,"rb").read(5).startswith(b"%PDF") and os.path.getsize(p) > 20000

def pdf_links_from_html(html, base):
    outs = []
    for pat in (r'<meta[^>]+name=["\']citation_pdf_url["\'][^>]+content=["\']([^"\']+)',
                r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+name=["\']citation_pdf_url["\']',
                r'href=["\']([^"\']*/download/[^"\']*)["\']',
                r'href=["\']([^"\']*\.pdf(?:\?[^"\']*)?)["\']',
                r'href=["\']([^"\']*/pdf/?[^"\']*)["\']'):
        for m in re.finditer(pat, html, re.I):
            outs.append(urllib.parse.urljoin(base, m.group(1)))
    seen, res = set(), []
    for u in outs:
        if u not in seen and not re.search(r"\.(png|jpg|css|js)(\?|$)", u, re.I):
            seen.add(u); res.append(u)
    return res[:6]

def rewrite(u):
    """常见仓储的直链改写规则。"""
    outs = []
    if "escholarship.org/uc/item/" in u:
        outs.append(re.sub(r"(/uc/item/[^/?#]+).*", r"\1.pdf", u))
    if "cambridge.org/core/services/aop-cambridge-core" in u:
        outs.append(u)
    if "brill.com/downloadpdf" in u:
        outs.append(u.replace("/downloadpdf/","/view/"))
    if "/article/view/" in u:
        outs.append(u.replace("/article/view/","/article/download/"))
    if "tandfonline.com/doi/abs/" in u:
        outs.append(u.replace("/doi/abs/","/doi/pdf/"))
    if "link.springer.com/chapter/" in u or "link.springer.com/article/" in u:
        outs.append(re.sub(r"/(chapter|article)/", "/content/pdf/", u) + ".pdf")
    return outs

def try_all(urls, dst, log):
    for u in urls:
        if not u: continue
        code, ctype, eff, _ = curl(u, dst)
        if is_pdf(dst):
            log.append(f"    OK  {code} {u[:96]}"); return True
        if os.path.exists(dst): os.remove(dst)
        # HTML? 挖里面的 pdf 链接
        if code.startswith("2") and ("html" in (ctype or "")):
            _,_,_, body = curl(u, None, 90)
            html = body.decode("utf-8","replace")
            for cand in pdf_links_from_html(html, eff or u) + rewrite(eff or u):
                c2,_,_,_ = curl(cand, dst)
                if is_pdf(dst):
                    log.append(f"    OK  {c2} (via landing) {cand[:80]}"); return True
                if os.path.exists(dst): os.remove(dst)
                time.sleep(0.5)
        log.append(f"    x   {code} {(ctype or '')[:24]} {u[:80]}")
        time.sleep(0.6)
    return False

if __name__ == "__main__":
    path, OUT = sys.argv[1], sys.argv[2]
    data = json.load(open(path))
    todo = []
    for blk in data:
        for c in blk.get("picked", []):
            if not c.get("file"):
                todo.append(c)
    print(f"待补救 {len(todo)} 条\n", flush=True)
    got = 0
    for i, c in enumerate(todo, 1):
        name = re.sub(r"[\s_]+","_", re.sub(r"[^\w一-鿿.\- ]+","_",
                f"{c.get('year') or 'nd'}_{c.get('title')}")).strip("_. ")[:115]
        dst = os.path.join(OUT, name + ".pdf")
        if is_pdf(dst): c["file"]=os.path.basename(dst); got+=1; continue
        doi = (c.get("doi") or "").replace("https://doi.org/","")
        urls = [c.get("pdf"), c.get("landing"), f"https://doi.org/{doi}" if doi else None]
        urls += rewrite(c.get("pdf") or "")
        log=[]
        ok = try_all(urls, dst, log)
        if ok: c["file"]=os.path.basename(dst); got+=1
        print(f"[{i:>3}/{len(todo)}] {'OK  ' if ok else 'fail'} {name[:74]}", flush=True)
        for l in log[:4]: print(l, flush=True)
        json.dump(data, open(path,"w"), ensure_ascii=False, indent=1)
    print(f"\n补救成功 {got}/{len(todo)}")
