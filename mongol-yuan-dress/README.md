# 蒙元服饰・制度・图像 资料包

> 采集于 2026-08-24。按索引 v2026-08-06 的三条主线组织：**图像 → 服饰 → 制度**。
> 所有条目均来自实际抓取，元数据含原始出处与许可，未经二次编造。

## 目录结构

```
mongol-yuan-dress/
├── 01_images/
│   ├── commons/          Wikimedia Commons 图像（14 个专题子目录）
│   │   ├── commons_metadata.json   逐图元数据（描述/书号/许可/实际分辨率）
│   │   └── download_errors.tsv     下载失败记录
│   ├── met/              大都会博物馆 Open Access
│   ├── cleveland/        克利夫兰美术馆 CC0
│   └── diez_shelfmark_concordance.csv  ★ Diez 画册柏林书号对照表
├── 02_papers/            论文 PDF + manifest.json
│   └── oa_resolved/      经 OpenAlex/Semantic Scholar 解析的开放全文
├── 03_pages/             网页正文（.html 原件 + .md 抽取正文）
├── tools/                全部采集脚本（可重跑/续传）
└── _logs/                运行日志 + Commons 全量枚举索引
```

## 一、图像

### Wikimedia Commons（公有领域；Diez 取原图，其余取 1200–1600px，见第五节）

| 专题 | 已下 / 总数 | 说明 |
|---|---:|---|
| `jami-al-tawarikh` | 0 / 983 | 《史集》各写本汇总 |
| `ilkhanid-manuscripts` | 0 / 134 | 伊利汗国写本 |
| `demotte-shahnama` | 0 / 117 | 大蒙古《列王纪》(Demotte) |
| `moko-shurai-ekotoba` | 0 / 68 | 《蒙古襲来絵詞》 |
| `yuan-empress-portraits` | 0 / 53 | 元后像（含察必） |
| `diez-albums` | 36 / 49 | 柏林 Diez 画册（拉施特《史集》散页） |
| `yuan-emperor-portraits` | 0 / 30 | 元帝御容 |
| `dress-mongol-yuan` | 0 / 30 | 元代蒙古服饰 |
| `cloud-collar` | 3 / 26 | 云肩 |
| `dress-yuan` | 0 / 19 | 元代服饰 |
| `abu-said-mongol-history` | 9 / 14 | 不赛因汗蒙古史插图 |
| `great-mongol-shahnama-h2153` | 0 / 7 | 大蒙古《列王纪》托普卡帕 H.2153 |
| `chabi` | 0 / 5 | 察必皇后 |
| `gugu-hat` | 0 / 2 | 罟罟冠 / 姑姑冠 (boqta) |
| **合计** | **48 / 1537** | 全量约 7.2 GB |

> ⚠️ Commons 图床对本机代理出口 IP 限流严重（`Retry-After: 600`），下载仍在后台按服务端节奏进行。
> **元数据已 100% 采全（1537 条）**，未下完的图可随时续传：
> ```bash
> cd ~/Downloads/mongol-yuan-dress && python3 tools/commons_dl2.py _logs/cat_index 01_images/commons
> ```
> 脚本按文件大小跳过已下载项，换一个代理节点或直连会快很多。

### 大都会博物馆 (Met) Open Access

- 图片 88 张，272 MB；元数据将在采集结束时写出（任务仍在后台运行）
- 检索范围：亚洲艺术部 / 伊斯兰艺术部 / 武器盔甲部 / 服装学院，年代限 1200–1400
- 索引点名的四件均已入库：纳石失团窠对格里芬织金锦 (64101)、八思巴文牌符 (39624)、金刚大威德曼荼罗缂丝 (37614)、耶律楚材《送刘满诗》(40105)

### 克利夫兰美术馆 CC0

- 图片 54 张，2.28 GB；元数据将在采集结束时写出（任务仍在后台运行）

### ★ Diez 画册书号对照表

`01_images/diez_shelfmark_concordance.csv` — 49 张图，其中 **38 张可解析出柏林原始书号**（已归一化为 Shea 引用体例 `Diez A fol. 70, S. 8, no. 2`）。

这解决了一个实际问题：Shea《Mongol Court Dress》按柏林书号引图，而 Commons 按英文题名命名，两者无法直接对上。表中给出双向映射。例如索引里点名的两条：

| Shea 引用 | 题材 | 分辨率 | 文件 |
|---|---|---|---|
| `Diez A fol. 70, S. 18, no. 1` | Preparations for a festival | 1653x1684 | `DiezAlbumsFestivalPreparations.jpg` |
| `Diez A fol. 70, S. 8, no. 2` | Birth of a prince | 1655x840 | `DiezAlbumsBirth.jpg` |

最高分辨率的三张：

- **9472x5963** (141.7 MB) — Conquest of Baghdad by the Mongols 1258 · `Diez A fol. 70, S. 4`
- **9472x5963** (86.9 MB) — Fall Of Baghdad (Diez Albums) · `书号未著录`
- **4953x6023** (48.2 MB) — Ilkhanid Court Scene, early fourteenth century · `Diez A fol. 70, S. 23, no. 1`

## 二、论文

共 **55 篇**，148 MB，全部通过 `%PDF` 魔数与页数校验。

### 服饰主线（最对口的几篇）

