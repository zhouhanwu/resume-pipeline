---
name: jobscan
description: Run the job-application discovery pipeline — sweep the configured sources and the Notion watch list, expand each company's board to leaf-level roles, rank them, write new ones to Notion as Discovered, and report a digest. Discovery only; it never builds a résumé or touches an application form. Use when the user says "run jobscan", "scan for jobs", "check for new postings", or triggers a scheduled run.
---

# jobscan — the discovery run

Argument: a lookback window in days. Default **7**. `/jobscan 30` widens it.

**This is the first half of a two-skill pipeline.** jobscan finds and ranks; the
user promotes what they want; `resume-build` builds and fills. This skill stops
at the digest — see step 9.

Read `profile/research-protocol.md` before starting. Its rules are binding here —
especially R1 (enumerate, don't sample), R2 (the application form is part of the
JD), R5 (a failed extraction is a blocker, not a finding) and R7 (rank, never
filter).

Anything browser-driven needs Chrome running, logged in, and the extension
granted access to the site. If a source is unreachable, **say so and raise** —
never report "no new postings" when the real answer is "I couldn't look."

---

## 0. Read the configuration

```bash
python3 -c "import json;c=json.load(open('config.json'));print(json.dumps(c['sources'],indent=1));print('lookback default 7')"
```

`config.json`'s `sources` block decides what this run sweeps. The Notion watch
list is the spine and is always on. The aggregator sources ship **disabled** —
they are UK-internship-specific and login-gated, so they are only useful to a
user who has said they use them.

**If every aggregator is off, that is a normal configuration, not a degraded
one.** Say in the digest that discovery was watch-list-only, so the user knows
coverage equals their own target list and can extend it.

## 1. Load state

**Pull both tables with one command. Do not read them through MCP.**

```bash
python3 pipeline/notion_pull.py --out-dir "$SCRATCH" --queue --stale <YYYY-MM-DD>
```

This writes `tracker.json` and `targets.json` and prints only counts, the
standing queue (step 9) and any closed-but-open rows (step 7). Reading the same
rows through MCP pushes every row through the conversation, which can cost a
third of a session on a large table. Setup lives in `pipeline/NOTION-SETUP.md`.

- Watch list → `targets.json` (the **Target Companies** table). Unfiltered, so
  take every row and apply `Watch Status = Active` yourself.
- Existing postings → `tracker.json` (the **Application Tracker** table). **This
  is the dedupe source of truth.** Pass it to `rank.py --known`. It contains
  *all* rows, not just open ones: a row at `Applied`, `Rejected` or `Abandoned`
  still means "already tracked", and re-creating it is a duplicate. `Abandoned`
  is a manual status the user sets when they've decided against a posting
  themselves — dedupe against it exactly like every other status; don't
  resurrect it as new.

**Never dedupe against a filtered view** — filtering out terminal statuses is
precisely what breaks dedupe.

**Pagination is handled inside the script and cannot be skipped.** `query_all()`
loops the cursor to exhaustion and raises rather than returning a short read. A
100-row page cap silently hiding every `Applied` row on page 2 looks like a
clean result and breaks dedupe completely. If the command exits non-zero, that
is a blocker under R5: stop and say so, never rank off a partial.

Also on disk:
- First-seen ledger: `pipeline/seen.json`. **It does not decide what is new** —
  it only preserves original discovery dates. Never hand-edit it to suppress a
  posting; the tracker decides.
- Run archive: `pipeline/runs/YYYY-MM-DD.json`, written by `rank.py` every run.

## 2. Sweep the configured discovery sources

For each enabled source in `config.sources`, sweep it to exhaustion. General
rules that apply to all of them:

- **Use the user's own saved filters exactly as they have them set.** Do not
  widen, reset or "improve" them. The filters are their curation, and changing
  them silently changes what the pipeline sees (R13).
- **Click to page 1 explicitly before sweeping.** Single-page apps restore prior
  pagination, and a sweep that assumes it starts on page 1 will miss page 1 —
  which is where the newest postings are (R14).
- **Log per-page row counts** and reconcile the unique total against the
  source's own stated count, reporting any gap (R15).
- **Include location in the dedupe key.** The same role in two cities is two
  postings, not one.
- **Apply no category filter.** Score everything that survives the lookback
  window and let the ranking sort it. A poorly-matched role landing at 22 is a
  useful signal the user can correct; one silently dropped is not (R7, R13).
- **A missing posted date is not evidence of being out of window.** Carry undated
  rows through with `opened: null` (recency scores zero) and list them in the
  digest under "undated — window unknown". A filter that requires a parseable
  date silently discards real postings.
- **Validate parsed values against their expected set** (R16). A column-misaligned
  row produces confident nonsense that passes every non-empty check, and a date
  in an unexpected format is a flag, not a null.

