# -*- coding: utf-8 -*-
"""页面 BUG 检查：用独立 chromium 真渲染，跑交互、抓控制台、查溢出、出截图。

产出：
  _src/rendered.txt      渲染后可见文本（供核对脚本做二次比对）
  _src/BUG检查报告.md     检查结果
  .shots/                截图

用法：复制到 <任务>/_src/ 下，改写下面 ===== 断言区 =====，然后
    python3 _src/页面检查.py
依赖：python3 + playwright

⚠️ 用**独立 chromium 实例**，不走共享的浏览器自动化服务——那种服务有 profile 锁，
   多个任务同时跑会撞车。
"""
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

BASE = Path(__file__).resolve().parent.parent
URL = (BASE / "index.html").as_uri()
SHOTS = BASE / ".shots"
SHOTS.mkdir(exist_ok=True)

# ============================================================================
# ===== 断言区：每次套版都要重写这一段 ======================================
# ============================================================================

# 页面标题里必须包含的词
TITLE_MUST = "<标题关键词>"

# 交互区块（Tab / 折叠区 / 分页）——按你这次的页面结构改。
# 格式：{ 区块标识: 切换后详情里必须出现的文字 }
TABS = {
    "<tab-id-1>": "<该 tab 的标题文字>",
    "<tab-id-2>": "<该 tab 的标题文字>",
}
TAB_COUNT = 2                     # 期望的 tab 数量
TAB_SELECTOR = ".people-tab"      # tab 按钮的选择器
TAB_DETAIL_SELECTOR = "#peopleDetail"   # 详情容器

# 某个 tab 展开后的明细断言（可选）。None = 跳过这项检查。
# 格式：[["1", "<维度名>", "<X.X>%"], ...]
EXPECT_DETAIL = None              # 例：[["1", "动机", "00.0%"], ["2", "设备", "00.0%"]]
DETAIL_ROW_SELECTOR = ".weight-item"
TAB_FOR_DETAIL = "<tab-id-1>"

# 表格行数断言（可选）。None = 跳过。
EXPECT_TABLE_ROWS = None          # 例：9
TABLE_ROW_SELECTOR = "#wgrid .wrow"

# 横向溢出扫描的视口宽度（这些是通用档位，一般不用改）
VIEWPORTS = (1920, 1600, 1440, 1296, 1200, 900, 691, 576, 375)

# 缩放实测（可选）。若页面用 `body { zoom }` 做整体缩放，这里断言实际生效的系数。
# None = 跳过。
EXPECT_ZOOM = None                # 例：1.44
ZOOM_PROBE = ".topbar-logo-mark"  # 探针选择器，见下方说明

# ============================================================================
# ===== 断言区结束。以下为通用机制，通常不需要改 =============================
# ============================================================================

report, problems, rendered = [], [], []


def log(ok, msg):
    report.append(("  OK  " if ok else "  FAIL") + "  " + msg)
    if not ok:
        problems.append(msg)


