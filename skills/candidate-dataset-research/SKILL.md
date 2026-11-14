---
name: candidate-dataset-research
description: Before building training data for a small model, find what already exists on the Hugging Face Hub. Search datasets for the task, including datasets that can be transformed into training pairs, open and vet the promising ones (schema, sample rows, size, licence), file the keepers in a public or private candidates collection with a one-line verdict on each, and optionally write a blend manifest saying which go into training and how much of each. Use when the user says "find datasets for", "candidate dataset research", "what's out there for this task", "is there a dataset I can use", "add it to the candidates", "put together a data blend", or is about to synthesise or hand-build a training set.
---

# Candidate dataset research

## 1. Load your settings

Find the data folder (see `shared/settings.md`: `$HF_RESEARCH_HOME`, `$CLAUDE_USER_DATA/hf-research/`, then `~/.claude-user-data/hf-research/`). Read `profile.env` and `candidate-dataset-research.md` there if they exist. They win over the defaults below, and comments in `profile.env` are instructions. With no profile, use the defaults below and offer `setup` at the end.

Profile keys used: `HF_RESEARCH_DEFAULT_OWNER` (owner of the candidates collection, default the token's username), `HF_RESEARCH_OWNERS`, `HF_RESEARCH_DEFAULT_VISIBILITY` (default `private`).

People often build their own training sets when the Hub already holds something usable. Run this before synthesising or annotating data
for a new small model, and whenever the user asks what exists.

```bash
S="${CLAUDE_PLUGIN_ROOT}/scripts/hf-hub.py"
python3 "$S" search dataset <words> [--filter language:en] [--filter license:cc-by-4.0] [--task text-classification] [--sort downloads|likes|trendingScore] [--limit 20]
python3 "$S" dataset-peek <owner/name> [--config C] [--split S] [--rows 5]   # splits + row counts, features, sample rows
python3 "$S" collections <owner>                                             # pick or create the candidates collection
python3 "$S" collection-new <owner> "<Task> Candidate Datasets" <public|private> "<one-line task>"
python3 "$S" collection-add <slug> dataset <owner/name> "<verdict note>"
```

Search needs no token for public data. With the token it also sees the user's private repos.

## Step 1: Frame what's needed, including derivable data

Write down the training pair the model needs, then list the kinds of dataset that **already
are** that pair and the kinds that can be **turned into** it. The second list is usually longer
and is where most finds come from.

Example, paragraph insertion (unbroken text in, paragraphed text out):
- already the pair: datasets of unparagraphed text with a paragraphed target (rare)
- derivable: any well-paragraphed English text in the right register, such as emails, letters
  or blog posts. Collapse the paragraph breaks to make the input, and the original is the target.

Other common derivations: punctuation or casing restoration (strip it from clean text),
summarisation or headline (article plus its lede or title), classification (a column or tag
that already holds the label), and span tagging (text with markup or structured fields).

## Step 2: Search wide

- 5 to 10 phrasings for each kind: the domain noun (`emails`, `email corpus`, `enron`,
  `business correspondence`), the task, and synonyms. Repo names rarely use the user's wording.
- Filters on **datasets**: `language:en` (on models it is the bare `en`, see
  `candidate-base-model-research`), `task_categories:<task>` via `--task`,
  `license:<id>`, `size_categories:10K<n<100K`. A filter the Hub doesn't recognise returns 200
  and an empty list, so retry without it before concluding nothing exists.
- Every dataset filter (modality, format, size, language, licence, domain tags such as
  `other=synthetic`, sub-tasks via `other=task_ids:<id>`) and how to combine them is in
  `hub-search-urls`: `scripts/hubexplorer.py datasets --task <id> --language he --modality audio --count`
  runs the search and gives the browsable URL, the API query and the count.
- Sort by `downloads` and then by `trendingScore`. Recent good sets have few downloads yet.
- Also check the user's own repos (`hf-hub.py search dataset <words>` with their owner as a filter, or `resolve`), so an existing set of
  theirs isn't missed. If the profile names a repo-search tool, use that too.
- Search papers when the task is studied: `GET https://huggingface.co/api/papers/search?q=<words>`.
  Papers often name the dataset they trained on.

Keep every query and its result count, the empty ones included. That is what makes "nothing
suitable exists" credible.

## Step 3: Vet the promising ones (open each, don't trust the card)

For each one that might be used, run `dataset-peek` and record:

| Check | Why |
| --- | --- |
| rows per split | is it large enough to matter, or large enough to subsample |
| features and a few rows | is the text really what the card says, and is the target there or derivable |
| the property the task depends on | e.g. for paragraphing: do the rows contain `\n\n`, or was the text flattened? A corpus scraped to one line per document is useless for it |
| language and register | a multilingual set may hold only a small English share |
| licence and gating | `cc-by-nc`, no licence, or gated affects whether a published model can use it |
| synthetic or real | synthetic sets can be fine, but say so: they bias the style |
| duplicates and boilerplate | signatures, disclaimers and reply chains dominate email corpora |

`viewer: false` means the dataset viewer can't read it (no parquet conversion, a script-based
loader, gated or private). Read the card and file list instead
(`GET https://huggingface.co/api/datasets/<id>`) and mark the checks as unverified.

Give each dataset a verdict: **use**, **use with transform** (say which transform),
**maybe** (what's unknown), or **reject** (why).

## Step 4: File the keepers

1. Ask public or private unless the user already said. Default to `HF_RESEARCH_DEFAULT_VISIBILITY`, else **private**, for active
   research. A private collection can hold other people's public datasets.
2. Owner: `HF_RESEARCH_DEFAULT_OWNER` unless the work belongs to one of `HF_RESEARCH_OWNERS` (the profile may say which work goes to which org). Say which owner you picked.
3. Reuse a collection that fits (`collections <owner>`). Otherwise create `<Task> Candidate Datasets`, e.g.
   `Paragraph Insertion Candidate Datasets`.
4. Add each **use**, **use with transform** and **maybe** dataset with a note of 500 characters or
   fewer: verdict, rows, licence, transform. Example note:
   `use with transform: 16k marketing emails, paragraphed; collapse \n\n -> input. cc-by-4.0, synthetic`.
   Rejects stay in the report and out of the collection.
5. The user's own data and models built from these candidates go into their normal collections
   (`hf-publisher-tools:collections`), not the candidates one.

## Step 5: Optional: the blend

When the user says which candidates go into training, write `blend.json` in the training
project (or `docs/` of the model's repo), one entry per source:

```json
{"as_of": "2026-10-25", "task": "paragraph-insertion", "sources": [
  {"dataset": "marketeam/Marketing-Emails", "revision": "<sha>", "config": "default", "split": "train",
   "columns": {"text": "0"}, "transform": "collapse-paragraphs", "rows": 8000, "share": 0.4,
   "license": "cc-by-4.0", "filters": "drop < 3 paragraphs; strip signatures"}
]}
```

Pin `revision` (`GET /api/datasets/<id>` → `sha`) so the blend is reproducible. Building the
blended dataset itself is a separate data-preparation job.

## Step 6: Report

A table: dataset, rows, licence, verdict, transform, then the collection URL
(`https://huggingface.co/collections/<slug>`), the queries that found nothing, and the gap,
meaning what still has to be synthesised or annotated. If the work is in a model-planning repo, write it into its `docs/prior-art.md` as well.

## Data storage

Candidate collections live on the Hub; `blend.json` goes in the training project, not the plugin. Private notes for this skill go in `<data folder>/candidate-dataset-research.md`; shared settings in `<data folder>/profile.env`. Nothing personal is stored in the plugin.
