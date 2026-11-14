#!/usr/bin/env python3
"""Favorite Models <-> Model Notes <-> Model Notebook.

Run with:  uv run --no-project --with huggingface_hub python3 model-notes.py <cmd> ...
(needs HF_TOKEN or `hf auth login`; settings come from HF_RESEARCH_* env vars or profile.env in the data folder)

  add <owner/model> --use-case TEXT --summary TEXT [--notes TEXT | --notes-file PATH]
      [--tags a,b] [--date YYYY-MM-DD]
      Adds the model to the favourites collection (HF_RESEARCH_FAVOURITES_COLLECTION, default 'Favorite Models') (if not there; the collection note is the
      summary), then appends one row to <HF_RESEARCH_MODEL_NOTES_DATASET> notes.jsonl. `added` is the
      date of the model's first row (kept for later notes), `noted` is today or --date.
  list [owner/model]      Print rows as JSON lines.
  remove-last <owner/model> --yes   Drop that model's newest row (fix a bad entry).

If HF_RESEARCH_MODEL_NOTES_SPACE is set, that Space reads notes.jsonl live; nothing to redeploy.
"""
import argparse, datetime, json, os, sys, tempfile, urllib.request
from pathlib import Path

from huggingface_hub import HfApi, hf_hub_download
from huggingface_hub.utils import EntryNotFoundError

def _data_folder():
    """Resolution order from shared/settings.md."""
    env = os.environ
    if env.get("HF_RESEARCH_HOME"):
        return Path(env["HF_RESEARCH_HOME"]).expanduser()
    if env.get("CLAUDE_USER_DATA"):
        return Path(env["CLAUDE_USER_DATA"]).expanduser() / "hf-research"
    ud = Path.home() / ".claude-user-data"
    if ud.exists():
        return ud / "hf-research"
    xdg = Path(env.get("XDG_DATA_HOME") or Path.home() / ".local/share") / "claude-plugins"
    return xdg / "hf-research" if xdg.exists() else ud / "hf-research"


def load_profile():
    """Read profile.env (KEY=value or KEY="value", ~ expanded). The environment wins over the file."""
    p = _data_folder() / "profile.env"
    if not p.is_file():
        return
    for line in p.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        k, v = k.strip(), v.strip()
        if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
            v = v[1:-1]
        elif " #" in v:
            v = v.split(" #", 1)[0].strip()
        if k.startswith("HF_RESEARCH_"):
            os.environ.setdefault(k, os.path.expanduser(v))


def hf_token():
    t = os.environ.get("HF_TOKEN", "").strip()
    if not t:
        p = Path.home() / ".cache/huggingface/token"
        t = p.read_text().strip() if p.exists() else ""
    if not t:
        sys.exit("no token: set HF_TOKEN or run `hf auth login`")
    return t


def whoami():
    req = urllib.request.Request("https://huggingface.co/api/whoami-v2",
                                 headers={"Authorization": "Bearer " + hf_token()})
    return json.load(urllib.request.urlopen(req, timeout=30))


def default_owner():
    return os.environ.get("HF_RESEARCH_DEFAULT_OWNER") or whoami()["name"]


load_profile()
FILE = "notes.jsonl"
api = HfApi(token=hf_token())
OWNER = default_owner()
DATASET = os.environ.get("HF_RESEARCH_MODEL_NOTES_DATASET") or f"{OWNER}/Model-Notes"
FAV_TITLE = os.environ.get("HF_RESEARCH_FAVOURITES_COLLECTION") or "Favorite Models"
_coll_slug = None


def collection_slug():
    """Slug of the favourites collection: found by title under the default owner, created (public) if absent."""
    global _coll_slug
    if _coll_slug is None:
        for c in api.list_collections(owner=OWNER):
            if c.title == FAV_TITLE:
                _coll_slug = c.slug
                break
        else:
            _coll_slug = api.create_collection(FAV_TITLE, namespace=OWNER, private=False).slug
    return _coll_slug


def load():
    try:
        p = hf_hub_download(DATASET, FILE, repo_type="dataset", force_download=True)
    except EntryNotFoundError:
        return []
    with open(p) as f:
        return [json.loads(l) for l in f if l.strip()]


def save(rows, msg):
    with tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False) as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    api.upload_file(path_or_fileobj=f.name, path_in_repo=FILE, repo_id=DATASET,
                    repo_type="dataset", commit_message=msg)
    os.unlink(f.name)


def hub_facts(model):
    info = api.model_info(model, expand=["pipeline_tag", "library_name", "cardData", "safetensors"])
    lic = (info.card_data or {}).get("license") if info.card_data else None
    params = None
    if info.safetensors and info.safetensors.total:
        n = info.safetensors.total
        params = f"{n/1e9:.1f}B" if n >= 1e9 else f"{n/1e6:.0f}M"
    return {"pipeline_tag": info.pipeline_tag, "library": info.library_name,
            "license": lic, "params": params}


def ensure_in_collection(model, note):
    slug = collection_slug()
    coll = api.get_collection(slug)
    if any(i.item_type == "model" and i.item_id == model for i in coll.items):
        return False
    api.add_collection_item(slug, item_id=model, item_type="model",
                            note=(note or "")[:500], exists_ok=True)
    return True


def cmd_add(a):
    notes = open(a.notes_file).read().strip() if a.notes_file else (a.notes or "")
    facts = hub_facts(a.model)  # also fails fast on a wrong id
    rows = load()
    today = a.date or datetime.date.today().isoformat()
    prior = [r for r in rows if r["model"] == a.model]
    added_now = ensure_in_collection(a.model, a.summary)
    row = {
        "model": a.model,
        "url": f"https://huggingface.co/{a.model}",
        "added": prior[0]["added"] if prior else today,
        "noted": today,
        "use_case": a.use_case,
        "summary": a.summary,
        "notes": notes,
        "tags": [t.strip() for t in (a.tags or "").split(",") if t.strip()],
        **facts,
    }
    rows.append(row)
    save(rows, f"Note on {a.model}: {a.use_case}")
    print(json.dumps({"collection_added": added_now, "notes_for_model": len(prior) + 1,
                      "row": row}, ensure_ascii=False, indent=1))


def cmd_list(a):
    for r in load():
        if not a.model or r["model"] == a.model:
            print(json.dumps(r, ensure_ascii=False))


def cmd_remove_last(a):
    if not a.yes:
        sys.exit("pass --yes")
    rows = load()
    idx = [i for i, r in enumerate(rows) if r["model"] == a.model]
    if not idx:
        sys.exit(f"no rows for {a.model}")
    dropped = rows.pop(idx[-1])
    save(rows, f"Remove last note on {a.model}")
    print(json.dumps(dropped, ensure_ascii=False))


p = argparse.ArgumentParser()
s = p.add_subparsers(dest="cmd", required=True)
x = s.add_parser("add"); x.add_argument("model"); x.add_argument("--use-case", required=True)
x.add_argument("--summary", required=True); x.add_argument("--notes"); x.add_argument("--notes-file")
x.add_argument("--tags"); x.add_argument("--date"); x.set_defaults(f=cmd_add)
x = s.add_parser("list"); x.add_argument("model", nargs="?"); x.set_defaults(f=cmd_list)
x = s.add_parser("remove-last"); x.add_argument("model"); x.add_argument("--yes", action="store_true")
x.set_defaults(f=cmd_remove_last)
a = p.parse_args(); a.f(a)
