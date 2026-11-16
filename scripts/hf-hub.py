#!/usr/bin/env python3
"""Hugging Face Hub repo primitives over the REST API (stdlib only).

Token: $HF_TOKEN, else ~/.cache/huggingface/token. Output is JSON on stdout.

  hf-hub.py orgs                                  owners this token can write to
  hf-hub.py exists     <dataset|model|space> <owner/name>
  hf-hub.py create     <dataset|model|space> <owner/name> <public|private> [--sdk gradio|static|docker]
                                                   (space only; default gradio)
  hf-hub.py visibility <dataset|model|space> <owner/name> <public|private>
  hf-hub.py delete     <dataset|model|space> <owner/name> --yes
  hf-hub.py collections <owner>                    owner's collections with their items
  hf-hub.py collection-new <owner> <title> <public|private> [description]
  hf-hub.py collection-add <collection-slug> <dataset|model|space|paper> <owner/name|arxiv-id> [note]
  hf-hub.py extract    <file|-|URL> [...] [--resolve]   every Hub/arXiv reference in text, Markdown, HTML or a
                                                   web page, deduplicated, in order; --resolve checks each.
                                                   Hub listing URLs (models?pipeline_tag=...&other=...) come back
                                                   separately under "searches"
  hf-hub.py related    <ref> [--limit N] [--co N]  neighbours of one model/dataset/Space/paper, by relation:
                                                   base model, derivatives (fine-tunes, quants), training data,
                                                   models trained on it, Spaces using it, repos citing a paper,
                                                   and items from other people's collections that hold it
  hf-hub.py audit      <owner|snapshot.json>     collection hygiene: empty, singletons, no description,
                                                   duplicate titles, overlapping pairs, items with no note
  hf-hub.py resolve    <url|owner/name|arxiv-id> ...  type, canonical id, exists, private, summary for each
                                                   (bare owner/name tries model, dataset, space in that order)
  hf-hub.py collection <collection-slug>          one collection: title, description, items with item_id
  hf-hub.py collection-find <dataset|model|space> <owner/name>   every collection (any owner) holding the repo
  hf-hub.py collection-item <collection-slug> <dataset|model|space> <owner/name> [--note TEXT] [--position N]
  hf-hub.py collection-remove <collection-slug> <dataset|model|space> <owner/name>
  hf-hub.py collection-update <collection-slug> [--title T] [--description D] [--public|--private] [--position N]
  hf-hub.py collection-delete <collection-slug> --yes   (the items themselves are untouched)
  hf-hub.py orphans    <owner>                     owner's repos that are in none of its collections
  hf-hub.py space-status <owner/name>              runtime stage (BUILDING, RUNNING, *_ERROR...), hardware
  hf-hub.py space-restart <owner/name> [--factory] restart; --factory rebuilds from scratch
  hf-hub.py dois       <dataset|model> <owner> [<owner> ...] [--html FILE]
                                                   public repos without a DOI, with short ids (H01, D07);
                                                   --html writes a click-through checklist of settings pages
  hf-hub.py search     <dataset|model> [words] [--filter TAG ...] [--task PIPELINE_TAG] [--sort downloads|likes|lastModified|trendingScore]
                       [--limit N] [--max-params N[M|B]]   compact candidate rows; any owner
  hf-hub.py dataset-peek <owner/name> [--config C] [--split S] [--rows N]
                                                   dataset viewer: configs, splits, row counts, features, sample rows
  hf-hub.py model-info <owner/name>               params, licence, languages, context length, base model, gating
  hf-hub.py inventory  <out-dir> [owner ...]       write models.csv, datasets.csv and spaces.csv (one row per repo) for the
                                                   given owners, default: user + orgs where the role is admin/write
  hf-hub.py audio-layout <owner/name>             dataset file tree: audio files vs parquet, verdict
                                                   parquet | loose-audio | mixed | no-audio-files
  hf-hub.py home                                  the hf-research data folder (overlay): {data_dir, rule, profile, exists}
  hf-hub.py profile                               profile.env merged with the environment, as JSON
"""
import csv, json, os, sys, urllib.parse, urllib.request, urllib.error
from pathlib import Path

API = "https://huggingface.co/api"
VIEWER = "https://datasets-server.huggingface.co"
KINDS = {"dataset": "datasets", "model": "models", "space": "spaces"}


def data_home():
    """Resolve the hf-research data folder (see shared/settings.md). Returns (path, rule)."""
    env = os.environ
    if env.get("HF_RESEARCH_HOME"):
        return Path(env["HF_RESEARCH_HOME"]).expanduser(), "HF_RESEARCH_HOME"
    if env.get("CLAUDE_USER_DATA"):
        return Path(env["CLAUDE_USER_DATA"]).expanduser() / "hf-research", "CLAUDE_USER_DATA"
    root = Path.home() / ".claude-user-data"
    if root.is_dir():
        return root / "hf-research", "~/.claude-user-data"
    xdg = Path(env.get("XDG_DATA_HOME") or Path.home() / ".local/share") / "claude-plugins"
    if xdg.is_dir():
        return xdg / "hf-research", "XDG_DATA_HOME"
    return root / "hf-research", "default"


def home():
    d, rule = data_home()
    prof = d / "profile.env"
    return {"data_dir": str(d), "rule": rule, "profile": str(prof) if prof.is_file() else None,
            "exists": d.is_dir()}


