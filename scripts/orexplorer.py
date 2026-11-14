#!/usr/bin/env python3
"""orexplorer: an unofficial thin wrapper around OpenRouter's public model data, for model research.

Read-only discovery: what models exist, what each supports, which have a batch variant, what's
new, what's trending, who serves a model, and benchmark scores. It never runs inference. All
endpoints used are public and need no API key.

Output is JSON on stdout by default (built for agents); add --table for a human view.

Sources (checked 2026-11-14):
  GET https://openrouter.ai/api/v1/models                      catalogue (documented API)
  GET https://openrouter.ai/api/v1/models/<id>/endpoints       providers for one model (documented API)
  GET https://openrouter.ai/rankings                           trending, benchmarks and performance:
      undocumented. The page embeds react-query state in its Next.js flight payload with
      queryKeys ["rankings","models",{"view":"week"}], ["rankings","benchmarks"] and
      ["rankings","performance"]. If OpenRouter changes the page, these three commands break
      and report it; the catalogue commands don't depend on it.

Not affiliated with OpenRouter.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

VERSION = "1.1"
BASE = "https://openrouter.ai"
UA = {"User-Agent": f"orexplorer/{VERSION}", "Accept": "application/json"}
CACHE = Path(os.environ.get("OREXPLORER_CACHE", Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache")) / "orexplorer"))
TTL = int(os.environ.get("OREXPLORER_TTL", "600"))  # seconds

# Capability flag -> predicate over a catalogue record. Kept in one table so `capabilities`
# can list the vocabulary and agents don't have to guess flag names.
def _params(m): return set(m.get("supported_parameters") or [])
def _inp(m): return set((m.get("architecture") or {}).get("input_modalities") or [])
def _out(m): return set((m.get("architecture") or {}).get("output_modalities") or [])

CAPS = {
    "tools":            ("tool / function calling",          lambda m: "tools" in _params(m)),
    "parallel-tools":   ("parallel tool calls",              lambda m: "parallel_tool_calls" in _params(m)),
    "structured":       ("structured outputs (JSON schema)", lambda m: "structured_outputs" in _params(m)),
    "json":             ("response_format / JSON mode",      lambda m: "response_format" in _params(m)),
    "reasoning":        ("reasoning / thinking",             lambda m: "reasoning" in _params(m) or bool(m.get("reasoning"))),
    "reasoning-off":    ("reasoning model where thinking is optional", lambda m: bool(m.get("reasoning")) and not m["reasoning"].get("mandatory", False)),
    "no-reasoning":     ("no reasoning / plain instruct",    lambda m: not m.get("reasoning") and "reasoning" not in _params(m)),
    "reasoning-effort": ("reasoning_effort parameter",       lambda m: "reasoning_effort" in _params(m)),
    "logprobs":         ("logprobs",                         lambda m: "logprobs" in _params(m)),
    "web-search":       ("web_search_options",               lambda m: "web_search_options" in _params(m)),
    "seed":             ("seed (reproducibility)",           lambda m: "seed" in _params(m)),
    "vision":           ("image input",                      lambda m: "image" in _inp(m)),
    "audio-in":         ("audio input",                      lambda m: "audio" in _inp(m)),
    "video-in":         ("video input",                      lambda m: "video" in _inp(m)),
    "file-in":          ("file / PDF input",                 lambda m: "file" in _inp(m)),
    "text-out":         ("text output",                      lambda m: "text" in _out(m)),
    "open-weights":     ("open weights (has a Hugging Face id)", lambda m: bool(m.get("hugging_face_id"))),
    "image-out":        ("image output",                     lambda m: "image" in _out(m)),
    "audio-out":        ("audio output",                     lambda m: "audio" in _out(m)),
    "video-out":        ("video output",                     lambda m: "video" in _out(m)),
    "caching":          ("prompt caching priced",            lambda m: "input_cache_read" in (m.get("pricing") or {})),
    "free":             ("free variant (:free)",             lambda m: m["id"].endswith(":free")),
}


# ---------- fetching ----------

def fetch(url: str, *, raw: bool = False, ttl: int | None = None):
    ttl = TTL if ttl is None else ttl
    key = CACHE / (re.sub(r"[^A-Za-z0-9._-]", "_", url.removeprefix(BASE)) or "root")
    if ttl > 0 and key.exists() and time.time() - key.stat().st_mtime < ttl:
        body = key.read_text()
    else:
        headers = dict(UA)
        if raw:
            headers.update({"Accept": "text/html", "User-Agent": "Mozilla/5.0 (orexplorer)"})
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=60) as r:
                body = r.read().decode()
        except urllib.error.HTTPError as e:
            die(f"HTTP {e.code} from {url}")
        except urllib.error.URLError as e:
            die(f"cannot reach {url}: {e.reason}")
        CACHE.mkdir(parents=True, exist_ok=True)
        key.write_text(body)
    return body if raw else json.loads(body)


def catalogue() -> list[dict]:
    return fetch(f"{BASE}/api/v1/models")["data"]


def rankings() -> dict:
    """Decode the react-query state embedded in /rankings. Undocumented; fails loudly."""
    html = fetch(f"{BASE}/rankings", raw=True)
    dec = json.JSONDecoder()
    chunks = []
    for m in re.finditer(r"self\.__next_f\.push\(", html):
        try:
            arr, _ = dec.raw_decode(html, m.end())
        except ValueError:
            continue
        if len(arr) > 1 and isinstance(arr[1], str):
            chunks.append(arr[1])
    flight = "".join(chunks)
    out = {}
    for m in re.finditer(r'\{"dehydratedAt"', flight):
        try:
            q, _ = dec.raw_decode(flight, m.start())
        except ValueError:
            continue
        k = q.get("queryKey") or []
        if len(k) >= 2 and k[0] == "rankings":
            out[k[1]] = (q.get("state") or {}).get("data")
    if not out:
        die("could not find rankings data in https://openrouter.ai/rankings; the page layout has "
            "probably changed. Catalogue commands still work.")
    return out


# ---------- helpers ----------

def die(msg: str, code: int = 1):
    print(json.dumps({"error": msg}), file=sys.stderr)
    sys.exit(code)


def per_m(v) -> float | None:
    """USD per token string -> USD per million tokens."""
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    return None if f < 0 else round(f * 1e6, 4)


def reasoning_mode(m) -> str:
    """none: no reasoning. optional: thinking can be switched off. mandatory: cannot."""
    rr = m.get("reasoning")
    if rr and rr.get("mandatory"):
        return "mandatory"
    if not rr and "reasoning" not in _params(m):
        return "none"
    return "optional"


def json_mode(m) -> str | None:
    return "schema" if "structured_outputs" in _params(m) else "object" if "response_format" in _params(m) else None


def peak_prices(m):
    """Highest (in, out) across time-of-day pricing overrides, or None if the price never changes."""
    o = (m.get("pricing") or {}).get("overrides") or []
    if not o:
        return None
    top = max(o, key=lambda x: float(x.get("completion") or 0))
    pk = (per_m(top.get("prompt")), per_m(top.get("completion")))
    base = (per_m(m["pricing"].get("prompt")), per_m(m["pricing"].get("completion")))
    return pk if pk != base else None


def job_tokens(a):
    """Job size from --est-in/--est-out or --items x --in-per-item/--out-per-item; (0, 0) if unset."""
    if getattr(a, "items", 0):
        return a.items * a.in_per_item, a.items * a.out_per_item
    return getattr(a, "est_in", 0) or 0, getattr(a, "est_out", 0) or 0


def job_cost(tin, tout, pin, pout):
    if pin is None or pout is None or not (tin or tout):
        return None
    return round((tin * pin + tout * pout) / 1e6, 4)


def slug_index(models):
    """Map canonical_slug (dated permaslug) and id -> public id."""
    idx = {}
    for m in models:
        idx[m["id"]] = m["id"]
        if m.get("canonical_slug"):
            idx.setdefault(m["canonical_slug"], m["id"].split(":")[0])
    return idx


def summarise(m: dict, byid: dict, job=(0, 0)) -> dict:
    p = m.get("pricing") or {}
    arch = m.get("architecture") or {}
    base = m["id"].split(":")[0]
    pin, pout = per_m(p.get("prompt")), per_m(p.get("completion"))
    unpriced = pin == 0 and pout == 0 and not m["id"].endswith(":free")
    if unpriced:  # e.g. google/lyria-*: billed per request/output, not per token
        pin = pout = None
    bm = byid.get(f"{base}:batch")
    bi, bo = (per_m(bm["pricing"].get("prompt")), per_m(bm["pricing"].get("completion"))) if bm else (None, None)
    pk = peak_prices(m)
    row = {
        "id": m["id"],
        "name": m.get("name"),
        "created": time.strftime("%Y-%m-%d", time.gmtime(m.get("created") or 0)),
        "context": m.get("context_length"),
        "max_output": (m.get("top_provider") or {}).get("max_completion_tokens"),
        "input_per_m": pin,
        "output_per_m": pout,
        "token_priced": not unpriced and pin is not None,
        "image_in_per_m": per_m(p.get("image")),
        "input": arch.get("input_modalities"),
        "output": arch.get("output_modalities"),
        "caps": [c for c, (_, f) in CAPS.items() if c != "free" and f(m)],
        "reasoning_mode": reasoning_mode(m),
        "json_mode": json_mode(m),
        "batch": f"{base}:batch" in byid,
        "batch_input_per_m": bi,
        "batch_output_per_m": bo,
        "peak_input_per_m": pk[0] if pk else None,
        "peak_output_per_m": pk[1] if pk else None,
        "expires": m.get("expiration_date"),
        "knowledge_cutoff": m.get("knowledge_cutoff"),
        "hf": m.get("hugging_face_id") or None,
    }
    if job[0] or job[1]:
        row["est_sync"] = job_cost(*job, pin, pout)
        row["est_batch"] = job_cost(*job, bi, bo)
        row["est_peak"] = job_cost(*job, *pk) if pk else None
    return row


def emit(rows, args, cols=None):
    if not getattr(args, "table", False):
        json.dump(rows, sys.stdout, indent=None if getattr(args, "compact", False) else 1, ensure_ascii=False)
        print()
        return
    if isinstance(rows, dict):
        rows = [rows]
    if not rows:
        print("(no results)")
        return
    cols = cols or list(rows[0])
    def cell(v):
        if isinstance(v, list): return ",".join(map(str, v))
        if v is None: return "-"
        return str(v)
    w = {c: min(48, max(len(c), *(len(cell(r.get(c))) for r in rows))) for c in cols}
    print("  ".join(c.ljust(w[c]) for c in cols))
    for r in rows:
        print("  ".join(cell(r.get(c))[: w[c]].ljust(w[c]) for c in cols))


# ---------- commands ----------

def price_key(job):
    wi, wo = job if (job[0] or job[1]) else (1, 3)  # default: bulk-ish, output-heavy mix
    return lambda r: (r["input_per_m"] is None, wi * (r["input_per_m"] or 0) + wo * (r["output_per_m"] or 0))


def cmd_models(a):
    models = catalogue()
    byid = {m["id"]: m for m in models}
    ids = byid
    job = job_tokens(a)
    out = []
    if "free" in a.cap:
        a.cap = [c for c in a.cap if c != "free"]
        a.free = True
    since = time.time() - a.days * 86400 if a.days else None
    for m in models:
        mid = m["id"]
        if mid.endswith(":batch"):
            continue  # batch variants are folded into the base row's `batch` field
        if not a.free and mid.endswith(":free") and not a.include_free:
            continue
        if a.free and not mid.endswith(":free"):
            continue
        if mid.startswith("~") and not a.aliases:
            continue
        if a.q and not any(a.q.lower() in (m.get(k) or "").lower() for k in ("id", "name", "description")):
            continue
        if a.author and mid.split("/")[0] not in a.author:
            continue
        if any(not CAPS[c][1](m) for c in a.cap):
            continue
        if a.batch and f"{mid.split(':')[0]}:batch" not in ids:
            continue
        if a.min_context and (m.get("context_length") or 0) < a.min_context:
            continue
        if since and (m.get("created") or 0) < since:
            continue
        if a.no_expiring and m.get("expiration_date"):
            continue
        s = summarise(m, byid, job)
        if mid.startswith("openrouter/") and not a.aliases:
            continue  # routers (openrouter/auto, openrouter/free): not a model
        if a.max_in is not None and (s["input_per_m"] is None or s["input_per_m"] > a.max_in):
            continue
        if a.max_out is not None and (s["output_per_m"] is None or s["output_per_m"] > a.max_out):
            continue
        out.append(s)
    key = {
        "price": price_key(job),
        "context": lambda r: -(r["context"] or 0),
        "new": lambda r: r["created"],
        "name": lambda r: r["id"],
    }[a.sort]
    out.sort(key=key, reverse=(a.sort == "new"))
    total = len(out)
    out = out[: a.limit] if a.limit else out
    if a.table:
        emit(out, a, ["id", "created", "context", "input_per_m", "output_per_m", "batch"]
             + (["est_sync", "est_batch"] if job[0] or job[1] else ["caps"]))
        print(f"{total} match(es); prices US$ per 1M tokens", file=sys.stderr)
    else:
        emit({"count": total, "shown": len(out), "models": out}, a)


def cmd_model(a):
    models = catalogue()
    byid = {m["id"]: m for m in models}
    ids = byid
    hit = next((m for m in models if m["id"] == a.id or m.get("canonical_slug") == a.id), None)
    if not hit:
        near = [m["id"] for m in models if a.id.lower() in m["id"].lower()][:10]
        die(f"no model {a.id!r}" + (f"; did you mean: {', '.join(near)}" if near else ""))
    base = hit["id"].split(":")[0]
    rec = {"summary": summarise(hit, byid, job_tokens(a)), "variants": sorted(i for i in ids if i.split(":")[0] == base and i != hit["id"])}
    if not a.brief:
        rec["record"] = hit
        rec["batch_record"] = next((m for m in models if m["id"] == f"{base}:batch"), None)
    emit(rec, a)


def cmd_batch(a):
    """Every model with a :batch variant, batch vs sync price at the job's token mix."""
    models = catalogue()
    byid = {m["id"]: m for m in models}
    job = job_tokens(a)
    wi, wo = job if (job[0] or job[1]) else (1e6, 1e6)
    rows = []
    for m in models:
        if not m["id"].endswith(":batch"):
            continue
        base = m["id"].removesuffix(":batch")
        if a.terms and not any(t in base for t in a.terms):
            continue
        sync = byid.get(base)
        bi, bo = per_m(m["pricing"].get("prompt")), per_m(m["pricing"].get("completion"))
        si, so = (per_m(sync["pricing"].get("prompt")), per_m(sync["pricing"].get("completion"))) if sync else (None, None)
        cb, cs = job_cost(wi, wo, bi, bo), job_cost(wi, wo, si, so)
        cheaper = "?" if cs is None else "batch" if cb < cs else "sync" if cs < cb else "same"
        row = {"id": base, "batch_input_per_m": bi, "batch_output_per_m": bo, "input_per_m": si, "output_per_m": so,
               "cheaper": cheaper, "reasoning_mode": reasoning_mode(m), "json_mode": json_mode(m),
               "context": m.get("context_length")}
        if job[0] or job[1]:
            row["est_batch"], row["est_sync"] = job_cost(*job, bi, bo), job_cost(*job, si, so)
        rows.append(row)
    if a.dearer_only:
        rows = [r for r in rows if r["cheaper"] == "sync"]
    rows.sort(key=lambda r: (r["batch_input_per_m"] or 0) + (r["batch_output_per_m"] or 0))
    n = len(rows)
    rows = rows[: a.limit] if a.limit else rows
    if a.table:
        emit(rows, a, ["id", "batch_input_per_m", "batch_output_per_m", "input_per_m", "output_per_m", "cheaper",
                       "reasoning_mode", "json_mode"] + (["est_batch", "est_sync"] if job[0] or job[1] else []))
        print(f"{n} batch models; US$ per 1M tokens. A batch job runs on the base id via POST /api/v1/batches.",
              file=sys.stderr)
    else:
        emit({"count": n, "shown": len(rows), "note": "batch job runs on the base id via POST /api/v1/batches",
              "models": rows}, a)


