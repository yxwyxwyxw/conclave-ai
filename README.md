<p align="center">
  <img alt="License" src="https://img.shields.io/badge/license-MIT-blue" />
  <img alt="Python" src="https://img.shields.io/badge/python-3.9+-gold" />
  <img alt="Status" src="https://img.shields.io/badge/status-alpha-c14438" />
</p>

<h1 align="center">命理裁决台 · 天机秘册</h1>

<p align="center"><strong>多 Agent 命理辩论裁决引擎</strong> — AI 驱动的八字与紫微斗数双流派分析系统</p>

<p align="center">
  <a href="#%E4%B8%AD%E6%96%87">中文</a>
  ·
  <a href="#english">English</a>
</p>

---

<div id="中文">

## ✦ 更新日志

| 版本 | 日期 | 说明 |
|------|------|------|
| **v0.2.0** | 2026-05 | Web 管理台上线：中国风单页 UI、八卦圈登录、SSE 实时事件流、粒子动效系统 |
| **v0.1.0** | 2026-04 | 核心辩论裁决引擎：八字 + 紫微双流派分析、裁判控题、结构化辩论、终局裁决、报告合成 |
| **v0.0.1** | 2026-03 | 项目初始化：基础 CLI、分析器骨架、数据模型定义 |

> 项目处于 alpha 阶段，API 和辩论协议仍在迭代。欢迎提 Issue 和 PR。

---

## ✦ 为什么做这个

当前 AI 命理分析工具普遍存在三个问题：

1. **单一流派视角** — 八字归八字、紫微归紫微，各说各的，用户只能看到片面的结论。不同流派之间对同一命盘的解释经常冲突，但没有机制让它们对质。
2. **黑盒打分** — 常见做法是让模型输出一个 `confidence` 分数，然后用规则词表判断"谁更对"。这种做法把裁决简化为数字比较，丢失了推理过程的全部信息量。
3. **开放式聊天** — 让两个 LLM 无约束地对聊，产出大量文本但缺乏结构。没有控题、没有裁决、没有终局，用户面对的是两段并行独白而不是真正的辩论。

命理裁决台解决的是这个具体问题：**让两个流派在裁判的控题下，围绕真正的争点进行结构化辩论，并基于辩论文本本身做出裁决。**

---

## ✦ 核心技术原理

### 1. 先分析、再争论、再裁决（三阶段流水线）

不同于端到端聊天方案，系统将一次运行拆为三个严格分离的阶段：

- **分析阶段**：八字和紫微各自输出完整的自然语言分析文本，互不干扰
- **辩论阶段**：裁判从两份分析中提取争点，双方仅围绕该争点回应，每轮检查是否跑题、是否继续
- **裁决阶段**：基于整段辩论记录做终局裁决，不依赖任何置信度分数

