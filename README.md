<p align="center">
  <img alt="License" src="https://img.shields.io/badge/license-MIT-blue" />
  <img alt="Python" src="https://img.shields.io/badge/python-3.9+-gold" />
  <img alt="Status" src="https://img.shields.io/badge/status-alpha-c14438" />
</p>

<h1 align="center">命理裁决台 · 天机秘册</h1>

<p align="center"><strong>多 Agent 命理辩论裁决引擎</strong> — AI 驱动的八字与紫微斗数双流派分析系统</p>

<p align="center"><a href="README_EN.md">English</a></p>

---

## 更新日志

| 版本 | 日期 | 说明 |
|------|------|------|
| **v0.2.0** | 2026-05 | Web 管理台上线：中国风单页 UI、八卦圈登录、SSE 实时事件流、粒子动效系统 |
| **v0.1.0** | 2026-04 | 核心辩论裁决引擎：八字 + 紫微双流派分析、裁判控题、结构化辩论、终局裁决、报告合成 |
| **v0.0.1** | 2026-03 | 项目初始化：基础 CLI、分析器骨架、数据模型定义 |

> 项目处于 alpha 阶段，API 和辩论协议仍在迭代。

---

## 为什么做这个

当前 AI 命理分析工具普遍存在三个问题：

1. **单一流派视角** — 八字归八字、紫微归紫微，各说各的。不同流派之间对同一命盘的解释经常冲突，但没有机制让它们对质。
2. **黑盒打分** — 让模型输出一个 `confidence` 分数，用规则词表判断"谁更对"。裁决简化为数字比较，丢失了推理过程。
3. **开放式聊天** — 两个 LLM 无约束地对聊，产出大量文本但缺乏结构。没有控题、没有裁决，用户面对的是并行独白而不是辩论。

命理裁决台解决的是这个具体问题：**让两个流派在裁判的控题下，围绕真正的争点进行结构化辩论，并基于辩论文本本身做出裁决。**

---

## 核心技术原理

### 1. 先分析、再争论、再裁决（三阶段流水线）

- **分析阶段**：八字和紫微各自输出完整的自然语言分析文本，互不干扰
- **辩论阶段**：裁判从两份分析中提取争点，双方仅围绕该争点回应，每轮检查是否跑题、是否继续
- **裁决阶段**：基于整段辩论记录做终局裁决，不依赖任何置信度分数

### 2. 文本驱动裁决

裁判阅读双方完整回应链，判断哪一方回应更直接、推理链更完整、是否存在回避关键问题的情况。不使用 confidence 分数，不用关键词对撞。

### 3. 裁判控题

裁判从两份分析中筛出真正有冲突的问题，每轮给出明确讨论边界。发现跑题时要求重新回应。明确区分"已充分辩论"和"无法继续"。

### 4. 结构化输出

报告必须包含四类信息：**共识**、**分歧**、**保留意见**、**补充资料建议**，缺一不可。

### 5. 可回放追踪

每次运行自动落盘完整 trace，包含原始输入、各阶段输出、辩论记录、裁决结果。支持事后回放。

### 6. 多模型适配

统一的 adapter 层屏蔽不同 LLM 提供商差异。当前支持 OpenAI / Anthropic / OpenRouter / DeepSeek。

### 7. 流式事件推送

Web 端通过 SSE 实时推送运行进度 — 分析完成、争点识别、每轮辩论、裁决结果按时间序到达前端。

---

## 功能特性

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
| 受控辩论 | 双方只回应裁判点名的争点 |
| 逐轮裁决 | 每轮检查回应质量，决定是否继续 |
| 终局裁决 | 基于完整辩论文本的独立裁决 |

### 交互界面

| 特性 | 说明 |
|------|------|
| CLI 命令行 | 支持 `--demo` / `--query` / `--replay-trace` |
| Web 管理台 | 中国风单页应用，八卦圈登录、实时事件流 |
| SSE 流式推送 | 分析进度按事件实时到达前端 |

