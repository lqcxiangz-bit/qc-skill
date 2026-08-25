#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数一份 skill 的规矩，给判断提供线索。

    python3 count.py <目标文件> [--max 20]

它只负责数，不负责下结论。正则一定会认错，所以：
每一条命中都要人工看一眼原文再算数，别把这里的数字直接贴到页面上。
"""

import re
import sys
import argparse

# ── 要找的东西 ───────────────────────────────────────────────

BAN = re.compile(
    r"不要|不许|不能|不得|不该|不应|禁止|切忌|严禁|勿(?!论)"
    r"|(?<![区特分识差个派级类鉴辨告])别(?![的人名字号])"
    r"|never|don'?t|do not|must not|avoid|no longer",
    re.I,
)

REASON = re.compile(
    r"因为|由于|导致|否则|不然|以免|防止|会变成|会让|会打|会显|会破坏|会丢"
    r"|——|—[^—]|（[^）]{2,}）|\([^)]{4,}\)"
    r"|because|since|otherwise|causes?|leads? to|result",
    re.I,
)

HESITATE = re.compile(
    r"优先|通常|一般来说|一般是|一般用|视情况|看情况|除非|但如果|大多数|多数时候"
    r"|倾向于|不一定|也可以|酌情|按需"
    r"|prefer|usually|generally|typically|unless|depends|in most cases",
    re.I,
)

VAGUE = re.compile(
    r"独特|专业(?!术语)|优雅|高质量|深刻|出色|精美|完美|优秀|卓越|高级感|有品味|大气|美观"
    r"|unique|professional|elegant|high[- ]quality|beautiful|excellent|polished",
    re.I,
)

TRACE = re.compile(
    r"\d+\s*(px|em|rem|%|字|行|条|个|秒|分钟|ms|KB|MB|次)"
    r"|#[0-9A-Fa-f]{3,8}\b"          # 十六进制色号——最硬的那种具体痕迹
    r"|rgba?\([^)]+\)|hsla?\([^)]+\)"
    r"|v?\d+\.\d+"
    r"|[\w./-]+\.(md|py|js|json|html|yaml|yml|sh|txt|css)"
    r"|报错|异常|崩|翻车|踩过|踩坑|事故|丢过|上次|之前.{0,6}(出过|漏|错)"
    r"|Error|Exception|traceback",
    re.I,
)

SENT_END = re.compile(r"(?<=[。！？；!?;])")


def sentences(path):
    """把文件切成句子，每句带行号。跳过围栏代码块。"""
    out, in_fence, skipped = [], False, 0
    with open(path, encoding="utf-8") as f:
        for lineno, raw in enumerate(f, 1):
            line = raw.rstrip("\n")
            if line.lstrip().startswith("```"):
                in_fence = not in_fence
                skipped += 1
                continue
            if in_fence:
                skipped += 1
                continue
            body = line.lstrip("#>-*+ \t").strip()
            if not body:
                continue
            for piece in SENT_END.split(body):
                piece = piece.strip()
                if len(piece) >= 4:
                    out.append((lineno, piece))
    return out, skipped


def show(title, hits, limit):
    print(f"\n{title}（{len(hits)} 条）")
    print("─" * 64)
    if not hits:
        print("  （无）")
        return
    for lineno, text in hits[:limit]:
        if len(text) > 76:
            text = text[:76] + "…"
        print(f"  第 {lineno:>4} 行  {text}")
    if len(hits) > limit:
        print(f"  …… 还有 {len(hits) - limit} 条（--max 调整显示条数）")


def main():
    ap = argparse.ArgumentParser(add_help=True)
    ap.add_argument("path", help="要数的 skill 文件")
    ap.add_argument("--max", type=int, default=20, help="每类最多列几条（默认 20）")
    args = ap.parse_args()

    try:
        sents, skipped = sentences(args.path)
    except OSError as e:
        sys.exit(f"读不了这个文件：{e}")

    with_reason, without_reason = [], []
    hesitate, vague, trace = [], [], []

    for lineno, s in sents:
        if BAN.search(s):
            (with_reason if REASON.search(s) else without_reason).append((lineno, s))
        if HESITATE.search(s):
            hesitate.append((lineno, s))
        if VAGUE.search(s):
            vague.append((lineno, s))
        if TRACE.search(s):
            trace.append((lineno, s))

    bans = len(with_reason) + len(without_reason)

    print("=" * 64)
    print(f"数完了：{args.path}")
    print("=" * 64)
    print(f"  正文句子      {len(sents)} 句（跳过代码块 {skipped} 行）")
    print(f"  「不要这样做」 {bans} 条")
    if bans:
        pct = round(len(with_reason) * 100 / bans)
        print(f"      ├ 说了为什么  {len(with_reason)} 条（{pct}%）")
        print(f"      └ 没说为什么  {len(without_reason)} 条")
    print(f"  犹豫的地方    {len(hesitate)} 处")
    print(f"  模糊的目标词  {len(vague)} 处")
    print(f"  具体的痕迹    {len(trace)} 处")

    show("① 说了为什么的禁令 —— 矿在这里，逐条读括号", with_reason, args.max)
    show("② 没说为什么的禁令 —— 多半是配置，别在上面花深度", without_reason, args.max)
    show("③ 犹豫的地方 —— 作者也没有干净答案，是真前沿", hesitate, args.max)
    show("④ 模糊的目标词 —— 没法验收的要求，越多越可疑", vague, args.max)
    print("\n⑤ 具体的痕迹 —— 数字/版本/文件名/报错，越多越像真踩过")
    print("─" * 64)
    print(f"  共 {len(trace)} 处，分布在第 "
          + "、".join(str(n) for n, _ in trace[:24])
          + ("… 行" if len(trace) > 24 else " 行") if trace else "  （无）")

    print("\n" + "!" * 64)
    print("这些是线索，不是结论。")
    print("正则会认错——「不要紧」会被当成禁令，插入语的破折号会被当成理由。")
    print("每一条都回原文看一眼再算数。别把上面的数字直接贴到页面上。")
    print("!" * 64)


if __name__ == "__main__":
    main()
