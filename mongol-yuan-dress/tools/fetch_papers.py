#!/usr/bin/env python3
"""按 URL 清单抓 PDF，校验 %PDF 魔数，输出 manifest。"""
import json, os, re, subprocess, sys, time, urllib.parse

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")
REFERER = {
    "srvm-yuan": "https://silkroadvirtualmuseum.com/yuan-dynasty-elibrary/",
    "srvm-golden-horde": "https://silkroadvirtualmuseum.com/the-golden-horde-elibrary/",
    "srvm-mongol-japan": "https://silkroadvirtualmuseum.com/mongol-invasion-of-japan-elibrary/",
}
def safe(s, n=110):
    s = re.sub(r"[^\w一-鿿.\- ]+", "_", s or "paper")
    return re.sub(r"[\s_]+", "_", s).strip("_. ")[:n] or "paper"

def fetch(rec, outdir, jar):
    url, title = rec["url"], rec.get("title") or ""
    name = safe(title) or safe(os.path.basename(urllib.parse.urlparse(url).path))
    dst = os.path.join(outdir, f"{name}.pdf")
    if os.path.exists(dst) and os.path.getsize(dst) > 20000:
        rec.update(status="cached", file=os.path.basename(dst),
                   bytes=os.path.getsize(dst)); return rec
    ref = REFERER.get(rec.get("src"), f"https://{rec['host']}/")
    cmd = ["curl","-sL","--compressed","--max-time","180","--retry","2","--retry-delay","3",
           "-A",UA,"-e",ref,
           "-H","Accept: application/pdf,text/html;q=0.9,*/*;q=0.8",
           "-H","Accept-Language: en-US,en;q=0.9,zh-CN;q=0.8",
           "-H","Sec-Fetch-Dest: document","-H","Sec-Fetch-Mode: navigate","-H","Sec-Fetch-Site: cross-site",
           "-H","Upgrade-Insecure-Requests: 1",
           "-b",jar,"-c",jar,"-o",dst,
           "-w","%{http_code}|%{content_type}|%{size_download}|%{url_effective}", url]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=200)
        code, ctype, size, eff = (r.stdout.split("|", 3) + ["","","",""])[:4]
    except subprocess.TimeoutExpired:
        code, ctype, size, eff = "timeout", "", "0", url
    magic = b""
    if os.path.exists(dst):
        with open(dst,"rb") as f: magic = f.read(5)
    ok = magic.startswith(b"%PDF") and os.path.getsize(dst) > 20000
    if not ok and os.path.exists(dst):
        head = open(dst,"rb").read(400)
        os.remove(dst)
        rec["sniff"] = head[:200].decode("utf-8","replace").replace("\n"," ")
    rec.update(status="ok" if ok else f"FAIL http={code} type={ctype.strip()} size={size}",
               file=os.path.basename(dst) if ok else None,
               bytes=os.path.getsize(dst) if ok else 0,
               final_url=eff.strip())
    return rec

if __name__ == "__main__":
    urls = json.load(open(sys.argv[1])); outdir = sys.argv[2]
    os.makedirs(outdir, exist_ok=True)
    jar = os.path.join(outdir, ".cookies.jar")
    res = []
    for i, rec in enumerate(urls, 1):
        r = fetch(dict(rec), outdir, jar)
        res.append(r)
        mark = "OK " if r["status"] in ("ok","cached") else "FAIL"
        print(f"[{i:>2}/{len(urls)}] {mark} {(r.get('title') or r['url'])[:78]:<80} "
              f"{r['bytes']/1024:.0f}KB  {'' if mark=='OK ' else r['status']}", flush=True)
        json.dump(res, open(os.path.join(outdir,"manifest.json"),"w"), ensure_ascii=False, indent=1)
        time.sleep(1.2)
    n = sum(1 for r in res if r["status"] in ("ok","cached"))
    print(f"\n成功 {n}/{len(res)}")
