# AI Model Research

An agent plugin for researching AI models: what exists, what each model supports, what it costs, what's new, what's trending and what serves it. Skills sit on top of small, unofficial, read-only CLIs. The CLI does the fetching and filtering and the skill interprets the results, so the same commands work for an agent, a shell script or a person.

| Source | CLI | Status |
|---|---|---|
| [OpenRouter](https://openrouter.ai) | `orexplorer` (`scripts/orexplorer.py`) | v1.1, 2026-11-14 |
| [Hugging Face Hub](https://huggingface.co) | `hubexplorer` (`scripts/hubexplorer.py`) | v1.0, 2026-11-14, from [HF-URLs](https://github.com/danielrosehill/HF-URLs) |

> **Unofficial.** These CLIs aren't affiliated with OpenRouter or Hugging Face. They're for discovery and evaluation only: they never run inference and need no API key.

## orexplorer

A stdlib Python CLI. It outputs JSON by default; `--table` gives a human view and `--compact` gives one-line JSON. Results are cached for 10 minutes in `~/.cache/orexplorer` (`OREXPLORER_TTL`, `OREXPLORER_CACHE`, `--no-cache`).

```bash
# inside the plugin (what the skills do)
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/orexplorer.py capabilities --table

# standalone
uv tool install git+https://github.com/danielrosehill/AI-Model-Research-Plugin
orexplorer models --batch --cap tools --cap structured --max-out 2 --table
```

| Command | What it returns | Source |
|---|---|---|
| `models` | The catalogue, filtered by `--cap <flag>` (repeatable), `--batch`, `--max-in/--max-out` (US$/1M tokens), `--min-context`, `--author`, `--days`, `-q`, `--free`, and sorted by `--sort price\|context\|new\|name` | `/api/v1/models` |
| `capabilities` | Every `--cap` flag with its meaning and model count | `/api/v1/models` |
| `model <id>` | Summary, variants (`:batch`, `:free`) and the full raw record | `/api/v1/models` |
| `endpoints <id>` | Providers serving the model: price, quantization, context, uptime | `/api/v1/models/<id>/endpoints` |
| `new --days N` | Models added recently | `/api/v1/models` |
| `trending [--rising]` | Top 20 models by tokens this week, with week-on-week change | `openrouter.ai/rankings` ⚠ |
| `benchmarks <agentic\|coding\|intelligence>` | Artificial Analysis scores as shown by OpenRouter | `openrouter.ai/rankings` ⚠ |
| `performance` | p50 throughput and latency per model, plus the fastest provider | `openrouter.ai/rankings` ⚠ |
| `stats` | Catalogue size and models per author | `/api/v1/models` |
| `batch [terms]` | Every model with a `:batch` variant: batch vs sync price, which is cheaper at the job's token mix, `--dearer-only` | `/api/v1/models` |
| `bulk [terms]` | Sync models fit for bulk jobs: paid, text-only output, JSON mode, reasoning can be off, not expiring (`--max-out` defaults to 2) | `/api/v1/models` |

`models`, `model`, `batch` and `bulk` take `--est-in/--est-out` (or `--items` with `--in-per-item/--out-per-item`) to add `est_sync`, `est_batch` and `est_peak` job costs, and the price sort then uses the job's token mix.

Capability flags: `tools`, `parallel-tools`, `structured`, `json`, `reasoning`, `reasoning-off` (thinking is optional), `no-reasoning`, `reasoning-effort`, `logprobs`, `web-search`, `seed`, `vision`, `audio-in`, `video-in`, `file-in`, `image-out`, `audio-out`, `video-out`, `text-out`, `open-weights` (has a Hugging Face id), `caching`, `free`. Routers (`openrouter/*`) are hidden unless `--aliases`; models billed per request rather than per token (e.g. `google/lyria-*`) show `null` prices and `"token_priced": false`, sorted last. They come from `supported_parameters`, `architecture.*_modalities`, `reasoning` and `pricing`.

**Batch:** a model is batch-capable when the catalogue also lists `<id>:batch` (87 of 471 ids on 2026-11-14). The batch job itself runs on the base id through `POST /api/v1/batches`. For running batch jobs, see the `batch-inference` plugin.

**⚠ Rankings scraping (undocumented):** `trending`, `benchmarks` and `performance` read the react-query state that `https://openrouter.ai/rankings` embeds in its Next.js flight payload (`self.__next_f.push` chunks), under the queryKeys `["rankings","models",{"view":"week"}]`, `["rankings","benchmarks"]` and `["rankings","performance"]`. OpenRouter has no public rankings API: `/api/v1/models?order=top-weekly` is accepted but ignored, and `/api/frontend/*` returns 404 (checked 2026-11-14). If the page changes, these commands exit with a JSON error, and the catalogue commands keep working. Ranking slugs are dated permaslugs (`tencent/hy4-20261104`), which the CLI maps back to public ids through `canonical_slug`.

## hubexplorer

Find models and datasets on the Hugging Face Hub by task and filter. Give it plain flags and it builds the right query, with each parameter's prefix and AND/OR behaviour handled. It runs the query against the public Hub API and returns a compact JSON shortlist, together with the matching website URL. **Unofficial**: it's not affiliated with Hugging Face. It's a thin wrapper around the public Hub API, for discovery and evaluation only. Stdlib Python; `HF_TOKEN` is optional.

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/hubexplorer.py models --task audio-to-audio --sort downloads
hubexplorer models --task text-generation --library gguf --language he --app lmstudio --params 0-12B
hubexplorer models --provider groq --provider together          # served by either
hubexplorer models --quantized-of Qwen/Qwen3-8B --library gguf
hubexplorer datasets --task automatic-speech-recognition --language he --modality audio --sort likes
hubexplorer task any-to-any      # task page, models and datasets URLs for every sort order
hubexplorer values apps | sorts | rules | info
```

**Provenance:** `scripts/hubexplorer.py` is a copy of `src/hubexplorer/cli.py` from [HF-URLs](https://github.com/danielrosehill/HF-URLs). `data/hf-urls/` holds that repo's `hf-urls.json` and `languages.json`: every Hub task with its models and datasets URLs, plus every filter value with a checked result count. `data/hf-urls/VERSION` records which HF-URLs release the copy came from. To update, copy all three from a new release. A `uv tool install` of this repo has no `data/`, so on first use hubexplorer downloads the data from HF-URLs into `~/.cache/hubexplorer`.

**How filters combine:** different parameters combine with AND. Comma-separated values inside one parameter are also AND, except `apps` and `inference_provider`, where they're OR. A task URL takes one task. Sorts: `trending`, `likes`, `downloads`, `created`, `modified`; models also `most_params` and `least_params`, datasets `most_rows` and `least_rows`. Those last four are website-only. The full rules are in the `hub-search-urls` skill and the HF-URLs README.

## Skills

| Skill | What it does |
|---|---|
| `or-lookup-models` | Foundation skill: fetches the catalogue or one model's record |
| `or-quick-lookup` | Mid-conversation capability and pricing snapshot of one model |
| `or-find-tool-models` | Tool / function-calling models |
| `or-find-vision-models` | Image-input models |
| `or-find-audio-models` | Audio-input models |
| `or-recommend-model` | Interactive recommendation: asks about budget, context and modalities, then gives a ranked shortlist |
| `or-compare-models` | Head-to-head comparison of 2+ models |
| `or-evaluate-model` | Deep evaluation: catalogue, providers, benchmarks, model card, licence |
| `or-research-models` | Open-ended exploration: themes, families, what's new, what's trending, fastest |
| `or-cost-projection` | Workload cost (requests × tokens) on one or more models |
| `or-find-alternative` | Cheaper or similar alternatives to a reference model, with trade-offs |

Hugging Face Hub (task first: start from [huggingface.co/tasks](https://huggingface.co/tasks), then the models within the task):

| Skill | What it does |
|---|---|
| `task-directory` | Every Hub task with its page, models URL and datasets URL, by category, plus task groups. No fetch needed |
| `hub-search-urls` | Filtered, ranked Hub searches with hubexplorer: format (GGUF, ONNX), language, local app, inference provider, model type, size, licence, sort order |
| `hf-tasks` | The task map as data: find, task detail, groups, `--refresh` for a live re-read |
| `task-model-research` | From a need to its task(s) to a vetted model shortlist |
| `transcription-model-research` | Speech-to-text models across ASR, audio-text-to-text and any-to-any |
| `candidate-base-model-research` | Base models for a fine-tune: real parameter count, licence, context, formats |
| `candidate-dataset-research` | Datasets that are, or can be turned into, training data |
| `gated-access` | Pre-fill a gated repo's access form from your saved answers, ask before submitting |
| `setup-collections-workspace` | A private repo for collection curation (inbox, plans, snapshots, tidy log), registered as `HF_RESEARCH_COLLECTIONS_WORKSPACE` |
| `expand-collection` | "Here's what I found, add anything I missed": seeds + discovery (`related`, tag searches) into one collection |
| `tidy-collections` | Audit singletons, overlaps, duplicates, missing descriptions; propose, apply, log |
| `gather-collection-links` | Hub/arXiv links from text, pages, tabs or search → deduplicated, filed now or staged in an inbox |
| `bundle-collection` | A list of Hub ids plus a purpose → a collection with notes |
| `model-notebook` | Log a model you rate: favourites collection plus a notes dataset |
| `setup` | Write your private Hugging Face profile (`~/.claude-user-data/hf-research/`, see `shared/settings.md`) |

The Hugging Face scripts (`hf-tasks.py`, `hf-hub.py`, `gated.py`) are stdlib-only. `model-notes.py` needs `huggingface_hub`. Maintainers: run `scripts/build-task-directory.py` before a release; it regenerates `skills/task-directory/SKILL.md` from `data/tasks-snapshot.json` and `data/hf-urls/`.

## History

- 2026-11-14: the Model-Scout MCP (`npx model-scout-mcp`) was replaced by the bundled `orexplorer` CLI. The skills now call the CLI, so the plugin needs no MCP server. The same day, the Hugging Face research plugin (`hf-research`, repo HF-Research-Plugin, last at 1.2.0) was merged in with its skills, scripts, `hubexplorer` and the HF-URLs data, so this is now the single model-research plugin. Its user data stays in `~/.claude-user-data/hf-research/`.
- Earlier, this plugin subsumed the standalone `open-router-model-research` plugin and [Model-Scout-MCP](https://github.com/danielrosehill/Model-Scout-MCP).

## Installation

```bash
claude plugins install ai-model-research@danielrosehill
```

## License

MIT
