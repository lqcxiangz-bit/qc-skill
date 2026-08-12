# Skill Anatomist v3 protocol

## 1. Keep three flows separate

### Usage flow

```text
我的问题 → 我怎么开口 → 我提供什么 → 是否需要选择 → 我收到什么 → 我怎么使用结果
```

### Result-formation explanation

Explain why the prescribed method produces the expected result:

```text
先做 X → 产生 Y → 再用 Z 整理或检查 → 所以最终得到 W
```

### Internal implementation

Which file, function, tool, or command performs each part. This is optional depth and comes last. Never substitute implementation for usage.

## 2. Beginner executive summary

Before internal detail, answer in ordinary Chinese:

- What is it in one everyday sentence?
- What real problem does it solve?
- Three representative suitable situations.
- Two or three close but unsuitable situations.
- What can the user say?
- What must the user provide?
- What will the user receive?
- What are the most valuable lessons?
- What should not be copied or relied on?
- Recommendation: use directly, study selectively, learn specific parts, cautionary case, or insufficient evidence — with a plain reason and no grade.

A beginner who stops here must understand the practical situation.

## 3. Jargon translation ladder

1. Describe the idea without the term.
2. Give a familiar analogy.
3. Explain its action here.
4. Explain user impact.
5. Reveal and define the exact term in optional depth.

Examples:

- CLI → 不是点按钮，而是通过文字命令给程序下口令的入口。
- schema → 规定数据必须有哪些格子、每格装什么的一张表格模板。
- assertion → 用来判断结果是否达标的一道检查题。
- environment variable → 程序启动前从环境里读取的一张便签。
- local HTTP server → 临时在本机开一个网页入口，让浏览器读取或提交内容。

## 4. Sharp professor annotations

Weak notes say “这句很重要”, “设计很巧妙”, or merely restate. Rewrite them.

For high-leverage passages, answer at least one evidence-supported question:

### Why A instead of plausible B?

Name a credible alternative and benefit. Explain the actual tradeoff and why A fits these constraints. Teach how to choose, not “A is always better”.

### Which shortcut does this close?

Name the concrete default failure: skipped verification, unnecessary questions, generic output, indiscriminate loading, hidden decisions, or another supported route. Explain how the rule blocks it.

### Which fuzzy goal becomes which controllable action?

Example: `结果要专业` becomes `生成后渲染并检查溢出、遮挡和缺页`. Teach this conversion as reusable technique.

### What is left unsaid or deliberately open?

Identify useful judgment space, explicit exceptions, missing failure cases, or platform assumptions. Distinguish intentional openness from omission; say unknown if evidence cannot decide.

Standard shape: `忠实翻译`, `小白解释`, `教授批注`, optional `为什么这样而不是那样`, and `学走 / 别照搬`.

Do not invent alternatives or criticism to appear insightful. Mention weakness only when it changes correct use or teaches a transferable principle.

## 5. Complete source classroom

Represent every substantive target `SKILL.md` part in original order: frontmatter, headings, paragraphs, lists, examples, and code blocks. Assign `S001`, `S002`, … . Maintain:

```text
source range → segment IDs → represented yes/no → reason if no
```

Every segment has complete original, faithful Chinese translation, beginner explanation, professor annotation, learn-or-avoid guidance, and term definitions when needed.

Let `N` be the substantive count:

```text
coverage ledger count
= dossier total_segments
= dossier segment-array length
= HTML embedded segment count
```

Depth never excuses omission. Use concise notes for connective text and deeper notes for high-leverage decisions.

If access, copyright, or another restriction prevents full reproduction, call it `选段精读`, explain why, and never imply full coverage.

## 6. HTML textbook

Read this section only after manuscript and dossier are frozen.

Required order: executive summary; usage; why result emerges; internal anatomy; design lessons; copying cautions; complete/selected source classroom; transfer; quiet appendix.

Do not make ratings, hard caps, risk radar, or review methodology primary navigation.

First screen shows plain explanation, suitable/unsuitable scenarios, example requests, input/output, lessons, cautions, and recommendation. A memorable thesis may follow but cannot replace clarity.

Usage visual uses first-person steps and may distinguish `你会看到` from optional `你看不到，但按设计会做`.

Source classroom:

- Wide screen: original and translation side by side with semantic divider.
- Teaching note below or clearly separate.
- Mobile: original, translation, note stacked.
- Original and translation stay visible; deeper note may expand.
- Show progress such as `12/48` and search without hiding unvisited segments.

Learner prose and translation normally at least 17px desktop; annotation 16px; labels 12–13px. Do not use monospaced fonts for Chinese prose.

Choose one memorable teaching mechanism, preferably annotated source or learning spine. Use numbering only for real sequence and columns only for real distinctions. Avoid dashboards, metric cards, severity colors, gratuitous gradients, staggered entrances, and hover scaling.

Offline single file: embedded CSS/JS, no external fonts, CDNs, remote images, analytics, or network requests. Respect reduced motion, semantic headings, visible focus, contrast, responsive layout, and safe escaping.

Deliberately reject A/B/C grade before understanding, audit-first good/bad structure, fewer-passages rule for promised full source, and target aesthetics overriding the learning system.

## 7. Autonomous completion

Use one direction:

```text
complete reading + evidence → frozen manuscript → dossier → HTML from dossier
```

Gates:

1. Availability: selected skill instructions, required reference, target source, and necessary supporting material were read.
2. Beginner teaching: self-contained summary, genuine user flow, translated jargon, learning-first judgment.
3. Source coverage: ledger, dossier count, segment array, and HTML count equal; required fields non-empty.
4. Consistency: all artifacts have the same recommendation, usage steps, source mode/count, lessons, and cautions.
5. HTML integrity: offline, embedded data parses, all units render, learner-first navigation, safe escaping, keyboard/mobile/contrast checks.

Visual inspection supplements deterministic checks; it does not replace them.

Status:

- `complete`: every gate passed.
- `created, unverified`: files written but required read-back or checks unavailable.
- `incomplete`: known mismatch, missing material, or failed gate.

Never call a successful write completion. Do not ask a parent to inject instructions, request missing sections, repair HTML, reconcile counts, or finish work.

A valid evaluation uses a fresh agent with no parent intervention. If intervention occurs, label it contaminated, exclude it from evidence, revise separately, and restart.

Report exact source mode/count, usage-step count, HTML embedded count, every gate result, visual-check result, and environment limits.
