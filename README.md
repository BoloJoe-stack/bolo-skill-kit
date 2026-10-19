# Bolo 的 skill 工具包

面向 Claude Code 及兼容 AI 编码助手的中文 skill 集合。

各 skill 均源自实际项目实践，记录的是已验证的问题与处置方式，而非通用最佳实践。

## 目录

| Skill | 功能 |
|---|---|
| [webpage-retemplate](webpage-retemplate/) | 依据既有网页版式生成新页面，附内容保真核对管线 |
| [project-update](project-update/) | 项目收尾流程：文档更新、自检、敏感内容扫描、提交与推送 |
| [page-shot](page-shot/) | 多标签页 / 分页 / 超长滚动网页的逐页整页截图 |
| [lit-source-search](lit-source-search/) | 为文档条目检索英文学术文献依据，每轮输出 5 篇候选后暂停 |
| [autonomous-mode](autonomous-mode/) | 长任务的授权式工作模式：方案照走、细节自决，只有四类硬停，收尾交一份「决策＋结果」文档 |

各目录包含：

- `SKILL.md` —— skill 本体
- `README.md` —— 功能定位、设计依据与注意事项
- 部分含 `templates/` —— 可直接复用的脚本

## 安装

将目标 skill 目录整体复制至 skills 目录：

```bash
# 项目级（仅对当前项目生效）
cp -r webpage-retemplate <项目目录>/.claude/skills/

# 用户级（对所有项目生效）
cp -r webpage-retemplate ~/.claude/skills/
```

重启会话后生效。触发方式见各 skill 的 `description` 字段。

## 说明

### 关于「project-update」的敏感内容扫描

该 skill 记录了一项已验证的失效情形：**用于记录"已扫描哪些敏感模式"的说明文字，其本身会被扫描规则命中**。

处置方式为：每条模式必须附带**尾部长度限定**。真实 token 形如 `ghp_` 加 36 位字符，而文档中提及模式名时其后通常紧跟反引号或空格，长度不足，因而不会触发误报。

### 关于「webpage-retemplate」的核对管线

网页版式复刻的主要风险不在于页面生成，而在于内容失真。该 skill 因此配备双向机器核对：

- 正向查漏：原文中的数字、名称、文献、断言句是否均出现在页面上
- 反向校验：页面上的数字与文本块能否在原文中找到对应，用于防止内容杜撰
- 链接比对：DOI 与 URL 双向核对

配套两个可直接复用的 Python 脚本，位于 `webpage-retemplate/templates/`。

### 关于「autonomous-mode」的能力边界

该 skill 降低的是**询问成本**，不降低**验证成本**。它要求把"派独立复核子代理"和"即时落档"当作默认动作，这两项开销高于不加载时的做法——省下来的是人被打断的次数，不是总工作量。适用边界与失效模式均写在规范内（含一张"我会怎么判断错"的对照表）。

## 目录结构

```
bolo-skill-kit/
├── README.md
├── webpage-retemplate/
│   ├── SKILL.md
│   ├── README.md
│   └── templates/
│       ├── fidelity_check.py    内容保真核对（正向 / 反向 / 链接）
│       └── page_check.py        页面检查（控制台 / 溢出 / 截图 / 渲染文本）
├── project-update/
│   ├── SKILL.md
│   └── README.md
├── page-shot/
│   ├── SKILL.md
│   └── README.md
├── lit-source-search/
│   ├── SKILL.md
│   └── README.md
└── autonomous-mode/
    ├── SKILL.md
    └── README.md
```

## 许可

MIT
