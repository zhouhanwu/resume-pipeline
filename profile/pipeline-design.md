# Application pipeline — why it is shaped this way

Not a how-to. `profile/HOW-TO.md` is the how-to. This file records the design
decisions, so that when one of them looks inconvenient at 1am you can see what
it was protecting against before you remove it.

---

## The shape

```
  /jobscan                →  you review, promote rows  →  /resume-build
  sweep · expand · rank      (selection is yours)          build · gate · evaluate · fill
  write Status=Discovered                                  → Status=Ready to submit
                                                           → you vet and click submit
```

Two skills, one human gate between them, one human gate at the end. Both gates
are load-bearing.

## The operating target

An opening should go from *published* to *applied* inside 72 hours, because
early applications are read by a fresher reviewer against fewer competitors —
and because many campus programmes are functionally rolling regardless of the
stated deadline.

**The 72-hour target never outranks the build quality gate.** A generic CV on day
one is worse than a tailored one on day four. When the two conflict, quality
wins and the delay gets recorded.

## Decisions, and what each protects

### The tracker is the source of truth, not the local ledger

`is_new` is derived from an export of the live Notion tracker, never from
`pipeline/seen.json`. The ledger survives only to preserve original discovery
dates.

**What it protects:** if the ledger decided what was new, a run that stamped keys
but failed to write the Notion rows would mark those openings as seen with
nothing to show for them, and they would be silently skipped on every subsequent
run. With the tracker authoritative, a lost write is self-correcting — no row
means still new, so it gets offered again.

Three ordering rules follow, and breaking any one reopens the bug:

1. `seen.json` is committed **after** the Notion rows exist, never during ranking.
2. Every run is archived to `pipeline/runs/` before anything downstream can fail.
3. Running `rank.py` without `--known` is refused. An unreachable tracker reads
   as "empty", which would mark every posting new and duplicate the whole board.

### Dedupe against every status, including terminal ones

A row at `Applied`, `Rejected` or `Abandoned` still means "already tracked".
Re-creating it is a duplicate. This is why the pipeline reads the **unfiltered**
view rather than a "currently open" one — a filtered view hides exactly the
statuses dedupe depends on.

### Rank, never filter

Every posting that survives the lookback window gets scored and written. Nothing
is dropped for being a poor fit.

**What it protects:** a badly-matched role scoring 22 is a visible signal you can
correct — "actually, I'd take that one". A badly-matched role silently dropped
teaches you nothing and cannot be recovered. Failing a *stated* hard bar
multiplies the score by 0.1; it still never removes the row.

### Selection is the human's, and only the human's

`/jobscan` writes everything at `Status = Discovered`. Promotion to `To apply` is
manual, always. `/resume-build` never promotes a row to create work for itself.

**What it protects:** the entire value of a discovery pass is that it is
*indiscriminate* — it shows you everything. If the same agent both selected and
built, the selection would quietly narrow to whatever is easy to build, and
you'd never see what was skipped.

### Leaf-level indexing

One posting is not one role. A single "Internships" listing can hold two tracks
or a four-division tree, distinguishable only inside the application form. Each
distinct track becomes its own rankable row.

This is also where R2 gets satisfied: table text is enough to rank a posting
provisionally, but not to confirm a stated eligibility bar or a hidden form
requirement. Only rows that survive the dedupe check get opened — a posting
earns a browser navigation only after it's been established as new.

### Status is the idempotency mechanism

| Status | Meaning | Who sets it |
|---|---|---|
| `Discovered` | Found and ranked, not selected | `/jobscan` |
| `To apply` | You want this one | **You** |
| `Ready to submit` | Built, gated, form filled | `/resume-build` |
| `Applied` | Sent | **You** |

A row wrongly marked `Ready to submit` looks finished and will never be picked
up again. That is the silent-miss failure this whole pipeline exists to prevent,
so the rule is strict: set it **only** when the PDF passed its gates *and* the
form is actually filled. If the build succeeded but the form was gated or
half-filled, the row stays at `To apply` and the reason gets said out loud.

### Bulk reads and writes go through scripts, not through the conversation

`notion_pull.py` and `notion_push.py` exist because moving table rows through the
conversation is enormously expensive — a single run writing ~95 rows through
tool calls can consume a third of a session's context, with an equally large
confirmation coming back. The same rows through a script cost one summary line.

The MCP Notion tools remain the right choice for ad-hoc questions ("what's in
the tracker for Acme?"). The scripts are for the bulk, repetitive traffic the two
skills generate every run.

### The batch cap

`/resume-build` drains at most three `To apply` rows per run, highest score
first. A full-queue drain risks exhausting a session mid-run, which strands
every role at once instead of finishing some. One role finished beats three
half-done.

### Never submit

No skill in this repo clicks a submit button or ticks a certification checkbox.
This is not a configurable preference.

**What it protects:** the obvious thing — an application going out with a
half-filled field or a wrong answer. But also the less obvious one: it keeps a
human reading every page before it is sent, which is the only remaining check
that catches a plausible-but-wrong bullet that survived every gate above.

One-click apply flows get the same treatment. Being one click from sending is a
reason for more caution, not less.

### The never-fill list

Cover letters, "why this firm", "describe a time when", referees, demographics
with no prefer-not-to-say option, transcripts, and every government identifier.

Category B answers are left **empty** and reported back with the question text
verbatim. Drafting into a live field is the specific risk: an unedited draft that
slips through review goes out in your name, in a voice that isn't yours.

---

## Known risks

- **Source coverage is only as good as the watch list.** The watch list is the
  spine of discovery and it is yours to maintain. A company that isn't on it and
  isn't on an aggregator simply never appears.
- **Judgement inputs are soft.** `fit` and `p_admission` are supplied per posting
  by a model. They are recorded in the run archive so a later run can be audited
  against an earlier one, but `p_admission` in particular should never be
  presented as precise.
- **Boards change shape.** Every ATS quirk in `research-protocol.md` is a fact
  about a system somebody else controls. When a sweep returns a suspiciously
  round number, assume the pagination broke rather than that the board shrank.
- **The knowledge base decays if Loop 1 is skipped.** This is the real one.
  Everything here is machinery for turning `master-profile.md` into pages; none
  of it improves the source material.
