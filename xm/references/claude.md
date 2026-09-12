# claude (Anthropic Claude Code CLI) —— 实测笔记

实测版本 `2.1.237`,macOS,2026-09-02。

## 本机凭证与沙箱

本机 Claude Code 使用长期凭证，正常运行 `xm` 不需要逐次登录。Codex 沙箱可能因
无法读取 macOS 钥匙串而返回 `loggedIn: false`；这时应在获得当次系统权限后读取
已有凭证或运行 `xm`，而不是重新执行登录流程。

`claude auth login`、`claude auth logout` 和账号切换都必须由用户明确发起。沙箱外
也确认凭证失效时，只报告状态并等待用户决定。不要保存或展示完整邮箱、令牌或 OAuth
授权链接。

## 非交互权限必须显式收口

`claude -p` 的 `--permission-prompts` 默认值是 `host`。在交互式 SDK host 里这没问题，
但 `xm` 只是拉起一个无人值守子进程，没有任何人能回答权限请求。实测后果是：Claude
正常开始任务，工具请求碰到审批后便一直等待；stdout 没有最终答案，最终只表现成外层
600 秒超时。

适配器因此固定传 `--permission-prompts none`。未预授权的工具会立即被拒绝，Claude
仍可换路或明确说明边界。确实需要联网调研时，显式预授权只读工具：

```bash
xm run -a claude \
  --arg claude=--allowedTools \
  --arg claude=WebSearch,WebFetch \
  -f /tmp/task.md --human
```

不要默认放开 Bash 或全部工具；这既扩大权限，也会重新引入难以审计的副作用。

## 其余实测行为

- `-p` 走 argv 或 stdin **都通**(实测 8.4s / 6.9s)。适配器默认走 stdin,绕开 argv 长度上限。
- stdout 就是答案本体,干净,无事件流、无 ANSI,stderr 为空。
- 未登录时当前版本返回 rc=1，并在 stdout 写 `Not logged in · Please run /login`；
  适配器也把该文案列为失败特征，避免未来退出码变化后误判为答案。
- `--model` 收别名(`fable`/`opus`/`sonnet`)也收全名。

## ⚠️ 唯一的麻烦:CLAUDE.md 污染

claude 会加载 `~/.claude/CLAUDE.md`(全局)**加上** cwd 的 `CLAUDE.md`。
`xm run --isolate` 换个空临时目录,只能挡住后者。

唯一能全关的开关是 `--bare`,但它同时把认证限死成 `ANTHROPIC_API_KEY` /
`apiKeyHelper`(**不读 OAuth、不读钥匙串**)——用订阅登录的机器上直接用不了。

所以:**拿 claude 当盲评裁判时,全局 CLAUDE.md 的污染挡不住。**
`xm` 会在 manifest 的 `warnings` 里标出来。要干净就换一家当裁判。
(这条在 v2 的 `xm judge` 里会变成硬约束。)

## 没有内建超时

只能靠 `xm` 外层的 `--timeout` 硬超时。被外层 kill 的现象是「一点输出都没有」。
先看 Claude 会话记录是否停在权限请求；不要直接把超时调大，因为无人响应的审批
等多久都不会完成。

## 关于「在 claude 里调 claude」

完全可以,就是起一个全新的进程、全新的上下文。但要注意它**不知道你这边的对话**,
prompt 里该给的背景一个都不能省。
