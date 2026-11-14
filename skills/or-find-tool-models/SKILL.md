---
name: or-find-tool-models
description: Use when the user wants to find OpenRouter models that support tool use / function calling. Supports price, context, provider and batch filtering. Triggers on phrases like "OpenRouter models with tool use", "which OR models support function calling", "find tool-calling models on OpenRouter", "MCP-compatible models on OpenRouter", "models for agentic workflows on OR".
---

# Find OpenRouter Tool-Calling Models

Filter the OpenRouter catalog to models that declare tool/function calling support, then rank or summarize them based on the user's stated criteria (price, context, provider).

## When to use

The user wants to discover models suitable for agentic / tool-using workflows on OpenRouter — function calling, MCP, code agents, structured tool invocation.

## Workflow

CLI: `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/orexplorer.py` (JSON default, `--table` for humans, prices US$ per 1M tokens).

1. If the user gave no criteria, ask one short question: budget ceiling? minimum context? preferred providers? batch OK?
2. Query, mapping criteria to flags:
   ```bash
   python3 ${CLAUDE_PLUGIN_ROOT}/scripts/orexplorer.py models --cap tools --sort price --limit 10 --table
   ```
   - Budget: `--max-in X --max-out Y`; context: `--min-context N`; provider: `--author google` (repeatable); recent: `--days 90`
   - Sort: `price` (input + 3x output, default), `context`, `new`, `name`
   - Stricter needs: add `--cap parallel-tools`, `--cap structured`, `--cap json`; reasoning: `--cap reasoning`; batch pricing: `--batch`
   - The total count is in the `count` field (or the header line with `--table`): use it for the summary line.
3. Return the top 5-10 as a markdown table: ID, Context, Prompt $/1M, Completion $/1M, Other caps.

## Notes

- Prices are already US$ per 1M tokens in CLI output.
- Routers (`openrouter/*`) are hidden unless `--aliases`. Models billed per request, not per token, show null prices with `"token_priced": false` and sort last.
- Free models (`:free`, price 0; use `--free` or `--include-free`) often have rate limits and lower reliability: flag this when recommending them.
- Some models list `tools` but have caveats in their description: `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/orexplorer.py model <id>` if relevant.

## Output

Markdown table sorted by the user's stated criterion (default: cheapest completion price). Include a one-line summary of how many tool-capable models exist in the catalog total.
