<p align="center">
  <img alt="License" src="https://img.shields.io/badge/license-MIT-blue" />
  <img alt="Python" src="https://img.shields.io/badge/python-3.9+-gold" />
  <img alt="Status" src="https://img.shields.io/badge/status-alpha-c14438" />
</p>

<h1 align="center">命理裁决台 · 天机秘册</h1>

<p align="center"><strong>多 Agent 命理辩论裁决引擎</strong> — AI 驱动的八字与紫微斗数双流派分析系统</p>

<p align="center">
  <a href="#-更新日志">更新日志</a> ·
  <a href="#-核心技术原理">技术原理</a> ·
  <a href="#-快速开始">快速开始</a> ·
  <a href="#-使用指南">使用指南</a> ·
  <a href="#-参考文献">参考文献</a>
</p>

---

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

2. **黑盒打分** — 常见做法是让模型输出一个 `confidence` 分数，然后用规则词表判断“谁更对”。这种做法把裁决简化为数字比较，丢失了推理过程的全部信息量。

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

参考：[Agent-as-a-Judge](https://github.com/metauto-ai/agent-as-a-judge) — 把裁判当成独立能力层，而不是最后一句总结。

### 3. 裁判控题

裁判的职责不只是“最后判谁赢”。在辩论阶段，裁判持续介入：

- **筛出争点**：从两份分析中识别真正有冲突的具体问题，不是笼统的“你们意见不同”
- **限定范围**：每轮给出明确的讨论边界，禁止跑题
- **纠偏与重答**：发现回应偏离争点时要求重新回应
- **终局条件**：明确区分“该争点已充分辩论”和“无法继续”（如模型持续跑题）

参考：[Multi_Agent_Judge_Bias](https://github.com/Henrymachiyu/Multi_Agent_Judge_Bias) — 提醒裁判偏差风险，不把单次裁决当作绝对结论。

### 4. 结构化输出保障

报告必须包含四类信息，缺一不可：

- **共识** — 双方明确一致的部分
- **分歧** — 双方立场不同的争议点
- **保留意见** — 信息不足、无法下结论的部分
- **补充资料建议** — 如果用户能提供 X，可以更确定 Y

这四类信息的设计来自 [M-MAD: Multidimensional Multi-Agent Debate](https://aclanthology.org/2025.acl-long.351/) 的先拆维度再综合判断的思路。

### 5. 可回放追踪

每次运行自动落盘完整 trace — 包含原始输入、各阶段输出、辩论记录、裁决结果。支持事后回放，方便：

- 调试裁判控题策略
- 分析模型波动对裁决稳定性的影响
- 作为评测基准的候选样本

### 6. 多模型适配

通过统一的 adapter 层屏蔽不同 LLM 提供商的差异。当前支持：

| 提供商 | 说明 |
|--------|------|
| **OpenAI** | GPT-4o / GPT-4.1 等 |
| **Anthropic** | Claude 系列 |
| **OpenRouter** | 多模型路由 |
| **DeepSeek** | DeepSeek-V3 / R1 |

参考：本项目 `src/divination_fusion/adapters.py`。

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
| **CLI 命令行** | 终端调试入口，支持 `--demo` / `--query` / `--replay-trace` |
| **Web 管理台** | 中国风单页应用，八卦圈登录、实时事件流、报告渲染 |
| SSE 流式推送 | 分析进度按事件实时到达前端 |
| 粒子动效系统 | 光标跟随粒子、点击爆炸效果、笔触扩散动画 |

### 工程能力

| 特性 | 说明 |
|------|------|
| 多模型适配 | OpenAI / Anthropic / OpenRouter / DeepSeek |
| 运行可回放 | 自动落盘 trace，支持事后 review |
| 文本安全 | 内置安全策略层，过滤敏感内容 |
| 测试覆盖 | pytest 测试套件覆盖核心链路 |

---

## ✦ 竞品对比

| 维度 | 命理裁决台 (本项目) | 单一 LLM 算命 | 多 Agent 开放聊天 |
|------|---------------------|----------------|-------------------|
| **流派覆盖** | 八字 + 紫微双流派 | 通常单流派 | 不确定 |
| **冲突处理** | 裁判识别争点，结构化辩论 | 无冲突机制 | 无约束对聊 |
| **裁决方式** | 基于辩论文本的独立裁决 | 直接给结论 | 无裁决 |
| **控题机制** | 裁判全程控题、纠偏 | 无 | 无 |
| **报告结构** | 共识·分歧·保留·补充 | 一段话 | 两端话 |
| **可回放** | 完整 trace 落盘 | 无 | 极少 |
| **交互界面** | CLI + Web 双入口 | 通常只有聊天界面 | 通常只有聊天界面 |
| **模型适配** | 4 家提供商 | 通常 1 家 | 不确定 |

---

## ✦ 快速开始

### 前置条件

- Python 3.9+
- 至少一个 LLM API Key（OpenAI、Anthropic、OpenRouter 或 DeepSeek）

### macOS

```bash
git clone https://github.com/yxwyxwyxw/conclave-ai.git
cd conclave-ai
python3 -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'

# 设置 API Key
export OPENAI_API_KEY="sk-..."
# 或使用其他提供商
export ANTHROPIC_API_KEY="sk-ant-..."
export OPENROUTER_API_KEY="sk-or-..."
export DEEPSEEK_API_KEY="sk-..."

# 运行
.venv/bin/divination-fusion --demo
```

### Linux

```bash
git clone https://github.com/yxwyxwyxw/conclave-ai.git
cd conclave-ai
python3 -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'

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

登录后进入管理台：
1. 点击「新建分析」，填写查询和出生信息
2. 观察实时事件流 — 分析进度、争点识别、辩论记录按 SSE 事件到达
3. 辩论结束后，报告自动渲染 — 共识、分歧、保留意见一目了然

### 运行测试

```bash
# 运行全部测试
.venv/bin/pytest

# 运行特定测试文件
.venv/bin/pytest tests/test_battle.py

# 带详细输出
.venv/bin/pytest -v
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
├── agents/           # 入口 Agent（用户意图解析、请求标准化）
├── battle/           # 辩论引擎（回合管理、回应生成、跑题检测）
├── judge/            # 裁判裁决（争点提取、控题、终局裁决）
├── report/           # 报告合成（共识·分歧·保留·补充）
├── safety/           # 安全策略层（内容过滤、边界检查）
├── services/         # 归一化等服务（出生信息校验、时区转换）
├── systems/          # 流派分析器
│   ├── bazi/         #   八字分析器
│   └── astrology/    #   紫微斗数分析器
├── evals/            # 评测基准
├── adapters.py       # 多模型适配层
├── auth.py           # Web 端认证
├── chart_engine.py   # 命盘计算引擎
├── cli.py            # 命令行入口
├── models.py         # Pydantic 数据模型
├── orchestrator.py   # 运行编排器
├── prompts.py        # 系统提示词管理
├── session_store.py  # 会话持久化
├── text_debate.py    # 文本辩论协议
├── trace.py          # 运行回放与追踪
├── web_ui.py         # Web 界面（嵌入式 HTML）
├── webapp.py         # FastAPI 应用入口
└── workflow.py       # 工作流定义

prompts/              # 系统提示词（15 个提示词文件）
tests/                # 测试套件（15 个测试文件）
docs/                 # 设计文档
```

---

## ✦ 设计参考与致谢

本项目在多个层面借鉴了外部项目的优秀设计，特此说明。

### UI / 交互设计

| 来源 | 借鉴内容 | 对应位置 |
|------|----------|---------|
| [道缘占卜馆 (zj30/-)](https://github.com/zj30/-) | 中国风暗色配色体系（`--gold: #d4a574`、深色渐变底 + 径向金光晕）、光标跟随粒子系统（✦/·/◇ 符号交替、每 30ms 生成 2 粒子）、点击爆炸粒子（8-12 粒子环形扩散）、笔触四向扩散动画、卡片淡入过渡动画、中央圆形按钮交互隐喻 | `web_ui.py` CSS 变量、粒子引擎、Hero 屏幕、八卦圈登录动效 |
| [kwcode (val1813/kwcode)](https://github.com/val1813/kwcode) | README 文档结构：更新日志表格、痛点驱动动机说明、编号技术原理、竞品对比矩阵、平台分列快速开始、参考文献表、架构红线 | `README.md` 整体结构与表述风格 |

### UI 设计迭代记录

在与 Claude Code 的多轮协作中，Web 界面经历了以下关键迭代：

| 迭代 | 讨论与决策 |
|------|-----------|
| 背景深度 | 从 `#1a1410` → `#0f0a06` → 最终 `#1e1813 / #120e0a` 双色径向渐变，平衡深色氛围与可见性 |
| 金色光晕 | 径向渐变 opacity 从 0.025 → 0.06，装饰环从 0.06 → 0.08，确保暗底上金色可见 |
| 粒子密度 | 光标跟随粒子从稀疏调整为每 30ms 2 粒子，点击爆炸 8-12 粒子 |
| 八卦圈登录 | 取代顶部丑陋登录栏，中央八卦圈点击展开密码输入，保留点击动画 |
| Spinner 行为 | 修复页面初始加载和 SSE 等待期间的转圈卡死问题 |

### 辩论机制演进

系统裁决机制经历了一次根本转向：

- **旧方案（已废弃）**：分析员输出结构化 `confidence` 分数 → 规则词表判断冲突 → 按分数高低裁决
- **新方案（当前）**：自然语言分析文本 → 裁判从文本中提取争点 → 受控辩论 → 基于辩论文本终局裁决

这一转向的核心洞察来自 [Agent-as-a-Judge](https://github.com/metauto-ai/agent-as-a-judge) 的理念：裁判应该是独立能力层，而不是最后一句话总结。同时也参考了 [Multi_Agent_Judge_Bias](https://github.com/Henrymachiyu/Multi_Agent_Judge_Bias) 的警示：不能过度迷信单次裁决结果。

---

## ✦ 参考文献

### 多 Agent 辩论与裁决框架

| 来源 | 类型 | 参考点 |
|------|------|--------|
| [Deb8flow](https://github.com/iason-solomos/Deb8flow) | GitHub | 分阶段编排、明确回合边界、主持/裁判角色分离 |
| [MALLM](https://github.com/Multi-Agent-LLMs/mallm) | GitHub | 裁判在讨论中途介入、纠偏、回合控制 |
| [Agent-as-a-Judge](https://github.com/metauto-ai/agent-as-a-judge) | GitHub | 裁判作为独立能力层，不退化为一句话总结 |
| [Multi_Agent_Judge_Bias](https://github.com/Henrymachiyu/Multi_Agent_Judge_Bias) | GitHub | 裁判偏差审视，避免过度迷信单次裁决 |
| [M-MAD: Multidimensional Multi-Agent Debate](https://aclanthology.org/2025.acl-long.351/) | ACL 2025 | 先拆维度再综合判断的多维辩论框架 |
| [Chain-of-Thought Prompting](https://arxiv.org/abs/2201.11903) | NeurIPS 2022 | 大语言模型中的思维链推理 |
| [Constitutional AI](https://arxiv.org/abs/2212.08073) | arXiv | 通过 AI 反馈进行无害化训练 |

### 玄学与命理系统

| 来源 | 类型 | 参考点 |
|------|------|--------|
| [Yuan（元）](https://github.com/LZRight123/yuan) | GitHub | 综合命理 Agent Skill：八字/紫微/占星/称骨/数字命理六法融合。本项目 prompts 的 layering 架构、词法约束、输出自检清单均受其 SKILL.md 启发 |
| [esotericAI](https://openhunts.com/winners?date=2026-03-26) | SaaS | AI 塔罗 + 占星平台。动态解读生成（非硬编码模板）、分层洞察模型（Cosmic Blueprint 可钻取输出）、防 prompt 注入实践 |
| [Kerykeion](https://github.com/gcali/kerykeion) | GitHub | Python 占星计算库，SVG 星盘生成，结构化本命盘/合盘/行运数据导出 |
| [OpAstro](https://dev.to/dakidarts/opastro-building-an-open-core-astrology-engine-developers-can-actually-use-ljf) | GitHub | 开源占星引擎，Swiss Ephemeris 天文计算，open-core 模式（免费引擎 + 付费解读层） |
| [太乙神数 (Taiyi)](https://github.com/topics/taiyi?l=python) | GitHub | 中国古代三式之一太乙神数的 Python 实现，涵盖年/月/日/时/分计与命法 |
| [缘份居 Astrology Toolkit](https://www.cnblogs.com/yuanfenju/p/19985408) | WordPress | 八字/紫微/奇门/六爻/塔罗 API 插件，零本地性能损耗 |

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

## ✦ 参与贡献

欢迎提交 Issue 和 PR。项目处于早期阶段，以下方向尤其值得关注：

- **更多流派接入**：奇门遁甲、六爻、星盘等
- **裁判控题策略优化**：更细粒度的跑题标记、重答机制
- **辩论回放可视化**：时间轴视图展示辩论进程
- **评测基准**：标注真实争点与裁决结果的 gold set
- **国际化**：英语界面

提交 PR 前请确保 `pytest` 通过。

---

## ✦ 许可证

[MIT](LICENSE)

---

<p align="center"><em>天机秘册 · 古今相聚</em></p>
