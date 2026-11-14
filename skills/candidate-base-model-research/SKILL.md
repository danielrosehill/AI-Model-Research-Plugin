---
name: candidate-base-model-research
description: Find and shortlist base models on the Hugging Face Hub for a small fine-tune: search by task, size, language and licence, read each candidate's real parameter count, context length, architecture and export formats, check for existing fine-tunes of the task, and file the shortlist in a public or private candidates collection with a verdict note on each. Use when the user says "find a base model", "which model should I fine-tune", "base model candidates", "is there a small model for", "add it to the base candidates".
---

# Candidate base model research

## 1. Load your settings

Find the data folder (see `shared/settings.md`: `$HF_RESEARCH_HOME`, `$CLAUDE_USER_DATA/hf-research/`, then `~/.claude-user-data/hf-research/`). Read `profile.env` and `candidate-base-model-research.md` there if they exist. They win over the defaults below, and comments in `profile.env` are instructions. With no profile, use the defaults below and offer `setup` at the end.

Profile keys used: `HF_RESEARCH_DEFAULT_OWNER` (owner of the candidates collection, default the token's
username), `HF_RESEARCH_DEFAULT_VISIBILITY` (default `private`), `HF_RESEARCH_NAME_STYLE`.

The Hub-side counterpart to `candidate-dataset-research`: search, check and file. A full
planning write-up (requirements, tokenizer tests, decision record) belongs in a model-planning
workflow if you have one. Use this skill for a quick live shortlist.

```bash
S="${CLAUDE_PLUGIN_ROOT}/scripts/hf-hub.py"
python3 "$S" search model [words] --task <pipeline_tag> [--filter en] [--filter license:apache-2.0] [--max-params 400M] [--sort downloads|trendingScore] [--limit 20]
python3 "$S" search model --filter base_model:<base-id> [words]   # existing fine-tunes of a base
python3 "$S" model-info <owner/name>                              # params, licence, languages, context, architecture, formats
python3 "$S" collection-new <owner> "<Task> Base Model Candidates" <public|private> "<one-line task>"
python3 "$S" collection-add <slug> model <owner/name> "<verdict note>"
```

## Steps

1. **Hard filters** from the task and where it will run: maximum params (browser/CPU means
   under ~400M), language, licence for the intended release, and architecture (an encoder
   such as ModernBERT/DeBERTa for classification and tagging, a small seq2seq or decoder for
   rewriting tasks like paragraph insertion).
2. **Search.** By `--task` first, words second. `--max-params` filters on `safetensors.total`
   in the script, because the Hub's `num_parameters` filter does not bound size. Repos without
   safetensors (GGUF and others) are dropped by `--max-params`, so search again without it
   if a family seems missing.
3. **Look for the task already solved.** For each obvious base, run
   `search model --filter base_model:<id> <task words>`. A fine-tune that already exists may
   be a better starting point than the base, or may make training unnecessary.
4. **Check each candidate** with `model-info`: params, licence (flag gated, `other`, `nc`),
   languages (a model tagged with 100+ languages is not evidence that the target language
   works), context against the input length, and formats (ONNX/transformers.js/GGUF if the
   deployment needs them). Read the card's eval section for results on similar tasks.
5. **Shortlist** 2 to 3 with a recommendation and a runner-up to evaluate as well. The newest
   or most downloaded is not automatically the best on a narrow task.
6. **File.** Same rules as `candidate-dataset-research` Step 4: ask public or private (default
   from the profile, else private), reuse a fitting existing collection (`collections <owner>`),
   otherwise `<Task> Base Model Candidates`. Note example:
   `pick: 150M, 8k ctx, apache-2.0, ONNX; encoder, fine for token-level break tagging`.
7. **Report** a table (model, params, ctx, licence, formats, verdict), the collection URL and
   the existing fine-tunes found.

## Language tag trap

On **models** a language is a bare tag (`--filter en`, `--filter he`). `language:en` matches
only the few repos that carry that literal string as a tag (on 2026-10-25 these were Pashto GGUFs),
which looks like a result but isn't. The API ignores `?language=` (checked again on 2026-11-14: 3 of
50 results were tagged `he`), but the website's `models?language=he` does filter. hubexplorer
sends the right form to each. On **datasets** it is
the other way round (`language:en`).

## Data storage

Candidate collections live on the Hub under the owner you choose; nothing is written locally except what you ask for. Private notes for this skill go in `<data folder>/candidate-base-model-research.md`; shared settings in `<data folder>/profile.env`. Nothing personal is stored in the plugin.
