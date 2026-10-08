# Notion — one-time setup

`/setup` walks you through this conversationally. This file is the manual
version, and the reference for when something breaks.

**Why Notion at all.** The two skills need somewhere durable to keep the state
of every posting: found, selected, built, sent. Notion is a reasonable place for
that because you can also read and edit it on your phone. If you only want to
tailor résumés by hand, you can skip this entire file — `./build.sh` needs none
of it.

**Why scripts instead of the MCP tools.** Bulk reads and writes through MCP push
every row through the conversation, and a run writing ~95 rows can consume a
third of a session in JSON going up and an equally large confirmation coming
back. The same rows through `notion_push.py` cost one summary line. The MCP
Notion tools stay available and are still the right choice for ad-hoc questions
("what's in the tracker for Acme?").

---

## 1. Create the integration

1. Go to **notion.so/my-integrations** → **New integration**.
2. Name it something you'll recognise — `resume-pipeline`.
3. Associated workspace: the one you want the tables in.
4. Capabilities: **Read content**, **Update content**, **Insert content**.
   It does not need user information.
5. Copy the **Internal Integration Secret** (it starts `ntn_`).

## 2. Make a page to hold the table, and connect it

Create a page in that workspace — call it **Jobs**. Then, on that page:

**⋯ (top right) → Connections → Connect to → `resume-pipeline`**

The table gets created as a child of this page, so connecting the parent
covers it by inheritance.

Keep the page URL. Step 4 needs it.

## 3. Put the token where the scripts can read it

**Never paste the token into a Claude conversation, and never pass it as a
command-line argument** — it would land in your shell history and in the
transcript.

Preferred — add to **`~/.zshenv`** (not `~/.zshrc`):

```sh
export NOTION_TOKEN='ntn_...'
```

then `source ~/.zshenv`, or open a new terminal tab.

> ### It has to be `.zshenv`. This is the one that catches people.
>
> Claude Code's Bash tool spawns a **non-interactive** zsh, and zsh only reads
> `.zshrc` for interactive shells. A token in `.zshrc` works perfectly when you
> type commands yourself and is invisible to every script Claude runs — so the
> pipeline fails with "no Notion token found" while `echo $NOTION_TOKEN` in your
> own terminal looks completely fine.
>
> ```
> zsh -c   →  .zshrc NOT sourced,  .zshenv sourced
> zsh -lc  →  .zshrc NOT sourced,  .zshenv sourced
> ```
>
> On bash, the equivalent is `~/.bashrc` vs `~/.bash_profile` — put it somewhere
> a non-interactive shell will read.

Alternative — a file, which the scripts refuse to read unless it's locked down:

```sh
printf '%s' 'ntn_...' > pipeline/.notion-token
chmod 600 pipeline/.notion-token
```

> ⚠️ A token file syncs wherever the repo syncs. If this repo lives in a cloud
> drive, the token goes to that provider's servers and to every device on the
> account. **The environment variable does not.** Prefer the env var. If you use
> the file anyway, `.gitignore` already excludes it — but treat the token as
> compromised the day you stop trusting that sync, and rotate it from
> notion.so/my-integrations.

## 4. Create the table

```sh
python3 pipeline/notion_bootstrap.py --parent "<your Jobs page URL>"
```

This reads `pipeline/notion_schema.json`, creates **Application Tracker
(postings)** under that page, writes `pipeline/notion_config.json`, and verifies.

Useful flags:

```sh
python3 pipeline/notion_bootstrap.py --parent "<url>" --dry-run   # say what would happen
python3 pipeline/notion_bootstrap.py --verify                     # check an existing setup
```

It is safe to re-run: a table already recorded and still reachable is kept, not
duplicated.

If it reports `HTTP 404: Could not find page`, the integration isn't connected to
that page — redo step 2.

## 5. Verify end to end

```sh
python3 pipeline/notion_pull.py --out-dir /tmp/notion-check --queue
```

Expect something like:

```
tracker     0 rows  ->  /tmp/notion-check/tracker.json   [data_source endpoint]

standing queue
  (empty)
```

Zero rows is correct on a fresh setup. If you later get a row count that looks
far too low, that's a partial read and a blocker — say so rather than working
from it.

## 6. Add your source URLs

Notion holds your tracker, not your search list. `/jobscan` looks only at the
URLs under `sources.urls` in `config.json` — a saved Trackr or Jorb AI search,
for instance:

```json
"urls": [{"name": "Trackr", "url": "https://app.the-trackr.com/uk-tech/summer-internships"}]
```

A role that is not reachable from one of those pages never appears.

---

## Usage reference

### Read

```sh
# the tracker, plus the standing queue and any closed-but-open rows
python3 pipeline/notion_pull.py --out-dir "$SCRATCH" --queue --stale 2026-09-24

# just the tracker
python3 pipeline/notion_pull.py --out-dir "$SCRATCH" --table tracker
```

Pagination is internal and loops to exhaustion — `notion_pull.py` cannot return a
partial table, which is the failure a 100-row page cap otherwise causes silently.

### Write

```sh
# create rows (jobscan step 6)
python3 pipeline/notion_push.py --table tracker \
    --create "$SCRATCH/new_rows.json" --receipts "$SCRATCH/receipts.json"

# check payloads against the live schema without writing
python3 pipeline/notion_push.py --table tracker --create rows.json --dry-run

# set a status (resume-build step 8)
python3 pipeline/notion_push.py --table tracker --update \
  '{"page":"https://www.notion.so/<id>","properties":{"Status":"Ready to submit"}}'
```

`--create` input is a JSON array of:

```json
[{"properties": {"Company": "...", "Role": "...", "Status": "Discovered",
                 "Score": 65.2, "Location": "London", "Cycle": "Summer",
                 "Min Degree": "BSc", "Requires": "[\"CV\"]",
                 "Source": "[\"Trackr\"]", "Link": "https://...",
                 "date:Opened:start": "2026-09-14", "date:Opened:is_datetime": 0},
  "content": "optional page body — eligibility notes, JD caveats"}]
```

### The two guarantees that matter

**Unknown property names raise.** A typo'd column is a hard error listing the
real column names, not a silently dropped field.

**Writes are resumable, never duplicated.** Each successful create is appended to
`--receipts` immediately, keyed by `rank.py`'s `canonical_key()`. Re-running the
same `--create` with the same receipts file skips what already exists. A run that
dies at row 60 of 95 resumes; it does not double-write.

Nothing is recorded in the local ledger until Notion confirms the row, and the
ordering rule in `rank.py`'s docstring holds: **receipts first, then
`--commit-seen`**, using the key list `notion_push.py` prints.

---

## On reading through views vs. querying directly

A common and sensible rule is "read the tracker through its view, never through
a raw query" — because a stale query that misses a row you just promoted is the
whole failure the queue is meant to prevent.

These scripts call the same public REST API that the Notion UI and the MCP *view*
mode both read from, so they see what a view sees. Two things keep that intact:

1. **The tracker this pipeline reads is queried unfiltered**, so a direct
   data-source query returns the same set a default view shows. **If you add a
   filter to a view and start relying on it, that equivalence breaks** — the
   scripts still read everything, which for dedupe is what you want.
2. **Pagination is not the caller's responsibility.** `query_all()` loops the
   cursor internally and raises rather than returning a short read.

## Changing the schema

`pipeline/notion_schema.json` is the definition. Column **names** are
load-bearing — both skills and `rank.py` refer to them by name, so renaming one
means renaming it in the skills too. Adding a column is safe; the scripts ignore
what they don't know about.

If you add a column after bootstrapping, add it in Notion and in the schema file,
then `--verify` to confirm they match.
