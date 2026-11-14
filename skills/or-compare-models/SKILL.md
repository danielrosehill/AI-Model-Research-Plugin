---
name: or-compare-models
description: Use when the user wants to compare two or more OpenRouter models head-to-head. Triggers on phrases like "compare <model-a> and <model-b> on OpenRouter", "head-to-head OR comparison", "which is better — <model-a> or <model-b>", "side-by-side OpenRouter models", "diff these OR models".
---

# Head-to-Head OpenRouter Model Comparison

Build a structured side-by-side comparison of two or more OpenRouter models so the user can choose between them.

## When to use

The user has named 2+ specific OpenRouter models (or asked to compare picks from a previous recommendation) and wants a structured comparison.

## Workflow

### Step 1: Identify the models

If the user named the models, take their IDs as-is. If they referenced them indirectly ("compare the two cheapest tool-calling models"), first run the relevant filter (via `or-find-tool-models`) and pick the targets.

If a model ID is ambiguous or not found in the catalog, ask for clarification before proceeding.

### Step 2: Fetch catalog data

CLI: `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/orexplorer.py` (stdlib, no API key). JSON on stdout by default; `--table` for a human view; `--compact` for one-line JSON. Prices are already US$ per 1M tokens. Router entries (`openrouter/auto`, ...) have null prices (shown `-`): they route dynamically, so exclude them from price rankings.

For each model:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/orexplorer.py model <id> --brief     # price, context, modalities, caps, batch, knowledge cutoff, variants
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/orexplorer.py endpoints <id>         # per-provider price, quantization, uptime (add when price/reliability matters)
```

`--brief` omits the raw record. Use full `model <id>` only if you need `pricing.image`, `top_provider`, `per_request_limits` or the tokenizer. Optionally add `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/orexplorer.py performance -q <id>` for p50 latency/throughput (scrapes openrouter.ai/rankings, undocumented, may break; say so if used).

### Step 3: Build the comparison table

Render a markdown table with one column per model and one row per dimension. Recommended rows:

| Dimension | Model A | Model B |
|---|---|---|
| Provider | | |
| Context length | | |
| Max output tokens | | |
| Input modalities | | |
| Output modalities | | |
| Prompt $/1M tokens | | |
| Completion $/1M tokens | | |
| Image $/each (if vision, from full record) | | |
| Tool use support | yes/no | yes/no |
| Structured outputs | yes/no | yes/no |
| Tokenizer (full record) | | |
| Created (date) | | |
| Reasoning / batch support | | |
| Providers, uptime (from `endpoints`) | | |


### Step 4: Add a written summary

Below the table, write a 3–5 sentence summary highlighting:

- Where the models meaningfully differ (price ratio, context ratio, capability gaps)
- What each is better suited for, based on the differences
- A clear "if X matters most, pick A; if Y matters most, pick B" verdict

### Step 5: Offer to deepen the analysis

End with: "Want me to research either of these models beyond the OR catalog (model card, benchmarks, license)?" — route to `or-evaluate-model` if yes.

## Notes

- Don't bring in benchmark scores or qualitative judgments from memory. Stick to CLI facts in the table. Save subjective comparisons for the summary, and clearly mark them as your interpretation.
- If comparing more than 3 models, the table gets unwieldy — suggest grouping into pairs or running a recommendation flow instead.
- If two models are nearly identical (same family, e.g. `gpt-4o` vs `gpt-4o-2024-08-06`), say so explicitly and explain what differs (typically date / pricing tier).