def profile():
    """profile.env (KEY=value or KEY="value", # comments) merged with HF_RESEARCH_* from the environment."""
    d, _ = data_home()
    out = {}
    f = d / "profile.env"
    if f.is_file():
        for line in f.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            k, v = k.strip(), v.strip()
            if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
                v = v[1:-1]
            elif " #" in v:
                v = v.split(" #", 1)[0].rstrip()
            out[k] = os.path.expanduser(v) if v.startswith("~") else v
    for k, v in os.environ.items():
        if k.startswith("HF_RESEARCH_") and k != "HF_RESEARCH_HOME":
            out[k] = os.path.expanduser(v) if v.startswith("~") else v
    return out


def token():
    t = os.environ.get("HF_TOKEN", "").strip()
    if not t:
        p = Path.home() / ".cache/huggingface/token"
        t = p.read_text().strip() if p.exists() else ""
    if not t:
        sys.exit(json.dumps({"error": "no token: set HF_TOKEN or run `hf auth login`"}))
    return t


def call(method, path, body=None, full_url=None, auth=True):
    req = urllib.request.Request(full_url or API + path, method=method,
                                 data=json.dumps(body).encode() if body is not None else None)
    if auth:
        req.add_header("Authorization", f"Bearer {token()}")
    if body is not None:
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            if full_url is not None or method == "GET" and "limit=" in path:
                return r.status, (parse(r.read()), r.headers.get("Link"))
            return r.status, parse(r.read())
    except urllib.error.HTTPError as e:
        # A fine-grained token can get 403 on someone else's *public* collection (seen 2026-11-17 on
        # nvidia/parakeet-asr-...; anonymous GET returned it). Retry reads once without the token.
        if method == "GET" and auth and e.code in (401, 403):
            return call(method, path, body, full_url, auth=False)
        return e.code, parse(e.read())


def parse(raw):
    # DELETE /repos/delete answers 200 with a plain-text body, not JSON.
    try:
        return json.loads(raw) if raw else {}
    except ValueError:
        return {"raw": raw.decode(errors="replace")[:500]}


def split(repo_id):
    if "/" not in repo_id:
        sys.exit(json.dumps({"error": f"repo id must be owner/name, got {repo_id!r}"}))
    return repo_id.split("/", 1)


def orgs():
    _, d = call("GET", "/whoami-v2")
    fg = d.get("auth", {}).get("accessToken", {}).get("fineGrained")
    scoped = {s["entity"]["name"]: s["permissions"] for s in (fg or {}).get("scoped", [])}
    owners = [{"owner": d["name"], "type": "user", "role": "self"}]
    owners += [{"owner": o["name"], "type": "org", "role": o.get("roleInOrg")} for o in d.get("orgs", [])]
    for o in owners:
        # A classic write token writes everywhere the user can; a fine-grained one only where scoped.
        o["token_can_write"] = ("repo.write" in scoped.get(o["owner"], [])) if fg else \
            d.get("auth", {}).get("accessToken", {}).get("role") == "write"
    return {"user": d["name"], "token": d.get("auth", {}).get("accessToken", {}).get("displayName"),
            "owners": owners}


def exists(kind, repo_id):
    code, d = call("GET", f"/{KINDS[kind]}/{repo_id}")
    out = {"repo": repo_id, "type": kind, "http": code, "exists": code == 200}
    if code == 200:
        out["private"] = d.get("private")
        out["gated"] = d.get("gated")
    elif code in (401, 404):
        out["note"] = "absent, or private and outside this token's scope"
    return out


def create(kind, repo_id, vis, sdk=None):
    owner, name = split(repo_id)
    me = orgs()["user"]
    body = {"type": kind, "name": name, "private": vis == "private"}
    if kind == "space":
        body["sdk"] = sdk or "gradio"
    if owner != me:
        body["organization"] = owner
    code, d = call("POST", "/repos/create", body)
    url = d.get("url") or f"https://huggingface.co/{'' if kind == 'model' else KINDS[kind] + '/'}{repo_id}"
    return {"repo": repo_id, "type": kind, "visibility": vis, "http": code,
            "created": code == 200, "url": url, **({"error": d.get("error")} if code != 200 else {})}


def visibility(kind, repo_id, vis):
    code, d = call("PUT", f"/{KINDS[kind]}/{repo_id}/settings", {"private": vis == "private"})
    return {"repo": repo_id, "type": kind, "visibility": vis, "http": code, "ok": code == 200,
            **({"error": d.get("error")} if code != 200 else {})}


def delete(kind, repo_id):
    owner, name = split(repo_id)
    body = {"type": kind, "name": name}
    if owner != orgs()["user"]:
        body["organization"] = owner
    code, d = call("DELETE", "/repos/delete", body)
    return {"repo": repo_id, "type": kind, "http": code, "deleted": code == 200,
            **({"error": d.get("error")} if code != 200 else {})}


def paged(path):
    # List endpoints cap a page at 100 and give the next page as a Link: <...cursor=...>; rel="next".
    out, url = [], API + path
    while url:
        _, (d, link) = call("GET", None, full_url=url)
        out += d if isinstance(d, list) else []
        url = link.split(";")[0].strip("<> ") if link and 'rel="next"' in link else None
    return out


def collections(owner):
    res = []
    for c in paged(f"/collections?owner={owner}&limit=100"):
        _, d = call("GET", f"/collections/{c['slug']}")
        res.append({"slug": c["slug"], "title": c["title"], "private": c.get("private"),
                    "description": d.get("description"), "upvotes": d.get("upvotes"),
                    "last_updated": d.get("lastUpdated"),
                    "items": [{"type": i["type"], "id": i["id"], "note": (i.get("note") or {}).get("text")}
                              for i in d.get("items", [])]})
    return {"owner": owner, "collections": res}


def collection_new(owner, title, vis, description=""):
    code, d = call("POST", "/collections", {"title": title, "namespace": owner,
                                            "private": vis == "private", "description": description})
    return {"owner": owner, "title": title, "http": code, "created": code == 200,
            "slug": d.get("slug"), **({"error": d.get("error")} if code != 200 else {})}


