---
name: xm
description: "把一件事交给本机的其他 AI CLI(codex / agy-Gemini / claude)非交互地跑,可以一家、也可以多家并发跑同一题做对照,或同一家跑多遍看方差。**手动触发,绝不主动使用**:只有当用户明确要把事情派出去时才用(「用 codex 跑一下」「三家都问一遍」「让它们各写一版对比」「同一题跑三遍看稳不稳」「/xm …」)。用户只是在谈论这些模型或工具、句子里恰好出现 codex/gemini/claude 而没有让你去调用,不要用;你自己觉得「找个模型对一下更稳」也不要用。"
argument-hint: "<要派出去的任务> [给谁]"
---

# xm —— 把活派给本机的其他模型 CLI

`xm` 是一个并跑器:一个 prompt,N 个本地 agent CLI,并发跑,产物落盘。
适配层是数据(`adapters/*.toml`),每家 CLI 的入口、prompt 通道、答案在哪、
成功判据全在里面,**都是实测值**。

## 一、先分清:用户是在说话,还是在派活

**只在用户明确要把事情交出去的时候才跑。**

| 用户说 | 跑不跑 |
|---|---|
| 「用 codex 跑一下测试」「问问 gemini 这么写行不行」 | 跑,单家 |
| 「三家都问一遍」「让它们各写一版我对比」 | 跑,多家 |
| 「同一题跑三遍看它稳不稳」 | 跑,`--repeat` |
| 「codex 和 claude code 比呢」「agy 是什么」 | **不跑**,这是在问你 |
| (你自己想「交叉验证一下更稳」) | **不跑**,没让你找就别找 |

**别替用户选模型。** 他说 gemini 就走 agy,说 codex 就走 codex;
都没点名而任务确实需要外援时,问一句。

## Claude 认证边界

这台 Mac 已为 Claude Code 配置了长期本机凭证。调用 Claude 时读取现有凭证，
**禁止自动执行** `claude auth login`、`claude auth logout`，也禁止擅自切换账号。

Codex 沙箱可能读不到 macOS 钥匙串，从而把已登录误报成未登录。遇到这种情况：

1. 不要重新登录；在获得当次系统权限后，从沙箱外只读检查现有凭证或运行已获准的 `xm` 任务。
2. 只有沙箱外的 `claude auth status` 也确认 `loggedIn: false`，才向用户报告凭证确实失效。
3. 即使凭证失效，也只说明情况并等待用户明确要求；不得自行打开登录页。

系统弹出的“允许读取本机凭证/在沙箱外运行”是执行权限，不是账号登录授权，
不要混为一谈。不要在产物或回复中记录完整账号邮箱、令牌或 OAuth 链接。

## 二、跑之前必须先报价

每次调用都花用户的额度和十几秒。动手前先说清楚:

> 「要跑 3 家 × 2 遍 = 6 次调用,单次约 10-15 秒(并发),要跑吗?」

不确定就先 `--dry-run`,它只打印计划,不花一分额度。

## 三、怎么调

**永远走 `xm`,不要自己拼 CLI 参数。**
每家 CLI 的 flag 都有坑(codex 不给 stdin 会永久挂死、agy 的 prompt 必须写成
`-p=<prompt>`、答案有的在 stdout 有的在 `-o` 文件里),这些全在适配器里解决了。
你手搓命令行 = 把这些坑重新踩一遍。

```bash
xm doctor                        # 哪几家可用(不花额度);--ping 才真的各跑一次
xm agents                        # 列出适配器

# 单家派活
xm run -a codex -f /tmp/task.md --human

# 多家同题对照(并发)
xm run -a codex -a agy -a claude -f /tmp/task.md --human

# 同一家多采样,看它自己稳不稳
xm run -a agy --repeat 3 -f /tmp/task.md --human

# 指定模型 / 沙箱 / 隔离
xm run -a agy -m 'agy=Gemini 3.1 Pro (High)' -f /tmp/task.md --human
xm run -a codex --sandbox workspace-write -f /tmp/task.md --human
xm run -a codex --isolate-cwd -f /tmp/task.md --human

# Claude 联网调研：只预授权只读的搜索/抓取工具；其他权限请求会立即拒绝，不会挂住
xm run -a claude \
  --arg claude=--allowedTools \
  --arg claude=WebSearch,WebFetch \
  -f /tmp/task.md --human
```

**长 prompt 一律先落文件再 `-f`**,别在命令行里拼几千字。

关键参数:

