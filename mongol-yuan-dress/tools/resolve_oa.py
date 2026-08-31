#!/usr/bin/env python3
"""用 OpenAlex + Semantic Scholar 解析题名 -> 开放全文 PDF，并下载。"""
import json, os, re, subprocess, sys, time, urllib.parse, urllib.request

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")
def jget(url, tries=3):
    for a in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent":UA,"Accept":"application/json"})
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.loads(r.read().decode("utf-8"))
        except Exception:
            if a == tries-1: return None
            time.sleep(2*(a+1))

STOP=set("the a an of and in on for to with from into其 by at as is are between during".split())
def toks(s):
    return {w for w in re.findall(r"[a-z0-9\u4e00-\u9fff]+",(s or "").lower()) if w not in STOP and len(w)>2}
def match(query, title):
    """候选题名必须覆盖查询里足够多的实词，才算同一篇。"""
    q,t = toks(query), toks(title)
    if not q or not t: return 0.0
    return len(q & t) / len(q)

def safe(s,n=110):
    s=re.sub(r"[^\w一-鿿.\- ]+","_",s or "paper"); return re.sub(r"[\s_]+","_",s).strip("_. ")[:n] or "paper"

def curl_pdf(url, dst, ref=None):
    cmd=["curl","-sL","--compressed","--max-time","180","-A",UA,
         "-H","Accept: application/pdf,*/*","-H","Accept-Language: en-US,en;q=0.9",
         "-H","Sec-Fetch-Dest: document","-H","Sec-Fetch-Mode: navigate",
         "-o",dst,"-w","%{http_code}",url]
    if ref: cmd[2:2]=["-e",ref]
    try: r=subprocess.run(cmd,capture_output=True,text=True,timeout=200)
    except subprocess.TimeoutExpired: return False,"timeout"
    ok=False
    if os.path.exists(dst):
        ok = open(dst,"rb").read(5).startswith(b"%PDF") and os.path.getsize(dst)>20000
        if not ok: os.remove(dst)
    return ok, r.stdout.strip()

def openalex(title):
    d=jget("https://api.openalex.org/works?per-page=3&search="+urllib.parse.quote(title))
    for w in (d or {}).get("results",[])[:3]:
        loc=w.get("best_oa_location") or {}
        yield {"src":"openalex","title":w.get("display_name"),"doi":w.get("doi"),
               "year":w.get("publication_year"),"oa":w.get("open_access",{}).get("is_oa"),
               "pdf":loc.get("pdf_url"),"landing":loc.get("landing_page_url"),
               "venue":(w.get("primary_location") or {}).get("source",{} ).get("display_name") if (w.get("primary_location") or {}).get("source") else None}

def s2(title):
    d=jget("https://api.semanticscholar.org/graph/v1/paper/search?limit=3&fields="
           "title,year,externalIds,openAccessPdf,venue&query="+urllib.parse.quote(title))
    for w in (d or {}).get("data",[])[:3]:
        oap=w.get("openAccessPdf") or {}
        yield {"src":"s2","title":w.get("title"),"year":w.get("year"),"venue":w.get("venue"),
               "doi":(w.get("externalIds") or {}).get("DOI"),"pdf":oap.get("url"),"oa":bool(oap.get("url"))}

WANTED = json.load(open(sys.argv[1]))
OUT = sys.argv[2]; os.makedirs(OUT, exist_ok=True)
report=[]
for q in WANTED:
    label = q if isinstance(q,str) else q["q"]
    extra = [] if isinstance(q,str) else q.get("direct",[])
    print(f"\n=== {label[:90]} ===", flush=True)
    cands=[]
    for f in (openalex, s2):
        try: cands += list(f(label))
        except Exception as e: print("   api fail", e, flush=True)
        time.sleep(1.0)
    for c in cands:
        print(f"   [{c['src']}] oa={c.get('oa')} m={match(label,c.get('title')):.2f} "
              f"{str(c.get('year')):<5} {(c.get('title') or '')[:66]}", flush=True)
        if c.get("pdf"): print(f"       pdf: {c['pdf'][:110]}", flush=True)
    for c in cands: c["match"] = round(match(label, c.get("title")), 2)
    urls = extra + [c["pdf"] for c in cands if c.get("pdf") and c["match"] >= 0.55]
    if not urls and any(c.get("pdf") for c in cands):
        print("   (有 PDF 但题名不匹配，跳过；见 oa_resolution.json)", flush=True)
    got=None
    for u in dict.fromkeys(urls):
        dst=os.path.join(OUT, safe(label)+".pdf")
        ok,code = curl_pdf(u, dst)
        print(f"   -> {'OK  ' if ok else 'fail'} [{code}] {u[:100]}", flush=True)
        if ok: got={"url":u,"file":os.path.basename(dst),"bytes":os.path.getsize(dst)}; break
        time.sleep(1.0)
    report.append({"query":label,"candidates":cands,"downloaded":got})
    json.dump(report, open(os.path.join(OUT,"oa_resolution.json"),"w"), ensure_ascii=False, indent=1)
n=sum(1 for r in report if r["downloaded"])
print(f"\n拿到全文 {n}/{len(report)}")