ITEM_KINDS = {**KINDS, "paper": "papers"}


def resolve_one(ref):
    """URL, owner/name or arXiv id -> {type, id, exists, private, summary}."""
    import re
    r = ref.strip().rstrip("/")
    r = re.sub(r"^https?://(www\.)?(huggingface\.co|hf\.co)/", "", r)
    r = re.sub(r"^https?://arxiv\.org/(abs|pdf)/", "papers/", r).removesuffix(".pdf")
    parts = r.split("/")
    if parts[0] in ("datasets", "spaces", "models", "papers"):
        kinds = [{"datasets": "dataset", "spaces": "space", "models": "model", "papers": "paper"}[parts[0]]]
        parts = parts[1:]
    elif len(parts) == 1 and re.fullmatch(r"\d{4}\.\d{4,5}(v\d+)?", parts[0]):
        kinds = ["paper"]
    else:
        kinds = ["model", "dataset", "space"]
    if kinds == ["paper"]:
        pid = re.sub(r"v\d+$", "", parts[0])
        code, d = call("GET", f"/papers/{pid}")
        return {"ref": ref, "type": "paper", "id": pid, "exists": code == 200,
                "title": d.get("title"), "summary": (d.get("summary") or "")[:300]}
    if len(parts) < 2:
        return {"ref": ref, "exists": False, "error": "need owner/name"}
    rid = "/".join(parts[:2])  # drops /tree/main, /blob/..., /discussions/...
    for k in kinds:
        code, d = call("GET", f"/{KINDS[k]}/{rid}")
        if code == 200:
            card = d.get("cardData") or {}
            return {"ref": ref, "type": k, "id": d.get("id", rid), "exists": True,
                    "private": d.get("private"), "gated": d.get("gated"),
                    "pipeline_tag": d.get("pipeline_tag"), "sdk": d.get("sdk"),
                    "pretty_name": card.get("pretty_name") or card.get("title"),
                    "description": (d.get("description") or "")[:300] or None,
                    "tags": [t for t in d.get("tags", []) if ":" not in t][:12]}
    return {"ref": ref, "id": rid, "tried": kinds, "exists": False, "http": code}


HUB_RESERVED = {"docs", "blog", "learn", "tasks", "pricing", "settings", "login", "join", "api",
                "organizations", "collections", "posts", "new", "new-dataset", "new-space", "enterprise",
                "chat", "inference-endpoints", "terms-of-service", "privacy", "search", "notifications"}


def extract(sources, do_resolve=False):
    """Pull Hub and arXiv references out of text/Markdown/HTML (files, stdin or fetched pages)."""
    import re, html as _html
    texts = []
    for s in sources:
        if s == "-":
            texts.append(sys.stdin.read())
        elif re.match(r"https?://", s):
            req = urllib.request.Request(s, headers={"User-Agent": "hf-hub.py extract"})
            with urllib.request.urlopen(req, timeout=30) as f:
                texts.append(f.read().decode("utf-8", "replace"))
        else:
            texts.append(Path(s).read_text(errors="replace"))
    text = _html.unescape("\n".join(texts))
    pat = re.compile(r"(?:https?://)?(?:www\.)?(?:huggingface\.co|hf\.co)/((?:datasets/|spaces/|models/|papers/)?[\w.-]+(?:/[\w.-]+)?)"
                     r"|arxiv\.org/(?:abs|pdf)/(\d{4}\.\d{4,5})")
    # Hub listing URLs (models?pipeline_tag=..., models?other=..., datasets?task_categories=...) are
    # search leads, not items: returned separately as {kind, params} for `search` to run.
    searches, sseen = [], set()
    for m in re.finditer(r"(?:huggingface\.co|hf\.co)/(models|datasets|spaces)\?([^\s\"'<>)\]]+)", text):
        params = {k: v for k, v in urllib.parse.parse_qsl(m.group(2)) if v}
        key = (m.group(1), tuple(sorted(params.items())))
        if params and key not in sseen:
            sseen.add(key)
            searches.append({"kind": m.group(1).rstrip("s"), "params": params,
                             "url": f"https://huggingface.co/{m.group(1)}?{urllib.parse.urlencode(params)}"})
    seen, refs = set(), []
    for m in pat.finditer(text):
        if m.group(2):
            ref = f"papers/{m.group(2)}"
        else:
            parts = m.group(1).rstrip(".").split("/")
            if parts[0] == "models":
                parts = parts[1:]
            if not parts or not parts[0]:
                continue
            head = parts[0]
            if head in HUB_RESERVED:
                continue
            if head == "papers":
                if len(parts) < 2 or not re.fullmatch(r"\d{4}\.\d{4,5}(v\d+)?", parts[1]):
                    continue
                ref = "papers/" + re.sub(r"v\d+$", "", parts[1])
            elif head in ("datasets", "spaces"):
                if len(parts) < 3:
                    continue  # bare /datasets or /datasets/<owner>: not a repo
                ref = "/".join(parts[:3])
            else:
                if len(parts) < 2:
                    continue  # profile or org page
                ref = "/".join(parts[:2])
        if ref.lower() not in seen:
            seen.add(ref.lower())
            refs.append(ref)
    items = [resolve_one(r) for r in refs] if do_resolve else refs
    return {"count": len(refs), "refs": items, "searches": searches}


def _ids(path):
    code, d = call("GET", path)
    d = d[0] if isinstance(d, tuple) else d  # call() returns (body, Link) for paged GETs
    return [x["id"] for x in d] if code == 200 and isinstance(d, list) else []


