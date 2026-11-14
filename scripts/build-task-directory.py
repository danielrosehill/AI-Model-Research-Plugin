#!/usr/bin/env python3
"""Maintainer tool: rebuild the shipped task map before a release.

  build-task-directory.py            read the live taxonomy, write data/tasks-snapshot.json,
                                      regenerate skills/task-directory/SKILL.md, print the diff
  build-task-directory.py --offline  regenerate the skill from the existing snapshot only

The skill is generated: edit this script, never the SKILL.md by hand.
"""
import importlib.util
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SNAP = ROOT / "data" / "tasks-snapshot.json"
GROUPS = ROOT / "data" / "task-groups.json"
OUT = ROOT / "skills" / "task-directory" / "SKILL.md"
HFURLS = ROOT / "data" / "hf-urls" / "hf-urls.json"  # shipped copy of github.com/danielrosehill/HF-URLs
CATS = {"nlp": "Text", "cv": "Vision", "audio": "Audio", "multimodal": "Multimodal",
        "tabular": "Tabular", "rl": "Reinforcement learning", "other": "Other", None: "Uncategorised"}

spec = importlib.util.spec_from_file_location("hft", ROOT / "scripts" / "hf-tasks.py")
hft = importlib.util.module_from_spec(spec)
spec.loader.exec_module(hft)


def short(text, n=110):
    text = (text or "").replace("|", "/").replace("\n", " ").strip()
    if len(text) <= n:
        return text
    cut = text[:n].rsplit(" ", 1)[0].rstrip(",.;:")
    return cut + "…"


def render(snap):
    groups = json.loads(GROUPS.read_text())
    ds = {t["id"]: t.get("datasets_url") for t in json.loads(HFURLS.read_text())["tasks"]} if HFURLS.exists() else {}
    date = snap["fetched"][:10]
    lines = [
        "---",
        "name: task-directory",
        "description: Every Hugging Face task with its task page and model-listing URL, built in, so model "
        "research can jump straight to the right task without fetching anything. Grouped by category, plus "
        "task groups for needs that span tasks (transcription, video generation, embeddings, …). Use first for "
        "any \"find a model for X\", \"which task is X\", \"show me the latest X models\", \"link to the HF "
        "task page for X\" request; use hf-tasks --refresh only if this map looks out of date.",
        "---",
        "",
        "# Hugging Face task directory",
        "",
        f"The task map from [huggingface.co/tasks](https://huggingface.co/tasks) as of **{date}**, "
        f"{snap['count']} tasks. It ships with the plugin and is refreshed with each release, so "
        "use it as it is, with no fetch needed.",
        "",
        "For each task:",
        "",
        "- **Page:** `https://huggingface.co/tasks/<id>`, the explainer, with curated models, "
        "datasets, Spaces and metrics (only for tasks marked with a page).",
        "- **Models:** `https://huggingface.co/models?pipeline_tag=<id>&sort=trending`. Swap the sort "
        "for `downloads`, `likes`, `created` or `modified`. Add `&search=<word>` or "
        "`&library=<lib>` to narrow it.",
        "- **Datasets:** `https://huggingface.co/datasets?task_categories=task_categories:<id>`. Note the "
        "prefix: dataset filters carry it, model filters mostly don't. \"none\" means the Hub has no dataset "
        "category for that task.",
        "- **Narrowing** (library, language, app, provider, model type, size, licence): build the URL with "
        "`hub-search-urls` / `scripts/hub-url.py`, which knows each parameter's prefix and how values combine.",
        "- **API:** `https://huggingface.co/api/models?pipeline_tag=<id>&sort=trendingScore&limit=50`, "
        "or `python3 \"${CLAUDE_PLUGIN_ROOT}/scripts/hf-tasks.py\" models <id>`.",
        "",
        "## Is this map out of date?",
        "",
        "Re-read it live with `python3 \"${CLAUDE_PLUGIN_ROOT}/scripts/hf-tasks.py\" taxonomy --refresh` "
        "(see `hf-tasks`) when any of these holds:",
        "",
        "- the user says so;",
        "- a model's `pipeline_tag` isn't listed here;",
        "- no task below fits the need;",
        f"- this map is more than about three months old (it is dated {date}).",
        "",
        "A live read is saved in your data folder, and later reads use it.",
        "",
        "## Task groups (needs that span tasks)",
        "",
        "| Group | Tasks | For |",
        "| --- | --- | --- |",
    ]
    for name, g in groups.items():
        lines.append(f"| `{name}` | " + ", ".join(f"`{t}`" for t in g["tasks"]) + f" | {short(g.get('about'), 90)} |")
    lines += ["", "Search a whole group: `hf-tasks.py models <group> --sort trending`. For speech-to-text, use "
              "`transcription-model-research`.", ""]
    by = {}
    for t in snap["tasks"]:
        by.setdefault(t.get("category"), []).append(t)
    order = [c for c in CATS if c in by] + [c for c in by if c not in CATS]
    for c in order:
        lines += [f"## {CATS.get(c, c)}", "", "| Task | Page | Models | Datasets | What it does |", "| --- | --- | --- | --- | --- |"]
        for t in sorted(by[c], key=lambda x: x["id"]):
            page = f"[page](https://huggingface.co/tasks/{t['id']})" if t.get("has_page") else "none"
            models = f"[models](https://huggingface.co/models?pipeline_tag={t['id']}&sort=trending)"
            dsu = ds.get(t["id"])
            dcell = f"[datasets]({dsu}&sort=trending)" if dsu else "none"
            lines.append(f"| `{t['id']}` | {page} | {models} | {dcell} | {short(t.get('summary')) or t.get('label', '')} |")
        lines.append("")
    lines += [
        "## Data storage",
        "",
        "Reads nothing and writes nothing. This file is generated by `scripts/build-task-directory.py` "
        "from `data/tasks-snapshot.json` and `data/hf-urls/hf-urls.json`.",
        "",
    ]
    return "\n".join(lines)


def main():
    old = json.loads(SNAP.read_text()) if SNAP.exists() else None
    if "--offline" in sys.argv:
        snap = old
    else:
        snap = hft.live()
        SNAP.write_text(json.dumps(snap, indent=1))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(render(snap))
    diff = {}
    if old and snap is not old:
        o = {t["id"]: t for t in old["tasks"]}
        n = {t["id"]: t for t in snap["tasks"]}
        diff = {"added": sorted(set(n) - set(o)), "removed": sorted(set(o) - set(n)),
                "changed": sorted(k for k in set(n) & set(o)
                                  if any(n[k].get(f) != o[k].get(f) for f in hft.FIELDS))}
    print(json.dumps({"fetched": snap["fetched"], "count": snap["count"], "skill": str(OUT), **diff}, indent=1))


if __name__ == "__main__":
    main()
