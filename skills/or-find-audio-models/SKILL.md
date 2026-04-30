---
name: or-find-audio-models
description: Use when the user wants to find OpenRouter models that accept audio input. Triggers on phrases like "OpenRouter audio models", "models that accept audio on OR", "speech input models on OpenRouter", "OpenRouter models for transcription", "audio-capable LLMs on OpenRouter".
---

# Find OpenRouter Audio-Input Models

Filter the OpenRouter catalog to models that accept audio input, then rank or summarize based on user criteria.

## When to use

The user wants to discover models on OpenRouter that can process spoken/audio input — for transcription, voice understanding, audio QA, multimodal voice agents.

## Workflow

1. Fetch the catalog:
   ```bash
   curl -s https://openrouter.ai/api/v1/models -H "Accept: application/json"
   ```
2. Filter `data[]` where `architecture.input_modalities` includes `"audio"`.
3. The audio-input model set on OpenRouter is small (often a handful of Gemini and GPT-4o variants). If the result set is empty, tell the user clearly and suggest alternatives:
   - Use a dedicated STT API (Whisper, Deepgram, Gemini transcription) and pass text to an LLM
   - Use a multimodal model that accepts text + image (a screenshot of a waveform or transcript) — usually wrong fit, mention only if relevant
4. For each match, surface: supported audio formats (if listed in description), pricing (often charged per second or per token after transcription), and context length.
5. If the user has a preference (cheapest, longest audio supported), rank accordingly.

## Notes

- Audio pricing on OR varies — some models bill per audio token, others per audio second. Read the model description carefully and quote the relevant figure.
- Audio capability is a fast-moving area; the catalog is the source of truth — do not rely on memory for which models currently support audio.

## Output

Markdown table or short list (since the set is small): ID, Context, Audio handling notes, Pricing notes, Caveats. If the set is empty, recommend a fallback workflow.
