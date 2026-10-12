# -*- coding: utf-8 -*-
"""核对：页面（index.html）上呈现的文字 与 原文（_src/原始文档.md）是否一致。

三类检查：
  1. 正向——原文里的数字/人名/文献/断言句，页面是否都有（防漏）
  2. 反向——页面上的数字/文本块，原文里是否找得到（防杜撰）
  3. 链接——DOI 双向比对

若存在 _src/rendered.txt（浏览器渲染后的 DOM 文本），
则对「渲染结果」做同样的核对——因为**运行期生成的内容**（Tab 里的数据、
动态渲染的表格）在静态 HTML 里根本看不到。

用法：复制到 <任务>/_src/ 下，改写下面 ===== 断言区 ===== 的四张表，然后：
    python3 _src/页面检查.py    # 先渲染，产出 rendered.txt
    python3 _src/核对脚本.py    # 再核对
"""
import re, sys, html, unicodedata
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
SRC = (BASE / "_src" / "原始文档.md").read_text(encoding="utf-8")
HTML_RAW = (BASE / "index.html").read_text(encoding="utf-8")
RENDERED_PATH = BASE / "_src" / "rendered.txt"

# ---------- 页面文本：静态 HTML(+script) ----------
SCRIPTS = re.findall(r"<script\b.*?</script>", HTML_RAW, flags=re.S | re.I)
body = re.sub(r"<script\b.*?</script>", " ", HTML_RAW, flags=re.S | re.I)
body = re.sub(r"<style\b.*?</style>", " ", body, flags=re.S | re.I)
body = re.sub(r"<!--.*?-->", " ", body, flags=re.S)
BODY_HTML = body

# 块级切分：给块级收尾标签插分隔符，便于逐块比对
BLOCK = r"(?:p|li|h1|h2|h3|h4|div|section|button|footer|nav|ul|ol|tr|td)"
b = re.sub(rf"</{BLOCK}>", "\n", body, flags=re.I)
b = re.sub(r"<br\s*/?>", "\n", b, flags=re.I)
b = re.sub(r"<[^>]+>", " ", b)
BLOCKS = [html.unescape(x).strip() for x in b.split("\n")]

# ---------- 渲染文本（若已生成） ----------
RENDERED = RENDERED_PATH.read_text(encoding="utf-8") if RENDERED_PATH.exists() else None

# 归一化：抹掉零宽字符、空白、各种标点与全角半角差异
# （不抹平这些，「《书名》」vs 斜体、全角括号 vs 半角括号 会被判成不一致）
ZERO = "​‌‍﻿"
DROP = "　 \t\r\n*\\《》「」『』“”‘’\"'（）()[]【】、，,；;：:·.。—－-–…&"


def norm(s):
    s = unicodedata.normalize("NFKC", s)
    for ch in ZERO:
        s = s.replace(ch, "")
    return "".join(c for c in s if c not in DROP)


NS = norm(SRC)
NH = norm(" ".join([html.unescape(re.sub(r"<[^>]+>", " ", body)), " ".join(SCRIPTS)]))
NR = norm(RENDERED) if RENDERED else None
HAY = NR if NR else NH

fails, oks = [], []


def must(label, needle):
    """一条断言：原文该有、页面也该有。三种失败分别报 [漏]/[多]/[无]。"""
    a, h = norm(needle) in NS, norm(needle) in HAY
    if a and h:
        oks.append(label)
    elif a:
        fails.append(f"[漏] {label} —— 原文有、页面无：{needle[:64]}")
    elif h:
        fails.append(f"[多] {label} —— 页面有、原文无：{needle[:64]}")
    else:
        fails.append(f"[无] {label} —— 两边都找不到：{needle[:64]}")


# ============================================================================
# ===== 断言区：每次套版都要重写这一段 ======================================
# ===== 下面全是**格式示例**（虚构内容），照格式换成你这次的真内容 ==========
# ============================================================================

# ===== 1. 数字与散点事实 =====
# (标签, 必须能在原文和页面上都找到的字符串)
for label, n in [
    ("样本量", "<样本量数字>"),
    ("特征数", "<N> 个特征"),
    ("关键百分比", "<X.X>%"),
    ("某结论句", "<原文里的一句完整结论>"),
]:
    must(label, n)

