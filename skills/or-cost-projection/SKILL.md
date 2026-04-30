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

1. Call `mcp__model-scout__consider_models` with the model ID(s), workload parameters, and cost-projection intent.
2. For each model, retrieve input and output pricing (per 1M tokens).
3. Calculate total cost: (input_tokens × input_price/1M) + (output_tokens × output_price/1M), multiplied by request count.
4. If a daily rate was given, extrapolate to monthly (×30) and annual (×365).
5. Present results as a table ranked by cheapest-first, showing per-model totals and absolute cost spread (difference vs. cheapest option).

## Output / side effects

User receives a cost table with per-model totals, monthly/annual projections if applicable, and explicit ranking. No persistent artifacts.

## Safety / constraints

Cost estimates are based on published OpenRouter pricing at the time of the lookup. Actual usage may incur additional fees (e.g., cache writes). Confirm workload assumptions with the user before committing.