def related(ref, limit=8, co=3):
    """Neighbours of one Hub item, grouped by how they relate. No ranking beyond the Hub's own sort."""
    r = resolve_one(ref)
    if not r.get("exists"):
        return {"seed": r, "error": "not found"}
    kind, rid, out = r["type"], r["id"], {}
    q = lambda x: urllib.parse.quote(x, safe="/:")
    if kind == "model":
        _, d = call("GET", f"/models/{rid}")
        card = d.get("cardData") or {}
        base = card.get("base_model")
        out["base_model"] = base if isinstance(base, list) else ([base] if base else [])
        ds = card.get("datasets")
        out["trained_on"] = ds if isinstance(ds, list) else ([ds] if ds else [])
        out["derivatives"] = _ids(f"/models?filter=base_model:{q(rid)}&sort=downloads&limit={limit}")
        out["spaces_using"] = _ids(f"/spaces?models={q(rid)}&sort=likes&limit={limit}")
    elif kind == "dataset":
        out["models_trained_on_it"] = _ids(f"/models?filter=dataset:{q(rid)}&sort=downloads&limit={limit}")
        out["spaces_using"] = _ids(f"/spaces?datasets={q(rid)}&sort=likes&limit={limit}")
    elif kind == "space":
        _, d = call("GET", f"/spaces/{rid}")
        out["models_used"] = d.get("models", [])[:limit]
        out["datasets_used"] = d.get("datasets", [])[:limit]
    elif kind == "paper":
        out["models_citing"] = _ids(f"/models?filter=arxiv:{rid}&sort=downloads&limit={limit}")
        out["datasets_citing"] = _ids(f"/datasets?filter=arxiv:{rid}&sort=downloads&limit={limit}")
        out["spaces_citing"] = _ids(f"/spaces?filter=arxiv:{rid}&sort=likes&limit={limit}")
    if kind != "paper" and co:
        cols = []
        code, lst = call("GET", f"/collections?item={KINDS[kind]}/{q(rid)}&sort=upvotes&limit={co}")
        lst = lst[0] if isinstance(lst, tuple) else lst
        for c in (lst if code == 200 and isinstance(lst, list) else [])[:co]:
            _, full = call("GET", f"/collections/{c['slug']}")
            cols.append({"slug": c["slug"], "title": c["title"], "upvotes": c.get("upvotes"),
                         "items": [f"{i['type']}:{i['id']}" for i in full.get("items", [])
                                   if (i["type"], i["id"]) != (kind, rid)][:25]})
        out["co_collected"] = cols
    return {"seed": {"type": kind, "id": rid}, "related": out}


def audit(src):
    """Hygiene report over an owner's collections (live, or a saved `collections` JSON)."""
    import re
    data = json.loads(Path(src).read_text()) if src.endswith(".json") else collections(src)
    cols = data["collections"]
    norm = lambda t: re.sub(r"[^a-z0-9]+", " ", t.lower()).strip()
    sets = {c["slug"]: {(i["type"], i["id"]) for i in c["items"]} for c in cols}
    titles = {}
    for c in cols:
        titles.setdefault(norm(c["title"]), []).append(c["slug"])
    overlaps = []
    for i, a in enumerate(cols):
        for b in cols[i + 1:]:
            sa, sb = sets[a["slug"]], sets[b["slug"]]
            if len(sa) >= 2 and len(sb) >= 2:
                inter = len(sa & sb)
                small = min(len(sa), len(sb))
                if inter and inter / small >= 0.5:
                    overlaps.append({"a": a["title"], "b": b["title"], "shared": inter,
                                     "of_smaller": small, "a_slug": a["slug"], "b_slug": b["slug"]})
    brief = lambda c: {"title": c["title"], "slug": c["slug"], "items": len(c["items"])}
    return {
        "owner": data.get("owner"), "collections": len(cols),
        "empty": [brief(c) for c in cols if not c["items"]],
        "singletons": [brief(c) for c in cols if len(c["items"]) == 1],
        "no_description": [brief(c) for c in cols if "description" in c and not c.get("description")],
        "duplicate_titles": [v for v in titles.values() if len(v) > 1],
        "overlapping": sorted(overlaps, key=lambda o: -o["shared"]),
        "items_without_note": sum(1 for c in cols for i in c["items"] if not i.get("note")),
        "items_total": sum(len(c["items"]) for c in cols),
    }


def collection_add(slug, kind, repo_id, note=None):
    body = {"item": {"type": kind, "id": repo_id}}
    if note:
        body["note"] = note
    code, d = call("POST", f"/collections/{slug}/items", body)
    # 409 = already in the collection.
    return {"collection": slug, "repo": repo_id, "type": kind, "http": code,
            "added": code == 200, **({"error": d.get("error")} if code != 200 else {})}


def collection(slug):
    code, d = call("GET", f"/collections/{slug}")
    if code != 200:
        return {"collection": slug, "http": code, "error": d.get("error")}
    return {"slug": d["slug"], "title": d["title"], "description": d.get("description"),
            "private": d.get("private"), "owner": d.get("owner", {}).get("name"),
            "url": f"https://huggingface.co/collections/{d['slug']}",
            "items": [{"item_id": i["_id"], "type": i["type"], "id": i["id"], "position": i.get("position"),
                       "note": (i.get("note") or {}).get("text")} for i in d.get("items", [])]}


def current_slug(slug):
    # A rename changes the slug; the old one 307-redirects on GET, but PATCH/DELETE on it fail with 307.
    code, d = call("GET", f"/collections/{slug}")
    return d.get("slug", slug) if code == 200 else slug


