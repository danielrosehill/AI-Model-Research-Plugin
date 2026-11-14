---
name: or-lookup-models
description: Use when the user wants to look up models in the OpenRouter catalog — a specific model by ID, a filtered slice, catalogue stats, or raw catalog data for downstream filtering. Triggers on phrases like "look up an OpenRouter model", "get the OpenRouter catalog", "what does OpenRouter list for <model-id>", "how many models are on OpenRouter", "fetch OR models". This is the foundation skill the other OR research skills build on.
---

# OpenRouter Model Lookup

Fetch the OpenRouter model catalog and return either the full catalog or a single model's record. The endpoint is unauthenticated — no API key required.

## When to use

- User asks for raw catalog data, a specific model's metadata, or a list of models
- Another skill in this plugin needs catalog data to filter or rank models

## CLI

`python3 ${CLAUDE_PLUGIN_ROOT}/scripts/orexplorer.py <cmd>` wraps the unauthenticated public catalog (`https://openrouter.ai/api/v1/models`). Stdlib only, no API key. JSON on stdout by default; `--table` for humans; `--compact` for one-line JSON. Results are cached 600s (`--no-cache` to bypass). Prices are already US$ per 1M tokens.

| Need | Command |
|---|---|
| One model | `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/orexplorer.py model <id> --brief` (summary + variants); without `--brief` also the full raw record and `:batch` record |
| Search by text | `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/orexplorer.py models -q <substring>` (matches id, name, description) |
| Slice | `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/orexplorer.py models --author anthropic --sort new --limit 0` |
| Filter | `--cap <flag>` (repeatable), `--min-context`, `--max-in`, `--max-out`, `--batch`, `--days N`, `--free` / `--include-free`, `--aliases` (`~` router aliases) |
| Capability flags | `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/orexplorer.py capabilities` (flag names with model counts) |
| Catalogue size | `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/orexplorer.py stats` (total and models per author) |
| Providers for a model | `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/orexplorer.py endpoints <id>` |

`models` returns `{count, shown, models[]}` with per-model `id, name, created, context, max_output, input_per_m, output_per_m, input[], output[], caps[], batch, knowledge_cutoff, hf`. Default `--limit` is 25 (`0` = all); `count` is the total match. Sort: `price` (input + 3x output), `context`, `new`, `name`.

## Workflow

1. Single model: `model <id> --brief`, present a compact summary block.
2. Full catalogue: report `stats` (count, top authors) and a sample of IDs; never dump everything unless asked.
3. Slice (e.g. "all Anthropic models"): `models --author <prefix> --limit 0`.
4. Fields not in the summary (`pricing.image`, `top_provider`, `per_request_limits`, tokenizer) are in `record` from the full `model <id>`. Raw `record.pricing` values (image, audio, web_search, cache) are USD per token or per unit, not per 1M: multiply by 1,000,000 only for those raw fields.

## Pricing notes

Summary prices are US$ per 1M tokens: do not multiply again. Routers (`openrouter/*`) are hidden unless `--aliases`. Models billed per request, not per token, show null prices with `"token_priced": false` and sort last.

## Output

- Single model: a compact summary block showing id, context, modalities, pricing per 1M, supported parameters.
- Multiple models: a markdown table with columns: ID, Context, In Modalities, Prompt $/1M, Completion $/1M.
- Cite the source as the OpenRouter public catalog (via orexplorer) and note the fetch date.

## Caching

The catalog changes frequently. The CLI caches for 600s; do not reuse results across sessions, re-run.
