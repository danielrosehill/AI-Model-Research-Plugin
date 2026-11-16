---
name: tidy-collections
description: Tidy up a Hugging Face account's collections - find single-item collections, pairs that overlap heavily, duplicate titles, collections with no description and items with no note - then propose merges, renames, descriptions and deletions, apply the ones the user approves, and log them. Use on "tidy up my collections", "clean up the collections", "which collections overlap", "dedupe my collections", "merge X into Y", "my collections are a mess".
---

# Tidy collections

## 1. Load your settings

Find the data folder (see `shared/settings.md`). Read `profile.env` and `tidy-collections.md` there if they exist; they win.
With `HF_RESEARCH_COLLECTIONS_WORKSPACE` set, work from its snapshot and write the log there.

```bash
S="${CLAUDE_PLUGIN_ROOT}/scripts/hf-hub.py"
"$WS/bin/snapshot"                                  # refresh first (workspace), else:
python3 "$S" collections <owner> > /tmp/cols.json   # one API call per collection
python3 "$S" audit "$WS/snapshots/<owner>.json"     # or /tmp/cols.json, or <owner> to fetch live
python3 "$S" collection <slug>
python3 "$S" collection-add|collection-remove|collection-item|collection-update|collection-delete ...
```

`audit` returns `empty`, `singletons`, `no_description`, `duplicate_titles` (case and punctuation folded),
`overlapping` (pairs where the shared items are ≥ 50% of the smaller collection, both with ≥ 2 items) and the count of
items with no note.

## 2. Read before proposing

Overlap is not always a fault. Leave alone, and say why:
- **superset collections** by design (`X - All` holding `X - Mine` and `X - Third Party`; an org's "all repos" front door);
- **facets**: the same item in a task collection and a device or language collection (On-Device ASR and Android STT);
- collections the user's notes (`tidy-collections.md`) list as intentional, or that a website mirrors (check profile notes).

Real problems: two collections for one purpose (`Voice Enhancement` vs `Audio restoration`), near-duplicate titles,
singletons that belong in an existing topical collection, empty collections, public collections with no description.

## 3. Propose, in one batch

A table grouped by action: **merge** (from → into, items moving, items already there), **move singleton** (into
which), **rename**, **describe** (proposed ≤ 150 chars), **delete** (empty, or emptied by a merge). Cap a pass at
about 20 actions, starting with the largest overlaps; say how many remain. Ask once for approval of the batch;
the user can strike lines.

## 4. Apply

- Merge: `collection-add` every item of the source into the target **with its note**, verify with `collection`,
  then `collection-delete` the source. Deletion is irreversible: only after the approval and the verification.
  Before deleting a public collection, search the user's sites and repos for its slug (live pages may link to it).
- Rename/describe: `collection-update` (a rename changes the slug; the script handles it; record the new slug).
- Notes: filling 800 missing notes is not a tidy-up; offer it as a separate pass per collection.

## 5. Record

Workspace: `log/YYYY-MM-DD-tidy.md` with each action, old and new slugs, item counts; re-run `bin/snapshot`; commit
and push. Reply with counts per action and what remains for the next pass.

## Data storage

Reads `profile.env` and `tidy-collections.md`; writes the workspace log and snapshot. Collection changes go to the Hub.