参考：[Deb8flow](https://github.com/iason-solomos/Deb8flow) 的分阶段编排设计、[MALLM](https://github.com/Multi-Agent-LLMs/mallm) 的裁判中途介入机制。

### 2. 文本驱动裁决

裁决的唯一依据是辩论文本本身 — 裁判阅读双方的完整回应链，判断：

- 哪一方对对方论点的回应更直接
- 哪一方的推理链更完整
- 是否存在一方回避了关键问题

不再使用 `confidence` 分数、不再用关键词对撞判断冲突、不再把 battle 写成开放式群聊。

### 3. 裁判控题

裁判的职责不只是"最后判谁赢"。在辩论阶段，裁判持续介入：

- **筛出争点**：从两份分析中识别真正有冲突的具体问题
- **限定范围**：每轮给出明确的讨论边界，禁止跑题
- **纠偏与重答**：发现回应偏离争点时要求重新回应
- **终局条件**：明确区分"该争点已充分辩论"和"无法继续"

### 4. 结构化输出保障

报告必须包含四类信息，缺一不可：

- **共识** — 双方明确一致的部分
- **分歧** — 双方立场不同的争议点
- **保留意见** — 信息不足、无法下结论的部分
- **补充资料建议** — 如果用户能提供 X，可以更确定 Y

### 5. 可回放追踪

每次运行自动落盘完整 trace — 包含原始输入、各阶段输出、辩论记录、裁决结果。支持事后回放，方便调试裁判控题策略、分析模型波动对裁决稳定性的影响、作为评测基准的候选样本。

### 6. 多模型适配

通过统一的 adapter 层屏蔽不同 LLM 提供商的差异。当前支持：OpenAI / Anthropic / OpenRouter / DeepSeek。

### 7. 流式事件推送

Web 端通过 Server-Sent Events (SSE) 实时推送运行进度 — 分析完成、争点识别、每轮辩论、裁决结果等事件按时间序到达前端，用户不需要刷新页面。

---

## ✦ 功能特性

### 分析引擎

| 特性 | 说明 |
|------|------|
| 八字分析 | 日主强弱、十神格局、大运流年、五行生克 |
| 紫微斗数分析 | 命宫十二宫、四化星曜、三方四正 |
| 流派可扩展 | 系统架构预留了新流派接入点 |

### 辩论与裁决

| 特性 | 说明 |
|------|------|
| 自动争点识别 | 裁判从两份分析文本中提取冲突点 |
| 受控辩论 | 双方只回应裁判点名的争点，不跑题 |
| 逐轮裁决 | 每轮检查回应质量，决定是否继续 |
| 终局裁决 | 基于完整辩论文本的独立裁决 |

### 交互界面

| 特性 | 说明 |
|------|------|
| CLI 命令行 | 终端调试入口，支持 `--demo` / `--query` / `--replay-trace` |
| Web 管理台 | 中国风单页应用，八卦圈登录、实时事件流、报告渲染 |
| SSE 流式推送 | 分析进度按事件实时到达前端 |

### 工程能力

| 特性 | 说明 |
|------|------|
| 多模型适配 | OpenAI / Anthropic / OpenRouter / DeepSeek |
| 运行可回放 | 自动落盘 trace，支持事后 review |
| 文本安全 | 内置安全策略层，过滤敏感内容 |
| 测试覆盖 | pytest 测试套件覆盖核心链路 |

---

## ✦ 竞品对比

| 维度 | 本项目 | 单一 LLM 算命 | 多 Agent 开放聊天 |
|------|--------|---------------|-------------------|
| 流派覆盖 | 八字 + 紫微双流派 | 通常单流派 | 不确定 |
| 冲突处理 | 裁判识别争点，结构化辩论 | 无冲突机制 | 无约束对聊 |
| 裁决方式 | 基于辩论文本的独立裁决 | 直接给结论 | 无裁决 |
| 控题机制 | 裁判全程控题、纠偏 | 无 | 无 |
| 报告结构 | 共识·分歧·保留·补充 | 一段话 | 两端话 |
| 可回放 | 完整 trace 落盘 | 无 | 极少 |
| 交互界面 | CLI + Web 双入口 | 通常只有聊天界面 | 通常只有聊天界面 |
| 模型适配 | 4 家提供商 | 通常 1 家 | 不确定 |

---

## ✦ 快速开始

### 前置条件

- Python 3.9+
- 至少一个 LLM API Key（OpenAI、Anthropic、OpenRouter 或 DeepSeek）

### macOS / Linux

```bash
git clone https://github.com/yxwyxwyxw/conclave-ai.git
cd conclave-ai
python3 -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'

# 设置 API Key
export OPENAI_API_KEY="sk-..."

# 运行
.venv/bin/divination-fusion --demo
```

### Windows (PowerShell)

```powershell
git clone https://github.com/yxwyxwyxw/conclave-ai.git
cd conclave-ai
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e ".[dev]"

.venv\Scripts\divination-fusion.exe --demo
```

---

## ✦ 使用指南

### CLI 命令

```bash
# 运行内置演示案例
.venv/bin/divination-fusion --demo

# 自定义查询
.venv/bin/divination-fusion --query "请分析我未来三年的事业运势"

# 指定出生信息
.venv/bin/divination-fusion \
  --query "我的财运如何" \
  --birth-date "1990-06-12" \
  --birth-time "07:45" \
  --birth-place "上海"

# 回放某次运行
.venv/bin/divination-fusion --replay-trace runs/<run_id>

# 查看帮助
.venv/bin/divination-fusion --help
```

### Web 管理台

```bash
# 设置登录密码
export DIVINATION_ADMIN_PASSWORD='你的密码'

# 启动服务
.venv/bin/divination-fusion-web
```

打开 http://127.0.0.1:8000/ ，点击中央八卦圈，输入密码登录。

### 运行测试

```bash
.venv/bin/pytest          # 运行全部测试
.venv/bin/pytest -v       # 带详细输出
```

---

## ✦ 开发者安装

```bash
git clone https://github.com/yxwyxwyxw/conclave-ai.git
cd conclave-ai
python3 -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
```

## ✦ 项目结构

```
src/divination_fusion/
├── agents/           # 输入解析与请求构造
├── battle/           # 辩论引擎
├── judge/            # 裁判裁决
├── report/           # 报告合成
├── safety/           # 安全策略层
├── services/         # 字段归一化
├── systems/          # 流派分析器
│   ├── bazi/         #   八字
│   └── astrology/    #   紫微斗数
├── evals/            # 评测基准
├── adapters.py       # 多模型适配层
├── auth.py           # Web 认证
├── chart_engine.py   # 命盘计算
├── cli.py            # 命令行入口
├── models.py         # 数据模型
├── orchestrator.py   # 运行编排
├── prompts.py        # 提示词管理
├── session_store.py  # 会话持久化
├── text_debate.py    # 辩论协议
├── trace.py          # 运行追踪
├── web_ui.py         # Web 界面
├── webapp.py         # FastAPI 应用
└── workflow.py       # 工作流定义

prompts/              # 系统提示词
tests/                # 测试套件
```

---

## ✦ 架构红线

以下原则不会因为功能迭代而改变：

1. **先分析，再争论，再裁决，再出报告** — 阶段顺序不可跳过或合并
2. **争论单位是"具体争点"** — 不是整场随便聊，不是开放式群聊
3. **信息不足时必须明确保留** — 不能编造结论
4. **报告必须区分共识、分歧、保留意见、补充资料建议** — 四类缺一不可
5. **裁决基于文本，不基于分数** — 不使用 confidence 打分体系
6. **每次运行自动落盘 trace** — 可回放、可审查

---

## ✦ 参考文献

| 来源 | 类型 | 参考点 |
|------|------|--------|
| [Deb8flow](https://github.com/iason-solomos/Deb8flow) | GitHub | 分阶段编排、回合边界 |
| [MALLM](https://github.com/Multi-Agent-LLMs/mallm) | GitHub | 裁判中途介入、纠偏 |
| [Agent-as-a-Judge](https://github.com/metauto-ai/agent-as-a-judge) | GitHub | 裁判作为独立能力层 |
| [Multi_Agent_Judge_Bias](https://github.com/Henrymachiyu/Multi_Agent_Judge_Bias) | GitHub | 裁判偏差审视 |
| [M-MAD](https://aclanthology.org/2025.acl-long.351/) | ACL 2025 | 先拆维度再综合判断 |

---

## ✦ 许可证

[MIT](LICENSE)

---

</div>

---

<div id="english">

## ✦ Changelog

| Version | Date | Notes |
|---------|------|-------|
| **v0.2.0** | 2026-05 | Web dashboard: Chinese-style SPA, Bagua circle login, SSE real-time events, particle effects |
| **v0.1.0** | 2026-04 | Core debate engine: BaZi + ZiWei analysis, judge-controlled debate, structured arguments, final ruling, report synthesis |
| **v0.0.1** | 2026-03 | Project init: basic CLI, analyzer skeleton, data models |

> Alpha stage. API and debate protocol are still evolving. Issues and PRs welcome.

---

## ✦ Motivation

Current AI divination tools share three common problems:

1. **Single-school perspective** — BaZi and Zi Wei Dou Shu operate in isolation. Users get one-sided conclusions. Cross-school contradictions have no resolution mechanism.
2. **Black-box scoring** — Models output a `confidence` score, then keyword rules decide "who is right". This reduces judgment to numeric comparison, discarding the entire reasoning process.
3. **Unstructured chat** — Two LLMs talk freely, producing verbose text with no structure. No topic control, no judgment, no termination — the user reads two parallel monologues, not a real debate.

This project solves one specific problem: **two schools debating on structured issues under a judge's control, with rulings based on debate text itself.**

---

## ✦ Core Technical Principles

### 1. Analyze → Debate → Judge (Three-Stage Pipeline)

Each session is split into three strictly separated stages:
- **Analysis**: BaZi and ZiWei each produce complete natural-language analysis independently
- **Debate**: The judge extracts issues from both analyses; each school responds only to the named issue
- **Judgment**: Final ruling based on the full debate transcript, independent of any confidence score

### 2. Text-Driven Judgment

The sole basis for judgment is the debate text itself. The judge reads the full chain of responses to determine:
- Which side addresses the other's arguments more directly
- Which side's reasoning chain is more complete
- Whether either side evades key questions

No confidence scores, no keyword matching, no open-ended group chat.

### 3. Judge-Controlled Debate

The judge does more than just "decide who wins." During the debate phase, the judge:
- **Extracts issues**: identifies genuine conflicts from analysis texts
- **Constrains scope**: sets clear boundaries per round
- **Corrects**: requests re-response when answers go off-topic
- **Terminates**: distinguishes "sufficiently debated" from "cannot continue"

### 4. Structured Output

Every report must contain four categories:
- **Consensus** — points where both schools agree
- **Disagreement** — points where positions differ
- **Reservations** — areas with insufficient information
- **Suggested follow-ups** — what additional data would clarify uncertainty

### 5. Replayable Tracing

Every session automatically saves a complete trace: raw input, stage outputs, debate transcripts, rulings. Supports post-hoc review and debugging.

### 6. Multi-Model Support

A unified adapter layer abstracts over LLM providers: OpenAI, Anthropic, OpenRouter, DeepSeek.

### 7. Real-Time Event Stream

The web dashboard uses Server-Sent Events (SSE) to push progress in real-time — analysis completion, issue detection, each debate round, rulings.

---

## ✦ Quick Start

### Prerequisites

- Python 3.9+
- At least one LLM API key (OpenAI, Anthropic, OpenRouter, or DeepSeek)

```bash
git clone https://github.com/yxwyxwyxw/conclave-ai.git
cd conclave-ai
python3 -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'

# Set API key
export OPENAI_API_KEY="sk-..."

# Run demo
.venv/bin/divination-fusion --demo
```

---

## ✦ Architecture Invariants

1. Analyze → Debate → Judge → Report — stages are never skipped or merged
2. Debate unit is "specific issue" — not open-ended chat
3. Insufficient information must be explicitly stated — no fabricated conclusions
4. Reports distinguish consensus, disagreement, reservations, and follow-ups — all four required
5. Judgment is text-based, not score-based — no confidence scoring
6. Every session auto-saves a trace — replayable and auditable

---

## ✦ License

[MIT](LICENSE)

---

</div>

<p align="center"><em>天机秘册 · 古今相聚</em></p>