with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={"width": 1440, "height": 1000})

    console_errs, page_errs, failed_req = [], [], []
    page.on("console", lambda m: console_errs.append(f"{m.type}: {m.text}") if m.type == "error" else None)
    page.on("pageerror", lambda e: page_errs.append(str(e)))
    page.on("requestfailed", lambda r: failed_req.append(f"{r.url} :: {r.failure}"))

    page.goto(URL, wait_until="load", timeout=30000)
    page.wait_for_timeout(1500)

    # ---------- 1. 控制台与未捕获异常 ----------
    log(not console_errs, f"console.error 数量 = {len(console_errs)}" + (f" -> {console_errs}" if console_errs else ""))
    log(not page_errs, f"未捕获 JS 异常 = {len(page_errs)}" + (f" -> {page_errs}" if page_errs else ""))

    # ---------- 2. 标题 ----------
    title = page.title()
    log(TITLE_MUST in title, f"页面标题 = {title}（应含「{TITLE_MUST}」）")

    # ---------- 3. 导航锚点必须全部命中真实 section ----------
    nav_ids = page.eval_on_selector_all(".topbar-nav a", "els => els.map(e => e.getAttribute('href'))")
    sec_ids = page.eval_on_selector_all("section[id]", "els => els.map(e => e.id)")
    bad_nav = [h for h in nav_ids if h and h.lstrip("#") not in sec_ids]
    log(not bad_nav, f"导航锚点全部命中 section：{nav_ids}（无效：{bad_nav}）")

    # ---------- 4. 交互区块切换 ----------
    tabs = page.eval_on_selector_all(TAB_SELECTOR, "els => els.length")
    log(tabs == TAB_COUNT, f"交互区块数量 = {tabs}（应为 {TAB_COUNT}）")

    for t, expect_text in TABS.items():
        page.click(f'{TAB_SELECTOR}[data-type="{t}"]')
        page.wait_for_timeout(400)
        txt = page.inner_text(TAB_DETAIL_SELECTOR)
        active = page.eval_on_selector(f"{TAB_SELECTOR}.active", "e => e.dataset.type")
        log(active == t and expect_text in txt,
            f"Tab[{t}] 切换正常，详情含「{expect_text}」（active={active}）")

    # ---------- 5. 明细行断言（可选） ----------
    if EXPECT_DETAIL is not None:
        page.click(f'{TAB_SELECTOR}[data-type="{TAB_FOR_DETAIL}"]')
        page.wait_for_timeout(400)
        got = page.eval_on_selector_all(DETAIL_ROW_SELECTOR, """els => els.map(e => [
            e.querySelector('.weight-rank')?.innerText.trim(),
            e.querySelector('.weight-name')?.innerText.trim(),
            e.querySelector('.weight-num')?.innerText.trim()])""")
        log(got == EXPECT_DETAIL, f"明细行渲染正确 = {got}")

    # ---------- 6. 表格行数断言（可选） ----------
    if EXPECT_TABLE_ROWS is not None:
        rows = page.eval_on_selector_all(TABLE_ROW_SELECTOR, "els => els.length")
        log(rows == EXPECT_TABLE_ROWS, f"表格行数 = {rows}（应为 {EXPECT_TABLE_ROWS}）")

    # ---------- 7. 横向溢出（逐档视口，必查） ----------
    for w in VIEWPORTS:
        page.set_viewport_size({"width": w, "height": 900})
        page.wait_for_timeout(300)
        over = page.evaluate(
            "() => document.documentElement.scrollWidth - document.documentElement.clientWidth")
        log(over <= 1, f"视口 {w}px 横向溢出 = {over}px")

    # ---------- 8. 缩放系数实测（可选） ----------
    if EXPECT_ZOOM is not None:
        page.set_viewport_size({"width": 1440, "height": 1000})
        page.wait_for_timeout(400)
        fs = page.evaluate("""(probe) => {
          // getComputedStyle 返回「设定值」，不反映 zoom；
          // 故实测同一元素在 zoom 1 与当前值下的「渲染像素」，取真实缩放系数。
          //
          // ⚠️ 探针必须选「尺寸不随可用宽度变化」的元素：
          //    改 zoom 会改变可用宽度，若用含长文本的块测高度，
          //    换行行数会随之变化 → 比值失真。
          //    固定尺寸的方块（如 logo mark）只受 zoom 影响。
          const el = () => document.querySelector(probe);
          const h = () => el().getBoundingClientRect().height;
          const z = getComputedStyle(document.body).zoom;
          const hZoomed = h();
          document.body.style.zoom = '1';
          const hPlain = h();
          document.body.style.zoom = '';   // 还原为样式表里的值
          return { zoom: z, scale: +(hZoomed / hPlain).toFixed(4) };
        }""", ZOOM_PROBE)
        log(abs(float(fs["zoom"]) - EXPECT_ZOOM) < 0.001, f"body 计算样式的 zoom = {fs['zoom']}")
        log(abs(fs["scale"] - EXPECT_ZOOM) < 0.02, f"实测缩放系数 = {fs['scale']}（应为 {EXPECT_ZOOM}）")

    # ---------- 9. 截图 ----------
    page.set_viewport_size({"width": 1440, "height": 1000})
    page.wait_for_timeout(300)
    page.screenshot(path=str(SHOTS / "01-full-1440.png"), full_page=True)
    page.set_viewport_size({"width": 375, "height": 900})
    page.wait_for_timeout(400)
    page.screenshot(path=str(SHOTS / "03-mobile-375.png"), full_page=True)

    # ---------- 10. 渲染文本落地（供核对脚本用） ----------
    page.set_viewport_size({"width": 1440, "height": 1000})
    page.wait_for_timeout(300)
    rendered.append("=== BODY ===\n" + page.inner_text("body"))
    # 动态生成的内容必须逐个切过去抓，静态 HTML 里看不到
    for t in TABS:
        page.click(f'{TAB_SELECTOR}[data-type="{t}"]')
        page.wait_for_timeout(250)
        rendered.append(f"=== {TAB_DETAIL_SELECTOR}[{t}] ===\n" + page.inner_text(TAB_DETAIL_SELECTOR))

    # ---------- 11. 外部请求失败 ----------
    # 离线环境下字体 CDN 拉不到属预期；其余资源失败要报。
    if failed_req:
        font_like = [u for u in failed_req if any(
            k in u for k in ("fonts.googleapis", "fonts.gstatic", "font"))]
        log(True, f"外部请求失败 {len(failed_req)} 条（其中疑似字体 {len(font_like)} 条，离线属预期）")
        rest = [u for u in failed_req if u not in font_like]
        if rest:
            log(False, f"非字体资源请求失败：{rest}")

    browser.close()

(BASE / "_src" / "rendered.txt").write_text("\n\n".join(rendered), encoding="utf-8")
(BASE / "_src" / "BUG检查报告.md").write_text(
    "# BUG 检查报告\n\n基准：chromium（headless）真渲染 index.html\n\n"
    + "\n".join(report)
    + f"\n\n结论：{'全部通过，无 BUG' if not problems else f'发现 {len(problems)} 个 BUG'}\n",
    encoding="utf-8")

print("\n".join(report))
print()
print("结论：", "全部通过，无 BUG" if not problems else f"发现 {len(problems)} 个 BUG")
sys.exit(1 if problems else 0)
