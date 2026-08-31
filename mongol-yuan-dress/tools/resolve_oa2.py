#!/usr/bin/env python3
"""双模式开放全文解析：
   exact  = 已知题名，要求题名重合度 >= 0.55
   topic  = 主题扫描，只要 OpenAlex 标记 OA 且题名/摘要命中蒙元关键词就收
"""
import json, os, re, subprocess, sys, time, urllib.parse, urllib.request

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")
TOPIC_RE = re.compile(r"mongol|yuan|ilkhan|il-khan|chinggis|genghis|khubilai|kublai|"
                      r"golden horde|jochi|chagatai|semu|nasij|boqta|jisun|keshig|"
                      r"khitan|jurchen|tangut|steppe|nomad|silk road|timurid", re.I)
STOP = set("the a an of and in on for to with from into by at as is are between during its".split())

def jget(url, tries=3):
    for a in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.loads(r.read().decode("utf-8"))
        except Exception:
            if a == tries - 1: return None
            time.sleep(2 * (a + 1))

def toks(s):
    return {w for w in re.findall(r"[a-z0-9一-鿿]+", (s or "").lower())
            if w not in STOP and len(w) > 2}

def title_match(q, t):
    a, b = toks(q), toks(t)
    return len(a & b) / len(a) if a and b else 0.0

def unabstract(inv):
    if not inv: return ""
    pos = {}
    for w, ix in inv.items():
        for i in ix: pos[i] = w
    return " ".join(pos[k] for k in sorted(pos))[:1200]

def safe(s, n=115):
    s = re.sub(r"[^\w一-鿿.\- ]+", "_", s or "paper")
    return re.sub(r"[\s_]+", "_", s).strip("_. ")[:n] or "paper"

def curl_pdf(url, dst):
    cmd = ["curl", "-sL", "--compressed", "--max-time", "200", "-A", UA,
           "-H", "Accept: application/pdf,*/*", "-H", "Accept-Language: en-US,en;q=0.9",
           "-H", "Sec-Fetch-Dest: document", "-H", "Sec-Fetch-Mode: navigate",
           "-o", dst, "-w", "%{http_code}", url]
    try: r = subprocess.run(cmd, capture_output=True, text=True, timeout=230)
    except subprocess.TimeoutExpired: return False, "timeout"
    ok = False
    if os.path.exists(dst):
        ok = open(dst, "rb").read(5).startswith(b"%PDF") and os.path.getsize(dst) > 20000
        if not ok: os.remove(dst)
    return ok, r.stdout.strip()

def openalex(query, n):
    d = jget(f"https://api.openalex.org/works?per-page={n}"
             f"&filter=open_access.is_oa:true&search={urllib.parse.quote(query)}")
    for w in (d or {}).get("results", []):
        loc = w.get("best_oa_location") or {}
        src = (w.get("primary_location") or {}).get("source") or {}
        yield {"api": "openalex", "title": w.get("display_name"), "year": w.get("publication_year"),
               "doi": w.get("doi"), "venue": src.get("display_name"),
               "pdf": loc.get("pdf_url"), "landing": loc.get("landing_page_url"),
               "abstract": unabstract(w.get("abstract_inverted_index")),
               "cited_by": w.get("cited_by_count")}

def s2(query, n):
    d = jget(f"https://api.semanticscholar.org/graph/v1/paper/search?limit={n}"
             f"&fields=title,year,abstract,externalIds,openAccessPdf,venue,citationCount"
             f"&query={urllib.parse.quote(query)}")
    for w in (d or {}).get("data", []):
        oap = w.get("openAccessPdf") or {}
        if not oap.get("url"): continue
        yield {"api": "s2", "title": w.get("title"), "year": w.get("year"),
               "doi": (w.get("externalIds") or {}).get("DOI"), "venue": w.get("venue"),
               "pdf": oap.get("url"), "abstract": (w.get("abstract") or "")[:1200],
               "cited_by": w.get("citationCount")}

if __name__ == "__main__":
    spec = json.load(open(sys.argv[1])); OUT = sys.argv[2]
    os.makedirs(OUT, exist_ok=True)
    report, seen_doi, seen_file = [], set(), set()
    for item in spec:
        q, mode = item["q"], item.get("mode", "exact")
        n = 25 if mode == "topic" else 4
        print(f"\n=== [{mode}] {q[:88]} ===", flush=True)
        cands = []
        for fn in (openalex, s2):
            try: cands += list(fn(q, n))
            except Exception as e: print("   api fail:", e, flush=True)
            time.sleep(1.1)
        picked = []
        for c in cands:
            if not c.get("pdf"): continue
            doi = (c.get("doi") or "").lower().replace("https://doi.org/", "")
            if doi and doi in seen_doi: continue
            if mode == "exact":
                c["match"] = round(title_match(q, c.get("title")), 2)
                if c["match"] < 0.55: continue
            else:
                blob = (c.get("title") or "") + " " + (c.get("abstract") or "")
                if not TOPIC_RE.search(blob): continue
                c["match"] = None
            if doi: seen_doi.add(doi)
            picked.append(c)
        print(f"   候选 {len(cands)} / 采纳 {len(picked)}", flush=True)
        for c in picked:
            name = safe(f"{c.get('year') or 'nd'}_{c.get('title')}")
            if name in seen_file: continue
            seen_file.add(name)
            dst = os.path.join(OUT, name + ".pdf")
            if os.path.exists(dst) and os.path.getsize(dst) > 20000:
                c["file"] = os.path.basename(dst); print(f"   cached {name[:76]}", flush=True); continue
            ok, code = curl_pdf(c["pdf"], dst)
            c["file"] = os.path.basename(dst) if ok else None
            c["http"] = code
            print(f"   {'OK  ' if ok else 'fail'} [{code:>3}] {name[:74]}", flush=True)
            time.sleep(0.8)
        report.append({"query": q, "mode": mode, "picked": picked})
        json.dump(report, open(os.path.join(OUT, "oa_resolution.json"), "w"),
                  ensure_ascii=False, indent=1)
    got = sum(1 for r in report for c in r["picked"] if c.get("file"))
    print(f"\n合计拿到全文 {got} 篇")