def collection_find(kind, repo_id):
    # ?item=<plural>/<owner>/<name> lists collections from any owner that hold the repo.
    return {"repo": repo_id, "type": kind, "collections": [
        {"slug": c["slug"], "title": c["title"], "owner": c.get("owner", {}).get("name"), "private": c.get("private")}
        for c in paged(f"/collections?item={KINDS[kind]}/{repo_id}&limit=100")]}


def item_id(slug, kind, repo_id):
    # Item edits address the item's own _id, not the repo id.
    for i in collection(slug).get("items", []):
        if (i["type"], i["id"]) == (kind, repo_id):
            return i["item_id"]
    sys.exit(json.dumps({"error": f"{kind} {repo_id} is not in {slug}"}))


def collection_item(slug, kind, repo_id, note=None, position=None):
    body = {**({"note": note} if note is not None else {}), **({"position": position} if position is not None else {})}
    slug = current_slug(slug)
    code, d = call("PATCH", f"/collections/{slug}/items/{item_id(slug, kind, repo_id)}", body)
    return {"collection": slug, "repo": repo_id, "http": code, "ok": code == 200, **body,
            **({"error": d.get("error")} if code != 200 else {})}


def collection_remove(slug, kind, repo_id):
    slug = current_slug(slug)
    code, d = call("DELETE", f"/collections/{slug}/items/{item_id(slug, kind, repo_id)}")
    return {"collection": slug, "repo": repo_id, "type": kind, "http": code, "removed": code == 200,
            **({"error": d.get("error")} if code != 200 else {})}


def collection_update(slug, body):
    slug = current_slug(slug)
    code, d = call("PATCH", f"/collections/{slug}", body)
    # The slug changes with the title; the response carries the new one.
    return {"collection": slug, "http": code, "ok": code == 200, **body,
            **({"slug": (d.get("data") or d).get("slug")} if code == 200 else {"error": d.get("error")})}


def collection_delete(slug):
    slug = current_slug(slug)
    code, d = call("DELETE", f"/collections/{slug}")
    return {"collection": slug, "http": code, "deleted": code == 200,
            **({"error": d.get("error")} if code != 200 else {})}


def space_status(repo_id):
    code, d = call("GET", f"/spaces/{repo_id}/runtime")
    if code != 200:
        return {"space": repo_id, "http": code, "error": d.get("error")}
    return {"space": repo_id, "stage": d.get("stage"), "hardware": (d.get("hardware") or {}).get("current"),
            "requested_hardware": (d.get("hardware") or {}).get("requested"),
            "error": d.get("errorMessage"), "url": f"https://huggingface.co/spaces/{repo_id}"}


def space_restart(repo_id, factory=False):
    code, d = call("POST", f"/spaces/{repo_id}/restart{'?factory=true' if factory else ''}")
    return {"space": repo_id, "factory": factory, "http": code, "ok": code == 200,
            **({"error": d.get("error")} if code != 200 else {})}


def orphans(owner):
    held = {(i["type"], i["id"]) for c in collections(owner)["collections"] for i in c["items"]}
    out = []
    for kind, plural in KINDS.items():
        for r in paged(f"/{plural}?author={owner}&limit=100"):
            if (kind, r["id"]) not in held:
                out.append({"type": kind, "id": r["id"], "private": r.get("private"),
                            "created": (r.get("createdAt") or "")[:10]})
    return {"owner": owner, "orphans": out}


def dois(kind, owners, html_out=None):
    # A minted DOI shows as a "doi:10.57967/hf/<n>" tag on the repo (checked 2026-10-25). Private
    # repos can't have one, so they are left out. Ids are owner initial + position by creation
    # date, so they stay put while the owner only adds repos (a deleted repo shifts later ids).
    res = []
    for owner in owners:
        rs = sorted(paged(f"/{KINDS[kind]}?author={owner}&limit=100&full=true"), key=lambda r: r.get("createdAt") or "")
        pub = [r for r in rs if not r.get("private")]
        missing = [r for r in pub if not any(t.startswith("doi:") for t in r.get("tags", []))]
        res.append({"owner": owner, "public": len(pub), "with_doi": len(pub) - len(missing),
                    "missing": [{"ref": f"{owner[0].upper()}{i:02d}", "id": r["id"], "gated": bool(r.get("gated")),
                                 "settings": f"https://huggingface.co/{'datasets/' if kind == 'dataset' else ''}{r['id']}/settings"}
                                for i, r in enumerate(missing, 1)]})
    if html_out:
        Path(html_out).write_text(doi_html(kind, res))
    return {"type": kind, "owners": res, **({"html": html_out} if html_out else {})}