def cmd_bulk(a):
    """Sync models fit for bulk work: paid, text out only, not expiring, JSON mode, reasoning can be off."""
    models = catalogue()
    byid = {m["id"]: m for m in models}
    job = job_tokens(a)
    rows = []
    for m in models:
        mid = m["id"]
        if mid.endswith((":batch", ":free")) or mid.startswith("openrouter/") or (mid.startswith("~") and not a.aliases):
            continue
        if _out(m) != {"text"} or m.get("expiration_date"):
            continue
        if reasoning_mode(m) == "mandatory" and not a.reasoning_ok:
            continue
        if json_mode(m) is None and not a.no_json:
            continue
        if a.terms and not any(t in mid for t in a.terms):
            continue
        if a.min_context and (m.get("context_length") or 0) < a.min_context:
            continue
        s = summarise(m, byid, job)
        if not s["input_per_m"] or not s["output_per_m"]:
            continue
        if s["output_per_m"] > a.max_out or (a.max_in and s["input_per_m"] > a.max_in):
            continue
        rows.append(s)
    rows.sort(key=price_key(job))
    n = len(rows)
    rows = rows[: a.limit] if a.limit else rows
    if a.table:
        emit(rows, a, ["id", "input_per_m", "output_per_m", "peak_output_per_m", "reasoning_mode", "json_mode",
                       "context", "created", "batch"] + (["est_sync", "est_peak"] if job[0] or job[1] else []))
        print(f"{n} candidates. Listing claims only: probe a shortlist before use.", file=sys.stderr)
    else:
        emit({"count": n, "shown": len(rows), "note": "listing claims only; probe a shortlist before use",
              "models": rows}, a)


