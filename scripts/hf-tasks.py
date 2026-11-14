#!/usr/bin/env python3
"""Hugging Face Tasks: the Hub's task taxonomy (https://huggingface.co/tasks), read live.

Stdlib only. No token needed (public endpoints); HF_TOKEN is sent if set.

Two live sources, merged:
  /api/models-tags-by-type  -> every pipeline_tag the Hub filters models by, with its
                               category (subType: nlp, cv, audio, multimodal, rl, other)
  /api/tasks                -> the tasks that have a task page: summary, curated models,
                               datasets, Spaces, metrics, libraries
A pipeline tag can exist without a task page (has_page: false) and the reverse is rare.

Default: no network. The map shipped with the plugin (data/tasks-snapshot.json, refreshed with
each plugin release) or your newer saved snapshot is used. --refresh reads live, saves a
snapshot in ${CLAUDE_PLUGIN_DATA}/tasks/ (else <data folder>/cache/tasks/) and diffs it with the previous map. Optional auto-refresh:
set HF_RESEARCH_TASKS_MAX_AGE_DAYS. If a live read fails, the saved or shipped map is used.
Every output says which source it used and when that was fetched.

Commands (all print JSON):
  taxonomy [--refresh]       every task: id, label, category, has_page, summary, page URL,
                             models URL; on a live read also added/removed/changed
  groups                     named task groups (needs that span tasks), built-in + yours
  group <name>               one group: its tasks, search words and notes
  find <words...>            tasks ranked by match on id, label and summary
  task <id>                  one task in full: summary, curated models/datasets/Spaces,
                             libraries, metrics, plus live model count
  models <id>[,<id>...] [--sort trending|downloads|likes|created|modified] [--limit N]
              [--search Q] [--library L] [--min-downloads N]
                             live Hub models for one or more tasks (merged, deduped,
                             each model lists the tasks it was found under); a group name
                             works in place of the ids
"""
import datetime
import json
import os
import pathlib
import re
import sys
import urllib.parse
import urllib.request

API = "https://huggingface.co/api"
SORTS = {"trending": "trendingScore", "downloads": "downloads", "likes": "likes",
         "created": "createdAt", "modified": "lastModified"}


def token():
    t = os.environ.get("HF_TOKEN")
    if t:
        return t
    p = pathlib.Path(os.environ.get("HF_HOME", "~/.cache/huggingface")).expanduser() / "token"
    return p.read_text().strip() if p.exists() else None


def get(path, params=None):
    url = f"{API}/{path}"
    if params:
        url += "?" + urllib.parse.urlencode(params, doseq=True)
    req = urllib.request.Request(url, headers={"User-Agent": "hf-research-tasks"})
    t = token()
    if t:
        req.add_header("Authorization", f"Bearer {t}")
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)


def data_dir():
    if os.environ.get("HF_RESEARCH_HOME"):
        return pathlib.Path(os.environ["HF_RESEARCH_HOME"]).expanduser()
    if os.environ.get("CLAUDE_USER_DATA"):
        return pathlib.Path(os.environ["CLAUDE_USER_DATA"]).expanduser() / "hf-research"
    home = pathlib.Path.home()
    if (home / ".claude-user-data").is_dir():
        return home / ".claude-user-data" / "hf-research"
    xdg = pathlib.Path(os.environ.get("XDG_DATA_HOME", home / ".local/share")) / "claude-plugins"
    if xdg.is_dir():
        return xdg / "hf-research"
    return home / ".claude-user-data" / "hf-research"


PLUGIN = pathlib.Path(__file__).resolve().parent.parent
BUILTIN = PLUGIN / "data" / "tasks-snapshot.json"
FIELDS = ("label", "category", "has_page", "summary")


def now():
    return datetime.datetime.now(datetime.timezone.utc)


def live():
    tags = get("models-tags-by-type")["pipeline_tag"]
    pages = get("tasks")
    out = {}
    for t in tags:
        p = pages.get(t["id"], {})
        out[t["id"]] = {"id": t["id"], "label": t.get("label"), "category": t.get("subType"),
                        "has_page": t["id"] in pages, "summary": p.get("summary")}
    for tid, p in pages.items():  # task pages with no pipeline tag
        if tid not in out:
            out[tid] = {"id": tid, "label": p.get("label"), "category": None,
                        "has_page": True, "summary": p.get("summary")}
    for tid, t in out.items():
        p = pages.get(tid, {})
        t["page"] = f"https://huggingface.co/tasks/{tid}" if t["has_page"] else None
        t["models_url"] = f"https://huggingface.co/models?pipeline_tag={tid}&sort=trending"
        t["curated"] = {k: p.get(k, []) for k in ("models", "datasets", "spaces", "metrics", "libraries", "widgetModels")}
    tasks = sorted(out.values(), key=lambda x: (x["category"] or "~", x["id"]))
    return {"fetched": now().isoformat(timespec="seconds"), "count": len(tasks), "tasks": tasks}


