---
name: setup
description: Create or update your private settings for the Hugging Face skills of ai-model-research (ex hf-research; profile.env in its data folder): default owner for collections, whether to auto-refresh the task map, model-notebook names, and your saved answers for gated-model access forms. Detects what it can from your token. Use on "set up hf-research", "configure hf", "change my default HF owner", or when a skill offers setup because no profile exists.
---

# Set up your Hugging Face profile

## 1. Find the data folder

`python3 "${CLAUDE_PLUGIN_ROOT}/scripts/hf-hub.py" home` prints it and the rule that picked
it (order in `shared/settings.md`). If `profile.env` exists, read it: this run updates it, it
doesn't start over.

## 2. Detect, then ask only for the rest

- `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/hf-hub.py" orgs` gives your username, your orgs and
  where the token can write. Propose `HF_RESEARCH_DEFAULT_OWNER` (your username). If it fails, the token is missing: tell the
  user to set `HF_TOKEN` or run `hf auth login`, then rerun.
- Ask in one message, with the defaults from `shared/settings.md` shown: default visibility
  for new collections, and how often to re-read the task map. Leave the model-notebook keys at
  their defaults unless the user uses other names.
- Offer to save gated-access answers (`HF_RESEARCH_ACCESS_*`: name, country, affiliation, job
  title, a default intended use). Store a date of birth only if the user asks.
- If the user's secrets come from a wrapper or manager, add a comment saying how to run the
  scripts (for example `# run scripts as: <wrapper> python3 ...`). Never write a secret value.

## 3. Write

Create the folder if needed and write `profile.env` as `KEY=value` lines, values with spaces
in double quotes, a comment above any non-obvious key. Leave out keys still at their default.
Show the user the file path and contents. If the folder is inside a git repository, commit
only this plugin's folder.

## Data storage

Writes `profile.env` in the data folder. Per-skill notes (`<skill-name>.md`) are written by
the user, or by an agent when asked to remember a rule for one skill.
