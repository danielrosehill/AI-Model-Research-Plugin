---
name: or-quick-lookup
description: Use when the user mentions an OpenRouter model ID mid-conversation and needs a quick capability/pricing snapshot — not a full evaluation.
---

# Quick Model Lookup

Retrieve a single model's essential metadata from OpenRouter: pricing, context length, supported modalities, and provider. This is the lightweight skill for rapid checks without deep evaluation.

## When to use

- User asks "what is [model-id]?" or "what model is that?"
- User asks about pricing for a specific model ("how much does X cost?")
- User asks a single-attribute question about a model ("is X vision-capable?", "what's the context window?")
- Mid-conversation mention of a model ID that needs quick clarification

## Inputs to gather

- Model ID (slash-form, e.g. `openai/gpt-4o` or `google/gemini-2.5-flash`)

## Procedure

1. Run `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/orexplorer.py model <id> --brief` (JSON; prices are US$ per 1M tokens). If it errors with "no model", the ID is wrong: try `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/orexplorer.py models -q <fragment> --table`.
2. Read `summary`: `input_per_m`, `output_per_m`, `context`, `max_output`, `input`/`output` modalities, `caps` (tools, vision, reasoning, ...), `batch`, `knowledge_cutoff`, `variants` (e.g. `:free`, `:batch`). Null prices mean a router model.
3. Return a 1-2 sentence summary with the key facts.

## Output / side effects

User receives pricing (input/output per 1M tokens), context window, modalities, and provider. No persistent artifacts.

If the user wants capability comparisons, benchmarks, or cost projections, suggest `or-evaluate-model`, `or-compare-models`, or `or-cost-projection` respectively.
