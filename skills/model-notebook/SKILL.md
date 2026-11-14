---
name: model-notebook
description: Record a Hugging Face model the user rates highly, with their scratch notes on how they used it. Adds it to a "Favorite Models" collection, appends a dated note to a notes dataset on the Hub, and optionally shows it in a notebook Space. Use on "add X to my favorite models", "note on model X", "I've been using X for…", "log this model", "what have I noted about X", "show my model notes".
---

# Model Notebook

## 1. Load your settings

Find the data folder (see `shared/settings.md`: `$HF_RESEARCH_HOME`, `$CLAUDE_USER_DATA/hf-research/`, then `~/.claude-user-data/hf-research/`). Read `profile.env` and `model-notebook.md` there if they exist. They win over the defaults below, and comments in `profile.env` are instructions. With no profile, use the defaults below and offer `setup` at the end.

Three linked pieces on the user's account (all names from `profile.env`, defaults shown):

| Piece | Key | Default | Role |
|---|---|---|---|
| Collection | `HF_RESEARCH_FAVOURITES_COLLECTION` | `Favorite Models` (public, under the default owner; created if missing) | The shortlist |
| Dataset | `HF_RESEARCH_MODEL_NOTES_DATASET` | `<default owner>/Model-Notes` (file `notes.jsonl`) | One row per note |
| Space | `HF_RESEARCH_MODEL_NOTES_SPACE` | unset (no Space) | Optional static viewer that reads `notes.jsonl` live in the browser; no redeploy |

The default owner is `HF_RESEARCH_DEFAULT_OWNER`, else the token's username. If the notes dataset does not exist,
create it first (`hf-publisher-tools:create-dataset`, or `hf repo create`) and tell the user it is public by design.

## Add a note

1. Resolve the model to its exact Hub id (`owner/name`). If the user gave a loose name, search
   (`hf-hub.py search model <q>` or `model-info`) and pick the obvious match; ask only if two are
   plausible.
2. From their scratch notes, write:
   - `--use-case`: what they used it for, 2–6 words (`Hebrew transcription`, `Local embeddings for RAG`).
     If one dump covers two distinct uses, make two notes.
   - `--summary`: one plain sentence, their verdict in their terms. Don't invent praise or numbers.
   - `--notes`: their scratch notes **as given** (treat voice-typed text as written; fix nothing beyond
     obvious punctuation). Long text: write it to a file and pass `--notes-file`.
   - `--tags`: a few lowercase tags if they help (`hebrew`, `gguf`, `on-device`).
3. Run:

```bash
S="${CLAUDE_PLUGIN_ROOT}/scripts/model-notes.py"
uv run --no-project --with huggingface_hub python3 "$S" add <owner/model> \
  --use-case "..." --summary "..." --notes "..." [--tags a,b] [--date YYYY-MM-DD]
```

The script needs `HF_TOKEN` or `hf auth login`, reads the `HF_RESEARCH_*` keys from the environment or
`profile.env`, adds the model to the favourites collection if missing (collection note = summary),
copies pipeline tag, library, licence and parameter count from the Hub, and appends the row.
`added` = date of the model's first note and is kept on later notes; `noted` = today or `--date`.
A second note on the same model adds a row, it doesn't overwrite.

4. Reply with one line: model, use case, whether it was newly added to the collection, and the
   Space link if `HF_RESEARCH_MODEL_NOTES_SPACE` is set.

## Other commands

- `list [owner/model]`: rows as JSON lines (answer "what did I say about X" from this).
- `remove-last <owner/model> --yes`: drop that model's newest row, for a bad entry the user asks to undo.
- Removing a model from the collection: `hf-hub.py collection-remove <slug> model <id>`; its notes stay
  unless the user asks to drop them too.

## Notes

- A public notes dataset is public: if the notes include anything that reads as private (client names,
  credentials, personal details), ask before writing.
- `notes.jsonl` is rewritten whole on each add (download, append, upload). Don't run two adds at once.

## Data storage

Reads `profile.env` and `model-notebook.md` from the data folder. Writes nothing there; notes live in the Hub dataset.
