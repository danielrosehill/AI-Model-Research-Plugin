---
name: or-find-audio-models
description: Use when the user wants to find OpenRouter models that accept audio input. Supports price, context, provider and batch filtering. Triggers on phrases like "OpenRouter audio models", "models that accept audio on OR", "speech input models on OpenRouter", "OpenRouter models for transcription", "audio-capable LLMs on OpenRouter".
---

# Find OpenRouter Audio-Input Models

Filter the OpenRouter catalog to models that accept audio input, then rank or summarize based on user criteria.

## When to use

The user wants to discover models on OpenRouter that can process spoken/audio input — for transcription, voice understanding, audio QA, multimodal voice agents.

## Workflow

CLI: `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/orexplorer.py` (JSON default, `--table` for humans, prices US$ per 1M tokens).

1. List audio-input models:
   ```bash
   python3 ${CLAUDE_PLUGIN_ROOT}/scripts/orexplorer.py models --cap audio-in --sort price --limit 0 --table
   ```
   Add `--max-in/--max-out`, `--min-context`, `--author` or `--cap tools` for user criteria. Routers (`openrouter/*`) are hidden unless `--aliases`. Models billed per request, not per token, show null prices with `"token_priced": false` and sort last.
2. If the user wants audio output too, use `--cap audio-out`. If the result set is empty, suggest a dedicated STT API (Whisper, Deepgram, Gemini transcription) feeding text to an LLM.
3. For each shortlisted model run `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/orexplorer.py model <id>` and read the description and `record.pricing.audio` for audio billing (per audio token vs per second) and supported formats.
4. Rank by user preference (cheapest, longest context).

## Notes

- Audio pricing on OR varies — some models bill per audio token, others per audio second. Read the model description carefully and quote the relevant figure. Raw `record.pricing` values (image, audio, web_search, cache) are USD per token or per unit, not per 1M: multiply by 1,000,000 only for those raw fields.
- Audio capability is a fast-moving area; the CLI/catalog is the source of truth — do not rely on memory for which models currently support audio.

## Output

Markdown table (short list if the filters narrow it): ID, Context, Audio handling notes, Pricing notes, Caveats. If the set is empty, recommend a fallback workflow.
