#!/usr/bin/env python3
"""Met Open Access + Cleveland CC0：检索 -> 元数据 -> 下高清图（stdlib only）。"""
import json, os, sys, time, urllib.parse, urllib.request, urllib.error, re

UA = "MongolDressResearch/1.0 (academic use)"
def get(url, timeout=90, tries=4):
    for a in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept":"application/json,*/*"})
            with urllib.request.urlopen(req, timeout=timeout) as r: return r.read()
        except Exception as e:
            if a == tries-1: raise
            time.sleep(2*(a+1))

def jget(url): return json.loads(get(url).decode("utf-8"))
def safe(s, n=90):
    s = re.sub(r'[^\w一-鿿.\- ]+', '_', (s or "untitled"))
    return re.sub(r'\s+', '_', s).strip('_')[:n] or "untitled"

def dl(url, dst):
    if os.path.exists(dst) and os.path.getsize(dst) > 2048: return "cached"
    try:
        data = get(url, timeout=240)
    except Exception as e:
        return f"FAIL {type(e).__name__}"
    if len(data) < 2048: return "FAIL tiny"
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    open(dst, "wb").write(data)
    return f"{len(data)/1048576:.1f}MB"

# ---------------- MET ----------------
MET = "https://collectionapi.metmuseum.org/public/collection/v1"
MET_SPECS = [
    (6,  ["Yuan","Mongol","nasij","paiza","textile","silk","robe","portrait","kesi","gold"]),
    (14, ["Mongol","Ilkhanid","Yuan","nasij","textile","silk","cloth of gold"]),
    (4,  ["Mongol","Yuan","Asian"]),
    (8,  ["Mongol","Yuan"]),
]
MET_EXTRA = [64101, 39624, 37614, 40105]
# 只有命中这些词才下图（元数据全留）
IMG_RE = re.compile(r"Yuan|Mongol|Ilkhan|Il-khan|nasij|cloth of gold|Textile|Costume|Silk", re.I)

def met(outdir):
    ids = set(MET_EXTRA)
    for dept, qs in MET_SPECS:
        for q in qs:
            try:
                d = jget(f"{MET}/search?hasImages=true&departmentId={dept}"
                         f"&dateBegin=1200&dateEnd=1400&q={urllib.parse.quote(q)}")
                got = d.get("objectIDs") or []
                ids.update(got); print(f"  [met] dept{dept} {q!r}: {len(got)}", flush=True)
            except Exception as e: print(f"  [met] dept{dept} {q!r} FAIL {e}", flush=True)
            time.sleep(0.35)
    print(f"  [met] union candidates: {len(ids)}", flush=True)
    recs, ndl = [], 0
    for i, oid in enumerate(sorted(ids)):
        try: o = jget(f"{MET}/objects/{oid}")
        except Exception: continue
        rec = {k: o.get(k) for k in ("objectID","title","objectDate","objectBeginDate","objectEndDate",
               "period","dynasty","culture","medium","dimensions","classification","objectName",
               "department","creditLine","accessionNumber","objectURL","artistDisplayName",
               "isPublicDomain","geographyType","country","region")}
        rec["localFiles"] = []
        blob = " ".join(str(o.get(k) or "") for k in
              ("period","dynasty","culture","objectDate","title","medium","classification","objectName"))
        if o.get("isPublicDomain") and o.get("primaryImage") and IMG_RE.search(blob):
            base = f"met_{o['objectID']}_{safe(o.get('title'))}"
            for n, u in enumerate([o["primaryImage"]] + (o.get("additionalImages") or [])):
                ext = os.path.splitext(urllib.parse.urlparse(u).path)[1] or ".jpg"
                dst = os.path.join(outdir, "files", f"{base}_{n:02d}{ext}")
                st = dl(u, dst)
                if not st.startswith("FAIL"):
                    rec["localFiles"].append(os.path.relpath(dst, outdir)); ndl += 1
                print(f"    {os.path.basename(dst)[:66]:<68} {st}", flush=True)
        recs.append(rec)
        if i % 50 == 0: print(f"  [met] {i}/{len(ids)} scanned, {ndl} imgs", flush=True)
        time.sleep(0.1)
    json.dump(recs, open(os.path.join(outdir, "met_metadata.json"), "w"), ensure_ascii=False, indent=1)
    print(f"  [met] {len(recs)} objects indexed, {ndl} images downloaded", flush=True)
    return len(recs)

# ---------------- CLEVELAND ----------------
CMA = "https://openaccess-api.clevelandart.org/api/artworks/"
CMA_QUERIES = ["Yuan dynasty","Mongol","Ilkhanid","cloth of gold","nasij","Yuan textile","silk Yuan"]

def cma(outdir):
    seen, recs = {}, []
    for q in CMA_QUERIES:
        try:
            d = jget(CMA + "?" + urllib.parse.urlencode({"q":q,"limit":100,"cc0":1,"has_image":1}))
        except Exception as e:
            print(f"  [cma] {q!r} FAIL {e}", flush=True); continue
        data = d.get("data") or []
        print(f"  [cma] {q!r}: {len(data)}", flush=True)
        for a in data: seen[a["id"]] = a
        time.sleep(0.4)
    for a in seen.values():
        blob = " ".join(str(a.get(k) or "") for k in ("culture","creation_date","title","technique","type","department"))
        if not re.search(r"Yuan|Mongol|Ilkhan|13th|14th", blob, re.I): continue
        imgs = a.get("images") or {}
        # full 常是 80MB+ 的 TIFF 转档；print(~3000px) 对服饰研究足够且快 20 倍
        u = (imgs.get("print") or imgs.get("web") or imgs.get("full") or {}).get("url")
        if not u: continue
        dst = os.path.join(outdir, "files", f"cma_{a['id']}_{safe(a.get('title'))}.jpg")
        st = dl(u, dst)
        print(f"    {os.path.basename(dst)[:70]:<72} {st}", flush=True)
        recs.append({k: a.get(k) for k in ("id","accession_number","title","creation_date","culture",
                     "technique","type","department","creditline","url","share_license_status","measurements")}
                    | {"localFile": os.path.relpath(dst, outdir) if not st.startswith("FAIL") else None})
    json.dump(recs, open(os.path.join(outdir, "cma_metadata.json"), "w"), ensure_ascii=False, indent=1)
    return len(recs)

if __name__ == "__main__":
    which, out = sys.argv[1], sys.argv[2]
    os.makedirs(out, exist_ok=True)
    print(("MET" if which=="met" else "CMA"), "->", out, flush=True)
    n = met(out) if which == "met" else cma(out)
    print("RECORDS:", n)
