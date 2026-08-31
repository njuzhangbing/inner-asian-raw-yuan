#!/usr/bin/env python3
"""Commons 下载器 v2：按专题分配分辨率，自适应退避应对字节限流。

实测：upload.wikimedia.org 对本机出口 IP 按 **字节** 限流，窗口约 6 MB。
故核心服饰类取原图，大宗写本库取 1500px 缩略图（够看织物纹样与冠服形制）。
"""
import json, glob, hashlib, os, re, sys, time, urllib.parse, urllib.request, urllib.error

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")
HDRS = {"User-Agent": UA, "Accept": "image/avif,image/webp,image/*,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9", "Referer": "https://commons.wikimedia.org/"}
API = "https://commons.wikimedia.org/w/api.php"

# 分辨率策略：original = 原图；数字 = 该宽度缩略图
RES = {
    # Diez 画册是本题图像证据的核心，保留原图
    "diez-albums": "original",
    # 其余一律 1200px：足以辨识冠服形制、织物纹样与人物等级，
    # 且字节量约为原图的 1/10 —— 在共享代理出口被按字节限流时这是唯一能跑完的配置。
    "gugu-hat": 1600, "cloud-collar": 1600, "chabi": 1600,
    "dress-mongol-yuan": 1600, "dress-yuan": 1600,
    "yuan-empress-portraits": 1600, "yuan-emperor-portraits": 1600,
    "great-mongol-shahnama-h2153": 1600, "abu-said-mongol-history": 1600,
    "moko-shurai-ekotoba": 1200, "ilkhanid-manuscripts": 1200,
    "demotte-shahnama": 1200, "jami-al-tawarikh": 1200,
}
ORDER = ["diez-albums","gugu-hat","cloud-collar","dress-mongol-yuan","dress-yuan","chabi",
         "yuan-empress-portraits","yuan-emperor-portraits","great-mongol-shahnama-h2153",
         "abu-said-mongol-history","moko-shurai-ekotoba","ilkhanid-manuscripts",
         "demotte-shahnama","jami-al-tawarikh"]
BIG_CAP = 6 * 1048576      # 原图超过 8MB 的，改取 2500px（否则一张就吃光配额）

backoff = [30]
def fetch(url, timeout=300):
    """带自适应退避的 GET。服务端 Retry-After 恒为 600，但实测恢复远快于此。"""
    for attempt in range(7):
        try:
            req = urllib.request.Request(url, headers=HDRS)
            with urllib.request.urlopen(req, timeout=timeout) as r:
                data = r.read()
            backoff[0] = 30   # 成功即复位
            return data
        except urllib.error.HTTPError as e:
            if e.code == 429:
                w = backoff[0]
                print(f"    [429] 退避 {w}s", flush=True)
                time.sleep(w); backoff[0] = min(int(backoff[0] * 1.5), 90); continue
            if attempt >= 2: raise
            time.sleep(5 * (attempt + 1))
        except Exception:
            if attempt >= 2: raise
            time.sleep(5 * (attempt + 1))
    raise RuntimeError("429 retries exhausted")

def api(params):
    p = dict(params, format="json", formatversion="2")
    for a in range(9):
        try:
            req = urllib.request.Request(API + "?" + urllib.parse.urlencode(p),
                                         headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=60) as r:
                d = json.loads(r.read().decode())
            time.sleep(0.4); return d
        except urllib.error.HTTPError as e:
            if e.code == 429:
                w = 20 * (a + 1)
                print(f"    [API 429 -> API 退避 {w}s]", flush=True)
                time.sleep(w); continue
            if a == 4: raise
            time.sleep(3 * (a + 1))
        except Exception:
            if a == 4: raise
            time.sleep(3 * (a + 1))

