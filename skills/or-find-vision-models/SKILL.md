---
name: or-find-vision-models
description: Use when the user wants to find vision-capable / multimodal image-input models on OpenRouter. Supports price, context, provider and batch filtering. Triggers on phrases like "OpenRouter vision models", "image-capable models on OR", "models that accept images on OpenRouter", "multimodal models on OpenRouter", "OCR-capable OR models", "find a vision model on OpenRouter for <task>".
---

# Find OpenRouter Vision Models

Filter the OpenRouter catalog to models that accept image input, then rank or summarize based on user criteria.

## When to use

The user wants to discover models that can process images on OpenRouter — for OCR, image understanding, visual QA, document parsing, screenshot analysis, etc.

## Workflow

CLI: `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/orexplorer.py` (JSON default, `--table` for humans, prices US$ per 1M tokens).

1. If criteria are vague, ask one short question: budget? volume of images? text length per request?
2. Query:
   ```bash
   python3 ${CLAUDE_PLUGIN_ROOT}/scripts/orexplorer.py models --cap vision --sort price --limit 10 --table
   ```
   Add `--min-context`, `--max-in/--max-out`, `--author`, `--cap tools`, `--cap structured`, `--batch` as needed. Total matches are in `count` / the table header.
3. `--cap vision` is any image input, including generation models. For understanding/OCR add `--cap text-out` and drop rows whose `output` also lists image/audio. For generation use `--cap image-out`.
4. `image_in_per_m` in each row is the raw per-image/per-unit image price scaled by 1M (null when the model has none). For exact billing read `record.pricing.image` from `model <id>`.
5. For OCR/documents favour large context and families known for OCR (Gemini, Qwen-VL); flag this as your judgement from the description.

## Notes

- Some models charge per image rather than per token: show both costs.
- Routers (`openrouter/*`) are hidden unless `--aliases`. Models billed per request, not per token, show null prices with `"token_priced": false` and sort last.
- Flag limited vision (small max image size, few images per request) when the description says so.

## Output

Markdown table sorted by the user's criterion (default: cheapest input+output, with image fee noted). Include a count of total vision-capable models in the catalog.
