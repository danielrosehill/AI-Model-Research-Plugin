---
name: or-find-vision-models
description: Use when the user wants to find vision-capable / multimodal image-input models on OpenRouter. Triggers on phrases like "OpenRouter vision models", "image-capable models on OR", "models that accept images on OpenRouter", "multimodal models on OpenRouter", "OCR-capable OR models", "find a vision model on OpenRouter for <task>".
---

# Find OpenRouter Vision Models

Filter the OpenRouter catalog to models that accept image input, then rank or summarize based on user criteria.

## When to use

The user wants to discover models that can process images on OpenRouter — for OCR, image understanding, visual QA, document parsing, screenshot analysis, etc.

## Workflow

1. Fetch the catalog:
   ```bash
   curl -s https://openrouter.ai/api/v1/models -H "Accept: application/json"
   ```
2. Filter `data[]` where `architecture.input_modalities` includes `"image"`.
3. Note the `pricing.image` field — many vision models charge a separate per-image fee on top of token costs. Surface this in output.
4. If the user expressed preferences (cheapest, largest context, specific use case), apply ranking:
   - **Cheapest** — sort by combined `pricing.prompt` + `pricing.image`
   - **Largest context** — sort by `context_length` descending
   - **Best for OCR/documents** — favor models with high context windows and known strong OCR (Gemini, Qwen-VL family); flag this from the model description
5. If criteria are vague, ask one short question: budget? volume of images? text length per request?
6. Return top 5–10 as a markdown table: ID, Context, Prompt $/1M, Completion $/1M, Image $ each, Other input modalities.

## Notes

- Some models accept images but charge per image (not per token). Always show both costs.
- A model listing `image` in input but not output is for image understanding only — not generation. Image generation models also list `image` in `output_modalities`. If the user wants generation, route to that subset.
- Flag if a model's vision capability is limited (low max image size, or supports only small batches) when this info is in the description.

## Output

Markdown table sorted by the user's criterion (default: cheapest combined cost). Include a count of total vision-capable models in the catalog.