### 工程能力

| 特性 | 说明 |
|------|------|
| 多模型适配 | OpenAI / Anthropic / OpenRouter / DeepSeek |
| 运行可回放 | 自动落盘 trace，支持事后 review |
| 文本安全 | 内置安全策略层 |
| 测试覆盖 | pytest 测试套件覆盖核心链路 |

---

## 快速开始

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
export OPENAI_API_KEY="sk-..."
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

## 使用指南

### CLI 命令

```bash
.venv/bin/divination-fusion --demo
.venv/bin/divination-fusion --query "请分析我未来三年的事业运势"
.venv/bin/divination-fusion --query "我的财运如何" --birth-date "1990-06-12" --birth-time "07:45"
.venv/bin/divination-fusion --replay-trace runs/<run_id>
.venv/bin/divination-fusion --help
```

### Web 管理台

```bash
export DIVINATION_ADMIN_PASSWORD='你的密码'
.venv/bin/divination-fusion-web
```

打开 http://127.0.0.1:8000/ ，点击中央八卦圈，输入密码登录。

### 运行测试

```bash
.venv/bin/pytest
```

---

## 项目结构

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
├── adapters.py       # 多模型适配
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

## 架构红线

1. **先分析，再争论，再裁决，再出报告** — 阶段顺序不可跳过或合并
2. **争论单位是"具体争点"** — 不是开放式群聊
3. **信息不足时必须明确保留** — 不能编造结论
4. **报告必须区分共识、分歧、保留意见、补充资料建议** — 四类缺一不可
5. **裁决基于文本，不基于分数**
6. **每次运行自动落盘 trace** — 可回放、可审查

---

## 参考文献

### 多 Agent 辩论与裁决框架

| 来源 | 类型 | 参考点 |
|------|------|--------|
| [Deb8flow](https://github.com/iason-solomos/Deb8flow) | GitHub | 分阶段编排、回合边界 |
| [MALLM](https://github.com/Multi-Agent-LLMs/mallm) | GitHub | 裁判中途介入、纠偏 |
| [Agent-as-a-Judge](https://github.com/metauto-ai/agent-as-a-judge) | GitHub | 裁判作为独立能力层 |
| [Multi_Agent_Judge_Bias](https://github.com/Henrymachiyu/Multi_Agent_Judge_Bias) | GitHub | 裁判偏差审视 |
| [M-MAD](https://aclanthology.org/2025.acl-long.351/) | ACL 2025 | 先拆维度再综合判断 |
| [Chain-of-Thought Prompting](https://arxiv.org/abs/2201.11903) | NeurIPS 2022 | 思维链推理 |
| [Constitutional AI](https://arxiv.org/abs/2212.08073) | arXiv | AI 反馈无害化训练 |

### 玄学与命理系统

| 来源 | 类型 | 参考点 |
|------|------|--------|
| [Yuan（元）](https://github.com/LZRight123/yuan) | GitHub | 综合命理 Agent，prompts layering 架构 |
| [esotericAI](https://openhunts.com/winners?date=2026-03-26) | SaaS | AI 塔罗 + 占星，动态解读生成 |
| [Kerykeion](https://github.com/gcali/kerykeion) | GitHub | Python 占星计算，SVG 星盘 |
| [OpAstro](https://dev.to/dakidarts/opastro-building-an-open-core-astrology-engine-developers-can-actually-use-ljf) | GitHub | 开源占星引擎 |
| [太乙神数 (Taiyi)](https://github.com/topics/taiyi?l=python) | GitHub | 太乙神数 Python 实现 |
| [缘份居 Astrology Toolkit](https://www.cnblogs.com/yuanfenju/p/19985408) | WordPress | 八字/紫微/奇门/六爻 API 封装 |

---

## 许可证

[MIT](LICENSE)

---

<p align="center"><em>天机秘册 · 古今相聚</em></p>
