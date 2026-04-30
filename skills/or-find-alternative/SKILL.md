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

1. Call `mcp__model-scout__get_model` with the reference model ID; extract its specs: pricing, context length, modalities, tool support, approximate quality tier, and provider.
2. Call `mcp__model-scout__consider_models` with the reference model's capabilities as filters and an "alternatives" intent, specifying the user's optimization goal (e.g. lower cost, same quality).
3. Retrieve 3–5 candidate models; calculate per-1M-token pricing for each (input + output combined).
4. Rank by the user's constraint (cheapest-first if cost-driven; quality-tier if quality-driven).
5. For each candidate, explicitly list: model ID, pricing (input/output per 1M), context window, capability deltas vs. reference (gained, lost, same).

## Output / side effects

User receives a ranked list of 3–5 alternatives with clear trade-offs. No persistent artifacts.

## Safety / constraints

Never present a cheaper alternative as a "free lunch." Always highlight what is being traded: quality regression, reduced context, missing modalities, or latency increases. Confirm the user's priority (cost, quality, speed) before recommending.