def cmd_endpoints(a):
    d = fetch(f"{BASE}/api/v1/models/{a.id}/endpoints")["data"]
    rows = []
    for e in d.get("endpoints") or []:
        p = e.get("pricing") or {}
        rows.append({
            "provider": e.get("provider_name"), "tag": e.get("tag"), "quantization": e.get("quantization"),
            "context": e.get("context_length"), "max_output": e.get("max_completion_tokens"),
            "input_per_m": per_m(p.get("prompt")), "output_per_m": per_m(p.get("completion")),
            "uptime_30m": e.get("uptime_last_30m"), "status": e.get("status"),
            "params": e.get("supported_parameters"),
        })
    rows.sort(key=lambda r: (r["input_per_m"] is None, (r["input_per_m"] or 0) + (r["output_per_m"] or 0)))
    if a.table:
        emit(rows, a, ["provider", "quantization", "context", "input_per_m", "output_per_m", "uptime_30m"])
    else:
        emit({"id": d.get("id"), "providers": len(rows), "endpoints": rows}, a)


def cmd_trending(a):
    r = rankings()
    data = r.get("models")
    if not isinstance(data, list):
        die("rankings payload has no weekly model list; page layout changed")
    idx = slug_index(catalogue())
    rows = []
    for i, x in enumerate(data, 1):
        slug = x.get("model_permaslug") or x.get("variant_permaslug")
        rows.append({
            "rank": i,
            "id": idx.get(slug, slug),
            "permaslug": slug,
            "variant": x.get("variant"),
            "tokens": (x.get("total_prompt_tokens") or 0) + (x.get("total_completion_tokens") or 0),
            "requests": x.get("count"),
            "change": round(x["change"], 3) if isinstance(x.get("change"), (int, float)) else None,
            "as_of": (x.get("date") or "")[:10],
        })
    if a.rising:
        rows.sort(key=lambda r: -(r["change"] or -1e9))
    rows = rows[: a.limit] if a.limit else rows
    emit(rows if a.table else {"source": f"{BASE}/rankings (week view, undocumented)", "models": rows}, a,
         ["rank", "id", "tokens", "requests", "change"])