def doi_html(kind, res):
    import html, datetime
    e = html.escape
    secs = "".join(
        f"<h2>{e(o['owner'])} <small>{len(o['missing'])} of {o['public']} public {kind}s without a DOI</small></h2><table>"
        + "".join(f'<tr><td><input type=checkbox data-id="{e(m["id"])}"></td><td class=r>{m["ref"]}</td>'
                  f'<td><a href="{m["settings"]}" target=_blank>{e(m["id"].split("/")[1])}</a>'
                  f'{" <span class=g>gated</span>" if m["gated"] else ""}</td></tr>' for m in o["missing"])
        + "</table>" for o in res)
    js = ("const k='hf-doi-done',s=new Set(JSON.parse(localStorage.getItem(k)||'[]')),b=[...document.querySelectorAll('input')];"
          "const u=()=>{document.getElementById('c').textContent=`Done: ${b.filter(i=>i.checked).length} of ${b.length}.`};"
          "b.forEach(i=>{i.checked=s.has(i.dataset.id);i.onchange=()=>{i.checked?s.add(i.dataset.id):s.delete(i.dataset.id);"
          "localStorage.setItem(k,JSON.stringify([...s]));u()}});"
          "document.querySelectorAll('td a').forEach(a=>a.addEventListener('click',()=>{const i=a.closest('tr').querySelector('input');"
          "if(!i.checked){i.checked=true;i.onchange()}}));u();")
    return (f"<!doctype html><meta charset=utf-8><title>Hub {kind}s without a DOI</title><style>"
            "body{font:15px system-ui;max-width:760px;margin:2em auto;padding:0 1em}td{padding:.2em .5em}"
            ".r{font:13px ui-monospace,monospace;color:#666}small{color:#888;font-size:.8em}"
            ".g{background:#fde68a;border-radius:4px;padding:0 .4em;font-size:.8em}"
            "tr:has(input:checked) a{text-decoration:line-through;color:#999}#c{color:#888}</style>"
            f"<h1>Hugging Face {kind}s without a DOI</h1><p>Checked {datetime.date.today()}. Public repos only "
            "(private ones can't have a DOI). Each name opens the repo's Settings page. A DOI is permanent: the repo can "
            "then no longer be deleted, renamed, transferred or made private. Ticks are saved in this browser. "
            f"<span id=c></span></p>{secs}<script>{js}</script>")


def get(url):
    # Absolute-URL GET for search and the dataset viewer; returns (status, data).
    code, res = call("GET", None, full_url=url)
    return code, res[0] if isinstance(res, tuple) else res


def params_of(m):
    st = m.get("safetensors") or {}
    return st.get("total")


def size_arg(v):
    v = v.upper()
    mult = {"K": 1e3, "M": 1e6, "B": 1e9}.get(v[-1])
    return int(float(v[:-1]) * mult) if mult else int(v)


def search(kind, words, filters, task=None, sort="downloads", limit=20, max_params=None):
    # Traps (custom-model-planning/references/hub-search-recipes.md, re-checked 2026-10-25):
    # on models a language is a bare tag (filter=en), on datasets it is language:en;
    # num_parameters does not bound size, so max_params is applied here from safetensors.total.
    q = [("sort", sort), ("direction", "-1"), ("limit", str(limit if not max_params else min(limit * 5, 100)))]
    if words:
        q.append(("search", words))
    if task and kind == "model":
        q.append(("pipeline_tag", task))
    elif task:
        filters = filters + [f"task_categories:{task}"]
    q += [("filter", f) for f in filters]
    fields = ["downloads", "likes", "cardData", "tags", "lastModified", "gated"]
    fields += ["safetensors", "pipeline_tag"] if kind == "model" else ["description"]
    q += [("expand[]", f) for f in fields]
    code, d = get(f"{API}/{KINDS[kind]}?" + urllib.parse.urlencode(q))
    if code != 200 or not isinstance(d, list):
        return {"http": code, "error": d}
    rows = []
    for m in d:
        card, tags = m.get("cardData") or {}, m.get("tags") or []
        langs = card.get("language") or [t.split(":", 1)[1] for t in tags if t.startswith("language:")]
        langs = [langs] if isinstance(langs, str) else langs
        row = {"id": m["id"], "downloads": m.get("downloads"), "likes": m.get("likes"),
               "license": card.get("license") or next((t[8:] for t in tags if t.startswith("license:")), None),
               "languages": langs[:8] + (["+%d more" % (len(langs) - 8)] if len(langs) > 8 else []),
               "gated": m.get("gated"), "modified": (m.get("lastModified") or "")[:10]}
        if kind == "model":
            n = params_of(m)
            if max_params and (n is None or n > max_params):
                continue
            row.update(params=n, pipeline=m.get("pipeline_tag"))
        else:
            row["size"] = next((t[16:] for t in tags if t.startswith("size_categories:")), None)
            row["tasks"] = [t.split(":", 1)[1] for t in tags if t.startswith("task_categories:")]
            row["about"] = " ".join((m.get("description") or "").split())[:200]
        rows.append(row)
    return {"query": [f"{k}={v}" for k, v in q if k != "expand[]"], "count": len(rows[:limit]), "results": rows[:limit]}


def dataset_peek(repo_id, config=None, split=None, n=5):
    ds = urllib.parse.quote(repo_id)
    code, sp = get(f"{VIEWER}/splits?dataset={ds}")
    if code != 200:
        return {"dataset": repo_id, "http": code, "viewer": False, "error": sp.get("error")}
    splits = sp.get("splits", [])
    _, info = get(f"{VIEWER}/size?dataset={ds}")
    sizes = {(s["config"], s["split"]): s.get("num_rows") for s in info.get("size", {}).get("splits", [])}
    config = config or splits[0]["config"]
    split = split or next((s["split"] for s in splits if s["config"] == config and s["split"] == "train"),
                          next(s["split"] for s in splits if s["config"] == config))
    code, fr = get(f"{VIEWER}/first-rows?dataset={ds}&config={urllib.parse.quote(config)}&split={urllib.parse.quote(split)}")
    clip = lambda v: v[:400] + "…" if isinstance(v, str) and len(v) > 400 else v
    return {"dataset": repo_id, "viewer": True,
            "splits": [{"config": s["config"], "split": s["split"], "rows": sizes.get((s["config"], s["split"]))}
                       for s in splits],
            "sampled": {"config": config, "split": split},
            "features": {f["name"]: f["type"].get("dtype") or f["type"].get("_type") for f in fr.get("features", [])},
            "rows": [{k: clip(v) for k, v in r["row"].items()} for r in fr.get("rows", [])[:n]],
            **({"error": fr.get("error")} if code != 200 else {})}