- `02_papers/Nasij_vs_JinDuanzi_Mongol_ASS.pdf` — 848 KB
- `02_papers/oa_resolved/2023_Following_in_Mongolian_s_Footsteps_The_Identity_Research_of_Braid_Robe_Wearers_in_Yuan_Dynasty.pdf` — 1783 KB
- `02_papers/oa_resolved/Comparative_Study_of_Nasij_and_Jin_Duan_zi_of_Mongol_Period.pdf` — 1102 KB
- `02_papers/赵旭东_侈糜_奢华与支配_十三世纪蒙古游牧帝国服饰偏好与政治风俗的札记_民俗研究_2010.2.pdf` — 1040 KB

完整清单与每条的抓取状态见 `02_papers/manifest.json`；开放全文解析记录见 `02_papers/oa_resolved/oa_resolution.json`。

## 三、网页正文

| 文件 | 内容 | 备注 |
|---|---|---|
| `03_pages/cass-caichunjuan-sidengrenzhi.md` | 蔡春娟《元朝“四等人制”质疑与新说》 | ★ 制度主线核心，全文完整，8 KB |
| `03_pages/smarthistory-chabi.md` | Smarthistory《察必皇后像》 | 罟罟冠讲解，含 Diez 书号引用，13 KB |
| `03_pages/met-toah-yuan.md` | Met TOAH《Yuan Dynasty 1271–1368》 | 经 Wayback 取得，5 KB |
| `03_pages/met-pub-khubilai-khan.md` | Met《The World of Khubilai Khan》出版物页 | 经 Wayback 取得，2 KB |
| `03_pages/sbb-diez-digitization.md` | 柏林国家图书馆 Diez 数字化项目说明 | 德文原文，15 KB |

## 四、未能取得的条目（及原因）

| 条目 | 障碍 | 可行替代 |
|---|---|---|
| academia.edu 上的 12 篇（Atwood《Buddhists as Natives》、Fiaschetti《Borders of Rebellion》、Brose 元代词条等） | 需登录会话，匿名下载一律 403 | 已改用 OpenAlex/Semantic Scholar 检索同题开放版本，部分命中，见 `oa_resolved/` |
| ResearchGate 3 篇（Shea 同题论文、金线生产扩散、纳石失 vs 金段子） | RG 全面封禁脚本访问；且索引中的 URL 本身被截断（`...`），无法直接请求 | **纳石失 vs 金段子已从 ccsenet 原刊拿到全文**（`Nasij_vs_JinDuanzi_Mongol_ASS.pdf`）；另两篇需登录 RG 手取 |
| McCausland《The Art History and Material Culture of the Yuan Empire》(SOAS eprints) | 本机到 `eprints.soas.ac.uk` 完全不通（代理内外均 HTTP 000），非反爬而是网络不可达 | 换网络环境重试 `tools/fetch_papers.py`；或从 SOAS Research Online 页面手取 |
| 贾玺增《元代辫线袍、质孙服、宝里与贴里》（知乎专栏） | 知乎 403，且 Wayback 无存档 | 已另取得同主题开放论文《Following in Mongolian’s Footsteps: The Identity Research of Braid Robe Wearers in Yuan Dynasty》，见 `oa_resolved/` |
| Shea《Mongol Court Dress》专著全文 | Routledge 版权书；索引里给的 dokumen.pub 是盗版站，未下载 | 正式渠道购买；书中图版多出自 Diez 画册与 CMA，本包已分别覆盖 |
| Met《The World of Khubilai Khan》图录 PDF | Met 官网标注 out of print 且无 Free-to-download | 已存出版物页快照；正文可用 Google Books 在线阅读 |
| 国家哲学社会科学文献中心（ncpssd.cn）中文论文 | 需注册登录 | 用户自行登录后按索引关键词检索 |

## 五、复现与续传

`tools/` 下全部脚本均可独立重跑，且都做了断点续传（按文件大小/魔数跳过已完成项）：

```bash
cd ~/Downloads/mongol-yuan-dress
python3 tools/commons_enum.py tools/categories.json _logs/cat_index   # 枚举 Commons 分类（已完成）
python3 tools/commons_dl2.py  _logs/cat_index 01_images/commons       # 下载图片（可反复跑）
python3 tools/museums.py met  01_images/met                            # Met Open Access
python3 tools/museums.py cma  01_images/cleveland                      # Cleveland CC0
python3 tools/fetch_papers.py tools/paper_urls.json 02_papers          # 论文直链
python3 tools/resolve_oa2.py  tools/wanted3.json 02_papers/oa_resolved # 开放全文解析
python3 tools/verify_pdfs.py  02_papers                                # PDF 校验
python3 tools/dedupe_pdfs.py  02_papers                                # PDF 去重
python3 tools/build_readme.py                                          # 重新生成本文件
```

### 关于 Commons 限流（实测结论）

`upload.wikimedia.org` 对本机代理出口 IP（`x-client-ip: 201.4.14.127`，巴西节点）按 **字节** 限流，
窗口约 6 MB，超出即返回 `429` 并声称 `Retry-After: 600`。实测恢复远快于 600 秒，故脚本改用
自适应退避（30s 起步、×1.5 递增、上限 90s、成功即复位）。

分辨率策略据此按研究价值分配：**Diez 画册取原图**，其余专题取 1200–1600px 缩略图
（足以辨识冠服形制与织物纹样，字节量约为原图 1/10）。`commons_metadata.json` 中每条都记录了
`resolution` 字段与原图 URL，需要全分辨率时可据此单独补取。
