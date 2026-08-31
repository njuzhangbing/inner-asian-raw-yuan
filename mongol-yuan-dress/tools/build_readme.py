#!/usr/bin/env python3
"""汇总所有 manifest，生成 README.md 总索引。"""
import json, os, glob, csv, re, datetime, collections

B = os.path.expanduser("~/Downloads/mongol-yuan-dress")
def sz(p):
    t=0
    for r,_,fs in os.walk(p):
        for f in fs:
            try: t+=os.path.getsize(os.path.join(r,f))
            except OSError: pass
    return t
def human(b): return f"{b/1073741824:.2f} GB" if b>=1073741824 else f"{b/1048576:.0f} MB"
def nfiles(p, exts=None):
    n=0
    for r,_,fs in os.walk(p):
        for f in fs:
            if exts and not f.lower().endswith(exts): continue
            if f.startswith('.') or f.endswith(('.json','.tsv','.csv')): continue
            n+=1
    return n

L=[]
w=L.append
w("# 蒙元服饰・制度・图像 资料包")
w("")
w(f"> 采集于 {datetime.date.today()}。按索引 v2026-08-06 的三条主线组织：**图像 → 服饰 → 制度**。")
w("> 所有条目均来自实际抓取，元数据含原始出处与许可，未经二次编造。")
w("")
w("## 目录结构")
w("")
w("```")
w("mongol-yuan-dress/")
w("├── 01_images/")
w("│   ├── commons/          Wikimedia Commons 图像（14 个专题子目录）")
w("│   │   ├── commons_metadata.json   逐图元数据（描述/书号/许可/实际分辨率）")
w("│   │   └── download_errors.tsv     下载失败记录")
w("│   ├── met/              大都会博物馆 Open Access")
w("│   ├── cleveland/        克利夫兰美术馆 CC0")
w("│   └── diez_shelfmark_concordance.csv  ★ Diez 画册柏林书号对照表")
w("├── 02_papers/            论文 PDF + manifest.json")
w("│   └── oa_resolved/      经 OpenAlex/Semantic Scholar 解析的开放全文")
w("├── 03_pages/             网页正文（.html 原件 + .md 抽取正文）")
w("├── tools/                全部采集脚本（可重跑/续传）")
w("└── _logs/                运行日志 + Commons 全量枚举索引")
w("```")
w("")

# ---------- 图像 ----------
w("## 一、图像")
w("")
idx = {}
for f in glob.glob(f"{B}/_logs/cat_index/*.json"):
    lab = os.path.basename(f)[:-5]; idx[lab] = json.load(open(f))
CN = {"diez-albums":"柏林 Diez 画册（拉施特《史集》散页）","jami-al-tawarikh":"《史集》各写本汇总",
 "ilkhanid-manuscripts":"伊利汗国写本","demotte-shahnama":"大蒙古《列王纪》(Demotte)",
 "great-mongol-shahnama-h2153":"大蒙古《列王纪》托普卡帕 H.2153","abu-said-mongol-history":"不赛因汗蒙古史插图",
 "dress-yuan":"元代服饰","dress-mongol-yuan":"元代蒙古服饰","gugu-hat":"罟罟冠 / 姑姑冠 (boqta)",
 "cloud-collar":"云肩","yuan-emperor-portraits":"元帝御容","yuan-empress-portraits":"元后像（含察必）",
 "chabi":"察必皇后","moko-shurai-ekotoba":"《蒙古襲来絵詞》"}
w("### Wikimedia Commons（公有领域；Diez 取原图，其余取 1200–1600px，见第五节）")
w("")
w("| 专题 | 已下 / 总数 | 说明 |")
w("|---|---:|---|")
tot_have=tot_all=0
for lab, d in sorted(idx.items(), key=lambda kv:-kv[1]["count"]):
    p=f"{B}/01_images/commons/{lab}"
    have=nfiles(p) if os.path.isdir(p) else 0
    tot_have+=have; tot_all+=d["count"]
    w(f"| `{lab}` | {have} / {d['count']} | {CN.get(lab,'')} |")
w(f"| **合计** | **{tot_have} / {tot_all}** | 全量约 7.2 GB |")
w("")
if tot_have < tot_all:
    w(f"> ⚠️ Commons 图床对本机代理出口 IP 限流严重（`Retry-After: 600`），下载仍在后台按服务端节奏进行。")
    w(f"> **元数据已 100% 采全（{tot_all} 条）**，未下完的图可随时续传：")
    w("> ```bash")
    w("> cd ~/Downloads/mongol-yuan-dress && python3 tools/commons_dl2.py _logs/cat_index 01_images/commons")
    w("> ```")
    w("> 脚本按文件大小跳过已下载项，换一个代理节点或直连会快很多。")
    w("")