def cmd_benchmarks(a):
    b = rankings().get("benchmarks") or {}
    aa = {k: v for k, v in (b.get("aaData") or {}).items() if isinstance(v, list)}
    if a.list or not a.category:
        emit({"categories": sorted(aa), "source": "Artificial Analysis via openrouter.ai/rankings"}, a)
        return
    if a.category not in aa:
        die(f"unknown category {a.category!r}; have: {', '.join(sorted(aa))}")
    idx = slug_index(catalogue())
    rows = [{"rank": i, "id": idx.get(x.get("permaslug"), x.get("heuristic_openrouter_slug") or x.get("permaslug")),
             "name": x.get("aa_name"), "score": x.get("score")}
            for i, x in enumerate(aa[a.category], 1)]
    rows = rows[: a.limit] if a.limit else rows
    emit(rows, a, ["rank", "id", "score", "name"])


def cmd_performance(a):
    rows = rankings().get("performance")
    if not isinstance(rows, list):
        die("rankings payload has no performance list; page layout changed")
    idx = slug_index(catalogue())
    out = [{"id": idx.get(x.get("id"), x.get("id")), "requests": x.get("request_count"),
            "p50_latency_ms": x.get("p50_latency"), "p50_tps": x.get("p50_throughput"),
            "fastest_provider": x.get("best_throughput_provider"), "providers": x.get("provider_count")}
           for x in rows]
    if a.q:
        out = [r for r in out if a.q.lower() in r["id"].lower()]
    key = {"tps": lambda r: -(r["p50_tps"] or 0), "latency": lambda r: r["p50_latency_ms"] or 1e12,
           "requests": lambda r: -(r["requests"] or 0)}[a.sort]
    out.sort(key=key)
    out = out[: a.limit] if a.limit else out
    emit(out, a, ["id", "p50_tps", "p50_latency_ms", "requests", "fastest_provider"])


