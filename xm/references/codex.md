# codex (OpenAI Codex CLI) —— 实测笔记

实测版本 `codex-cli 0.145.0`,macOS,2026-09-02。以下都是跑出来的,不是抄文档的。

## 🔴 不给显式 stdin 会永久挂住

最贵的一个坑。`codex exec` 的 help 里写着「stdin is piped 时会当作 `<stdin>` 块追加」,
于是**只要 stdin 是个管道,它就一直读到 EOF**。父进程 stdin 被继承时(在 CI 里、
在别的 agent 里、在 `subprocess.run(input=None)` 里)就是这种情况。

实测:不给 stdin → 60s、90s 两次全部超时,期间**没有任何输出、没有报错**,
现象跟「模型在慢慢想」一模一样。给一个空 stdin → 12s 正常返回。

`xm` 一律显式喂 stdin(argv 模式下喂空字节),所以走 `xm` 不会撞上。
手搓命令行记得 `< /dev/null`。

## 不在 git 仓库里直接拒跑

rc=1,0.2 秒,stderr:`Not inside a trusted directory and --skip-git-repo-check was
not specified.` 在 `/tmp` 里跑最容易撞上。适配器的 `entry` 里已经常驻了这个 flag。

## 答案从 `-o` 取,不从 stdout

v0.145.0 实测:stdout 其实是干净答案,会话头/模型名/token 统计全在 **stderr**。
但 stdout 的行为历史上变过(老版本是事件流),而 `-o/--output-last-message` 是
「最后一条消息」的显式契约,跨版本稳定。适配器用 `-o`,stdout 另存 `stdout.log`。

## 沙箱三档,默认只读

`-s read-only`(默认,`approval: never`)/ `workspace-write` / `danger-full-access`。
它说「我没法修改文件」时,先看是不是没给 `-s workspace-write`,别去改 prompt。
**要它动文件先问用户。**

## 会读 cwd 的 AGENTS.md

在你仓库里跑 = 带着仓库规矩跑,通常正是你要的。但当盲评裁判时那就是泄题——
用 `xm run --isolate` 挪到空临时目录。

## 两个独立子命令

`codex review`(非交互代码评审)和 `codex apply`(把 diff 打回工作区)是独立入口,
该用就用,别用 `exec` 硬凑。这两个 v1 的 xm 不封装。
