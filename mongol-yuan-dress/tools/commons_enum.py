#!/usr/bin/env python3
"""枚举 Wikimedia Commons 分类下的文件 + 元数据（stdlib only）。"""
import json, sys, time, urllib.parse, urllib.request, urllib.error, re, html

API = "https://commons.wikimedia.org/w/api.php"
UA = "MongolDressResearch/1.0 (academic use; contact via local)"

def api(params):
    params = dict(params, format="json", formatversion="2")
    url = API + "?" + urllib.parse.urlencode(params)
    for attempt in range(7):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=60) as r:
                d = json.loads(r.read().decode("utf-8"))
            time.sleep(0.7)          # 礼貌节流
            return d
        except urllib.error.HTTPError as e:
            if e.code == 429:
                wait = 10 * (attempt + 1)
                print(f"   429 -> sleep {wait}s", flush=True); time.sleep(wait); continue
            if attempt == 6: raise
            time.sleep(3 * (attempt + 1))
        except Exception:
            if attempt == 6: raise
            time.sleep(3 * (attempt + 1))

def members(cat, ns):
    out, cont = [], {}
    while True:
        d = api({"action":"query","list":"categorymembers","cmtitle":cat,
                 "cmnamespace":ns,"cmlimit":"500", **cont})
        out += d.get("query",{}).get("categorymembers",[])
        cont = d.get("continue") or {}
        if not cont: return out

def files_recursive(cat, depth=1, seen=None):
    seen = seen if seen is not None else set()
    if cat in seen: return []
    seen.add(cat)
    fs = [m["title"] for m in members(cat, 6)]
    if depth > 0:
        for sub in members(cat, 14):
            fs += files_recursive(sub["title"], depth-1, seen)
    return fs

def clean(v):
    return re.sub(r"\s+"," ", re.sub(r"<[^>]+>"," ", html.unescape(v or ""))).strip()

def info(titles):
    out = []
    for i in range(0, len(titles), 20):
        chunk = titles[i:i+20]
        d = api({"action":"query","prop":"imageinfo",
                 "iiprop":"url|size|mime|extmetadata|sha1",
                 "titles":"|".join(chunk)})
        for p in d.get("query",{}).get("pages",[]):
            ii = (p.get("imageinfo") or [{}])[0]
            em = ii.get("extmetadata",{})
            out.append({
                "title": p.get("title"),
                "url": ii.get("url"),
                "descurl": ii.get("descriptionurl"),
                "w": ii.get("width"), "h": ii.get("height"),
                "bytes": ii.get("size"), "mime": ii.get("mime"),
                "sha1": ii.get("sha1"),
                "description": clean(em.get("ImageDescription",{}).get("value")),
                "credit": clean(em.get("Credit",{}).get("value")),
                "artist": clean(em.get("Artist",{}).get("value")),
                "date": clean(em.get("DateTimeOriginal",{}).get("value")),
                "license": clean(em.get("LicenseShortName",{}).get("value")),
                "usageterms": clean(em.get("UsageTerms",{}).get("value")),
            })
        time.sleep(0.8)
    return out

if __name__ == "__main__":
    import os
    cats = json.load(open(sys.argv[1]))
    outdir = sys.argv[2]; os.makedirs(outdir, exist_ok=True)
    for label, spec in cats.items():
        dst = os.path.join(outdir, label + ".json")
        if os.path.exists(dst):
            print(f"{label:<44} cached", flush=True); continue
        cat, depth = spec["cat"], spec.get("depth", 1)
        try:
            titles = sorted(set(files_recursive(cat, depth)))
            print(f"{label:<44} enumerated {len(titles)} titles", flush=True)
            recs = info(titles) if titles else []
        except Exception as e:
            print(f"!! {label}: {e}", flush=True); continue
        json.dump({"category": cat, "count": len(recs), "files": recs},
                  open(dst, "w"), ensure_ascii=False, indent=1)
        tot = sum(r["bytes"] or 0 for r in recs)
        print(f"{label:<44} {len(recs):>5} files  {tot/1048576:>9.1f} MB  DONE", flush=True)
