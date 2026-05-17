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

## Quick Start

### Prerequisites

- Python 3.9+
- At least one LLM API key (OpenAI, Anthropic, OpenRouter, or DeepSeek)

```bash
git clone https://github.com/yxwyxwyxw/conclave-ai.git
cd conclave-ai
python3 -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
export OPENAI_API_KEY="sk-..."
.venv/bin/divination-fusion --demo
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

| Source | Type | Reference |
|--------|------|-----------|
| [Deb8flow](https://github.com/iason-solomos/Deb8flow) | GitHub | Staged pipeline, round boundaries |
| [MALLM](https://github.com/Multi-Agent-LLMs/mallm) | GitHub | Judge intervention, correction |
| [Agent-as-a-Judge](https://github.com/metauto-ai/agent-as-a-judge) | GitHub | Judge as independent capability layer |
| [Multi_Agent_Judge_Bias](https://github.com/Henrymachiyu/Multi_Agent_Judge_Bias) | GitHub | Judge bias awareness |
| [M-MAD](https://aclanthology.org/2025.acl-long.351/) | ACL 2025 | Dimension-first then comprehensive judgment |

---

## License

[MIT](LICENSE)

---

<p align="center"><em>Celestial Archive · Where Past and Present Converge</em></p>
