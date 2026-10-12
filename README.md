# Bolo 的 skill 工具包

一组给 **Claude Code**（及兼容的 AI 编码助手）用的中文 skill。每个都是实际做项目时攒下来的，不是照着模板写的——**里面记的是踩过的坑，不是想象出来的最佳实践**。

## 有什么

| Skill | 一句话 |
|---|---|
| **[简洁输出](简洁输出/)** | 让 AI 回复更短、结论先行，技术事实一个不丢。**带 A/B 实测结论和已知失效边界** |
| **[webpage-retemplate](webpage-retemplate/)** | 照一份现成网页的版式做新页面，**含机器核对管线**证明内容与原文一致 |
| **[project-update](project-update/)** | 项目收尾一条龙：补文档 + 自检 + **敏感扫描** + commit + push |
| **[page-shot](page-shot/)** | 把多 tab / 翻页 / 超长滚动的网页**逐页截成整页长图** |
| **[lit-source-search](lit-source-search/)** | 给文档里"有结论、缺依据"的条目找英文学术文献，**每轮 5 篇候选就停下等你挑** |

每个目录下有：

- `SKILL.md` —— skill 本体
- `README.md` —— 这个 skill 的说明、来历、注意事项
- 有些还带 `templates/`（可直接复制的脚本）

## 安装

把想要的 skill 目录整个拷进 skills 目录：

```bash
# 项目级（只对当前项目生效）
cp -r 简洁输出 <你的项目>/.claude/skills/

# 用户级（对你所有项目生效）
cp -r 简洁输出 ~/.claude/skills/
```

重启会话后生效。触发方式看各 skill 的 `description`（多数支持中英文触发词）。

## 几个说明

**关于「简洁输出」**——它不是又一个"请简洁一点"的提示词。我们做过 A/B 对照测试，**它的效果边界是可复现的**：

| 任务类型 | 输出篇幅 | 信息完整性 |
|---|---|---|
| 撰写文档、解释问题 | 减少约 50% | 基本无损失 |
| 代码审查、问题排查 | 减少 34%–45% | ⚠️ **实测会遗漏发现，不推荐单独使用** |

**一个带实测失效边界的提示词，比一百个"请简洁"有用。** 这也是为什么它值得单独拎出来。

**关于「project-update」的敏感扫描**——里面有一条真实踩过的坑：*记录"我扫描过哪些敏感模式"的那句话，本身就会被扫描器命中*。解法是**每条模式都必须带「尾巴长度」**（真 token 是 `ghp_` + 36 位，文档里提到时后面跟的是反引号，长度不够，自然不报）。这类经验是这份文档里最值钱的部分。

**关于「webpage-retemplate」的核对管线**——仿站最难的不是做出来，是**证明你没瞎编**。所以它带了一套双向机器核对：正向查漏（原文有的页面上有没有）+ 反向防杜撰（页面上的原文里找不找得到）+ 链接双向比对。配套两个可直接复制的 Python 脚本。

## 目录结构

```
自创skill/
├── README.md                  ← 本文件
├── 简洁输出/
│   ├── SKILL.md
│   └── README.md
├── webpage-retemplate/
│   ├── SKILL.md
│   ├── README.md
│   └── templates/
│       ├── fidelity_check.py  内容保真核对（正向/反向/链接）
│       └── page_check.py      页面 BUG 检查（控制台/溢出/截图/渲染文本）
├── project-update/
│   ├── SKILL.md
│   └── README.md
├── page-shot/
│   ├── SKILL.md
│   └── README.md
└── lit-source-search/
    ├── SKILL.md
    └── README.md
```

## 许可

MIT
