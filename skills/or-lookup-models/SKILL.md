---
name: or-lookup-models
description: Use when the user wants to look up models in the OpenRouter catalog — fetch the full model list, look up a specific model by ID, or get raw catalog data for downstream filtering. Triggers on phrases like "look up an OpenRouter model", "get the OpenRouter catalog", "what does OpenRouter list for <model-id>", "fetch OR models". This is the foundation skill the other OR research skills build on.
---

# OpenRouter Model Lookup

Fetch the OpenRouter model catalog and return either the full catalog or a single model's record. The endpoint is unauthenticated — no API key required.

## When to use

- User asks for raw catalog data, a specific model's metadata, or a list of models
- Another skill in this plugin needs catalog data to filter or rank models

## Endpoint

```
GET https://openrouter.ai/api/v1/models
```

Returns `{ "data": [ { ...model... }, ... ] }`. Each model has fields including:

- `id` — e.g. `openai/gpt-4o-mini`
- `name` — display name
- `created` — unix timestamp
- `description`
- `context_length` — max context tokens
- `architecture.input_modalities` — array, e.g. `["text", "image"]`
- `architecture.output_modalities` — array
- `architecture.tokenizer`
- `pricing.prompt` — USD per token (string)
- `pricing.completion` — USD per token (string)
- `pricing.image`, `pricing.request`, `pricing.web_search`
- `top_provider.context_length`, `top_provider.max_completion_tokens`
- `supported_parameters` — array, e.g. `["tools", "tool_choice", "response_format", "structured_outputs"]`
- `per_request_limits` (nullable)

## Workflow

1. Fetch the catalog with curl or WebFetch:
   ```bash
   curl -s https://openrouter.ai/api/v1/models -H "Accept: application/json"
   ```
2. If the user named a specific model ID, filter to that record and return it cleanly formatted.
3. If they asked for the full catalog, return a brief summary (count, sample of IDs) — never dump the whole JSON to the user unless they ask.
4. If they want a slice (e.g. "all Anthropic models"), filter `data[].id` by prefix and return matching records.

## Pricing notes

Prices are returned as strings in USD per **token** (not per million). To display per-1M-tokens, multiply by 1,000,000. Always show prices as `$X.XX / 1M tokens` for readability unless the user wants raw values.

## Output

- Single model: a compact summary block showing id, context, modalities, pricing per 1M, supported parameters.
- Multiple models: a markdown table with columns: ID, Context, In Modalities, Prompt $/1M, Completion $/1M.
- Always cite the data source as the OpenRouter catalog endpoint and note the timestamp of fetch.

## Caching

The catalog changes frequently. Do not cache results across invocations — re-fetch each time the skill runs.
