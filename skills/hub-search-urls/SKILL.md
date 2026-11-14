---
name: hub-search-urls
description: Search the Hugging Face Hub with hubexplorer (shipped, unofficial thin wrapper around the Hub API) and build search URLs that actually filter, by combining task, library/format (gguf, onnx, mlx), language, local app (LM Studio, Ollama, llama.cpp), inference provider (Groq, Together, fal…), model type (base, finetune, quantized, merge), parameter count, licence, and dataset modality/format/size. The plugin ships every valid value and the combining rules (HF-URLs data), so the agent can form its own searches. Use when you need a filtered models or datasets list, on "GGUF models for X", "Hebrew ASR datasets", "what can I run in LM Studio", "which models does Groq serve", "quantized versions of <model>", "finetunes of <model>", or to narrow any research skill's search.
---

# Hub search URLs

A Hub listing is one base URL and a set of filter parameters. Get the parameter names and
prefixes right and the list filters correctly. Get one wrong and the Hub doesn't complain, it
quietly gives a near-empty list (`models?license=mit`: 71 models; `license=license:mit`:
215,033). This skill explains the pattern. `scripts/hubexplorer.py` applies it, runs the search
and returns a compact shortlist. It is unofficial and has no connection to Hugging Face: a thin
wrapper around the public Hub API, for discovery and evaluation only.