def cmd_capabilities(a):
    models = [m for m in catalogue() if not m["id"].endswith(":batch")]
    rows = [{"flag": c, "meaning": d, "models": sum(1 for m in models if f(m))} for c, (d, f) in CAPS.items()]
    rows.append({"flag": "--batch", "meaning": "has a :batch variant (OpenRouter Batch API)",
                 "models": sum(1 for m in catalogue() if m["id"].endswith(":batch"))})
    emit(rows, a, ["flag", "models", "meaning"])


def cmd_stats(a):
    models = catalogue()
    authors = {}
    for m in models:
        if m["id"].endswith((":batch", ":free")):
            continue
        authors[m["id"].split("/")[0]] = authors.get(m["id"].split("/")[0], 0) + 1
    emit({
        "total_ids": len(models),
        "batch_variants": sum(m["id"].endswith(":batch") for m in models),
        "free_variants": sum(m["id"].endswith(":free") for m in models),
        "authors": dict(sorted(authors.items(), key=lambda kv: -kv[1])),
        "fetched": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }, a)


# ---------- CLI ----------

def main(argv=None):
    global TTL
    ap = argparse.ArgumentParser(prog="orexplorer", description=__doc__.split("\n\n")[0],
                                 epilog="Unofficial. Not affiliated with OpenRouter. JSON by default; --table for humans.")
    ap.add_argument("--version", action="version", version=f"orexplorer {VERSION}")
    ap.add_argument("--no-cache", action="store_true", help=f"bypass the {TTL}s cache")
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--table", action="store_true", help="human-readable table instead of JSON")
    common.add_argument("--compact", action="store_true", help="single-line JSON")
    est = argparse.ArgumentParser(add_help=False)
    g = est.add_argument_group("job cost estimate (adds est_* fields; price sort uses this token mix)")
    g.add_argument("--est-in", type=float, default=0, help="job input tokens")
    g.add_argument("--est-out", type=float, default=0, help="job output tokens")
    g.add_argument("--items", type=int, default=0, help="item count, with --in-per-item and --out-per-item")
    g.add_argument("--in-per-item", type=float, default=0)
    g.add_argument("--out-per-item", type=float, default=0)
    sub = ap.add_subparsers(dest="cmd", required=True)

    m = sub.add_parser("models", parents=[common, est], help="filter the catalogue")
    m.add_argument("-q", help="substring in id, name or description")
    m.add_argument("--cap", action="append", default=[], choices=sorted(CAPS),
                   help="require a capability (repeatable); see `capabilities`")
    m.add_argument("--batch", action="store_true", help="only models with a :batch variant")
    m.add_argument("--author", action="append", help="provider prefix, e.g. google, deepseek (repeatable)")
    m.add_argument("--min-context", type=int)
    m.add_argument("--max-in", type=float, help="max input US$/1M tokens")
    m.add_argument("--max-out", type=float, help="max output US$/1M tokens")
    m.add_argument("--days", type=int, help="added in the last N days")
    m.add_argument("--free", action="store_true", help="only :free variants")
    m.add_argument("--include-free", action="store_true", help="include :free variants alongside paid")
    m.add_argument("--aliases", action="store_true", help="include ~ aliases and variable-price routers (openrouter/auto)")
    m.add_argument("--no-expiring", action="store_true", help="drop models with an expiration_date")
    m.add_argument("--sort", choices=["price", "context", "new", "name"], default="price",
                   help="price = input + 3x output, or the job's token mix when given (default)")
    m.add_argument("--limit", type=int, default=25, help="0 = all (default 25)")
    m.set_defaults(fn=cmd_models)

    s = sub.add_parser("model", parents=[common, est], help="one model: summary, variants, full record")
    s.add_argument("id")
    s.add_argument("--brief", action="store_true", help="summary and variants only")
    s.set_defaults(fn=cmd_model)

    bt = sub.add_parser("batch", parents=[common, est], help="models with a :batch variant: batch vs sync price, which is cheaper")
    bt.add_argument("terms", nargs="*", help="substring filters on the id")
    bt.add_argument("--dearer-only", action="store_true", help="only models where batch costs more than sync")
    bt.add_argument("--limit", type=int, default=0, help="0 = all (default)")
    bt.set_defaults(fn=cmd_batch)

    bk = sub.add_parser("bulk", parents=[common, est],
                        help="sync models fit for bulk jobs: paid, text-only out, JSON mode, reasoning can be off, not expiring")
    bk.add_argument("terms", nargs="*", help="substring filters on the id")
    bk.add_argument("--max-out", type=float, default=2.0, help="max output US$/1M (default 2)")
    bk.add_argument("--max-in", type=float, default=0)
    bk.add_argument("--min-context", type=int, default=0)
    bk.add_argument("--reasoning-ok", action="store_true", help="keep models whose reasoning cannot be switched off")
    bk.add_argument("--no-json", action="store_true", help="keep models with no JSON mode")
    bk.add_argument("--aliases", action="store_true", help="keep ~vendor/*-latest aliases (listed price unreliable)")
    bk.add_argument("--limit", type=int, default=25, help="0 = all (default 25)")
    bk.set_defaults(fn=cmd_bulk)

    e = sub.add_parser("endpoints", parents=[common], help="providers serving a model, with prices")
    e.add_argument("id")
    e.set_defaults(fn=cmd_endpoints)

    n = sub.add_parser("new", parents=[common], help="models added recently, :free variants included (models --sort new --days N --include-free)")
    n.add_argument("--days", type=int, default=7)
    n.add_argument("--limit", type=int, default=50)
    n.set_defaults(fn=lambda a: cmd_models(argparse.Namespace(
        **{**vars(m.parse_args([])), **{"days": a.days, "sort": "new", "limit": a.limit, "include_free": True,
                                        "table": a.table, "compact": a.compact}})))

    t = sub.add_parser("trending", parents=[common], help="top models by tokens this week (openrouter.ai/rankings)")
    t.add_argument("--rising", action="store_true", help="sort by week-on-week change instead of volume")
    t.add_argument("--limit", type=int, default=20)
    t.set_defaults(fn=cmd_trending)

    b = sub.add_parser("benchmarks", parents=[common], help="Artificial Analysis scores shown on /rankings")
    b.add_argument("category", nargs="?", help="e.g. intelligence; omit to list categories")
    b.add_argument("--list", action="store_true")
    b.add_argument("--limit", type=int, default=20)
    b.set_defaults(fn=cmd_benchmarks)

    p = sub.add_parser("performance", parents=[common], help="p50 latency and throughput per model")
    p.add_argument("-q", help="substring in id")
    p.add_argument("--sort", choices=["tps", "latency", "requests"], default="tps")
    p.add_argument("--limit", type=int, default=25)
    p.set_defaults(fn=cmd_performance)

    c = sub.add_parser("capabilities", parents=[common], help="list --cap flags with model counts")
    c.set_defaults(fn=cmd_capabilities)

    st = sub.add_parser("stats", parents=[common], help="catalogue size and models per author")
    st.set_defaults(fn=cmd_stats)

    a = ap.parse_args(argv)
    if a.no_cache:
        TTL = 0
    a.fn(a)


if __name__ == "__main__":
    try:
        main()
    except BrokenPipeError:
        pass