def thumburls(titles, width):
    """批量取指定宽度的缩略图 URL（API 调用不计入字节限流）。"""
    out = {}
    for i in range(0, len(titles), 20):
        d = api({"action":"query","prop":"imageinfo","iiprop":"url|size",
                 "iiurlwidth":str(width),"titles":"|".join(titles[i:i+20])})
        for p in d.get("query",{}).get("pages",[]):
            ii = (p.get("imageinfo") or [{}])[0]
            if ii.get("thumburl"):
                out[p["title"]] = (ii["thumburl"], ii.get("thumbwidth"), ii.get("thumbheight"))
    return out

def safe(t, n=120):
    t = re.sub(r"^File:", "", t or "")
    t = re.sub(r"[^\w一-鿿ぁ-ヿ.\- ]+", "_", t)
    return re.sub(r"[\s_]+", "_", t).strip("_. ")[:n] or "file"

if __name__ == "__main__":
    idx_dir, base = sys.argv[1], sys.argv[2]
    os.makedirs(base, exist_ok=True)
    mpath = os.path.join(base, "commons_metadata.json")
    manifest = json.load(open(mpath)) if os.path.exists(mpath) else {}
    err = open(os.path.join(base, "download_errors.tsv"), "a")
    grand_new = grand_bytes = 0

    labels = [os.path.basename(f)[:-5] for f in glob.glob(os.path.join(idx_dir, "*.json"))]
    labels.sort(key=lambda l: ORDER.index(l) if l in ORDER else 99)

    for label in labels:
        d = json.load(open(os.path.join(idx_dir, label + ".json")))
        res = RES.get(label, 1500)
        outdir = os.path.join(base, label); os.makedirs(outdir, exist_ok=True)
        recs = d["files"]
        # 需要缩略图的（整类缩略 或 原图过大）
        need = [r["title"] for r in recs
                if res != "original" or (r.get("bytes") or 0) > BIG_CAP]
        tmap = thumburls(need, 2500 if res == "original" else res) if need else {}
        print(f"\n### {label}  ({len(recs)} 张, 策略={'原图' if res=='original' else str(res)+'px'})",
              flush=True)
        entries, new, cached, failed = [], 0, 0, 0
        for r in recs:
            title = r["title"]
            use_thumb = title in tmap
            url, tw, th = tmap.get(title, (None, None, None))
            url = url or (r.get("url") or "").split("?")[0]
            if not url: continue
            ext = ".jpg" if use_thumb else os.path.splitext(url)[1] or ".jpg"
            dst = os.path.join(outdir, safe(title).rsplit(".", 1)[0] + ext)
            exp = None if use_thumb else r.get("bytes")
            if os.path.exists(dst) and os.path.getsize(dst) > 5000 and \
               (exp is None or abs(os.path.getsize(dst) - exp) < 64):
                cached += 1
            else:
                try:
                    data = fetch(url)
                    if not use_thumb and r.get("sha1") and hashlib.sha1(data).hexdigest() != r["sha1"]:
                        raise RuntimeError("sha1 mismatch")
                    open(dst, "wb").write(data)
                    new += 1; grand_new += 1; grand_bytes += len(data)
                    if new % 10 == 0:
                        print(f"    {new} new / {cached} cached  "
                              f"({grand_bytes/1048576:.0f} MB 本次)", flush=True)
                except Exception as e:
                    failed += 1
                    err.write(f"{label}\t{title}\t{type(e).__name__}: {e}\n"); err.flush()
                    continue
                time.sleep(0.5)
            entries.append({
                "file": os.path.relpath(dst, base),
                "resolution": (f"{tw}x{th} (thumb)" if use_thumb else f"{r.get('w')}x{r.get('h')} (original)"),
                **{k: r.get(k) for k in ("title","descurl","w","h","bytes","mime","sha1",
                                          "description","credit","artist","date","license")}})
        manifest[label] = {"category": d["category"], "policy":
                           ("original" if res == "original" else f"{res}px thumbnail"),
                           "count": len(entries), "files": entries}
        json.dump(manifest, open(mpath, "w"), ensure_ascii=False, indent=1)
        print(f"    -> new {new} / cached {cached} / fail {failed}", flush=True)
    print(f"\nDONE  新下载 {grand_new} 张 / {grand_bytes/1073741824:.2f} GB", flush=True)