The data comes from [HF-URLs](https://github.com/danielrosehill/HF-URLs) and ships in
`data/hf-urls/`: every task, every filter value with its URL and result count, and the rules.
`python3 "${CLAUDE_PLUGIN_ROOT}/scripts/hubexplorer.py" info` shows which data version is shipped.

## 1. Load your settings

Read `hub-search-urls.md` in the data folder (`shared/settings.md`) if it exists. It holds
the user's routine filters (their languages, the apps they run, the providers they use).
Apply those when the request leaves them open.

## 2. The construction pattern

```
https://huggingface.co/<models|datasets>?<param>=<value>[,<value>...]&<param>=<value>...&sort=<sort>
```

- **Different parameters → AND.** `pipeline_tag=text-generation&library=gguf&language=he`
  means text generation, and GGUF, and Hebrew.
- **Comma inside one parameter → AND** (`library=gguf,mlx` = models with both), **except**
  `apps` and `inference_provider`, where a comma means OR (`inference_provider=groq,together`
  = served by either).
- **One task per URL.** For a need that spans tasks, build one URL per task.
- **Keep `:` and `,` literal**; percent-encode `<`, `>` and spaces.
- **Sort:** one `sort=` per URL. This is the ranking, so choose it for the question being asked:

| `sort=` | Ranks by | Use for |
| --- | --- | --- |
| `trending` (default) | momentum this week | "what's hot", new releases gaining ground |
| `downloads` | downloads in the last 30 days | what people actually run; established picks |
| `likes` | all-time likes | community favourites |
| `created` | newest first | "what's new in X" |
| `modified` | recently updated | actively maintained |
| `most_params` / `least_params` | parameter count (models) | biggest, or smallest that fits |
| `most_rows` / `least_rows` | row count (datasets) | largest / smallest datasets |

The API spells these differently (`trendingScore`, `createdAt`, `lastModified`). It has no
params or rows sort, and it rejects the web names. hubexplorer translates them for you.
For a broad survey, run two rankings (e.g. `trending` and `downloads`) and merge them.

### Models

| Want | Parameter | Example |
| --- | --- | --- |
| Task | `pipeline_tag` | `pipeline_tag=any-to-any` |
| Library / file format | `library` | `library=gguf`, `library=onnx`, `library=mlx` |
| Language | `language` (bare code) | `language=he` |
| Runs in a local app | `apps` (OR) | `apps=lmstudio`, `apps=ollama`, `apps=llama.cpp`, `apps=vllm` |
| Hosted inference | `inference_provider` (OR) | `inference_provider=groq`; `=all` for any provider |
| Model type | `other` | `other=base`, `finetune`, `quantized`, `merge`, `adapter` |
| Other tags | `other` | `other=moe`, `4-bit`, `eval-results`, `decision-model`, `region:eu`, `deploy:azure` |
| Size | `num_parameters` | `num_parameters=min:0,max:6B` (K, M, B, T) |
| Licence | `license` (prefixed) | `license=license:apache-2.0` |
| Derived from a model | `other` | `other=base_model:quantized:Qwen/Qwen3-8B` (also `finetune`, `adapter`, `merge`) |
| Trained on a dataset | `dataset` | `dataset=dataset:mozilla-foundation/common_voice_17_0` |
| Org, name | `author`, `search` | `author=openai`, `search=whisper` |

Use `apps=`, not `other=`, for apps. The sidebar's links read `other=lmstudio`, but the page
rewrites them to `apps=lmstudio` when clicked. `other=lmstudio` only matches the literal tag
(154 models, against 238,915).

### Datasets

Dataset values carry their facet as a prefix, unlike most model values:

| Want | Parameter | Example |
| --- | --- | --- |
| Task | `task_categories` | `task_categories=task_categories:automatic-speech-recognition` |
| Modality | `modality` | `modality=modality:audio` (`audio,text` = both) |
| Format | `format` | `format=format:parquet` |
| Size | `size_categories` | `size_categories=size_categories:1K%3Cn%3C10K` |
| Language | `language` (prefixed) | `language=language:he` |
| Licence, library | `license`, `library` | `license=license:cc-by-4.0`, `library=library:pandas` |
| Domain, sub-task | `other` | `other=synthetic`, `other=medical`, `other=task_ids:extractive-qa` |
| Benchmarks | `benchmark` | `benchmark=benchmark:official` |

### JSON API

The same filters work on `https://huggingface.co/api/<models|datasets>?…`. Tag filters become
`filter=<same value>`, repeatable (AND). `pipeline_tag`, `author`, `search`, `apps`,
`inference_provider` and `num_parameters` keep their names. For sorting by trend, use
`sort=trendingScore`. Every hubexplorer search prints this form as `api`.

## 3. Search with hubexplorer

```bash
H="${CLAUDE_PLUGIN_ROOT}/scripts/hubexplorer.py"
python3 "$H" models --task audio-to-audio --sort downloads
python3 "$H" models --task text-generation --library gguf --language he --sort downloads
python3 "$H" models --app lmstudio --task image-text-to-text --params 0-12B
python3 "$H" models --provider groq --provider cerebras          # either provider
python3 "$H" models --quantized-of Qwen/Qwen3-8B --library gguf
python3 "$H" models --type base --task automatic-speech-recognition --count   # --count: listing total
python3 "$H" datasets --task automatic-speech-recognition --language he --modality audio --sort likes
python3 "$H" models --task text-to-speech --sort most_params --url   # URLs only, no network
python3 "$H" task any-to-any        # page, models and datasets URLs for every sort, counts
python3 "$H" values apps            # known values (+ counts) for a facet
python3 "$H" sorts | rules | info
```

Output is JSON: `web` (the listing URL to give the user), `api`, and `results`. Each result has:
id, url, task, library, params, licence, languages, base model, live providers, downloads
(30-day and all-time), likes, trending, gated, created and modified dates. `--limit` defaults to 20.

The tool adds prefixes for you (`--license mit` becomes `license:mit`). It warns on stderr
when a value isn't in the shipped list. Treat that warning as a likely typo, not a reason to
stop: the Hub adds tags all the time. An empty result comes back with a hint. Drop filters
one at a time before you conclude nothing exists.

## 4. Hand back

Give the user the URL (they can open it and adjust it in the sidebar), plus what you found
through it. When a research skill sent you here, go back to that skill with the URL or API
query.

## Data storage

Reads `data/hf-urls/` in the plugin and `hub-search-urls.md` in the data folder. Writes
nothing. To refresh the shipped data, a maintainer rebuilds HF-URLs and copies its `data/*.json`
into `data/hf-urls/` (see `README.md`).