# ===== 2. 分组/人群：名称 + 特征组合 + 权重 =====
# (分组名, [核心特征1, 特征2, ...], [(维度, 权重数值), ...])
# 权重会被拼成 "维度 12.3%" 去核对——页面上的权重表必须与原文逐项一致。
GROUPS = [
    ("<分组A>", ["<特征1>", "<特征2>", "<特征3>"], [("动机", 00.0), ("设备", 00.0)]),
    ("<分组B>", ["<特征1>", "<特征2>", "<特征3>"], [("动机", 00.0), ("设备", 00.0)]),
]
for name, combo, ws in GROUPS:
    must(f"分组名 {name}", name)
    for c in combo:
        must(f"{name}·特征 {c}", c)
    for lab, v in ws:
        must(f"{name}·权重 {lab} {v}%", f"{lab} {v}%")

# ===== 3. 文献条目 =====
# 作者 (年份). 标题 的原样字符串。文献最容易在抄版时被截断或改年份。
for r in [
    "<Author, A. (YYYY). Title of the Work>",
    "<Author, B., & Author, C. (YYYY). Another Title>",
]:
    must(f"文献 {r[:44]}", r)

# ===== 4. 关键断言句 =====
# 原文里那些「一字之差意思就变」的句子。抄版时改写措辞最容易在这里掉字。
for s in [
    "<原文里一句必须逐字保留的断言>",
    "<另一句带限定词的断言，如『在……的前提下』>",
]:
    must(f"断言 {s[:34]}", s)

# ============================================================================
# ===== 断言区结束。以下为通用机制，通常不需要改 =============================
# ============================================================================


# ===== 5. DOI 双向比对 =====
STOP = r"\s)\]　。，,；;）】」》"


def tails(text, with_href):
    """with_href=True 走 href 属性里的 DOI；False 走正文裸写的 DOI:10.xxxx/yyy。"""
    pat = (r'href="https?://[^"]*?(10\.\d{4,}/[^"]+)"' if with_href
           else rf"(10\.\d{{4,}}/[^{STOP}]+)")
    return {m.lower().rstrip("/").rstrip(".") for m in re.findall(pat, text, flags=re.I)}


src_doi, htm_doi = tails(SRC, False), tails(HTML_RAW, True)
miss, extra = sorted(src_doi - htm_doi), sorted(htm_doi - src_doi)
if not miss and not extra:
    oks.append(f"DOI 双向比对通过（{len(src_doi)} 个）")
else:
    if miss:
        fails.append(f"[漏] 页面缺 DOI：{miss}")
    if extra:
        fails.append(f"[多] 页面多 DOI：{extra}")

# ===== 6. 百分比反向扫描（防杜撰） =====
h_p = {p.replace(" ", "") for p in re.findall(r"\d+\.\d+\s*%", HAY if NR else BODY_HTML + " ".join(SCRIPTS))}
s_p = {p.replace(" ", "") for p in re.findall(r"\d+\.\d+\s*%", SRC)}
orphan = sorted(h_p - s_p)
if orphan:
    fails.append(f"[多] 页面出现原文没有的百分比：{orphan}")
else:
    oks.append(f"百分比反向扫描通过（页面 {len(h_p)} 个，原文 {len(s_p)} 个）")

# ===== 7. 文本块反向扫描（防杜撰） =====
# 页面上的每个文本块，拿去原文里找。找不到的都列出来人工过：
#   可接受的连接语 / 标题  vs  新增事实（后者必须删）
src_blocks = {norm(x) for x in re.split(r"[。；\n]", SRC) if len(norm(x)) >= 10}
unmatched = []
for blk in BLOCKS:
    n = norm(blk)
    if len(n) < 10:
        continue
    if n in NS:
        continue
    if any(n in sb or sb in n for sb in src_blocks):
        continue
    unmatched.append(blk)

# ===== 输出 =====
out = ["=" * 72, f"正向核对通过 {len(oks)} 项", "=" * 72]
out += ["  ✓ " + o for o in oks]
if fails:
    out += ["", "!" * 72, f"不合格 {len(fails)} 项", "!" * 72] + ["  ✗ " + f for f in fails]
out += ["", "=" * 72,
        f"文本块反向扫描：{len(unmatched)} 块在原文中找不到对应",
        "（应全部为连接语/自撰文案——逐条确认没有新增事实）",
        "=" * 72]
out += ["  ? " + s for s in unmatched]
out += ["", "核对基准：" + ("浏览器渲染后的 DOM 文本" if RENDERED else "静态 HTML 源码（尚未渲染）"),
        "结论：" + ("全部通过" if not fails else f"存在 {len(fails)} 项不一致，需返工")]

(BASE / "_src" / "核对结果.md").write_text("\n".join(out), encoding="utf-8")
print(f"正向通过 {len(oks)} / 不合格 {len(fails)} / 待确认文本块 {len(unmatched)}")
print("详见 _src/核对结果.md")
sys.exit(1 if fails else 0)
