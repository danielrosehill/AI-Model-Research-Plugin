---
name: bundle-collection
description: Bundle a list of Hugging Face things the user gives (URLs or ids of models, datasets, Spaces, papers; their own or anyone's) into a collection, new or existing, with a title, description and per-item notes that say what they were collected for. Use on "make a collection of these", "bundle these into a collection", "add these to my X collection", "update the collection with these", or a pasted list of HF links with a purpose.
---

# Bundle a list into a collection

## 1. Load your settings

Find the data folder (see `shared/settings.md`: `$HF_RESEARCH_HOME`, `$CLAUDE_USER_DATA/hf-research/`, then `~/.claude-user-data/hf-research/`). Read `profile.env` and `bundle-collection.md` there if they exist. They win over the defaults below, and comments in `profile.env` are instructions. With no profile, use the defaults below and offer `setup` at the end.

Input: a list of Hub references and, in the user's words, what they're for ("TTS models I'm
weighing", "Hebrew ASR datasets to train on"). Output: one collection that holds exactly those
items, described by that purpose. Distinct from `collections`, which files the user's own repos by
what they are; here the purpose is the organising idea.

```bash
S="${CLAUDE_PLUGIN_ROOT}/scripts/hf-hub.py"
python3 "$S" resolve <ref> <ref> ...     # each: type, canonical id, exists, private, card summary/tags
python3 "$S" collections <owner>         # existing collections, to reuse one
python3 "$S" collection-new <owner> "<Title>" public "<description>"
python3 "$S" collection-add <slug> <model|dataset|space|paper> <id> "<note>"
python3 "$S" collection-update <slug> --description "<description>"   # updating an existing one
python3 "$S" collection-item <slug> <type> <id> --position N          # order
python3 "$S" collection <slug>           # read back
```

## Steps

1. **Resolve every reference** in one `resolve` call. It takes `huggingface.co/...` URLs (any
   sub-path: `/tree/main`, `/blob/...`), bare `owner/name` (tries model, then dataset, then
   Space), `datasets/…`, `spaces/…`, arXiv URLs/ids and `huggingface.co/papers/<id>`. List any
   `exists: false` back to the user and carry on with the rest; don't guess a substitute.
2. **Owner.** `HF_RESEARCH_DEFAULT_OWNER` (else the token's username) unless the user names an org, or
   every item is an org's own work and the purpose is that org's (then use the org). Third-party
   items are fine in the user's collections.
3. **New or existing.** If the user names a collection, or `collections <owner>` has one whose title
   matches the purpose closely, update that one (add the missing items, refresh the description
   if the purpose has widened). Otherwise create. Don't ask which; say which way you went.
4. **Title** ≤ 60 chars, Title Case, names the purpose not the format
   (`Hebrew ASR Training Candidates`, not `Datasets 3`). **Description** ≤ 150 chars (hard API
   limits, verified 2026-10-31: longer answers 400): the purpose in the user's terms, one sentence,
   no filler. Public by default (private items inside stay hidden); private only if the user says so.
5. **Notes**, one per item, ≤ 500 chars: why this item is in the bundle, using what the user said
   about it plus what `resolve` shows (task, size, language, licence if relevant). One line
   is usually enough. If no per-item reason was given, write the item's role in the purpose;
   don't pad.
6. **Order** as listed unless the purpose implies a ranking (shortlist, best first).
   Positions don't re-index, so set every item's `--position` if you reorder.
7. **Read back** with `collection <slug>` and verify the item count and types match the input.
   Reply with the collection URL, items added / already present (409) / not found, and the
   description used.

## Updating

"Add these to X" / "update X": same flow against the existing slug. Don't remove items the user
didn't mention unless they say the list replaces the collection ("make it exactly these"); then
`collection-remove` the rest. Notes on items already there are left alone unless a new reason is given.

## Data storage

Reads `profile.env` and `bundle-collection.md` from the data folder. Writes nothing there; changes go to the Hub.
