<p align="center">
  <img alt="License" src="https://img.shields.io/badge/license-MIT-blue" />
  <img alt="Python" src="https://img.shields.io/badge/python-3.9+-gold" />
  <img alt="Status" src="https://img.shields.io/badge/status-alpha-c14438" />
</p>

<h1 align="center">Divination Tribunal · Celestial Archive</h1>

<p align="center"><strong>Multi-Agent Divination Debate & Judgment Engine</strong> — An AI-driven analysis system integrating BaZi (Four Pillars) and Zi Wei Dou Shu (Purple Star Astrology)</p>

<p align="center"><a href="README.md">中文</a></p>

---

## Changelog

| Version | Date | Notes |
|---------|------|-------|
| **v0.2.0** | 2026-05 | Web dashboard: Chinese-style SPA, Bagua circle login, SSE real-time events, particle effects |
| **v0.1.0** | 2026-04 | Core debate engine: BaZi + ZiWei analysis, judge-controlled debate, structured arguments, final ruling, report synthesis |
| **v0.0.1** | 2026-03 | Project init: basic CLI, analyzer skeleton, data models |

> Alpha stage. API and debate protocol are still evolving.

---

## Motivation

Current AI divination tools share three common problems:

1. **Single-school perspective** — BaZi and Zi Wei Dou Shu operate in isolation. Users get one-sided conclusions. Cross-school contradictions have no resolution mechanism.
2. **Black-box scoring** — Models output a `confidence` score, then keyword rules decide "who is right". This reduces judgment to numeric comparison, discarding the entire reasoning process.
3. **Unstructured chat** — Two LLMs talk freely, producing verbose text with no structure. No topic control, no judgment — the user reads parallel monologues, not a real debate.

This project solves one specific problem: **two schools debating on structured issues under a judge's control, with rulings based on debate text itself.**

---

## Core Technical Principles

### 1. Analyze → Debate → Judge (Three-Stage Pipeline)

Each session is split into three strictly separated stages:
- **Analysis**: BaZi and ZiWei each produce complete natural-language analysis independently
- **Debate**: The judge extracts issues from both analyses; each school responds only to the named issue
- **Judgment**: Final ruling based on the full debate transcript, independent of any confidence score

### 2. Text-Driven Judgment

The judge reads the full response chain to determine which side addresses arguments more directly, which reasoning chain is more complete, and whether either side evades key questions. No confidence scores, no keyword matching.

### 3. Judge-Controlled Debate

The judge identifies genuine conflicts from analysis texts, sets clear boundaries per round, requests re-response when off-topic, and distinguishes "sufficiently debated" from "cannot continue."

### 4. Structured Output

Every report must contain four categories: **Consensus**, **Disagreement**, **Reservations**, and **Suggested Follow-ups**. All four are required.

### 5. Replayable Tracing

Every session automatically saves a complete trace: raw input, stage outputs, debate transcripts, rulings. Supports post-hoc review and debugging.

### 6. Multi-Model Support

A unified adapter layer abstracts over LLM providers: OpenAI, Anthropic, OpenRouter, DeepSeek.

### 7. Real-Time Event Stream

The web dashboard uses SSE to push progress in real-time — analysis completion, issue detection, each debate round, rulings.

---

## Features

### Analysis Engine

| Feature | Description |
|---------|-------------|
| BaZi Analysis | Day master strength, Ten Gods pattern, Great Luck cycles, Five Elements interaction |
| Zi Wei Dou Shu Analysis | 12 palaces, Four Transformations, star configurations |
| Extensible | Architecture supports plugging in new divination systems |

### Debate & Judgment

| Feature | Description |
|---------|-------------|
| Auto issue detection | Judge extracts conflicts from analysis texts |
| Controlled debate | Each school responds only to judge-named issues |
| Per-round judgment | Checks response quality each round, decides whether to continue |
| Final ruling | Independent judgment based on full debate transcript |

### Interfaces

| Feature | Description |
|---------|-------------|
| CLI | `--demo` / `--query` / `--replay-trace` support |
| Web dashboard | Chinese-style SPA, Bagua circle login, real-time event stream |
| SSE push | Progress delivered as events in real-time |

### Engineering

| Feature | Description |
|---------|-------------|
| Multi-model | OpenAI / Anthropic / OpenRouter / DeepSeek |
| Replayable tracing | Auto-saved traces for post-hoc review |
| Text safety | Built-in safety policy layer |
| Test coverage | pytest suite covering core pipeline |

