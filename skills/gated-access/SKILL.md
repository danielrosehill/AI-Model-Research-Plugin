---
name: gated-access
description: Get access to a gated Hugging Face model or dataset. Check whether you already have it, read the gate's form and licence prompt, pre-fill the answers from your saved profile, show the filled form and ask before anything is submitted, then submit it in a logged-in browser and confirm access. Use on "request access to <model>", "accept the licence for Llama/Gemma/…", "I need access to this gated model", "do I have access to X", or when a download fails with 401/403 "restricted".
---

# Request access to a gated repo

Gated repos make you fill in a form and accept terms before you can download. The answers
are mostly the same every time (name, country, affiliation, job title), so this skill keeps
them in your profile and fills them in. **It never submits without your yes:** the form is
an agreement made in your name.

## 1. Load your settings

Find the data folder (see `shared/settings.md`: `$HF_RESEARCH_HOME`,
`$CLAUDE_USER_DATA/hf-research/`, then `~/.claude-user-data/hf-research/`). Read
`profile.env` and `gated-access.md` there if they exist. The `HF_RESEARCH_ACCESS_*` keys
hold your answers. The notes may set a default intended-use wording, or give answers for
particular publishers. With no profile, ask for each answer and offer to save them at the end.

## 2. Check first

```bash
G="${CLAUDE_PLUGIN_ROOT}/scripts/gated.py"
python3 "$G" check <owner>/<name>                  # add --type dataset for a dataset
python3 "$G" check-many <repo> <repo> ...
```

| `access` | Meaning |
| --- | --- |
| `granted` | Done. You already have access, or the repo isn't gated |
| `not-granted` | Gated, and access isn't granted yet. This includes a request that is still pending |
| `no-token` | No token. Set `HF_TOKEN` or run `hf auth login`. A fine-grained token also needs "Read access to contents of all public gated repos you can access" |
| `not-found` | No such repo, or it is private |

This calls `GET /api/{models,datasets}/<repo>/auth-check` (checked live 2026-11-13: 403 with
"not in the authorized list" before access, 200 after).

## 3. Read the form

```bash
python3 "$G" form <owner>/<name>
```

This returns the gate mode (`auto`: granted on submit; `manual`: the publisher reviews), the
publisher's prompt (licence text or terms), each field with its type, any options, and a
`fill` value taken from your profile. `missing` lists the fields with no saved answer.
`consents` lists the checkboxes. The fields come from the card's `extra_gated_fields`.

## 4. Confirm with the user

Show, in one message:

- the repo, its gate mode, and a one-line summary of the terms (link to the full prompt or
  licence, and quote anything unusual: commercial limits, attribution, use bans, data
  sharing with the publisher);
- every field with the value you will enter. For a `select`, use one of its options exactly.
  For `intended use`, write a sentence specific to this request from the conversation, or
  the default in the notes;
- the consent boxes you will tick.

Ask for any missing answer and **ask whether to submit**. Wait for a clear yes. A yes covers
this form only. Never tick a consent box or submit on your own judgement. Then offer to save
new answers to `profile.env` (never the date of birth unless the user says so).

## 5. Submit in a browser

Requesting access has no API: the form posts with your logged-in web session. Use a browser
that is logged in to huggingface.co as the user (whichever browser tool you have). Open the
repo page, open the gate form ("Agree and access repository" or the publisher's button
text), enter exactly the confirmed values, tick only the confirmed boxes and submit. Take a
snapshot of the result.

If no logged-in browser is available, give the user the page link and the values to paste.

## 6. Verify

Run `check` again. An `auto` gate should show `granted` within seconds. For `manual`, the
result is `not-granted` until the publisher decides, and Hugging Face emails the user then. Say
which case applies. Don't report success on the form's "request sent" message alone.

## Data storage

Reads `profile.env` (the `HF_RESEARCH_ACCESS_*` answers) and `gated-access.md`. With the
user's yes, writes new answers back to `profile.env`. It keeps no record of requests.
