---
name: task-model-research
description: Find the right model for a job by starting from the Hugging Face Tasks taxonomy, not a keyword search. Map the need to its task(s) using the task directory shipped with the plugin (re-read live from huggingface.co/tasks only when it looks stale), then read that task's curated picks and the live models filed under it (trending, most downloaded, newest), vet the promising ones and return a shortlist with links. Use on "find me a video-to-video model", "what's good for speech enhancement", "is there a model that does X", "research models for X", "what's new in text-to-3D", or any model hunt or idea search.
---

# Research models from the task down

Searching the Hub by keyword finds whatever happens to use the word. Starting from the
**task** finds every model that does the job, including ones whose names give no hint. So the
order is always: task first, then models within the task.

## 1. Load your settings

Find the data folder (see `shared/settings.md`: `$HF_RESEARCH_HOME`, `$CLAUDE_USER_DATA/hf-research/`,
then `~/.claude-user-data/hf-research/`). Read `profile.env` and `task-model-research.md` there
if they exist. They win over the defaults below. Notes there may set hardware limits,
licence rules or where to file results.

## 2. Pin the need

From the request, get: input and output (video in, video out?), the actual job (upscale,
restyle, swap a character, interpolate frames), and any limits the user gave (runs locally,
VRAM, commercial licence, language). Ask only if the input/output pair is unclear: that is
what decides the task.

## 3. Find the task(s): start from the directory

Open `task-directory` (in this plugin). It lists every task with its page and model-listing URL, plus the task
groups, and needs no fetch. Pick the task or group that fits. Many needs touch two or three
tasks: "make this clip look like anime" is `video-to-video`, and also `image-to-video` and
`text-to-video` models that take a reference. Say which tasks you're covering and why.

```bash
S="${CLAUDE_PLUGIN_ROOT}/scripts/hf-tasks.py"
python3 "$S" find <the user's words>     # matching groups, then tasks, from the shipped map
python3 "$S" task <task-id>              # curated picks, libraries, metrics, live model count
```

If nothing fits, or the map looks out of date (see the directory's checklist), re-read it with
`python3 "$S" taxonomy --refresh` before concluding there is no task. For speech-to-text, use
`transcription-model-research`.

## 4. Pull the models within each task

```bash
python3 "$S" models <task-id> --sort trending  --limit 25
python3 "$S" models <task-id> --sort downloads --limit 25
python3 "$S" models <task-id> --sort created   --limit 15        # what's new
python3 "$S" models <task-id> --search <word> --library diffusers  # narrow inside the task
python3 "$S" models <id>,<id> --sort trending                     # several tasks as one pool
python3 "$S" models <group> --sort downloads                      # or a named group
```

Union these with the task's `curated_models` (the Hub team's picks, often the reference
implementations) and dedupe. `downloads_30d` is the Hub's rolling 30-day count. Trending
shows momentum this week. `base_model` shows which candidates are fine-tunes or LoRAs of the
same base, so group those under their base rather than listing each one.

To narrow inside a task by format, language, local app, inference provider, model type or
size (`library=gguf`, `language=he`, `apps=lmstudio`, `inference_provider=groq`,
`other=quantized`, `num_parameters=min:0,max:12B`), build the URL with `hub-search-urls`
(`scripts/hubexplorer.py models --task <id> ...`). It knows each parameter's prefix and which
ones combine with AND or OR. Give the user that URL along with the shortlist.

## 5. Vet the shortlist (5 to 8 models)

For each, read the model card (`https://huggingface.co/<id>`, or
`GET https://huggingface.co/api/models/<id>`):

- Does it actually do the job asked for, or only something next to it?
- Licence (commercial use?), gated or not.
- Size and hardware (parameter count, VRAM, quantised builds such as GGUF), and whether it
  runs with a standard library or needs its own repo.
- How to try it: a Space (the task's `curated_spaces`, or the model page's "Spaces using
  this model"), an inference provider, or local only.
- Its date. In fast-moving tasks, anything over a year old needs a reason to stay listed.

## 6. Report

A table, best fit first: model (linked), what it's best at, licence, size/hardware, how to
try it, downloads and trend. Then one line on each task you covered, plus anything the task
map surfaced that the user didn't ask about but should know (a newer task that fits better,
a curated dataset for evaluating). Name the date of the live read.

To keep the shortlist on the Hub, offer `bundle-collection`. If the goal is a fine-tune rather
than using a model as it is, go on with `candidate-base-model-research`.

## Data storage

Reads `profile.env` and `task-model-research.md`. Writes nothing unless the user files the
shortlist with `bundle-collection`.
