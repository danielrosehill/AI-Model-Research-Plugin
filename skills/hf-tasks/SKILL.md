---
name: hf-tasks
description: The Hugging Face Tasks taxonomy (huggingface.co/tasks) as data. Find the task for a need, read one task in full (curated models, datasets, Spaces, metrics), list task groups, and with --refresh re-read it live and report which tasks Hugging Face added or changed. The shipped map is used by default, with no network. Use on "which HF task is X", "what tasks does Hugging Face have", "what changed in the HF tasks", "refresh the task list", and inside task-model-research.
---

# Hugging Face Tasks

[huggingface.co/tasks](https://huggingface.co/tasks) is the Hub's map of what models do:
each task (for example `video-to-video` or `automatic-speech-recognition`) is a
`pipeline_tag` that every model on the Hub is filed under. It is the best place to start any
search for a model, because the task decides which models are even comparable. The list
changes: new tasks appear (`image-text-to-video`, `any-to-any`, `visual-document-retrieval`)
and summaries and curated picks are revised. **Never list tasks from memory.** Use the shipped map
(`task-directory`), and re-read it live when it looks stale.

## 1. Load your settings

Find the data folder (see `shared/settings.md`: `$HF_RESEARCH_HOME`, `$CLAUDE_USER_DATA/hf-research/`,
then `~/.claude-user-data/hf-research/`). Read `profile.env` and `hf-tasks.md` there if they
exist. They win over the defaults below. With no profile, the defaults work as they are.

## 2. Read the taxonomy

```bash
S="${CLAUDE_PLUGIN_ROOT}/scripts/hf-tasks.py"
python3 "$S" taxonomy              # every task, from the shipped (or your newer saved) map
python3 "$S" taxonomy --refresh    # force a live read now, saved and diffed with the last one
python3 "$S" find video to video  # which task(s) match a plain-words need
python3 "$S" task video-to-video  # one task in full
```

The script merges two public endpoints, no token needed:

| Endpoint | Gives |
| --- | --- |
| `GET /api/models-tags-by-type` → `pipeline_tag` | Every task the Hub files models under (52 on 2026-11-13), with its label and category (`subType`: nlp, cv, audio, multimodal, rl, other) |
| `GET /api/tasks` | The tasks that have a task page (47 on 2026-11-13): summary, curated models, datasets and Spaces, metrics, libraries |

A task without a page (`has_page: false`, for example `robotics`, `time-series-forecasting`,
`voice-activity-detection`) is still a real filter with models behind it. It just has no
curated picks.

### Which map is used

- **By default, the shipped map with no network.** `data/tasks-snapshot.json` comes with the
  plugin and is refreshed with each release. `task-directory` is the same map rendered as a
  page of links: start there for quick lookups. `source: builtin`.
- **`--refresh`:** reads live, saves `tasks-<date>.json` in `${CLAUDE_PLUGIN_DATA}/tasks/` (else the data folder's `cache/tasks/`), and reports
  `added`, `removed` and `changed` since the previous map. Later reads use it while it is
  newer than the shipped one. `source: live`, then `cache`.
- **Optional auto-refresh:** set `HF_RESEARCH_TASKS_MAX_AGE_DAYS` in the profile.
- **Live read fails:** the saved or shipped map is used, with the error shown.

Refresh when the user says the map is stale, when a model's `pipeline_tag` isn't in the map,
when no task fits a need, or when the map is more than about three months old. Report any
`added` tasks: a new task is often the answer to "is there a model for X yet".

### Task groups

Some needs span several tasks. Transcription, for example, lives under both
`automatic-speech-recognition` and `audio-text-to-text`. `python3 "$S" groups` lists the
named groups (built-in `data/task-groups.json`, plus your own `task-groups.json` in the data
folder, where yours win by name). `find` returns matching groups first. Anywhere a task id is
accepted, a group name works too.

## 3. Answer

- **"Which task is X?"** Run `find` with the user's words. Give the best one or two task ids,
  their labels and one-line summaries, and the page link `https://huggingface.co/tasks/<id>`.
  If the need straddles tasks (video editing from a prompt: `video-to-video`, and
  `image-text-to-video` for a still plus a prompt), say so and name each.
- **"What tasks are there?"** Group by category from the live output, with the count and the
  date fetched.
- **Going on to models?** Hand over to `task-model-research` with the task id(s).

## Data storage

Reads `profile.env`, `hf-tasks.md` and `task-groups.json`. A live read writes `tasks-<date>.json` to `${CLAUDE_PLUGIN_DATA}/tasks/`, or the data folder's `cache/tasks/` outside Claude Code (a rebuildable cache, not user content). Nothing else is written to the data
folder. One file per day, and earlier ones are kept for the diff.