| 参数 | 什么时候用 |
|---|---|
| `-a/--agent` | 可重复。点几次就跑几个;同一家点多次 = 多采样 |
| `-n/--repeat` | 每家跑几遍。看方差用 |
| `--isolate-cwd` | 换到空临时目录跑,不让它读到当前仓库的 `AGENTS.md`/`CLAUDE.md`。只隔离 cwd |
| `-j/--concurrency` | 同时最多跑几个(默认 4) |
| `--arg` | `agent=flag` 透传原始 flag,适配器表达不了的开关走这条 |
| `--gate` | 放宽判成败的条件。默认三条 check 全过才算成功 |
| `--sandbox` | 只有 codex 支持三档;**要它动文件必须显式给,而这一步先问用户** |
| `--dry-run` | 只打印计划 |
| `--human` | 人读摘要;不给就是 JSON(给程序用) |

## 三点五、要做对照评判就用 `xm judge`

用户说「让它俩比一下」「哪个写得好」「做个双盲」时:

```bash
xm judge --run <上一次的 run 目录> --human -c "<评判标准>"
```

三条铁律:

1. **你不能当裁判。** 你看过整个上下文,知道 A 是谁 —— 这不是盲评。
   `xm judge` 会自动挑一个没参赛的 CLI;都参赛了它会拒绝,别用
   `--allow-self-judge` 绕过去,先问用户。
2. **评判标准里不许出现模型名。**「哪个更像 Claude 的风格」直接泄题。
   xm 命中词表时只警告不拒跑(词表误报很多),**警告出现时你要自己判断**是真泄题
   还是误报(比如标准里提到臭氧 O3、寓言 fable)。写成能力维度,不写身份。
3. **别关多趟排列。** 各趟指向不同时**就是没有赢家**,照实报给用户,
   不要挑一个说给他听。退出码 1 是正常实验结果,3 才是裁判挂了。
4. **报结论时把边界一起报。** 「2 趟一致」不等于显著,工具自己会把
   「随机裁判也有 N% 概率产生同样一致」印在结论下面 —— 别把这句删掉。
   `contamination` 是三态:`clean` / `unverifiable`(有来源不明的答卷) /
   `contaminated`(裁判自己参赛了) —— 后两种必须告诉用户这条保证没成立。
   `outcome: tie` 是「一致判平局」,不是「选出了赢家」,别混着报。

## 四、怎么看结果

`--human` 那份摘要里,每行末尾是 `out.md` 的路径。**去读那个文件**。

产物长这样:

```
.xm/runs/<时间戳>-<slug>/
  prompt.md          原样存的 prompt
  plan.json          执行前就写好了 —— 跑挂了也知道原本要跑什么
  manifest.json      机器摘要:谁成谁败、耗时、字数、警告
  agents/01-codex/
    out.md           ← 答案本体,你要读的是这个
    stderr.log       报错和会话噪声(不污染答案)
    stdout.log       仅当答案从 -o 文件取时才有
```

## 五、怎么交代

**把 `out.md` 的原始内容给用户看,不要只给你自己的转述** —— 他要的是那个模型
说了什么。多家对照时逐家列出,由用户自己判断,除非他明确让你综合。

失败时贴真实报错(摘要里的 `reason` 已经是提炼过的)。三条最常见:

1. `unavailable` —— 那家 CLI 不在 PATH 上
2. 退出码非 0 —— reason 里有 stderr 末行,通常直接说明问题
3. 命中失败特征 —— **退出码是 0 但其实失败了**(agy 会这样)。别当成功报上去

manifest 里每条结果还带 `checks`:`process_ok` / `answer_present` /
`no_adapter_error` 三个字段,失败时 reason 前面会标出是哪条没过(如 `[process_ok] 退出码 3`)。
它们只是进程级健康检查,**不代表任务答对了** —— 内容对不对还得你或用户自己看。

## 六、每家 CLI 的坑

要细节时才读,别一上来全加载:

- `references/codex.md` —— stdin 死锁、git 检查、沙箱三档
- `references/agy.md` —— prompt 必须贴着 `-p=`、模型名两种写法、登录报错其实是网络问题
- `references/claude.md` —— CLAUDE.md 污染、`--bare` 为什么不能用

Claude 有一条额外红线：`-p` 默认会等待 host 回答工具权限，但 `xm` 没有交互式
host。适配器已固定使用 `--permission-prompts none`，让未预授权工具立即拒绝。
任务确实需要联网调研时，按上面的示例只放行 `WebSearch,WebFetch`；不要为了省事
放开全部工具。

`xm doctor` 会把每家的坑各印一行摘要。
