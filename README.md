# AI Model Research

A Claude Code plugin for researching, filtering, comparing, and evaluating AI models on [OpenRouter](https://openrouter.ai). Pulls live data from the OpenRouter catalog and enriches it with external research where appropriate.

This plugin **subsumes** two earlier projects:

- The standalone `open-router-model-research` plugin (8 catalog-fetching skills).
- The [`Model-Scout-MCP`](https://github.com/danielrosehill/Model-Scout-MCP) server, which is now bundled as the plugin's MCP backbone — providing in-process catalog caching and two consolidated tools (`get_model`, `consider_models`).

## What's inside

### MCP server

| Server | Provides |
|---|---|
| `model-scout` | `get_model` (direct ID lookup) and `consider_models` (filter / compare / recommend / cost / alternatives). Caches the OpenRouter catalog for ~10 minutes. |

### Skills

| Skill | What it does |
|---|---|
| `or-lookup-models` | Foundation skill — fetches the OpenRouter catalog or a single model's record. |
| `or-quick-lookup` | Lightweight mid-conversation snapshot of a single model (capability + pricing) via the MCP. |
| `or-find-tool-models` | Filters the catalog to models supporting tool use / function calling. |
| `or-find-vision-models` | Filters to vision-capable (image-input) models. |
| `or-find-audio-models` | Filters to models that accept audio input. |
| `or-recommend-model` | Interactive recommendation — asks about budget, context, modalities, then proposes a ranked shortlist. |
| `or-compare-models` | Builds a head-to-head side-by-side comparison of 2+ models. |
| `or-evaluate-model` | Deep evaluation of a single model — combines catalog data with model card, paper, license, benchmarks. |
| `or-research-models` | Open-ended exploration of the catalog around a theme, family, or use case. |
| `or-cost-projection` | Estimate the cost of running a workload (requests × tokens) on one or more models. |
| `or-find-alternative` | Find cheaper / similar alternatives to a reference model with explicit trade-off framing. |

## Why this plugin

The OpenRouter catalog is large and changes weekly. These skills:

- Always pull live catalog data — no stale recommendations from training memory.
- Share an in-process catalog cache via the bundled MCP, so repeated lookups don't re-hit the API.
- Cover the whole research lifecycle: discover → filter → recommend → compare → evaluate → cost → alternatives.
- Look beyond the OpenRouter catalog to underlying model cards, papers, and licenses where appropriate.

## Installation

```bash
claude plugins install ai-model-research@danielrosehill
```

No API key required — the OpenRouter catalog endpoint (`/api/v1/models`) is unauthenticated, and so are all the skills and MCP tools in this plugin. (You only need an `OPENROUTER_API_KEY` if you want to actually *call* a model through OpenRouter, which this plugin doesn't do — it's research-only.)

## Usage

The skills fire automatically when relevant. Example prompts:

- "Recommend an OpenRouter model for legal document summarization with a budget of $1/M tokens"
- "Compare claude-sonnet-4-5 and gpt-4o on OpenRouter"
- "What vision models are available on OpenRouter under $0.50/M?"
- "How much would 50k requests at 2k in / 500 out tokens cost on claude-sonnet-4.5?"
- "What's a cheaper alternative to gpt-4o with similar tool-use quality?"

## License

MIT