Record the cycle (`Summer` / `Off Cycle`) where the source states it. It is not
cosmetic — off-cycle roles get a mechanical uplift in `rank.py` because they draw
far fewer applicants.

`profile/research-protocol.md`'s "Established tool facts" has the per-ATS access
details and the two Workday quirks that each silently truncate a sweep.

## 3. Check every Active watch-list target at source

A tracker row is a company signal, never the role list. For each Active target,
branch on `ATS`:

- **API-backed** (Greenhouse, Lever, Workday, Ashby, SmartRecruiters, Workable,
  Eightfold) → hit the board directly via its JSON API. Fetch large payloads
  inside Chrome rather than with a summarising web-fetch tool, which truncates.
- **`ATS = Custom`** → **its own category, not a flavour of `Unresolved`.** The
  Board URL is already known; it just has no JSON API, so it needs a direct
  Chrome visit. Check it every run, same as the API-backed ones. Some targets
  carry a standing instruction to recheck every run — those are not optional.
- **`ATS = Unresolved`** → resolve it per the protocol's careers-page link-scan
  method. **Never guess tokens** — measured hit rate is about 1 in 8. Cache the
  result back to the Target Companies row along with `Last Checked`.

**Every category except `Unresolved` gets checked every run, no exceptions.**
API-backed and Custom targets are cheap — a known URL and one fetch — so there
is no time-budget excuse for skipping them. `Unresolved` is the only tier that
can legitimately be deferred under time pressure, and deferring it must be named
explicitly in the digest, never silently absorbed into another bucket.

## 4. Expand to leaves

**Dedupe before you click.** A posting earns a browser navigation only after it
has survived the tracker check. The sweep's table text — company, role, location,
and the URL already in the row's anchor `href` — is enough to compute
`canonical_key()` and diff against `--known` without opening anything. Only rows
that come back `is_new: true` get opened.

One posting is not one role. Open the application form and enumerate every
field; each distinct track becomes its own rankable leaf.

**This step is also where R2 gets satisfied, not the sweep.** Table text is
enough to rank a posting provisionally, but not to confirm a stated eligibility
bar or a hidden form requirement. For `is_new: true` rows, open the posting
before treating fit or eligibility as final.

**Capture the degree bar while the JD is open.** Record the *lowest*
qualification the role will accept, as `min_degree` — `BSc`, `Masters`, `PhD`, or
`Not stated`. It is the JD's floor, not its wish list: "BSc required, MSc
preferred" is `BSc`; "penultimate-year undergraduate" is `BSc`; "must be enrolled
in a PhD programme" is `PhD`. Use `Not stated` when the posting names no level —
that is the honest answer and a valid value. **Never infer a level the JD does
not state.** This is the one field table text cannot give you, which is another
reason R2 is satisfied here.

**A `canonical_key` miss is not proof a posting is new.** Tracker rows the user
created by hand have no `Link`, so the key falls back to matching normalised
company + role + location, and a sweep row phrased slightly differently won't
match even though it is the same posting. If a `Link`-less tracker row exists for
the same company, open the new-looking posting and compare by hand.

**Never fill or submit anything while indexing.** Opening a dropdown to read its
options is fine; anything that could post is not.

## 5. Rank

Build a JSON array — schema in `pipeline/rank.py`'s docstring — then:

```bash
cat postings.json | python3 pipeline/rank.py \
    --known tracker.json --today <YYYY-MM-DD> > ranked.json
```

`--known` is **required**. Without it `rank.py` refuses to run, because an
unexported tracker reads as empty, marks every posting new, and duplicates the
board. If you could not export the tracker, that is a blocked run — raise it
(R5); don't reach for `--no-known-check`.

Note the stderr line `reconcile: N Notion row(s) must exist` — step 6 has to
match it.

`rank.py` computes recency, visa and geography mechanically from `config.json`.
**You** supply two judgement values per posting, and they must be defensible:

- `fit` (0–1) — against `master-profile.md` §1 and the §5 proof-point map. §1
  already states which bucket is the owned floor and which is aspirational;
  apply that ranking without being asked (R10).
- `p_admission` (0–1) — do they clear the *stated* bars comfortably or
  marginally, what differentiates them against that firm's screen, intake size.
  The softest number in the system. **Never present it as precise.**

`eligible: false` only when a **stated** hard bar is failed — graduation year,
degree discipline, nationality or clearance. It multiplies the score by 0.1; it
never filters the row out.

**A `min_degree` above the candidate's level is one of those stated bars.** Read
the profile: a PhD floor against an undergraduate is `eligible: false`;
`Masters` is a judgement call, since some programmes take final-year
undergraduates. `BSc` and `Not stated` never imply ineligibility on their own.

Keep eligibility data in the `Min Degree` column, not appended to the `Role`
title. `Role` should read as the posting's actual name.

## 6. Write new postings to Notion

**Build the rows as a file and push them with one command. Do not create them
through MCP** — a 95-row batch that way costs roughly a third of a session.

