---
name: expand-collection
description: "Here's what I found, add anything I missed": take the Hugging Face models, datasets, Spaces or papers the user found (plus any Hub search URLs or tags they used), find what they missed - originals behind conversions, newer or real-time variants, well-known alternatives, items other curators group with them - and file seeds and finds together into one collection, reusing the user's existing collection on the topic if there is one. Use on "here's what I found, what else is there", "add these and anything I missed", "build out my X collection", "find more like these", "flesh out this collection".
---

# Expand a collection from the user's finds

## 1. Load your settings

Find the data folder (see `shared/settings.md`). Read `profile.env` and `expand-collection.md` there if they exist; they win over
the defaults below. If `HF_RESEARCH_COLLECTIONS_WORKSPACE` is set, use its `snapshots/INDEX.md` to find existing
collections and write the plan file to its `plans/` (step 7). Without one, call `collections <owner>`.

```bash
S="${CLAUDE_PLUGIN_ROOT}/scripts/hf-hub.py"
python3 "$S" extract found.md --resolve            # seeds + the search URLs the user pasted
python3 "$S" related <id> --limit 6 --co 2          # neighbours of one seed (see below)
python3 "$S" search model --filter <tag> --sort downloads|likes|trendingScore --limit 15
python3 "$S" collection <slug>                      # the existing target's items and notes
python3 "$S" collection-add <slug> <type> <id> "<note>"
```

`related` returns, per seed type: **model**: `base_model`, `trained_on`, `derivatives` (fine-tunes, quants,
conversions), `spaces_using`; **dataset**: `models_trained_on_it`, `spaces_using`; **Space**: `models_used`,
`datasets_used`; **paper**: repos citing the arXiv id. Models, datasets and Spaces also get `co_collected`: the most upvoted
collections by *other* people that hold the seed, with their items. A candidate turning up in several of these
is strong evidence.

## 2. Steps

1. **Seeds.** Save the user's message to a file and `extract --resolve` it. Report any `exists: false`. Listing URLs
   (`models?pipeline_tag=...`, `models?other=<tag>`) come back under `searches`: those are the user's search
   space, not items.
2. **Target.** Look for the user's existing collection on the topic (title match in the index, then the seeds'
   `collection-find`). Reuse it, even if it's small; mention any second collection that overlaps (a candidate for
   `tidy-collections`), don't merge here. Create a new one only when nothing fits.
3. **Discover**, wide and cheap:
   - `related` on every seed (`--limit 6 --co 2`);
   - `search` each tag the user gave **plus the obvious sibling tags** (read the seeds' tags: e.g. speech-enhancement →
     speech-denoising, speech-restoration, dereverberation, noise-suppression), each by `downloads`, `likes`
     and `trendingScore`, `--limit 15`.
   Merge everything into one candidate table: id, pipeline, downloads, likes, last modified, and the list of signals
   that found it (`tag:x`, `derivative<seed`, `co:<collection title>`).
4. **Select**, by judgement, about 8-15 additions:
   - **keep** originals with signal: several signals, or high likes, or a known lab; the **original** behind a seed that
     is a conversion (Sidon-GGUF → sidon-v0.1); newer and real-time variants of a seed family; one good port of a
     notable model whose upstream lives off the Hub (say so in the note);
   - **drop** mirrors and re-uploads (same name under another owner, 0 likes), personal fine-tunes with no card,
     items whose pipeline is clearly another task (TTS hits on an enhancement tag), and items better suited to a
     sibling collection the user already has (mention them instead);
   - format variants (GGUF/ONNX/MLX/CoreML/LiteRT) of something already kept: at most one, and only if the user cares
     about running locally.
5. **Notes.** Seeds: `Found by <user>. <what it is, from tags/card>`. Additions: `Added in discovery: <what it is and why
   it earns its place>`. One line each, ≤ 500 chars. Keep existing items' notes.
6. **File.** `collection-add` seeds first, then additions (200 added, 409 already there). If the collection has no
   description, set one (≤ 150 chars) naming the purpose. Read back and check the count.
7. **Record** (workspace only): `plans/<collection-slug-stem>.md` with date, seeds, searches run, kept (with signals)
   and notable drops with the reason. Commit and push. Next time, start from that file so dropped items aren't
   re-proposed.
8. **Reply**: collection URL, count before → after, the additions as a short list (id: one-line why), and
   anything left out on purpose that the user might want after all.

Later single links the user adds ("also this one") go through the same check: right collection for *what it does*?
If it's another task (an audio *editing* model offered for a speech *enhancement* collection), put it in the
collection that fits and say so in one line.

## Worked example (2026-11-17)

Input, pasted as is:

```
TAG: https://huggingface.co/models?pipeline_tag=audio-to-audio&
Subset: speech enhancement
Tags:
https://huggingface.co/models?other=speech-enhancement
https://huggingface.co/models?other=speech-denoising
https://huggingface.co/desert-ant-labs/clear
https://huggingface.co/sarulab-speech/DialogueSidon2
https://huggingface.co/audiojs/restore
https://huggingface.co/nvidia/RE-USE
https://huggingface.co/cstr/Sidon-GGUF
https://huggingface.co/cisco-ai/stupase
https://huggingface.co/jadechoghari/VoiceRestore
```

Ask: "here's what I found, add these into a collection; if I already started one, put them there, add anything I missed".

- `extract --resolve`: 7 models, all exist; 3 searches (`pipeline_tag=audio-to-audio`, `other=speech-enhancement`,
  `other=speech-denoising`).
- Target: existing **Voice Enhancement** (2 items, no description). **Audio restoration** overlapped (held RE-USE and
  Sidon-GGUF); left for tidy-collections.
- Discovery: `related` on the 7 seeds; tag searches on speech-enhancement, speech-denoising, speech-restoration,
  dereverberation, noise-suppression × 3 sorts. About 70 candidates.
- Kept 12 models + 1 Space: sarulab-speech/sidon-v0.1 (original of Sidon-GGUF), nvidia/NVIDIA-NemotronLabs-RE-USE and
  nvidia/Real-time_RE-USE (newer/streaming RE-USE), ResembleAI/resemble-enhance, LocalAI-io/LocalVQE, nineninesix/diamond-1.0,
  weya-ai/hush, sp-uhh/speech-enhancement-sgmse, speechbrain/metricgan-plus-voicebank, JacobLinCool/MP-SENet-DNS,
  starkdmi/MossFormer2-SE, soniqo/DeepFilterNet3-ONNX (port; upstream on GitHub), Space eustlb/audio-to-audio-models-on-the-hub.
- Dropped: tencent/AuK* (TTS), ~8 resemble-enhance and diamond-1.0 re-uploads, Sidon/RE-USE format ports beyond one,
  Quran-Lab/sawt-* (recitation-specific), arbazsiddiqui/voxlock (speaker isolation: user already has that collection).
- Result: 2 → 22 items, description set. A follow-up link, GeWu-Lab/SteerSound (instruction-guided audio editing), went
  to **Audio editing utilities** instead.

## Data storage

Reads `profile.env` and `expand-collection.md` from the data folder. Writes `plans/` in the collections workspace if one is set;
collection changes go to the Hub.