def model_info(repo_id):
    code, m = get(f"{API}/models/{repo_id}")
    if code != 200:
        return {"model": repo_id, "http": code, "error": m.get("error")}
    card = m.get("cardData") or {}
    _, cfg = get(f"https://huggingface.co/{repo_id}/resolve/main/config.json")
    cfg = cfg if isinstance(cfg, dict) else {}
    ctx = next((cfg[k] for k in ("max_position_embeddings", "n_positions", "max_seq_len", "seq_length") if k in cfg), None)
    langs = card.get("language") or []
    langs = [langs] if isinstance(langs, str) else langs
    return {"model": repo_id, "params": params_of(m), "pipeline": m.get("pipeline_tag"),
            "library": m.get("library_name"), "architectures": cfg.get("architectures"),
            "license": card.get("license"), "gated": m.get("gated"),
            "languages": langs if len(langs) <= 20 else langs[:20] + ["+%d more" % (len(langs) - 20)],
            "context": ctx, "base_model": card.get("base_model"),
            "downloads": m.get("downloads"), "likes": m.get("likes"),
            "modified": (m.get("lastModified") or "")[:10],
            "formats": sorted({t for t in m.get("tags", []) if t in ("onnx", "gguf", "safetensors", "transformers.js", "mlx")})}


def tagval(tags, prefix):
    return ";".join(t[len(prefix):] for t in tags if t.startswith(prefix))


INV_COMMON = ["id", "owner", "owner_type", "name", "visibility", "gated", "created", "last_modified",
              "downloads", "likes", "license", "doi"]
INV_EXTRA = {"model": ["pipeline_tag", "library", "base_model"],
             "dataset": ["modalities", "formats", "task_categories", "size_category"],
             "space": ["sdk"]}
INV_TAIL = ["sha"]  # head commit at export time (the list API carries it); last column so field numbers stay put


