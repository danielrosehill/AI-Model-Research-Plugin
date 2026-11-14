#!/usr/bin/env python3
"""Gated Hugging Face repos, from the requester's side. Stdlib only. Prints JSON.

  gated.py check <repo> [--type model|dataset]   do I have access? (GET /api/<type>s/<repo>/auth-check)
  gated.py form  <repo> [--type model|dataset]   gate mode, prompt and form fields, each field
                                                  pre-filled from the profile where a value fits
  gated.py check-many <repo> <repo> ...           check several at once

check: 200 = access granted (or not gated); 403 = gated and not granted (or still pending);
401 = no or bad token; 404 = no such repo (or private).
Requesting access has no API: the form is submitted in a browser logged in as the user.
"""
import json
import os
import pathlib
import re
import sys
import urllib.error
import urllib.request

API = "https://huggingface.co/api"
PREFIX = "HF_RESEARCH_ACCESS_"
# form label patterns -> profile key suffix
FIELD_KEYS = [
    (r"first\s*name|given\s*name", "FIRST_NAME"),
    (r"last\s*name|family\s*name|surname", "LAST_NAME"),
    (r"^name$|full\s*name|your\s*name", "FULL_NAME"),
    (r"birth", "DATE_OF_BIRTH"),
    (r"country|location|where.*based", "COUNTRY"),
    (r"affiliation|organi[sz]ation|company|institution|employer", "AFFILIATION"),
    (r"job|title|role|position|occupation", "JOB_TITLE"),
    (r"e-?mail", "EMAIL"),
    (r"intended\s*use|use\s*case|purpose|how.*(use|plan)|why", "INTENDED_USE"),
    (r"website|homepage|url", "WEBSITE"),
]


def data_dir():
    env, home = os.environ, pathlib.Path.home()
    if env.get("HF_RESEARCH_HOME"):
        return pathlib.Path(env["HF_RESEARCH_HOME"]).expanduser()
    if env.get("CLAUDE_USER_DATA"):
        return pathlib.Path(env["CLAUDE_USER_DATA"]).expanduser() / "hf-research"
    if (home / ".claude-user-data").is_dir():
        return home / ".claude-user-data" / "hf-research"
    xdg = pathlib.Path(env.get("XDG_DATA_HOME") or home / ".local/share") / "claude-plugins"
    if xdg.is_dir():
        return xdg / "hf-research"
    return home / ".claude-user-data" / "hf-research"


def profile():
    vals = {}
    f = data_dir() / "profile.env"
    if f.exists():
        for line in f.read_text().splitlines():
            m = re.match(r"\s*([A-Z0-9_]+)\s*=\s*(.*)$", line)
            if m and not line.lstrip().startswith("#"):
                v = m.group(2).strip()
                if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
                    v = v[1:-1]
                vals[m.group(1)] = os.path.expanduser(v)
    vals.update({k: v for k, v in os.environ.items() if k.startswith("HF_RESEARCH_")})
    return vals


def token():
    if os.environ.get("HF_TOKEN"):
        return os.environ["HF_TOKEN"]
    p = pathlib.Path(os.environ.get("HF_HOME", "~/.cache/huggingface")).expanduser() / "token"
    return p.read_text().strip() if p.exists() else None


def call(path, auth=True):
    req = urllib.request.Request(f"{API}/{path}", headers={"User-Agent": "hf-research"})
    t = token() if auth else None
    if t:
        req.add_header("Authorization", f"Bearer {t}")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            body = r.read().decode()
            return r.status, (json.loads(body) if body.strip().startswith(("{", "[")) else body)
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        try:
            body = json.loads(body)
        except ValueError:
            pass
        return e.code, body


def args_type(a):
    t = "model"
    if "--type" in a:
        t = a[a.index("--type") + 1]
        a = [x for i, x in enumerate(a) if x != "--type" and (i == 0 or a[i - 1] != "--type")]
    return a, t


def page(repo, t):
    return f"https://huggingface.co/{'datasets/' if t == 'dataset' else ''}{repo}"


def check(repo, t):
    code, body = call(f"{t}s/{repo}/auth-check")
    status = {200: "granted", 403: "not-granted", 401: "no-token", 404: "not-found"}.get(code, "error")
    out = {"repo": repo, "type": t, "http": code, "access": status, "page": page(repo, t)}
    if code != 200:
        out["detail"] = body.get("error") if isinstance(body, dict) else str(body)[:200]
    if not token():
        out["note"] = "no token found: set HF_TOKEN or run `hf auth login`"
    return out


def form(repo, t):
    code, info = call(f"{t}s/{repo}")
    if code != 200:
        return {"repo": repo, "http": code, "error": info}
    card = info.get("cardData") or {}
    prof = profile()
    fields = []
    for label, spec in (card.get("extra_gated_fields") or {}).items():
        kind = spec if isinstance(spec, str) else spec.get("type", "text")
        f = {"label": label, "type": kind}
        if isinstance(spec, dict) and spec.get("options"):
            f["options"] = [o if isinstance(o, str) else o.get("label", o.get("value")) for o in spec["options"]]
        if kind == "ip_location":
            f["fill"] = None
            f["note"] = "filled by Hugging Face from your IP; nothing to enter"
        elif kind == "checkbox":
            f["fill"] = None
            f["note"] = "a consent box: the user must agree to it explicitly"
        else:
            for pat, key in FIELD_KEYS:
                if re.search(pat, label, re.I):
                    v = prof.get(PREFIX + key)
                    if key == "FULL_NAME" and not v and prof.get(PREFIX + "FIRST_NAME"):
                        v = f"{prof.get(PREFIX + 'FIRST_NAME')} {prof.get(PREFIX + 'LAST_NAME', '')}".strip()
                    f["profile_key"] = PREFIX + key
                    f["fill"] = v or None
                    break
            else:
                f["fill"] = None
            if f.get("options") and f["fill"] and f["fill"] not in f["options"]:
                f["note"] = f"profile value {f['fill']!r} is not an option: pick the closest with the user"
        fields.append(f)
    return {
        "repo": repo, "type": t, "gated": info.get("gated"), "page": page(repo, t),
        "access": check(repo, t)["access"],
        "heading": card.get("extra_gated_heading"), "button": card.get("extra_gated_button_content"),
        "prompt": card.get("extra_gated_prompt"), "fields": fields,
        "missing": [f["label"] for f in fields if f.get("fill") is None and f["type"] not in ("ip_location", "checkbox")],
        "consents": [f["label"] for f in fields if f["type"] == "checkbox"],
    }


def main():
    a = sys.argv[1:]
    if not a or a[0] in ("-h", "--help"):
        print(__doc__)
        return
    a, t = args_type(a)
    cmd, rest = a[0], a[1:]
    if cmd == "check" and rest:
        print(json.dumps(check(rest[0], t), indent=1))
    elif cmd == "check-many" and rest:
        print(json.dumps([check(r, t) for r in rest], indent=1))
    elif cmd == "form" and rest:
        print(json.dumps(form(rest[0], t), indent=1))
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()