def cache_dir():
    """Rebuildable snapshots are a cache: Claude Code's ${CLAUDE_PLUGIN_DATA} when set,
    else <data folder>/cache (Public Plugin, Private Overlay standard)."""
    if os.environ.get("CLAUDE_PLUGIN_DATA"):
        return pathlib.Path(os.environ["CLAUDE_PLUGIN_DATA"]) / "tasks"
    return data_dir() / "cache" / "tasks"


def snapshots():
    d = cache_dir()
    return sorted(d.glob("tasks-*.json")) if d.is_dir() else []


def load_snapshot(f):
    return json.loads(pathlib.Path(f).read_text())


def age_days(snap):
    return (now() - datetime.datetime.fromisoformat(snap["fetched"])).total_seconds() / 86400


def profile_value(key, default=None):
    """Environment wins, then profile.env in the data folder."""
    if os.environ.get(key):
        return os.environ[key]
    f = data_dir() / "profile.env"
    if f.exists():
        for line in f.read_text().splitlines():
            m = re.match(r"\s*" + key + r"\s*=\s*(.*)$", line)
            if m:
                return m.group(1).strip().strip("\"'")
    return default


def taxonomy(refresh=False):
    """Return (snapshot, meta). Default: no network. The newest of your saved snapshots and the
    map shipped with the plugin is used. Live only with refresh=True, or when
    HF_RESEARCH_TASKS_MAX_AGE_DAYS is set and that newest map is older."""
    snaps = snapshots()
    cands = [(load_snapshot(f), str(f), "cache") for f in snaps[-1:]]
    if BUILTIN.exists():
        cands.append((load_snapshot(BUILTIN), str(BUILTIN), "builtin"))
    cands.sort(key=lambda c: c[0]["fetched"], reverse=True)
    max_age = profile_value("HF_RESEARCH_TASKS_MAX_AGE_DAYS")
    if cands and not refresh:
        snap, f, src = cands[0]
        if not max_age or age_days(snap) <= float(max_age):
            return snap, {"source": src, "file": f, "fetched": snap["fetched"],
                          "age_days": round(age_days(snap), 1)}
    try:
        snap = live()
    except Exception as e:  # offline, rate-limited, API change
        for f, src in ([(snaps[-1], "cache-stale")] if snaps else []) + [(BUILTIN, "builtin")]:
            if pathlib.Path(f).exists():
                old = load_snapshot(f)
                return old, {"source": src, "file": str(f), "fetched": old["fetched"],
                             "age_days": round(age_days(old), 1), "live_error": str(e)[:200]}
        raise
    meta = {"source": "live", "fetched": snap["fetched"]}
    d = cache_dir()
    d.mkdir(parents=True, exist_ok=True)
    f = d / f"tasks-{datetime.date.today().isoformat()}.json"
    prev = [p for p in snaps if p != f]
    base = load_snapshot(prev[-1]) if prev else (load_snapshot(BUILTIN) if BUILTIN.exists() else None)
    f.write_text(json.dumps(snap, indent=1))
    meta["file"] = str(f)
    if base:
        old = {t["id"]: t for t in base["tasks"]}
        new = {t["id"]: t for t in snap["tasks"]}
        meta["changes_since"] = base["fetched"]
        meta["added"] = sorted(set(new) - set(old))
        meta["removed"] = sorted(set(old) - set(new))
        meta["changed"] = sorted(k for k in set(new) & set(old)
                                 if any(new[k].get(x) != old[k].get(x) for x in FIELDS))
    return snap, meta


def cmd_taxonomy(args):
    snap, meta = taxonomy(refresh="--refresh" in args)
    tasks = [{k: t[k] for k in ("id", "label", "category", "has_page", "summary", "page", "models_url")}
             for t in snap["tasks"]]
    print(json.dumps({**meta, "count": len(tasks), "tasks": tasks}, indent=1))


def load_groups():
    groups = {}
    for f, origin in ((PLUGIN / "data" / "task-groups.json", "builtin"),
                      (data_dir() / "task-groups.json", "user")):
        if f.exists():
            for name, g in json.loads(f.read_text()).items():
                groups[name] = {**g, "origin": origin}
    return groups


def cmd_groups(args):
    g = load_groups()
    print(json.dumps({k: {"tasks": v["tasks"], "about": v.get("about"), "origin": v["origin"]}
                      for k, v in sorted(g.items())}, indent=1))


def cmd_group(args):
    if not args:
        sys.exit("group needs a name; see: groups")
    g = load_groups().get(args[0])
    if not g:
        sys.exit(f"no group {args[0]!r}; see: groups")
    print(json.dumps({"name": args[0], **g}, indent=1))