def inventory(out_dir, owners=None):
    # One full=true list call per owner and kind. The dataset list carries no file list (siblings),
    # so the audio-layout command is still needed per dataset (checked 2026-10-30).
    if not owners:
        owners = [o["owner"] for o in orgs()["owners"] if o["role"] in ("self", "admin", "write")]
    me = orgs()["user"]
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    counts = {}
    for kind in ("model", "dataset", "space"):
        rows = []
        for owner in owners:
            for r in paged(f"/{KINDS[kind]}?author={owner}&limit=100&full=true"):
                tags = r.get("tags") or []
                row = {"id": r["id"], "owner": owner, "owner_type": "user" if owner == me else "org",
                       "name": r["id"].split("/", 1)[1], "visibility": "private" if r.get("private") else "public",
                       "gated": r.get("gated") or "", "created": (r.get("createdAt") or "")[:10],
                       "last_modified": (r.get("lastModified") or "")[:10], "downloads": r.get("downloads"),
                       "likes": r.get("likes"), "license": tagval(tags, "license:"), "doi": tagval(tags, "doi:")}
                if kind == "model":
                    bm = (r.get("cardData") or {}).get("base_model") or ""
                    row.update(pipeline_tag=r.get("pipeline_tag") or "", library=r.get("library_name") or "",
                               base_model=";".join(bm) if isinstance(bm, list) else bm)
                elif kind == "space":
                    row.update(sdk=r.get("sdk") or "")
                else:
                    row.update(modalities=tagval(tags, "modality:"), formats=tagval(tags, "format:"),
                               task_categories=tagval(tags, "task_categories:"),
                               size_category=tagval(tags, "size_categories:"))
                row["sha"] = r.get("sha") or ""
                rows.append(row)
        rows.sort(key=lambda x: (x["owner"].lower(), x["name"].lower()))
        with open(out / f"{KINDS[kind]}.csv", "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=INV_COMMON + INV_EXTRA[kind] + INV_TAIL)
            w.writeheader()
            w.writerows(rows)
        counts[KINDS[kind]] = len(rows)
    return {"dir": str(out), "owners": owners, "counts": counts,
            "files": [str(out / f"{KINDS[k]}.csv") for k in ("model", "dataset", "space")]}


AUDIO_EXT = {".wav", ".mp3", ".flac", ".ogg", ".opus", ".m4a", ".aac", ".webm", ".aiff", ".aif"}


def audio_layout(repo_id):
    tree = paged(f"/datasets/{repo_id}/tree/main?recursive=true")
    if not tree:
        code, d = call("GET", f"/datasets/{repo_id}")
        return {"dataset": repo_id, "http": code, "error": d.get("error") or "empty tree"}
    files = [t for t in tree if t.get("type") == "file"]
    ext = lambda f: os.path.splitext(f["path"])[1].lower()
    audio = [f for f in files if ext(f) in AUDIO_EXT]
    # Audio the dataset card links to (an intro clip, a demo) is a card asset, not data: it stays a file.
    card = ""
    if any(f["path"] == "README.md" for f in files):
        req = urllib.request.Request(f"https://huggingface.co/datasets/{repo_id}/resolve/main/README.md")
        req.add_header("Authorization", f"Bearer {token()}")
        with urllib.request.urlopen(req, timeout=30) as r:
            card = r.read().decode(errors="replace")
    assets = [f["path"] for f in audio if f["path"] in card]
    audio = [f for f in audio if f["path"] not in assets]
    parquet = [f for f in files if ext(f) == ".parquet"]
    audio_dirs = sorted({os.path.dirname(f["path"]) for f in audio})
    # audiofolder metadata sits in an audio file's directory or one of its parents.
    meta = [f["path"] for f in files if os.path.basename(f["path"]) in ("metadata.jsonl", "metadata.csv")
            and any(d == os.path.dirname(f["path"]) or d.startswith(os.path.dirname(f["path"]) + "/")
                    or os.path.dirname(f["path"]) == "" for d in audio_dirs)] if audio else []
    verdict = ("mixed" if audio and parquet else "loose-audio" if audio else
               "parquet" if parquet else "no-audio-files")
    return {"dataset": repo_id, "verdict": verdict, "files": len(files),
            "audio_files": len(audio), "audio_bytes": sum(f.get("size") or 0 for f in audio),
            "card_assets": assets, "audio_ext": sorted({ext(f) for f in audio}), "audio_dirs": audio_dirs[:20],
            "audiofolder_metadata": meta, "parquet_files": [f["path"] for f in parquet][:20],
            "other_files": sorted(f["path"] for f in files if f not in audio and f not in parquet)[:30]}


def opt(a, flag):
    return a[a.index(flag) + 1] if flag in a and a.index(flag) + 1 < len(a) else None


def main(a):
    if not a or a[0] in ("-h", "--help"):
        sys.exit(__doc__)
    cmd, rest = a[0], a[1:]
    if cmd == "home":
        r = home()
    elif cmd == "profile":
        r = profile()
    elif cmd == "orgs":
        r = orgs()
    elif cmd == "dois" and len(rest) >= 2 and rest[0] in ("dataset", "model"):
        html_out = rest[rest.index("--html") + 1] if "--html" in rest else None
        r = dois(rest[0], [x for x in rest[1:] if x not in ("--html", html_out)], html_out)
    elif cmd in ("collections", "orphans") and rest:
        r = (collections if cmd == "collections" else orphans)(rest[0])
    elif cmd == "collection-new" and len(rest) >= 3 and rest[2] in ("public", "private"):
        r = collection_new(rest[0], rest[1], rest[2], " ".join(rest[3:]))
    elif cmd == "related" and rest:
        r = related(rest[0], int(opt(rest, "--limit") or 8), int(opt(rest, "--co") or 3))
    elif cmd == "audit" and rest:
        r = audit(rest[0])
    elif cmd == "extract" and rest:
        r = extract([x for x in rest if x != "--resolve"], "--resolve" in rest)
    elif cmd == "resolve" and rest:
        r = [resolve_one(x) for x in rest]
    elif cmd == "collection-add" and len(rest) >= 3 and rest[1] in ITEM_KINDS:
        r = collection_add(rest[0], rest[1], rest[2], " ".join(rest[3:]) or None)
    elif cmd == "collection" and rest:
        r = collection(rest[0])
    elif cmd == "collection-find" and len(rest) >= 2 and rest[0] in KINDS:
        r = collection_find(rest[0], rest[1])
    elif cmd == "collection-item" and len(rest) >= 3 and rest[1] in KINDS:
        r = collection_item(rest[0], rest[1], rest[2], opt(rest, "--note"),
                            int(opt(rest, "--position")) if "--position" in rest else None)
    elif cmd == "collection-remove" and len(rest) >= 3 and rest[1] in KINDS:
        r = collection_remove(rest[0], rest[1], rest[2])
    elif cmd == "collection-update" and rest:
        body = {k: opt(rest, f"--{k}") for k in ("title", "description") if f"--{k}" in rest}
        if "--public" in rest or "--private" in rest:
            body["private"] = "--private" in rest
        if "--position" in rest:
            body["position"] = int(opt(rest, "--position"))
        r = collection_update(rest[0], body) if body else sys.exit(__doc__)
    elif cmd == "collection-delete" and rest:
        if "--yes" not in rest:
            sys.exit("collection-delete is permanent: pass --yes")
        r = collection_delete(rest[0])
    elif cmd == "search" and rest and rest[0] in ("dataset", "model"):
        vals = {opt(rest, f) for f in ("--task", "--sort", "--limit", "--max-params")}
        filters = [rest[i + 1] for i, x in enumerate(rest[:-1]) if x == "--filter"]
        words = " ".join(x for x in rest[1:] if not x.startswith("--") and x not in vals and x not in filters)
        r = search(rest[0], words, filters, opt(rest, "--task"), opt(rest, "--sort") or "downloads",
                   int(opt(rest, "--limit") or 20), size_arg(opt(rest, "--max-params")) if "--max-params" in rest else None)
    elif cmd == "dataset-peek" and rest:
        r = dataset_peek(rest[0], opt(rest, "--config"), opt(rest, "--split"), int(opt(rest, "--rows") or 5))
    elif cmd == "inventory" and rest:
        r = inventory(rest[0], rest[1:])
    elif cmd == "audio-layout" and rest:
        r = audio_layout(rest[0])
    elif cmd == "model-info" and rest:
        r = model_info(rest[0])
    elif cmd == "space-status" and rest:
        r = space_status(rest[0])
    elif cmd == "space-restart" and rest:
        r = space_restart(rest[0], "--factory" in rest)
    else:
        if len(rest) < 2 or rest[0] not in KINDS:
            sys.exit(__doc__)
        kind, repo_id = rest[0], rest[1]
        if cmd == "exists":
            r = exists(kind, repo_id)
        elif cmd in ("create", "visibility"):
            if len(rest) < 3 or rest[2] not in ("public", "private"):
                sys.exit("visibility must be public or private")
            if cmd == "create":
                r = create(kind, repo_id, rest[2], rest[rest.index("--sdk") + 1] if "--sdk" in rest else None)
            else:
                r = visibility(kind, repo_id, rest[2])
        elif cmd == "delete":
            if "--yes" not in rest:
                sys.exit("delete is permanent: pass --yes")
            r = delete(kind, repo_id)
        else:
            sys.exit(__doc__)
    print(json.dumps(r, indent=2))


if __name__ == "__main__":
    main(sys.argv[1:])