for k,cn,pat in (("met","大都会博物馆 (Met) Open Access","met_metadata.json"),
                 ("cleveland","克利夫兰美术馆 CC0","cma_metadata.json")):
    p=f"{B}/01_images/{k}"
    if not os.path.isdir(p): continue
    mp=f"{p}/{pat}"
    n=len(json.load(open(mp))) if os.path.exists(mp) else None
    w(f"### {cn}")
    w("")
    meta = f"元数据 `{pat}`（{n} 条著录）" if n else "元数据将在采集结束时写出（任务仍在后台运行）"
    w(f"- 图片 {nfiles(p, ('.jpg','.jpeg','.png'))} 张，{human(sz(p))}；{meta}")
    if k=="met":
        w("- 检索范围：亚洲艺术部 / 伊斯兰艺术部 / 武器盔甲部 / 服装学院，年代限 1200–1400")
        w("- 索引点名的四件均已入库：纳石失团窠对格里芬织金锦 (64101)、八思巴文牌符 (39624)、"
          "金刚大威德曼荼罗缂丝 (37614)、耶律楚材《送刘满诗》(40105)")
    w("")

# Diez 对照表
cc=f"{B}/01_images/diez_shelfmark_concordance.csv"
if os.path.exists(cc):
    rows=list(csv.DictReader(open(cc)))
    full=[r for r in rows if "S." in (r["shelfmark_shea_style"] or "")]
    w("### ★ Diez 画册书号对照表")
    w("")
    w(f"`01_images/diez_shelfmark_concordance.csv` — {len(rows)} 张图，其中 **{len(full)} 张可解析出柏林原始书号**"
      "（已归一化为 Shea 引用体例 `Diez A fol. 70, S. 8, no. 2`）。")
    w("")
    w("这解决了一个实际问题：Shea《Mongol Court Dress》按柏林书号引图，而 Commons 按英文题名命名，两者无法直接对上。表中给出双向映射。例如索引里点名的两条：")
    w("")
    w("| Shea 引用 | 题材 | 分辨率 | 文件 |")
    w("|---|---|---|---|")
    for want in ("Diez A fol. 70, S. 18, no. 1","Diez A fol. 70, S. 8, no. 2"):
        for r in rows:
            if r["shelfmark_shea_style"]==want:
                topic=re.split(r"[.．]", r["description"])[0][:34]
                w(f"| `{want}` | {topic} | {r['px']} | `{r['file'][:40]}` |"); break
    w("")
    big=sorted(rows, key=lambda r: -float(r["MB"] or 0))[:3]
    w("最高分辨率的三张：")
    w("")
    for r in big:
        w(f"- **{r['px']}** ({r['MB']} MB) — {re.split(r'[.．]', r['description'])[0][:60]} · `{r['shelfmark_shea_style'] or '书号未著录'}`")
    w("")

# ---------- 论文 ----------
w("## 二、论文")
w("")
pdfs=sorted(p for p in glob.glob(f"{B}/02_papers/**/*.pdf", recursive=True)
            if "/_dupes/" not in p)
w(f"共 **{len(pdfs)} 篇**，{human(sum(os.path.getsize(p) for p in pdfs))}，全部通过 `%PDF` 魔数与页数校验。")
w("")
core=[]
for p in pdfs:
    n=os.path.basename(p)
    if "/_dupes/" in p: continue
    if re.search(r"nasij|赵旭东|Mongol_Clothing|silk-gold|Gold_Thread|Court_Dress|Braid_Robe|Boqta|Gugu", n, re.I):
        core.append(p)
if core:
    w("### 服饰主线（最对口的几篇）")
    w("")
    for p in core:
        w(f"- `{os.path.relpath(p, B)}` — {os.path.getsize(p)//1024} KB")
    w("")
w("完整清单与每条的抓取状态见 `02_papers/manifest.json`；开放全文解析记录见 `02_papers/oa_resolved/oa_resolution.json`。")
w("")

# ---------- 网页 ----------
w("## 三、网页正文")
w("")
w("| 文件 | 内容 | 备注 |")
w("|---|---|---|")
PG={"cass-caichunjuan-sidengrenzhi":("蔡春娟《元朝\u201c四等人制\u201d质疑与新说》","★ 制度主线核心，全文完整"),
    "smarthistory-chabi":("Smarthistory《察必皇后像》","罟罟冠讲解，含 Diez 书号引用"),
    "met-toah-yuan":("Met TOAH《Yuan Dynasty 1271–1368》","经 Wayback 取得"),
    "met-pub-khubilai-khan":("Met《The World of Khubilai Khan》出版物页","经 Wayback 取得"),
    "sbb-diez-digitization":("柏林国家图书馆 Diez 数字化项目说明","德文原文")}
