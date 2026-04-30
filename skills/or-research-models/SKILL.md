---
name: or-research-models
description: Use when the user wants open-ended exploration of OpenRouter models around a theme rather than a specific recommendation, comparison, or evaluation. Triggers on phrases like "explore OpenRouter models for <topic>", "what's available on OR for <area>", "show me what's new on OpenRouter", "survey of <model family> on OR", "research OpenRouter models for <use case>".
---

# Open-Ended OpenRouter Model Research

Survey-style exploration of the OpenRouter catalog for a topic, family, or use case the user is curious about — broader and looser than a recommendation flow.

## When to use

The user is exploring rather than choosing. Examples:

- "What's the state of open-source vision models on OpenRouter right now?"
- "Show me what DeepSeek has on OpenRouter"
- "What new models showed up on OR this month?"
- "I'm curious about cheap reasoning models on OpenRouter"

If the user wants a concrete pick, route to `or-recommend-model`. If they want to compare specific models, route to `or-compare-models`. Use this skill only for genuinely open-ended exploration.

## Workflow

### Step 1: Pin down the theme

The theme might be:
- A **provider / family** (`openai/`, `anthropic/`, `meta-llama/`, `deepseek/`, `qwen/`)
- A **capability** (reasoning, vision, audio, tool use, long context, multilingual)
- A **price tier** (free, sub-$1/M, premium)
- A **recency cut** (recently added — sort by `created` descending)

If the theme is fuzzy, ask one clarifying question to narrow it.

### Step 2: Gather the slice

Fetch the catalog and filter to the relevant slice:

```bash
curl -s https://openrouter.ai/api/v1/models -H "Accept: application/json"
```

Apply the filter and sort meaningfully (by created date for recency, by price for budget themes, by context for long-context themes).

### Step 3: Add light external context

Where useful, briefly contextualize the slice with external knowledge — what's the family known for, what's the recent narrative, what is the trade-off space. Keep this short (a few sentences). For deep dives on individual models, route to `or-evaluate-model`.

### Step 4: Present

Use a structure suited to exploration, not just a flat table:

```markdown
# <Theme> on OpenRouter

## Snapshot
- N models match this theme as of <fetch date>
- Price range: $... – $... per 1M tokens
- Context range: ... – ...

## Notable models

### <Model A>
- Why it stands out: ...
- Catalog facts: ...

### <Model B>
- ...

## What's missing / what to watch
- Gaps you noticed in the slice
- Models recently added or removed (if known)

## Suggested next steps
- "Want to compare A and B?" → or-compare-models
- "Want a recommendation for a specific task?" → or-recommend-model
- "Want to deep-dive on one of these?" → or-evaluate-model
```

## Notes

- This skill is meant to be informative and exploratory. Don't push the user toward a decision.
- Flag when the catalog has changed meaningfully since the user might have last looked (new families, deprecated models).
- If the theme returns nothing, say so plainly and suggest a related theme.
