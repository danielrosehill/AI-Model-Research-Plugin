---
name: or-recommend-model
description: Use when the user wants a recommendation for which OpenRouter model to use for a task — interactive, asks clarifying questions about budget, context, modalities, then proposes a ranked shortlist. Triggers on phrases like "recommend an OpenRouter model", "which OR model should I use for <task>", "help me pick a model on OpenRouter", "what's the best OR model for <task>", "suggest an OpenRouter model".
---

# Recommend an OpenRouter Model

Interactive recommendation flow: clarify the user's requirements, query the catalog, propose 2–3 ranked picks with rationale.

## When to use

The user wants guidance on choosing a model and has not given enough detail to filter directly. The task is open-ended ("help me pick" / "which model should I use for X").

## Workflow

### Step 1: Gather requirements

Ask the user a short set of clarifying questions — only the ones not already answered. Keep the round-trip tight:

1. **Use case** — what's the workload? (chat, agentic tool use, document parsing, code generation, summarization, vision, audio, structured extraction, etc.)
2. **Modalities** — text only? Need image input? Audio input? Image generation?
3. **Budget** — soft ceiling on $/1M tokens (prompt and completion), or "cheapest possible", or "quality matters more than cost"?
4. **Context window** — minimum context required? (typical buckets: 8K, 32K, 128K, 200K+, 1M+)
5. **Throughput / latency** — does response speed matter? Any provider preference?
6. **Tool use / structured output** — needs function calling? JSON mode? Strict structured outputs?
7. **Open-source preference** — does the user want only open-weights models (DeepSeek, Llama, Qwen, Mistral) or are proprietary models (OpenAI, Anthropic, Google) fine?

Don't ask all seven if the user has already answered some. If you have enough to make a reasonable shortlist after 2–3 questions, proceed.

### Step 2: Filter the catalog

Fetch `https://openrouter.ai/api/v1/models` and apply filters:

- Modality requirements → `architecture.input_modalities`
- Tool/structured output → `supported_parameters` includes `tools` / `structured_outputs`
- Context → `context_length >= user_minimum`
- Budget → `pricing.prompt` and `pricing.completion` within ceiling
- Open-weights only → filter out `openai/`, `anthropic/`, `google/` (proprietary), keep `meta-llama/`, `deepseek/`, `qwen/`, `mistralai/`, etc.

### Step 3: Rank and present

Score each candidate against the user's stated priorities (cost vs. capability vs. context). Present **2–3 recommendations**, not a long list:

- **Top pick** — best overall fit for stated criteria
- **Budget alternative** — cheapest viable option
- **Quality alternative** — if budget allows, the best-in-class option

For each recommendation provide:
- Model ID and provider
- Context length
- Prompt $/1M, Completion $/1M
- Why it fits this task (1–2 sentences referencing the user's stated criteria)
- Any caveats (rate limits, free-tier reliability, known weaknesses)

### Step 4: Offer follow-ups

End by offering: "Want a head-to-head comparison of these picks, or a deeper evaluation of any one model?" — those route to `or-compare-models` and `or-evaluate-model` respectively.

## Notes

- Do not recommend models from memory. Always fetch the catalog — it changes weekly.
- For agentic workflows, prioritize models with `tools` in `supported_parameters`. Mention if a candidate lacks this.
- Free-tier models (`pricing.*: "0"`) usually have stricter rate limits and lower availability — flag this when recommending one.
- If the user's requirements rule out everything in the catalog, say so plainly and suggest relaxing one constraint.
