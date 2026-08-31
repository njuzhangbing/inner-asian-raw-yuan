#!/usr/bin/env python3
"""按枚举结果下载 Commons 原图，sha1 校验 + 断点续传 + 并发。"""
import json, glob, hashlib, os, queue, re, sys, threading, time, urllib.parse, urllib.request, urllib.error

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")
HDRS = {"User-Agent": UA,
        "Accept": "image/avif,image/webp,image/*,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://commons.wikimedia.org/"}
def safe(s, n=120):
    s = re.sub(r"^File:", "", s or "")
    s = re.sub(r"[^\w一-鿿ぁ-ヿ.\- ]+", "_", s)
    return re.sub(r"[\s_]+", "_", s).strip("_. ")[:n] or "file"

lock = threading.Lock()
brake = threading.Event(); brake.set()   # set=放行, clear=全线暂停
BACKOFF = [30]                            # 自适应退避秒数（撞限流翻倍，成功则回落）
stats = {"ok":0,"cached":0,"fail":0,"bytes":0}

def worker(q, base, log):
    while True:
        try: label, rec = q.get_nowait()
        except queue.Empty: return
        try:
            d = os.path.join(base, label); os.makedirs(d, exist_ok=True)
            dst = os.path.join(d, safe(rec["title"]))
            if os.path.exists(dst) and rec.get("bytes") and abs(os.path.getsize(dst)-rec["bytes"]) < 64:
                with lock: stats["cached"] += 1
                q.task_done(); continue
            url = rec["url"].split("?")[0]
            data = None
            for attempt in range(6):
                brake.wait()                       # 若全线刹车，等解除
                try:
                    req = urllib.request.Request(url, headers=HDRS)
                    with urllib.request.urlopen(req, timeout=300) as r: data = r.read()
                    break
                except urllib.error.HTTPError as e:
                    if e.code == 429:
                        # 服务端 Retry-After 恒为 600，但实测窗口恢复快得多，
                        # 因此用自适应退避：30 -> 60 -> 120 -> 240 -> 480，成功后重置。
                        if brake.is_set():
                            brake.clear()
                            w = BACKOFF[0]
                            print(f"  [429] 暂停 {w}s（自适应，服务端声称 "
                                  f"{e.headers.get('Retry-After')}s）", flush=True)
                            time.sleep(w)
                            BACKOFF[0] = min(BACKOFF[0] * 2, 480)
                            brake.set()
                        else:
                            brake.wait()
                        continue
                    if attempt >= 2: raise
                    time.sleep(5 * (attempt + 1))
                except Exception:
                    if attempt >= 2: raise
                    time.sleep(5 * (attempt + 1))
            if data is None: raise RuntimeError("429 retries exhausted")
            got = hashlib.sha1(data).hexdigest()
            if rec.get("sha1") and got != rec["sha1"]:
                with lock:
                    stats["fail"] += 1
                    log.write(f"SHA1MISMATCH\t{label}\t{rec['title']}\n"); log.flush()
                q.task_done(); continue
            open(dst,"wb").write(data)
            with lock:
                stats["ok"] += 1; stats["bytes"] += len(data)
                BACKOFF[0] = max(30, BACKOFF[0] // 2)   # 成功则回落
                if stats["ok"] % 10 == 0:
                    print(f"  {stats['ok']} new / {stats['cached']} cached / {stats['fail']} fail "
                          f"/ {stats['bytes']/1073741824:.2f} GB", flush=True)
        except Exception as e:
            with lock:
                stats["fail"] += 1
                log.write(f"FAIL\t{label}\t{rec.get('title')}\t{type(e).__name__}: {e}\n"); log.flush()
        finally:
            q.task_done(); time.sleep(0.8)

if __name__ == "__main__":
    idx_dir, base = sys.argv[1], sys.argv[2]
    q = queue.Queue()
    manifest = {}
    # 按研究价值排序：服饰/肖像类优先，大宗写本图库殿后
    PRIO = ["diez-albums","gugu-hat","cloud-collar","dress-mongol-yuan","dress-yuan",
            "chabi","yuan-empress-portraits","yuan-emperor-portraits",
            "great-mongol-shahnama-h2153","abu-said-mongol-history",
            "moko-shurai-ekotoba","ilkhanid-manuscripts","demotte-shahnama","jami-al-tawarikh"]
    files = glob.glob(os.path.join(idx_dir, "*.json"))
    files.sort(key=lambda f: (PRIO.index(os.path.basename(f)[:-5])
                              if os.path.basename(f)[:-5] in PRIO else 99,
                              os.path.basename(f)))
    for f in files:
        label = os.path.basename(f)[:-5]
        d = json.load(open(f))
        manifest[label] = {"category": d["category"], "files": []}
        for rec in d["files"]:
            if not rec.get("url"): continue
            q.put((label, rec))
            manifest[label]["files"].append(
                {"file": os.path.join(label, safe(rec["title"])), **{k: rec.get(k) for k in
                 ("title","descurl","w","h","bytes","mime","sha1","description","credit","artist","date","license")}})
    total = q.qsize(); print(f"queued {total} files", flush=True)
    os.makedirs(base, exist_ok=True)
    json.dump(manifest, open(os.path.join(base,"commons_metadata.json"),"w"), ensure_ascii=False, indent=1)
    log = open(os.path.join(base,"download_errors.tsv"),"a")
    ts = [threading.Thread(target=worker, args=(q, base, log), daemon=True) for _ in range(1)]
    [t.start() for t in ts]; [t.join() for t in ts]
    print(f"DONE  new={stats['ok']} cached={stats['cached']} fail={stats['fail']} "
          f"{stats['bytes']/1073741824:.2f} GB", flush=True)
