# {{TITLE}}

Private workspace for curating the Hugging Face collections of `{{OWNERS}}`.
Created {{DATE}} by `ai-model-research:setup-collections-workspace`.

The Hub is the source of truth for what is *in* a collection. This repo holds what is on its way in,
plans for new collections, periodic snapshots (for search and deduplication without API calls) and a log
of tidy-ups.

| Path | Purpose |
|---|---|
| `inbox.md` | Links gathered but not yet filed, grouped by target collection (`gather-collection-links`). |
| `plans/` | One file per collection being built up with discovery (`expand-collection`): seeds, searches run, candidates kept and dropped. |
| `bin/snapshot` | `bin/snapshot [owner ...]`: writes `snapshots/<owner>.json` and `snapshots/INDEX.md` from the live Hub. Needs `HF_TOKEN`. |
| `snapshots/` | Generated. `INDEX.md` lists every collection; the JSON feeds `hf-hub.py audit`. |
| `log/` | One dated file per tidy-up pass (`tidy-collections`): what was merged, renamed or deleted, with slugs. |

## Skills (plugin `ai-model-research`)

| Skill | Use |
|---|---|
| `gather-collection-links` | Pull Hub/arXiv links out of text, pages or tabs; stage or file them. |
| `expand-collection` | "Here's what I found, add anything I missed": seeds + discovery into one collection. |
| `bundle-collection` | File a given list into a new or existing collection with notes. |
| `tidy-collections` | Audit for singletons, overlaps, duplicates, missing descriptions and notes; propose and apply fixes. |