def cmd_find(args):
    words = [w.lower() for w in re.split(r"[\s\-_/]+", " ".join(args)) if w]
    if not words:
        sys.exit("find needs words, e.g. find video to video")
    snap, meta = taxonomy()
    scored = []
    groups = [{"group": k, "tasks": v["tasks"], "about": v.get("about")} for k, v in load_groups().items()
              if any(w in (k + " " + " ".join(v.get("words", []))).lower() for w in words)]
    for t in snap["tasks"]:
        idw = t["id"].split("-")
        hay = " ".join(filter(None, [t["id"], t["label"], t["summary"]])).lower()
        s = sum(3 * idw.count(w) + hay.count(w) for w in words)
        if t["id"] == "-".join(words):
            s += 100
        if s:
            scored.append({"score": s, **{k: t[k] for k in ("id", "label", "category", "summary", "page")}})
    print(json.dumps({"source": meta["source"], "fetched": meta["fetched"], "groups": groups,
                      "tasks": sorted(scored, key=lambda x: -x["score"])[:12]}, indent=1))


def cmd_task(args):
    if not args:
        sys.exit("task needs an id, e.g. task video-to-video")
    tid = args[0]
    snap, meta = taxonomy(refresh="--refresh" in args)
    t = next((x for x in snap["tasks"] if x["id"] == tid), None)
    if not t:
        sys.exit(f"unknown task {tid!r}; run: find {tid.replace('-', ' ')}")
    try:
        n = len(get("models", {"pipeline_tag": tid, "limit": 1000, "expand[]": "pipeline_tag"}))
        count = n if n < 1000 else "1000+"
    except Exception as e:
        count = f"unavailable ({str(e)[:80]})"
    print(json.dumps({"source": meta["source"], "fetched": meta["fetched"], **t,
                      "live_model_count": count}, indent=1))


def cmd_models(args):
    if not args:
        sys.exit("models needs a task id")
    spec, rest = args[0], args[1:]
    groups = load_groups()
    tids = groups[spec]["tasks"] if spec in groups else spec.split(",")
    opt = {"--sort": "trending", "--limit": "25", "--search": None, "--library": None,
           "--min-downloads": "0"}
    i = 0
    while i < len(rest):
        if rest[i] in opt and i + 1 < len(rest):
            opt[rest[i]] = rest[i + 1]
            i += 2
        else:
            sys.exit(f"bad option {rest[i]!r}")
    params = {"sort": SORTS.get(opt["--sort"], opt["--sort"]),
              "direction": -1, "limit": int(opt["--limit"]),
              "expand[]": ["downloads", "likes", "trendingScore", "createdAt", "lastModified",
                           "library_name", "tags", "pipeline_tag", "gated"]}
    if opt["--search"]:
        params["search"] = opt["--search"]
    if opt["--library"]:
        params["library"] = opt["--library"]
    rows = {}
    for tid in tids:
        for m in get("models", {**params, "pipeline_tag": tid}):
            if (m.get("downloads") or 0) < int(opt["--min-downloads"]):
                continue
            if m["id"] in rows:
                rows[m["id"]]["tasks"].append(tid)
                continue
            tags = m.get("tags", [])
            rows[m["id"]] = {
                "id": m["id"], "url": f"https://huggingface.co/{m['id']}", "tasks": [tid],
                "downloads_30d": m.get("downloads"), "likes": m.get("likes"),
                "trending": m.get("trendingScore"), "library": m.get("library_name"),
                "created": (m.get("createdAt") or "")[:10], "modified": (m.get("lastModified") or "")[:10],
                "gated": m.get("gated"),
                "license": next((t[8:] for t in tags if t.startswith("license:")), None),
                "base_model": [t.split(":", 1)[1] for t in tags if t.startswith("base_model:") and t.count(":") == 1],
                "languages": [t for t in tags if len(t) == 2 and t.isalpha()][:12],
            }
    key = {"trending": "trending", "downloads": "downloads_30d", "likes": "likes",
           "created": "created", "modified": "modified"}.get(opt["--sort"], "trending")
    out = sorted(rows.values(), key=lambda r: r.get(key) or 0, reverse=True)
    print(json.dumps({"tasks": tids, "sort": opt["--sort"], "count": len(out), "models": out}, indent=1))


def main():
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help", "help"):
        print(__doc__)
        return
    cmd, args = sys.argv[1], sys.argv[2:]
    fn = {"taxonomy": cmd_taxonomy, "find": cmd_find, "task": cmd_task, "models": cmd_models,
          "groups": cmd_groups, "group": cmd_group}.get(cmd)
    if not fn:
        sys.exit(f"unknown command {cmd!r}; see --help")
    fn(args)


if __name__ == "__main__":
    main()
