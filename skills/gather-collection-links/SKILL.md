---
name: gather-collection-links
description: Gather Hugging Face links (models, datasets, Spaces, papers) from anywhere into collections - pasted text, a web page, an awesome-list or blog post, a model card's related links, open browser tabs, a Hub search, or things mentioned during a conversation - deduplicate them, check what is already collected, and either file them now or stage them in an inbox to file later. Use on "collect these", "grab the HF links from this page", "add everything in this list to a collection", "save this model for my X collection", "stage these", "what's in my collections inbox", "file the inbox".
---

# Gather links into collections

## 1. Load your settings

Find the data folder (see `shared/settings.md`). Read `profile.env` and `gather-collection-links.md` there if
they exist; they win over the defaults below. Keys used here:

- `HF_RESEARCH_DEFAULT_OWNER`: whose collections (default: the token's user).
- `HF_RESEARCH_COLLECTIONS_INBOX`: path to the staging file (default: `<data folder>/collections-inbox.md`).
  If the inbox lives in a git repo, commit and push after each change to it.
- `HF_RESEARCH_COLLECTIONS_INDEX`: optional path to a Markdown index of the owner's collections (title, slug),
  read instead of calling `collections <owner>`, which costs one API call per collection.

```bash
S="${CLAUDE_PLUGIN_ROOT}/scripts/hf-hub.py"
python3 "$S" extract <file|-|URL> [...]            # every Hub/arXiv reference, deduplicated, no API calls
python3 "$S" extract <file|-|URL> [...] --resolve  # same, each checked: type, canonical id, exists, summary
python3 "$S" collection-find <model|dataset|space> <owner/name>   # collections (any owner) already holding it
python3 "$S" collections <owner>                   # all the owner's collections with items (slow when many)
```

`extract` understands `huggingface.co` and `hf.co` URLs with any sub-path (`/tree/main`, `/viewer`,
`/blob/...`), `datasets/` and `spaces/` prefixes, `huggingface.co/papers/<id>` and arXiv abs/pdf links. It skips
docs, blog, tasks, search pages and bare user/org pages. Bare `owner/name` text without a URL is not
extracted: pass those to `resolve` directly.

## 2. Collect the references

| Source | How |
|---|---|
| Pasted text or a list | write it to a temp file (or pipe on stdin) and `extract --resolve` |
| A public web page (awesome-list, blog, leaderboard, README) | `extract <URL> --resolve`. If the fetch fails or the page is JS-rendered, fetch it with your web tools or a browser, save the text, extract from the file |
| A model or dataset card's links (base model, datasets used, related papers) | `extract https://huggingface.co/<id>/raw/main/README.md --resolve` |
| Open browser tabs | read the tab URLs with the browser tools available, then `resolve` them |
| A Hub search | `search` / `hubexplorer`, then take the ids the user picks |
| Mentioned during the conversation | `resolve` the ids as they come up |

Report anything with `exists: false` and carry on; never guess a substitute.

## 3. Purpose and target

Each link needs a reason it is being collected. Take it from what the user said; if a batch came with
no stated purpose, ask once for the batch, not per link. Then pick the target:

1. An existing collection of the owner's whose title matches the purpose: check the index file or
   `collections <owner>`. Prefer an existing one; collection sprawl is the usual failure.
2. Otherwise a new collection title (Title Case, ≤ 60 chars, names the purpose).
3. For each item, `collection-find` tells you whether it is already in that target (skip it) or in another
   of the owner's collections (mention it; adding to a second collection is fine when both fit).

## 4. File now or stage

- **File now** when the user asked to add or bundle, or the target is clear: hand the list, purpose and target
  to `bundle-collection` (it creates or updates, writes per-item notes, reads back).
- **Stage** when the user says "save", "stage", "for later", or the target is undecided: append to the inbox,
  under one `##` heading per target (an existing slug, `NEW: <Title>` or `UNSORTED`):

  ```
  ## owner/hebrew-asr-candidates-6ad6...
  - model ivrit-ai/whisper-large-v3 — strongest Hebrew fine-tune seen so far (from ivrit.ai blog, 2026-11-16)
  ```

  Skip lines already in the inbox (match on type + id).

## 5. File the inbox

On "file the inbox" / "flush": for each heading other than `UNSORTED`, run `bundle-collection` with its
lines as items and their reasons as notes. Remove each line once `collection <slug>` shows the item
(200 added or 409 already there). Leave `UNSORTED` lines and ask where they go in one question.
Reply with collection URLs and counts per target.

## Data storage

Reads `profile.env` and `gather-collection-links.md` from the data folder. Writes only the inbox file
(`HF_RESEARCH_COLLECTIONS_INBOX`); collection changes go to the Hub.