```bash
python3 pipeline/notion_push.py --table tracker \
    --create "$SCRATCH/new_rows.json" --receipts "$SCRATCH/receipts.json"
```

`new_rows.json` is a JSON array of
`{"properties": {...}, "content": "optional body text"}`. Put eligibility notes
and JD caveats in `content`, not in the `Role` title.

Run `--dry-run` first on a big batch: it validates every payload against the live
schema and writes nothing. An unknown property name is a hard error that lists
the real column names, so a typo can't silently drop a field.

**`--receipts` is not optional.** Each successful create is recorded the instant
Notion confirms it, keyed by `canonical_key()`. Re-running the same `--create`
with the same receipts file skips what already exists, so a run that dies at row
60 of 95 resumes instead of double-writing.

For every `is_new: true` leaf, create a row with:

- `Status = Discovered` — **always.** Selection is opt-in; the user promotes to
  `To apply`. **Never write `To apply` yourself.**
- `Source` — which sources surfaced it. Never leave empty; empty means the user
  created the row by hand.
- `Score`, `Opened`, `Closes`, `First Seen`, `Location`, `Role`, `Link`,
  `Requires`, `Cycle`, and the `Target Company` relation.
- `Min Degree` — **on every row.** If you genuinely could not read the JD,
  `Not stated` is the honest value; an empty cell means nobody looked.

**Then reconcile, then commit the ledger — in that order.** `notion_push.py`
prints `create: N requested, M written, K already present, F failed` and, when
`F > 0`, names every row that does **not** exist in Notion. Compare `M` against
the `reconcile: N` figure from step 5. If they differ, **say so in the digest and
name the failed rows** — a write that silently half-succeeded is a blocker, not a
footnote (R5).

```bash
# notion_push.py prints this exact array under "keys written this run"
echo '["<key>", ...]' | python3 pipeline/rank.py --commit-seen --today <YYYY-MM-DD>
```

Use that printed array verbatim. It contains only keys Notion confirmed, which is
precisely what `--commit-seen` must receive.

**Never commit a key for a row that was not written.** Stamping the ledger at
ranking time, before the write, marks live openings as seen with nothing to show
for them — and because the tracker is authoritative, the ordering above is what
makes that self-healing.

## 7. Prune dead postings

For rows at `Discovered` or `To apply` only: if the URL 404s or `Closes` has
passed, flag for archiving. **Never touch anything at `Applied` or beyond** —
those are permanent history.

If a row the user had prioritised closes unapplied, **surface it as a missed
opening.** That is the failure this system exists to prevent, and each one should
sharpen the `Expected Open` estimate on the Target Companies row.

## 8. Digest

Five-minute budget. Report:

- **Top 10 only**, one line each: role · company · opened N days ago · score ·
  the single reason it ranks there. Eligibility flags inline.
- Per role, the information split: **Category A** (CV, contact, education, MCQs —
  filled from `profile/application-facts.md`) versus **Category B**
  (why-this-firm, describe-a-time, referees, anything not pre-declared — the
  user writes these).
- **Sources that failed**, named explicitly. And if discovery was
  watch-list-only, say so.
- Missed openings from step 7.
- **The standing queue** — see step 9.

If a notification mechanism is available, send one under 200 characters leading
with what they'd act on.

## 9. Hand off — this skill never builds

**jobscan sweeps and reports. It does not build, and it does not fill forms.**

```
  /jobscan          →  they review, toggle rows to `To apply`  →  /resume-build
  sweep + rank         (selection is theirs, and only theirs)     build + fill
  write Discovered                                                → Ready to submit
```

Everything this run wrote is `Status = Discovered`. Promotion is theirs, so
building what the scanner just found would defeat the gate that exists to stop
exactly that. **Never promote a row yourself**, and never invoke `resume-build`
from here — not even for rows already at `To apply`. They run it when ready.

What this step *does* is report, in one line at the end of the digest:

- **`To apply`, not yet built** — the queue `/resume-build` will drain. Count and
  names.
- **`Ready to submit`** — built, form filled, waiting on their click. If any are
  older than a few days, say so: an unsubmitted `Ready to submit` row is the same
  missed-opening failure as step 7, one step further along.

Both sets are already in the step-1 export, so this costs nothing to compute.

## Hard rules

- **Never fill or submit anything at all during discovery.** Opening a dropdown
  to read its options is fine; anything that could post is not. Form-filling
  belongs to `resume-build`, and only after a row has been promoted.
- **Never click submit, and never tick a certification checkbox.** One-click
  apply flows get the same gate as everything else.
- **Never promote a row to `To apply`.** That is the user's decision and it is
  the only gate between "found" and "applied".
- **Never report "nothing new" when the truth is "I could not look."**
- The 72-hour target never outranks the build quality gate. A generic CV on day
  one is worse than a tailored one on day four.
