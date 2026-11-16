---
name: setup-collections-workspace
description: Set up a private Git repository as the user's Hugging Face collections workspace - inbox for links, plans for collections being built, periodic snapshots of every collection for search and deduplication, a log of tidy-ups - and register it with the plugin so the collection skills use it. Use on "set up a collections workspace", "make me a repo for my collections", "where should my collections scratchpad live", or when a collections skill finds HF_RESEARCH_COLLECTIONS_WORKSPACE unset and the user wants one.
---

# Set up a collections workspace

The collection skills work without a workspace (straight against the Hub). A workspace adds memory: links staged
for later, plans that remember what was dropped, snapshots so "do I already have a collection for this?" costs no
API calls, and a log of merges and deletions.

## 1. Load your settings

Find the data folder (see `shared/settings.md`) and read `profile.env`. If `HF_RESEARCH_COLLECTIONS_WORKSPACE` is already
set and the folder exists, say so and stop (offer a snapshot refresh instead).

## 2. Decide, with defaults (ask only what you can't infer)

- **Owners** to track: `HF_RESEARCH_DEFAULT_OWNER` (else the token's user), plus orgs the user names (`hf-hub.py orgs` lists
  them). Default: the user only.
- **Repo name**: `HF-Collections` unless the user's naming conventions say otherwise. **Private**: it holds private collection
  names and plans.
- **Where**: the user's usual clone folder for repos if their notes say; else `~/repos/HF-Collections`.
- **Host**: GitHub via `gh repo create <name> --private` if `gh` is authenticated; otherwise a local repo, and say so.

## 3. Create

```bash
T="${CLAUDE_PLUGIN_ROOT}/templates/collections-workspace"
mkdir -p "$WS" && cp -r "$T"/. "$WS"/
# fill placeholders: {{TITLE}} repo name, {{OWNERS}} comma list, {{OWNERS_LINES}} one per line, {{DATE}} today
cd "$WS" && git init -b main && git add -A && git commit -m "Collections workspace"
gh repo create <name> --private --source . --push     # if using GitHub
HF_HUB_SCRIPT="${CLAUDE_PLUGIN_ROOT}/scripts/hf-hub.py" bin/snapshot   # first snapshot (needs HF_TOKEN)
git add -A && git commit -m "First snapshot" && git push
```

Many collections take a while (one API call each, ~1 minute per 200); run it in the background for large accounts.

## 4. Register

Append to `profile.env` (create it via `setup` if missing):

```
HF_RESEARCH_COLLECTIONS_WORKSPACE=<absolute path>
```

The inbox (`<workspace>/inbox.md`) and index (`<workspace>/snapshots/INDEX.md`) follow from it; set
`HF_RESEARCH_COLLECTIONS_INBOX` or `_INDEX` only to point elsewhere.

## 5. Report

Path, remote URL, owners tracked, collection count from the first snapshot, and the four skills that now use it
(`gather-collection-links`, `expand-collection`, `bundle-collection`, `tidy-collections`). Suggest refreshing the
snapshot weekly (any scheduler; `bin/snapshot` is idempotent).

## Data storage

Writes the workspace repo and one line in `profile.env`.
