---
name: transcription-model-research
description: Find speech-to-text models for transcription or dictation on Hugging Face by searching every task where they live, not just ASR. Dedicated ASR models are under automatic-speech-recognition, audio-language models that transcribe when prompted are under audio-text-to-text, and omni models under any-to-any. Filter by language, size, streaming, timestamps and on-device formats, then shortlist. Use on "find a transcription model", "best dictation model for X", "speech to text for Hebrew/Spanish/…", "Whisper alternatives", "on-device ASR", "model for voice typing", "subtitles model".
---

# Transcription and dictation model research

A search under `automatic-speech-recognition` alone misses half the field. Since 2025 many of
the strongest transcribers are audio-language models filed under `audio-text-to-text`, and
some omni models under `any-to-any` take audio too. This skill searches all of them as one
pool. It is `task-model-research` specialised with the `transcription` task group.

## 1. Load your settings

Find the data folder (see `shared/settings.md`: `$HF_RESEARCH_HOME`,
`$CLAUDE_USER_DATA/hf-research/`, then `~/.claude-user-data/hf-research/`). Read
`profile.env` and `transcription-model-research.md` there if they exist. They win over the
defaults below. The notes often hold standing needs: languages, target devices, runtimes
already in use, models already tried.

## 2. Pin the need

Ask only for what the request leaves open:

- **Language(s)**, and whether speakers mix languages within a sentence (code-switching).
- **Mode**: batch files, live streaming dictation, or both.
- **Where it runs**: GPU server, desktop CPU, phone, browser, or a hosted API. This decides
  size and format.
- **Output extras**: word timestamps, punctuation and casing, diarisation, translation.

## 3. Confirm the tasks are current

```bash
S="${CLAUDE_PLUGIN_ROOT}/scripts/hf-tasks.py"
python3 "$S" group transcription          # the tasks this search spans, with notes
python3 "$S" find speech to text          # anything new in the taxonomy that also fits
```

If `find` turns up a task that isn't in the group (Hugging Face adds tasks over time), include
it and tell the user. To keep it, add it to `task-groups.json` in the data folder.

## 4. Pull candidates across all the tasks

```bash
python3 "$S" models transcription --sort trending  --limit 30
python3 "$S" models transcription --sort downloads --limit 30
python3 "$S" models transcription --sort created   --limit 20
python3 "$S" models transcription --search <language or family> --limit 30   # e.g. hebrew, parakeet, whisper
```

Each model lists the `tasks` it was found under, and `languages` from its tags. Language tags are
often missing: a model with no tags may still support the language, so check the card before
dropping it. Group fine-tunes under their `base_model`. A pile of Whisper fine-tunes is one
family, so report the best two or three and the count.

For local or hosted filters (`library=gguf`, `library=onnx`, `apps=lmstudio`,
`inference_provider=groq,fal-ai`, `language=he`), build the URL per task with `hub-search-urls`
(`scripts/hubexplorer.py models --task automatic-speech-recognition --language he --library onnx`).

Also run `python3 "$S" task automatic-speech-recognition` to see the curated models, datasets
and metrics (WER, CER).

## 5. Vet (6 to 10 models)

From each card, and from the files list for formats:

- Languages actually evaluated, and reported WER or CER on which benchmark. Don't compare
  numbers across benchmarks.
- Size, and the runtime it needs: `transformers`, NeMo, CTranslate2/faster-whisper,
  whisper.cpp/GGUF, ONNX/sherpa-onnx, MLX, Core ML. Note the on-device builds that exist.
- Streaming support, timestamps, punctuation, and the longest audio per call (audio-language
  models often cap a request at around 30 s to a few minutes).
- Licence (commercial use?), and gated or not. For a gated model, offer `gated-access`.
- For audio-language models: whether transcription is verbatim or paraphrased, and whether a
  prompt or chat template is needed.
- Date, and whether it is maintained.

## 6. Report

A table, best fit first: model (linked), type (dedicated ASR or audio-language), languages,
size and runtime, streaming and timestamps, licence, reported WER (benchmark named), downloads
and trend. Then a line per task searched, and a recommendation for the user's mode and device.
Name the date of the read.

Offer to file the shortlist as a collection (`bundle-collection`) and, if they want to test on
their own audio, list the two or three to try first.

## Data storage

Reads `profile.env`, `transcription-model-research.md` and `task-groups.json` (if present).
Writes nothing unless the user files the shortlist.
