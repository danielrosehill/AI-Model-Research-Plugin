---
name: or-cost-projection
description: Use when the user wants to estimate the cost of running a workload on a specific OpenRouter model (or shortlist) — produces a cost table with monthly/annual extrapolation.
---

# Cost Projection

Estimate the total cost of running a specific workload (defined by request volume, token counts, time window) on one or more OpenRouter models. Returns per-model breakdowns and comparative rankings.

## When to use

- User asks "how much would X requests cost on model Y?"
- User wants to compare cost across 2–3 models for the same workload
- User specifies a real-world usage scenario with request count, avg input tokens, avg output tokens
- User needs daily, monthly, or annual cost extrapolation

## Inputs to gather

- Model ID(s) (one or more slash-form identifiers)
- Workload volume: requests/day, total requests, or request frequency
- Average input tokens per request
- Average output tokens per request
- Time window (optional): day, month, year — defaults to daily if not specified

## Procedure

CLI: `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/orexplorer.py`; prices in its output are US$ per 1M tokens.

1. For each model ID: `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/orexplorer.py model <id> --brief` and read `summary.input_per_m` and `summary.output_per_m`. A model with null prices is a router: ask the user for a concrete model instead. If the user wants to know the cheapest provider, `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/orexplorer.py endpoints <id>` gives per-provider prices.
2. Compute per request: `input_tokens/1e6 * input_per_m + output_tokens/1e6 * output_per_m`. Multiply by request count.
3. If a daily rate was given, extrapolate to monthly (x30) and annual (x365).
4. If the job is not latency-sensitive and `summary.batch` is true, also project the `:batch` variant: `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/orexplorer.py model <id>:batch --brief` (check its prices; do not assume a discount).
5. Present a table ranked cheapest-first with per-model totals and the cost spread vs. the cheapest.

## Output / side effects

User receives a cost table with per-model totals, monthly/annual projections if applicable, and explicit ranking. No persistent artifacts.

## Safety / constraints

Cost estimates are based on published OpenRouter pricing at the time of the lookup. Actual usage may incur additional fees (e.g., cache writes, per-image or web-search fees, reasoning tokens billed as output). Confirm workload assumptions with the user before committing.
