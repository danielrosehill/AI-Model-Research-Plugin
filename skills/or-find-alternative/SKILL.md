---
name: or-find-alternative
description: Use when the user wants to find a cheaper or otherwise-similar alternative to a specific OpenRouter model — returns 3–5 ranked alternatives with trade-offs explicit.
---

# Find Model Alternative

Search for substitute models on OpenRouter that match the user's reference model in key capabilities while optimizing for cost, latency, or other constraints. Returns ranked candidates with explicit capability deltas.

## When to use

- User asks "what's cheaper than X but similar quality?"
- User wants to replace a model due to cost ("better alternative to Y that costs less")
- User needs a fallback with specific capabilities ("model like X that supports vision and tool use")
- User is exploring a capability-equivalent but cheaper tier

## Inputs to gather

- Reference model ID (slash-form)
- Primary constraint: price, quality, latency, or capability requirement (e.g. "must support vision")
- Optional secondary constraints (context length, provider preference, etc.)

## Procedure

CLI: `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/orexplorer.py`; prices in its output are US$ per 1M tokens.

1. `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/orexplorer.py model <ref-id> --brief`: note `input_per_m`, `output_per_m`, `context`, `input` modalities, `caps` (tools, structured, reasoning, ...), author.
2. Find candidates with the reference's capabilities as filters, e.g.:
   ```bash
   python3 ${CLAUDE_PLUGIN_ROOT}/scripts/orexplorer.py models --cap tools --cap vision --min-context 128000 --max-in <ref_in> --max-out <ref_out> --sort price --limit 15
   ```
   Add `--cap` for each capability that must be kept (`tools`, `vision`, `audio-in`, `structured`, `json`, `reasoning`, `caching`, ...; `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/orexplorer.py capabilities` lists them), `--author` to stay in or leave a vendor, `--batch` if batch pricing is acceptable. Set `--max-in/--max-out` to the reference prices for a cost-driven search. Add `--include-free` to also see `:free` variants.
3. Pick 3-5 candidates (drop router entries with null prices). For quality-driven searches, check `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/orexplorer.py benchmarks intelligence --limit 0` (or `coding`/`agentic`) to see which candidates rank near the reference; this scrapes openrouter.ai/rankings (undocumented, may break; say so). Without benchmark data, do not assert quality parity.
4. Rank by the user's constraint (cheapest-first if cost-driven; benchmark rank if quality-driven; `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/orexplorer.py performance -q <id>` if speed-driven).
5. For each candidate list: model ID, input/output per 1M, context, capability deltas vs. reference (gained, lost, same), and the price ratio vs. reference.

## Output / side effects

User receives a ranked list of 3–5 alternatives with clear trade-offs. No persistent artifacts.

## Safety / constraints

Never present a cheaper alternative as a "free lunch." Always highlight what is being traded: quality regression, reduced context, missing modalities, or latency increases. Confirm the user's priority (cost, quality, speed) before recommending.
