#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
把写定的段落数据渲染成长卷网页。

    python3 render.py passages.json -o out.html
    python3 render.py passages.json --check      # 只查不写
    python3 render.py --schema                   # 打印一份样例数据

为什么要有这个脚本：原文那一栏**按行号从原文件直接切出来**，不经过人手，
所以不可能漏字、不可能被顺手改写。转义、加粗渲染、段数核对也都在这儿做掉。
"""

import argparse
import html
import json
import re
import sys
from pathlib import Path

SCHEMA = {
    "source": "被拆的那份文件的路径",
    "target": "eli5",
    "title": "页面标题",
    "hero": "一句判断，不是一句介绍",
    "passages": [
        {
            "id": "S001",
            "lines": [1, 4],
            "type": "key  # key 重点段 / eye 全篇最要紧（最多 2 段）/ link 一般段",
            "zh": "说人话的翻译。原文栏不用写，脚本按 lines 自己切。",
            "ntag": "这条批注在回答什么问题",
            "note": ["批注正文，一段一条"],
            "choice": {
                "could": "它本来可以……",
                "chose": "但它选了……",
                "because": "因为……",
            },
            "incident": {
                "what": "出了什么事（只有讲禁令时才填）",
                "why": "为什么会这样",
                "cost": "不躲会怎样",
            },
            "ladder": "黑话 → 生活类比 → 在这里做什么 → 对你的影响",
            "learn": "换个地方也成立的",
            "avoid": "只在它这儿成立的，别抄",
            "merged": "如果这条合并了好几段原文，在这儿说明（会显示给读者）",
        }
    ],
}


# ── 文本处理 ─────────────────────────────────────────────────

def inline(text):
    """转义之后，把 **加粗** 和 `代码` 变成真正的标签。"""
    s = html.escape(str(text), quote=False)
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    s = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", s)
    return s


def block(text):
    """多行文本：保留换行，围栏代码块转成 <pre>。"""
    parts, out, in_fence, buf = text.split("\n"), [], False, []
    for line in parts:
        if line.lstrip().startswith("```"):
            if in_fence:
                out.append("<pre>" + html.escape("\n".join(buf), quote=False) + "</pre>")
                buf = []
            in_fence = not in_fence
            continue
        (buf if in_fence else out).append(line if in_fence else inline(line))
    if in_fence and buf:  # 没闭合的围栏
        out.append("<pre>" + html.escape("\n".join(buf), quote=False) + "</pre>")
    joined, res, para = out, [], []
    for chunk in joined:
        if chunk.startswith("<pre>"):
            if para:
                res.append("<p>" + "<br>".join(para) + "</p>")
                para = []
            res.append(chunk)
        elif chunk.strip() == "":
            if para:
                res.append("<p>" + "<br>".join(para) + "</p>")
                para = []
        else:
            para.append(chunk)
    if para:
        res.append("<p>" + "<br>".join(para) + "</p>")
    return "\n".join(res)


# ── 检查 ─────────────────────────────────────────────────────

def check(data, src_lines):
    errs, warns = [], []
    seen, covered = set(), set()
    eyes = 0
    total = len(src_lines)

    for i, p in enumerate(data.get("passages", []), 1):
        tag = p.get("id") or f"第 {i} 条"

        for field in ("id", "lines", "type", "zh"):
            if not p.get(field):
                errs.append(f"{tag}：缺 {field}")

        if p.get("id") in seen:
            errs.append(f"{tag}：段号重复")
        seen.add(p.get("id"))

        ptype = str(p.get("type", "")).split()[0] if p.get("type") else ""
        if ptype not in ("key", "eye", "link"):
            errs.append(f"{tag}：type 只能是 key / eye / link，现在是 {p.get('type')!r}")
        if ptype == "eye":
            eyes += 1

        ln = p.get("lines")
        if isinstance(ln, list) and len(ln) == 2 and all(isinstance(x, int) for x in ln):
            a, b = ln
            if not (1 <= a <= b <= total):
                errs.append(f"{tag}：行号 {a}-{b} 超出原文范围（共 {total} 行）")
            else:
                for n in range(a, b + 1):
                    if n in covered:
                        warns.append(f"{tag}：第 {n} 行和前面的段重叠")
                    covered.add(n)
        else:
            errs.append(f"{tag}：lines 要写成 [起始行, 结束行]")

        if ptype in ("key", "eye"):
            if not p.get("ntag"):
                errs.append(f"{tag}：重点段缺 ntag（这条批注在回答什么）")
            if not p.get("note"):
                errs.append(f"{tag}：重点段缺 note（批注正文）")
            c = p.get("choice") or {}
            missing = [k for k in ("could", "chose", "because") if not str(c.get(k, "")).strip()]
            if missing:
                errs.append(
                    f"{tag}：那个必填句式还有空格子 → {', '.join(missing)}"
                    "（「它本来可以___，但它选了___，因为___」填不满，"
                    "说明这段可能不是重点段，改成 link 简批）"
                )

        inc = p.get("incident")
        if inc:
            missing = [k for k in ("what", "why", "cost") if not str(inc.get(k, "")).strip()]
            if missing:
                errs.append(f"{tag}：讲禁令的三格没填完 → {', '.join(missing)}")

    if eyes > 2:
        errs.append(f"标了 {eyes} 段「先看这条」，最多 2 段——多了等于没标")

    # 有没有偷偷少放原文
    gaps = [n for n in range(1, total + 1) if n not in covered and src_lines[n - 1].strip()]
    if gaps:
        rngs, start, prev = [], None, None
        for n in gaps:
            if start is None:
                start = prev = n
            elif n == prev + 1:
                prev = n
            else:
                rngs.append((start, prev))
                start = prev = n
        rngs.append((start, prev))
        errs.append(
            "原文有没放进来的段落（第 "
            + "、".join(f"{a}-{b}" if a != b else str(a) for a, b in rngs)
            + " 行）。要么补上，要么合并到相邻段并在 merged 里写明。"
        )

    return errs, warns


# ── 渲染 ─────────────────────────────────────────────────────

def passage_html(p, src_lines):
    ptype = str(p.get("type", "link")).split()[0]
    a, b = p["lines"]
    src = "\n".join(src_lines[a - 1:b]).rstrip()
    cls = {"eye": "passage eye key", "key": "passage key", "link": "passage"}[ptype]

    parts = [f'<section class="{cls}" id="{html.escape(p["id"])}">']
    parts.append(f'<div class="marker"><span class="dot"></span>'
                 f'<span class="no">{html.escape(p["id"])}</span></div>')
    if ptype == "eye":
        parts.append('<div class="brow">◆ 先看这条</div>')
    if p.get("merged"):
        parts.append(f'<div class="merged">合并说明：{inline(p["merged"])}</div>')

    rng = f"{a}–{b} 行" if a != b else f"{a} 行"
    parts.append('<div class="bilingual">')
    parts.append(f'<div class="src"><div class="label">原文 · {rng}</div>{block(src)}</div>')
    parts.append(f'<div class="zh"><div class="label">说人话</div>{block(p["zh"])}</div>')
    parts.append("</div>")

    has_note = p.get("ntag") or p.get("note") or p.get("choice")
    if has_note:
        open_now = ptype == "eye"
        parts.append(
            f'<button class="note-toggle" aria-expanded="{"true" if open_now else "false"}">'
            f'<span class="seal">批</span>'
            f'<span class="t">{"收起批注" if open_now else "点击展开批注"}</span>'
            f'<span class="chev">›</span></button>'
        )
        parts.append(f'<div class="note-inner{" open" if open_now else ""}">'
                     f'<div class="note-body">')
        if p.get("ntag"):
            parts.append(f'<div class="ntag">{inline(p["ntag"])}</div>')
        for n in p.get("note", []):
            parts.append(block(n))

        c = p.get("choice") or {}
        if all(str(c.get(k, "")).strip() for k in ("could", "chose", "because")):
            parts.append(
                '<div class="choice">它本来可以 <b>' + inline(c["could"]) +
                '</b>，但它选了 <b>' + inline(c["chose"]) +
                '</b>，因为 <b>' + inline(c["because"]) + '</b>。</div>'
            )

        inc = p.get("incident") or {}
        if all(str(inc.get(k, "")).strip() for k in ("what", "why", "cost")):
            parts.append(
                '<div class="incident">'
                f'<div><span class="k">出了什么事</span><span class="v">{inline(inc["what"])}</span></div>'
                f'<div><span class="k">为什么会这样</span><span class="v">{inline(inc["why"])}</span></div>'
                f'<div><span class="k">不躲会怎样</span><span class="v">{inline(inc["cost"])}</span></div>'
                "</div>"
            )

        if p.get("ladder"):
            parts.append(f'<div class="ladder">{inline(p["ladder"])}</div>')
        if p.get("learn") or p.get("avoid"):
            parts.append('<div class="takeaway">')
            if p.get("learn"):
                parts.append(f'<div><span class="k good">可以学走</span>{inline(p["learn"])}</div>')
            if p.get("avoid"):
                parts.append(f'<div><span class="k warn">别抄</span>{inline(p["avoid"])}</div>')
            parts.append("</div>")
        parts.append("</div></div>")

    parts.append("</section>")
    return "\n".join(parts)


def main():
    ap = argparse.ArgumentParser(add_help=True)
    ap.add_argument("data", nargs="?", help="passages.json")
    ap.add_argument("-o", "--out", help="输出的 html")
    ap.add_argument("-t", "--template", help="模板（默认用 assets/scroll.html）")
    ap.add_argument("--check", action="store_true", help="只检查，不生成")
    ap.add_argument("--schema", action="store_true", help="打印一份样例数据")
    args = ap.parse_args()

    if args.schema:
        print(json.dumps(SCHEMA, ensure_ascii=False, indent=2))
        return
    if not args.data:
        ap.error("要给一个 passages.json（或用 --schema 看格式）")

    data = json.loads(Path(args.data).read_text(encoding="utf-8"))
    src_path = Path(data["source"])
    if not src_path.is_absolute():
        src_path = Path(args.data).parent / src_path
    src_lines = src_path.read_text(encoding="utf-8").split("\n")

    errs, warns = check(data, src_lines)
    for w in warns:
        print(f"  提醒  {w}")
    if errs:
        print(f"\n没过（{len(errs)} 条）：")
        for e in errs:
            print(f"  ✗ {e}")
        sys.exit(1)

    n = len(data["passages"])
    print(f"  ✓ {n} 段都齐了，原文 {len([l for l in src_lines if l.strip()])} 行没有漏的")

    # 先渲染出来（不落盘），这样 --check 也能查到渲染后才看得见的问题
    tpl_path = Path(args.template) if args.template else \
        Path(__file__).resolve().parent.parent / "assets" / "scroll.html"
    tpl = tpl_path.read_text(encoding="utf-8")
    if "<!--PASSAGES-->" not in tpl:
        sys.exit(f"模板里找不到 <!--PASSAGES--> 这个位置：{tpl_path}")

    body = "\n\n".join(passage_html(p, src_lines) for p in data["passages"])
    out = (tpl.replace("<!--PASSAGES-->", body)
              .replace("{{TITLE}}", html.escape(data.get("title", data.get("target", "拆解"))))
              .replace("{{TARGET}}", html.escape(data.get("target", "")))
              .replace("{{HERO}}", inline(data.get("hero", ""))))

    # ── 渲染后的两道硬检查，--check 和正式生成都要跑 ──
    hard = []
    # 外部请求：只查会真发请求的（<img src>/<script src>/<link href>）。
    # 正文里指向出处的 <a href> 不算——那是出处诚实，页面照样能离线打开。
    ext = re.findall(r'(?:\bsrc|<link[^>]*\bhref)="https?://[^"]+', out)
    if ext:
        hard.append(f"页面里有 {len(ext)} 个外部请求，这一页必须能离线打开：{ext[:2]}")
    # 裸露的 markdown 标记（<pre> 和 <code> 里的是有意展示，不算）
    clean = re.sub(r"<pre>.*?</pre>|<code>.*?</code>", "", out, flags=re.S)
    stray = re.findall(r"\*\*[^*\n]{1,40}\*\*", clean)
    if stray:
        hard.append(f"还有 {len(stray)} 处 ** 没变成加粗，例如 {stray[0]!r}")
    if hard:
        print(f"\n没过（{len(hard)} 条）：")
        for e in hard:
            print(f"  ✗ {e}")
        sys.exit(1)
    print("  ✓ 无外部请求，无裸露的 markdown 标记")

    if args.check:
        return

    out_path = Path(args.out) if args.out else Path(args.data).with_suffix(".html")
    out_path.write_text(out, encoding="utf-8")
    print(f"  ✓ 写好了：{out_path}（{len(out) // 1024} KB）")
    print("\n剩下四件事只有眼睛能查：真截图看一眼（桌面+手机）、"
          "图找个不知道的人看、三张场景图形状是不是长得一样、"
          "随手挑三句话问「不懂的人会不会卡住」。")


if __name__ == "__main__":
    main()
