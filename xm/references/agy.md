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
