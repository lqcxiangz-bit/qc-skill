# qc-skill

我的 WisCode / Claude Code / Codex skill 合集。按子目录组织，每个目录一个独立 skill。

## 目录

| Skill | 说明 |
| --- | --- |
| [skill-teardown](./skill-teardown) | 把一个 skill / 文档 / 提示词拆解成一篇「批注式长卷 HTML」——先质量裁决、再还原运行画面、最后逐段英文原文 + 中文译文 + 可展开深度批注。 |
| [skill-anatomist-v3](./skill-anatomist-v3) | 面向初学者的 Skill 解剖教授：先讲清什么时候用、怎么用和会得到什么，再解释设计因果，最后对 `SKILL.md` 做全文逐段翻译与教授批注。 |

## 安装

把对应目录复制到目标工具的 skill 加载路径即可：

```bash
# WisCode 全局 skill 目录
cp -r skill-teardown ~/.wiscode/skills/

# Codex 用户级 skill 目录
cp -r skill-anatomist-v3 ~/.agents/skills/
```

## 约定

- 每个 skill 是一个独立子目录，根目录至少有一个 `SKILL.md`。
- 大型 skill 可带 `references/`（按需加载的参考文档）、`assets/`（模板等输出资源）和 `agents/`（界面元数据等）。
