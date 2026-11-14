# AI Model Research

An agent plugin for researching AI models: what exists, what each model supports, what it costs, what's new, what's trending and what serves it. Skills sit on top of small, unofficial, read-only CLIs. The CLI does the fetching and filtering and the skill interprets the results, so the same commands work for an agent, a shell script or a person.

| Source | CLI | Status |
|---|---|---|
| [OpenRouter](https://openrouter.ai) | `orexplorer` (`scripts/orexplorer.py`) | v1.0, 2026-11-14 |
| Hugging Face Hub | `hubexplorer` | being merged in from the standalone HF-Research-Plugin |

> **Unofficial.** These CLIs aren't affiliated with OpenRouter or Hugging Face. They're for discovery and evaluation only: they never run inference and need no API key.

## orexplorer

A stdlib Python CLI. It outputs JSON by default; `--table` gives a human view and `--compact` gives one-line JSON. Results are cached for 10 minutes in `~/.cache/orexplorer` (`OREXPLORER_TTL`, `OREXPLORER_CACHE`, `--no-cache`).

```bash
# inside the plugin (what the skills do)
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/orexplorer.py capabilities --table

# standalone
uv tool install git+https://github.com/danielrosehill/Claude-AI-Model-Research-Plugin
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

Capability flags: `tools`, `parallel-tools`, `structured`, `json`, `reasoning`, `reasoning-off` (thinking is optional), `no-reasoning`, `reasoning-effort`, `logprobs`, `web-search`, `seed`, `vision`, `audio-in`, `video-in`, `file-in`, `image-out`, `audio-out`, `video-out`, `text-out`, `open-weights` (has a Hugging Face id), `caching`, `free`. Routers (`openrouter/*`) are hidden unless `--aliases`; models billed per request rather than per token (e.g. `google/lyria-*`) show `null` prices and `"token_priced": false`, sorted last. They come from `supported_parameters`, `architecture.*_modalities`, `reasoning` and `pricing`.

**Batch:** a model is batch-capable when the catalogue also lists `<id>:batch` (87 of 471 ids on 2026-11-14). The batch job itself runs on the base id through `POST /api/v1/batches`. For running batch jobs, see the `batch-inference` plugin.

**⚠ Rankings scraping (undocumented):** `trending`, `benchmarks` and `performance` read the react-query state that `https://openrouter.ai/rankings` embeds in its Next.js flight payload (`self.__next_f.push` chunks), under the queryKeys `["rankings","models",{"view":"week"}]`, `["rankings","benchmarks"]` and `["rankings","performance"]`. OpenRouter has no public rankings API: `/api/v1/models?order=top-weekly` is accepted but ignored, and `/api/frontend/*` returns 404 (checked 2026-11-14). If the page changes, these commands exit with a JSON error, and the catalogue commands keep working. Ranking slugs are dated permaslugs (`tencent/hy4-20261104`), which the CLI maps back to public ids through `canonical_slug`.

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

## History

- 2026-11-14: the Model-Scout MCP (`npx model-scout-mcp`) was replaced by the bundled `orexplorer` CLI. The skills now call the CLI, so the plugin needs no MCP server. The Hugging Face research plugin is being folded in so this becomes the single model-research plugin.
- Earlier, this plugin subsumed the standalone `open-router-model-research` plugin and [Model-Scout-MCP](https://github.com/danielrosehill/Model-Scout-MCP).

## Installation

```bash
claude plugins install ai-model-research@danielrosehill
```

## License

MIT
