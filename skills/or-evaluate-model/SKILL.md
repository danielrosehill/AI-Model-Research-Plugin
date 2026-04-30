---
name: or-evaluate-model
description: Use when the user wants a deep evaluation of a single OpenRouter model that goes beyond the OR catalog — model card, paper, benchmarks, license, known limitations. Triggers on phrases like "evaluate <model> for <task>", "deep dive on <OR model>", "research <model> beyond OpenRouter", "is <model> good for <use case>", "tell me everything about <OR model>", "model card for <model>".
---

# Evaluate an OpenRouter Model in Depth

Conduct a thorough evaluation of a single model the user is considering. Combine OpenRouter catalog data with external research — Hugging Face model card, original paper, license, benchmark coverage, community feedback — to give the user a confident go/no-go answer.

## When to use

The user has shortlisted a model (often from `or-recommend-model` or `or-compare-models`) and wants to understand it deeply before committing — for a real workflow, a production deployment, or a comparison against incumbents.

## Workflow

### Step 1: Catalog snapshot

Fetch the OpenRouter catalog and extract the target model's full record:

```bash
curl -s https://openrouter.ai/api/v1/models -H "Accept: application/json"
```

Capture: id, context_length, modalities, pricing, supported_parameters, top_provider info, description, created date.

### Step 2: External research

Go beyond the OR catalog. Use the available research tools (WebFetch, web search, Hugging Face MCP if available) to gather:

1. **Hugging Face model card** — for open-weights models, fetch from `huggingface.co/<org>/<repo>`. Look for: training data, training compute, licence, intended use, limitations, evaluation results.
2. **Original paper** — if the model has an arXiv paper, summarize key claims (architecture, training scale, headline benchmarks).
3. **Provider's own announcement / docs** — for proprietary models (OpenAI, Anthropic, Google), pull from official pages.
4. **License** — clearly state the licence and any commercial-use restrictions. This is especially important for Llama, Qwen, DeepSeek, Mistral families.
5. **Benchmark coverage** — what public benchmarks has it been tested on? Headline scores on MMLU, HumanEval, GSM8K, SWE-bench, etc. — but only cite scores you can actually find, never from memory.
6. **Known limitations / failure modes** — what is the model bad at? Reasoning depth, multilingual gaps, hallucination rates, refusal behavior?
7. **Community reception** — recent discussion, reviews, or notable usage reports if findable.

### Step 3: Synthesize for the user's use case

If the user mentioned a specific workflow (e.g. "I want to use this for legal document summarization"), explicitly evaluate fitness for that task:

- Does the context window comfortably hold typical inputs?
- Are the modalities right?
- Does the licence permit the intended use?
- Are there documented strengths or weaknesses for this task class?

### Step 4: Structured report

Output a structured evaluation report:

```markdown
# Evaluation: <Model ID>

## OpenRouter Catalog Snapshot
- Context: ...
- Pricing: ... / 1M prompt, ... / 1M completion
- Modalities: ...
- Supported parameters: ...

## Background
- Provider: ...
- Released: ...
- Architecture / scale (if known): ...
- Paper: <link if found>

## Capabilities
- ...

## Limitations & Known Issues
- ...

## Licence
- ...
- Commercial use: yes / no / conditional

## Benchmarks (if publicly reported)
- ...

## Fit for <user's stated use case>
- Verdict: strong / moderate / weak fit
- Reasoning: ...

## Recommendation
- Use this if: ...
- Avoid this if: ...
- Consider alternatives: <list 1–2 from OR catalog>
```

## Notes

- Be honest about what you could and could not verify. If you can't find a benchmark score or a model card, say so — don't invent.
- Cite external sources explicitly with URLs.
- If the model is proprietary and the provider publishes little detail, say that and lean on the OR catalog + provider docs.
- Do not pull benchmark numbers from memory. If WebFetch / web search is not available in the session, say "external benchmark lookup unavailable in this session — recommend re-running with web research enabled" rather than fabricating.