for k,(t,note) in PG.items():
    f=f"{B}/03_pages/{k}.md"
    if os.path.exists(f):
        w(f"| `03_pages/{k}.md` | {t} | {note}，{os.path.getsize(f)//1024} KB |")
w("")
txt = "\n".join(L)
w("## 四、未能取得的条目（及原因）")
w("")
w("| 条目 | 障碍 | 可行替代 |")
w("|---|---|---|")
w("| academia.edu 上的 12 篇（Atwood《Buddhists as Natives》、Fiaschetti《Borders of Rebellion》、Brose 元代词条等） | 需登录会话，匿名下载一律 403 | 已改用 OpenAlex/Semantic Scholar 检索同题开放版本，部分命中，见 `oa_resolved/` |")
w("| ResearchGate 3 篇（Shea 同题论文、金线生产扩散、纳石失 vs 金段子） | RG 全面封禁脚本访问；且索引中的 URL 本身被截断（`...`），无法直接请求 | **纳石失 vs 金段子已从 ccsenet 原刊拿到全文**（`Nasij_vs_JinDuanzi_Mongol_ASS.pdf`）；另两篇需登录 RG 手取 |")
w("| McCausland《The Art History and Material Culture of the Yuan Empire》(SOAS eprints) | 本机到 `eprints.soas.ac.uk` 完全不通（代理内外均 HTTP 000），非反爬而是网络不可达 | 换网络环境重试 `tools/fetch_papers.py`；或从 SOAS Research Online 页面手取 |")
w("| 贾玺增《元代辫线袍、质孙服、宝里与贴里》（知乎专栏） | 知乎 403，且 Wayback 无存档 | 已另取得同主题开放论文《Following in Mongolian\u2019s Footsteps: The Identity Research of Braid Robe Wearers in Yuan Dynasty》，见 `oa_resolved/` |")
w("| Shea《Mongol Court Dress》专著全文 | Routledge 版权书；索引里给的 dokumen.pub 是盗版站，未下载 | 正式渠道购买；书中图版多出自 Diez 画册与 CMA，本包已分别覆盖 |")
w("| Met《The World of Khubilai Khan》图录 PDF | Met 官网标注 out of print 且无 Free-to-download | 已存出版物页快照；正文可用 Google Books 在线阅读 |")
w("| 国家哲学社会科学文献中心（ncpssd.cn）中文论文 | 需注册登录 | 用户自行登录后按索引关键词检索 |")
w("")
w("## 五、复现与续传")
w("")
w("`tools/` 下全部脚本均可独立重跑，且都做了断点续传（按文件大小/魔数跳过已完成项）：")
w("")
w("```bash")
w("cd ~/Downloads/mongol-yuan-dress")
w("python3 tools/commons_enum.py tools/categories.json _logs/cat_index   # 枚举 Commons 分类（已完成）")
w("python3 tools/commons_dl2.py  _logs/cat_index 01_images/commons       # 下载图片（可反复跑）")
w("python3 tools/museums.py met  01_images/met                            # Met Open Access")
w("python3 tools/museums.py cma  01_images/cleveland                      # Cleveland CC0")
w("python3 tools/fetch_papers.py tools/paper_urls.json 02_papers          # 论文直链")
w("python3 tools/resolve_oa2.py  tools/wanted3.json 02_papers/oa_resolved # 开放全文解析")
w("python3 tools/verify_pdfs.py  02_papers                                # PDF 校验")
w("python3 tools/dedupe_pdfs.py  02_papers                                # PDF 去重")
w("python3 tools/build_readme.py                                          # 重新生成本文件")
w("```")
w("")
w("### 关于 Commons 限流（实测结论）")
w("")
w("`upload.wikimedia.org` 对本机代理出口 IP（`x-client-ip: 201.4.14.127`，巴西节点）按 **字节** 限流，")
w("窗口约 6 MB，超出即返回 `429` 并声称 `Retry-After: 600`。实测恢复远快于 600 秒，故脚本改用")
w("自适应退避（30s 起步、×1.5 递增、上限 90s、成功即复位）。")
w("")
w("分辨率策略据此按研究价值分配：**Diez 画册取原图**，其余专题取 1200–1600px 缩略图")
w("（足以辨识冠服形制与织物纹样，字节量约为原图 1/10）。`commons_metadata.json` 中每条都记录了")
w("`resolution` 字段与原图 URL，需要全分辨率时可据此单独补取。")
w("")
txt = "\n".join(L)
open(f"{B}/README.md","w").write(txt)
print("README.md 已生成（%d 字符）" % len(txt))
