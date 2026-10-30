# agy (Antigravity CLI → Gemini) —— 实测笔记

实测版本 `agy 1.1.24`,macOS,2026-09-02。
注意:Google 官方那个 `gemini` CLI 是**另一个二进制**,本机没装;要用那个得另写适配器。

## prompt 必须紧贴 `-p`,写成 `-p=<prompt>`

`-p`(= `--print`)是个字符串 flag,Go 的 flag 包让它吃掉紧随其后的那个 token。
所以:

```bash
agy -p "问题"                      # ✅
agy -p "问题" --model "…"          # ✅ 其他 flag 放后面
agy -p --print-timeout 180s "问题" # ❌ rc=2 —— -p 把 --print-timeout 当成了自己的值
echo "问题" | agy -p               # ❌ rc=2「flag needs an argument: -p」,管道内容它不看
```

第三条是实测踩出来的:agy 的报错还挺人性化——
`Attach the prompt to the flag (-p='your prompt') and move --print-timeout elsewhere`。
适配器用 `-p=<prompt>` 的等号形式,彻底消除歧义。

**只能走 argv,不接 stdin。** 所以有长度上限:macOS ARG_MAX ≥1MB 随便传;
**Windows 命令行上限 32767 字符**,超了报的是没头没尾的 returncode,不是「太长了」。
`xm` 按平台预算提前拦下来并说人话。

## 模型名两种写法,别混

```bash
--model "Gemini 3.7 Flash (High)"       # 带档位的全名,可单独用
--model gemini-3.7-flash --effort high  # slug 必须配 --effort
```

只给 slug 不给 `--effort` 是**直接报错**(rc=1,stderr 写明 requires --effort),
不是静默降级。`agy models` 出实时清单。

## 默认只等 5 分钟

`--print-timeout` 默认 `5m0s`,长任务会被半路砍断,现象像「模型没回答」。
`xm` 会按 `--timeout` 自动传这个 flag,并把外层 kill 时间设在它之上留 30s 余量——
好让 CLI 自己的报错先出来,而不是被我们 kill 掉(被 kill 的现象是「什么输出都没有」)。

## rc=0 不等于成功

agy 出错时有时候退出码仍是 0,只在输出开头写一行 `Error:`。
适配器的 `[success].forbid` 里有 `^\s*Error:` 兜底,`xm` 会判成失败。
**只看退出码就会把一次失败当成答卷存下来** —— 做对照时这是最坏的一种错。

## ⚠️ agy 是个 agent,headless 下它想用工具 = 静默零输出

2026-09-16 实测踩到。给它一段「review 这些代码改动」的 prompt——代码全文已经贴在
prompt 里了,按理不需要碰文件系统——它还是自己决定去调工具。`-p` 是非交互的,
没有 host 能弹权限确认,于是**自动拒绝,然后什么都不输出**:

```
退出码 0,stdout 0 字符
stderr 末行: jetski: no output produced — a tool required the "command"
permission that headless mode cannot prompt for, so it was auto-denied.
```

三个要命的地方叠在一起:

1. **退出码是 0**,和「跑通了但模型没话说」长得一模一样;
2. **真正的原因只在 stderr 最后一行**,stdout 干干净净;
3. prompt 自包含**并不能阻止它去调工具** —— 它是 agent,不是问答端点,
   会自己判断「要不要看一眼仓库」。

`xm` 的 `answer_present` 这条 check 正好挡住了(0 字 < 下限 1),判成 failed 并把
stderr 末行印出来。**这就是为什么不能把 gate 收窄成只看 `process_ok`** ——
只看退出码的话,这次会被当成一份空答卷存下来。

### 两种解法,默认选第一种

```bash
# 1) 在 prompt 开头钉死,别让它起调工具的念头(推荐)
#    "只根据下面粘贴的内容回答,不要调用任何工具、不要读文件、不要执行命令"

# 2) 真需要它在仓库里动手时,才透传放行 —— 这会自动批准任意命令,先问用户
xm run -a agy --arg agy=--dangerously-skip-permissions -f p.md
```

第二种等于把本机仓库的写权限交出去,**不要为了让它「跑通」就顺手加上**。
Claude 那边有 `--permission-prompts none` 可以只放行只读工具,agy 目前没有等价的
细粒度开关,只有全开或全拒两档。

### 补充:那句话要放在数据正上方,并且必须配重试

同日跑 1586 组重复人员判定(40 组一批、40 批)时又量了一次:

- 那句禁令**写在 prompt 末尾、紧挨着数据**比写在开头管用。放开头时仍偶发触发,
  移到「输入数据:」这一行的正上方之后,几十批里没再触发过。
- 但它**不是 100%**。仍然要在外层带重试:捕获「stdout 为空 or 以 `Error:` 开头」,
  把禁令再追加一遍重发。实测第二次都能过。
- 判成功**必须同时看退出码和 stdout 内容**,这两个单独看都会漏。

## ⚠️ 报「请重新登录」时先查网络

agy 自带 refresh_token(`~/.gemini/jetski-standalone-oauth-token`),续期要连
`oauth2.googleapis.com`。走代理的机器上代理一抽风刷新就失败,而 agy **一律报成**
`Authentication required. Please visit the URL to log in` —— 文案极具误导性,
照着去重新登录是白折腾。排查顺序:

```bash
curl -sI -m 10 https://oauth2.googleapis.com/     # 通不通
agy -p="ping"                                     # 再探一次,多半就过了
```

网络确认没问题、还是过不去,才是真的要重登:**打开 Antigravity 桌面应用**登录
Google 账号(CLI 没有 `login` 子命令)。桌面端平时不需要开着,只有首次登录要。
