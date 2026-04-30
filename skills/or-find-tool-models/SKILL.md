---
name: or-find-tool-models
description: Use when the user wants to find OpenRouter models that support tool use / function calling. Triggers on phrases like "OpenRouter models with tool use", "which OR models support function calling", "find tool-calling models on OpenRouter", "MCP-compatible models on OpenRouter", "models for agentic workflows on OR".
---

# Find OpenRouter Tool-Calling Models

Filter the OpenRouter catalog to models that declare tool/function calling support, then rank or summarize them based on the user's stated criteria (price, context, provider).

## When to use

The user wants to discover models suitable for agentic / tool-using workflows on OpenRouter — function calling, MCP, code agents, structured tool invocation.

## Workflow

1. Fetch the catalog:
   ```bash
   curl -s https://openrouter.ai/api/v1/models -H "Accept: application/json"
   ```
2. Filter `data[]` where `supported_parameters` includes `"tools"`. Optionally also require `"tool_choice"` for stricter filtering.
3. If the user expressed preferences (cheapest, largest context, specific provider), apply them:
   - **Cheapest** — sort by `pricing.completion` ascending
   - **Largest context** — sort by `context_length` descending
   - **Provider** — filter `id` by prefix (`openai/`, `anthropic/`, `google/`, `meta-llama/`, etc.)
4. If the user did not state criteria, ask one short clarifying question: budget ceiling? minimum context? preferred providers?
5. Return the top 5–10 matches as a markdown table: ID, Context, Prompt $/1M, Completion $/1M, Other supported params.

## Notes

- Prices in the catalog are USD per token. Multiply by 1,000,000 for $/1M-token display.
- Some models list `tools` but have caveats noted in their description — surface those if relevant.
- Free models (pricing all `"0"`) often have rate limits and lower reliability — flag this when recommending free models.

## Output

Markdown table sorted by the user's stated criterion (default: cheapest completion price). Include a one-line summary of how many tool-capable models exist in the catalog total.
