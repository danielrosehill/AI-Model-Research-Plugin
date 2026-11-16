# Your settings (the private overlay)

These are the Hugging Face skills (from the former hf-research plugin, merged into ai-model-research on
2026-11-14). The data folder keeps the name `hf-research`, so existing settings carry over. This plugin is public and generic. Everything that is specific to you, such as your
account, your organisations, naming rules, collection names and where exports go, lives
in a **data folder outside the plugin**. The skills read that folder each time they run,
so plugin updates never touch it.

## Find the data folder

Stop at the first match:

1. `$HF_RESEARCH_HOME`
2. `$CLAUDE_USER_DATA/hf-research/`
3. `~/.claude-user-data/hf-research/`, if `~/.claude-user-data` exists
4. `${XDG_DATA_HOME:-$HOME/.local/share}/claude-plugins/hf-research/`, if that root exists
5. `~/.claude-user-data/hf-research/` (default; `setup` creates it)

`python3 scripts/hf-hub.py home` prints the resolved folder and the rule that picked it.

## What it holds

```
<data folder>/
  profile.env        KEY=value. Comments are instructions for this user.
  <skill-name>.md    Private notes for one skill. They win over that skill's defaults.
  task-groups.json   your own task groups (needs that span several tasks)
  cache/tasks/       task-map snapshots, only outside Claude Code (inside it: ${CLAUDE_PLUGIN_DATA}/tasks/)
```

## The load step (every skill starts with it)

Read `profile.env` and `<skill-name>.md` from the data folder if they exist. They win over
the skill's defaults. Comments in `profile.env` are instructions too: follow them. With no
profile, use the defaults written in the skill and offer `setup` at the end.

## Keys in `profile.env`

All optional. A key that is unset falls back to the default shown.

| Key | Used by | Default |
| --- | --- | --- |
| `HF_RESEARCH_TASKS_MAX_AGE_DAYS` | hf-tasks and every research skill | unset: use the shipped map, re-read live only on request. Set a number of days to auto-refresh |
| `HF_RESEARCH_DEFAULT_OWNER` | bundle-collection, model-notebook, candidate-* (where collections go) | the token's own username |
| `HF_RESEARCH_DEFAULT_VISIBILITY` | new collections | `private` |
| `HF_RESEARCH_FAVOURITES_COLLECTION` | model-notebook | `Favorite Models` |
| `HF_RESEARCH_COLLECTIONS_INBOX` | gather-collection-links | `<data folder>/collections-inbox.md` |
| `HF_RESEARCH_COLLECTIONS_INDEX` | gather-collection-links | unset: call `collections <owner>` |
| `HF_RESEARCH_MODEL_NOTES_DATASET` | model-notebook | `<default owner>/Model-Notes` |
| `HF_RESEARCH_MODEL_NOTES_SPACE` | model-notebook | unset (no Space) |
| `HF_RESEARCH_ACCESS_FIRST_NAME`, `_LAST_NAME`, `_FULL_NAME`, `_COUNTRY`, `_AFFILIATION`, `_JOB_TITLE`, `_EMAIL`, `_WEBSITE`, `_INTENDED_USE`, `_DATE_OF_BIRTH` | gated-access | unset: asked for, then offered for saving |

Other files in the data folder:

| File | Holds |
| --- | --- |
| `task-groups.json` | your own task groups, same shape as the plugin's `data/task-groups.json`. Yours win by name |
| `cache/tasks/tasks-<date>.json` | task-map snapshots from `hf-tasks.py --refresh`, when `${CLAUDE_PLUGIN_DATA}` is not set |

## Secrets

The plugin never stores a secret and never says where yours live. It reads:

- `HF_TOKEN`, else `~/.cache/huggingface/token` (`hf auth login`)

If your secrets come from a wrapper or manager, say so in a comment in `profile.env`
(for example `# run scripts as: <wrapper> python3 ...`) and the skills will follow it.