---

## Quick Start

### Prerequisites

- Python 3.9+
- At least one LLM API key (OpenAI, Anthropic, OpenRouter, or DeepSeek)

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

## Usage Guide

### CLI Commands

```bash
.venv/bin/divination-fusion --demo
.venv/bin/divination-fusion --query "Analyze my career prospects for the next three years"
.venv/bin/divination-fusion --query "How is my wealth luck" --birth-date "1990-06-12" --birth-time "07:45"
.venv/bin/divination-fusion --replay-trace runs/<run_id>
.venv/bin/divination-fusion --help
```

### Web Dashboard

```bash
export DIVINATION_ADMIN_PASSWORD='your password'
.venv/bin/divination-fusion-web
```

Open http://127.0.0.1:8000/ , click the central Bagua circle, enter the password to log in.

### Running Tests

```bash
.venv/bin/pytest
```

---

## Project Structure

```
src/divination_fusion/
├── agents/           # Input parsing & request construction
├── battle/           # Debate engine
├── judge/            # Judgment & rulings
├── report/           # Report synthesis
├── safety/           # Safety policy layer
├── services/         # Field normalization
├── systems/          # Divination system analyzers
│   ├── bazi/         #   BaZi (Four Pillars)
│   └── astrology/    #   Zi Wei Dou Shu
├── evals/            # Evaluation benchmarks
├── adapters.py       # Multi-model adapter layer
├── auth.py           # Web authentication
├── chart_engine.py   # Chart calculation
├── cli.py            # Command-line entry
├── models.py         # Data models
├── orchestrator.py   # Run orchestration
├── prompts.py        # Prompt management
├── session_store.py  # Session persistence
├── text_debate.py    # Debate protocol
├── trace.py          # Run tracing
├── web_ui.py         # Web interface
├── webapp.py         # FastAPI application
└── workflow.py       # Workflow definition

prompts/              # System prompts
tests/                # Test suite
```

---

## Architecture Invariants

1. Analyze → Debate → Judge → Report — stages are never skipped or merged
2. Debate unit is "specific issue" — not open-ended chat
3. Insufficient information must be explicitly stated — no fabricated conclusions
4. Reports distinguish consensus, disagreement, reservations, and follow-ups — all four required
5. Judgment is text-based, not score-based
6. Every session auto-saves a trace — replayable and auditable

---

## References

### Multi-Agent Debate & Judgment

| Source | Type | Reference |
|--------|------|-----------|
| [Deb8flow](https://github.com/iason-solomos/Deb8flow) | GitHub | Staged pipeline, round boundaries |
| [MALLM](https://github.com/Multi-Agent-LLMs/mallm) | GitHub | Judge intervention, correction |
| [Agent-as-a-Judge](https://github.com/metauto-ai/agent-as-a-judge) | GitHub | Judge as independent capability layer |
| [Multi_Agent_Judge_Bias](https://github.com/Henrymachiyu/Multi_Agent_Judge_Bias) | GitHub | Judge bias awareness |
| [M-MAD](https://aclanthology.org/2025.acl-long.351/) | ACL 2025 | Dimension-first then comprehensive judgment |
| [Chain-of-Thought Prompting](https://arxiv.org/abs/2201.11903) | NeurIPS 2022 | Chain-of-thought reasoning |
| [Constitutional AI](https://arxiv.org/abs/2212.08073) | arXiv | Harmlessness via AI feedback |

### Divination & Astrology Systems

| Source | Type | Reference |
|--------|------|-----------|
| [Yuan](https://github.com/LZRight123/yuan) | GitHub | Comprehensive divination Agent |
| [esotericAI](https://openhunts.com/winners?date=2026-03-26) | SaaS | AI tarot + astrology |
| [Kerykeion](https://github.com/gcali/kerykeion) | GitHub | Python astrology library, SVG charts |
| [OpAstro](https://dev.to/dakidarts/opastro-building-an-open-core-astrology-engine-developers-can-actually-use-ljf) | GitHub | Open-source astrology engine |
| [Taiyi](https://github.com/topics/taiyi?l=python) | GitHub | Taiyi divination in Python |
| [Yuanfenju Astrology Toolkit](https://www.cnblogs.com/yuanfenju/p/19985408) | WordPress | BaZi/ZiWei/QiMen API |

---

## License

[MIT](LICENSE)

---

<p align="center"><em>Celestial Archive · Where Past and Present Converge</em></p>
