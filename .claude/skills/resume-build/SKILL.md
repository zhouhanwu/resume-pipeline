---
name: resume-build
description: Build and lodge applications end-to-end — drain the Notion `To apply` queue, fetch each JD, tailor a one-page résumé in the candidate's voice, pass the mechanical gates, run the two-pass adversarial evaluator, then fill every pre-declared field in the live application form and leave the tab open for them to vet and submit. Use when the user says "build a CV for <company>", "tailor my resume for <role>", "apply to <company>", or just "/resume-build" after promoting rows in the tracker.
---

# resume-build — gather, tailor, gate, evaluate, fill

This is the **second half of the pipeline**. `jobscan` sweeps and ranks; the user
promotes rows to `To apply`; this skill takes them from there to a filled,
unsubmitted form sitting in an open tab.

```
  /jobscan          →  they toggle rows to `To apply`  →  /resume-build
  sweep + rank         (selection is theirs)              gather → build → gate
  write Discovered                                        → evaluate → fill form
                                                          → Ready to submit
                                                          → they vet + click submit
```

**They click submit. Always. This skill never does.**

**Read first, every time:** `profile/master-profile.md` §5 (the proof-point map)
and **§6 (canonical wordings)**. §6 is not optional — re-deriving a wording it
already settles is the most common defect this system has.

Companion docs: `profile/HOW-TO.md` (the loop), `profile/evaluator-brief.md` (the
cold read), `profile/research-protocol.md` (choosing the role),
`profile/pipeline-design.md` (why the pipeline is shaped this way),
**`profile/application-facts.md` (every form answer — read it before touching a
field, and never re-ask what it already records)**. CLAUDE.md's truth rules
outrank everything here.

**If `config.json` still carries `"_example": true`, stop and run `/setup`.**
The build will refuse anyway, and building a fictional person's CV helps nobody.

---

## 0. Work out the queue

**No arguments → drain the queue, capped by `config.json`'s `queue.batch_cap`
(default 3).**

```bash
python3 pipeline/notion_pull.py --out-dir "$SCRATCH" --table tracker --queue
```

This writes `tracker.json` and prints the `To apply` / `Ready to submit` queue
already sorted by `Score` descending — that printed list *is* the queue. Take the
top N.

The cap exists because a full-queue drain risks exhausting the session mid-run,
stranding every role at once instead of finishing some. Remaining `To apply` rows
stay queued — say how many are left and their scores, and run `/resume-build`
again to take the next batch.

Two things the script handles that used to be manual:

- **Paging to the end.** `query_all()` loops the cursor internally and raises
  rather than returning a short read. A page cap means one call is never the
  whole queue. A non-zero exit is a blocker — never work off a partial.
- **Sorting.** `--queue` applies the `Status = To apply` filter and the `Score`
  descending sort, and puts rows with no `Score` last rather than letting a null
  break the ordering.

Skip a row only if it is genuinely finished: `applications/<slug>/` exists **and**
`dist/<Name>-Resume-<Label>.pdf` exists **and** `notes.md` records an evaluator
pass-2 score (or an explicit "no fixes were made"). A folder with no gated PDF is
*not* built — it's a half-finished run to resume. Say which rows you skipped and
why.

**With arguments → that one role.** `/resume-build acmecapital`, or a company
plus role where a company has several live. Works whether or not the row is at
`To apply`.

Never build a row at `Discovered`, `Applied`, `Rejected`, `Withdrawn` or
`Abandoned`, and **never promote a row yourself to create work.**

If the role is still being chosen at all, follow `profile/research-protocol.md`
first — a job-tracker row is a company signal, never the role list.

**§§1–8 run per role, start to finish, before the next role begins.** Don't batch
all the builds and then all the fills: the fill needs the JD and the form-field
list fresh from §1, and a failure halfway through a batched run strands every
role at once. One role finished beats three half-done.

## 1. Gather — fetch the JD and the form, don't wait to be handed them

```bash
./new-company.sh <slug> <region>
```

**Slug convention.** One live role at a company → the bare company slug
(`acmecapital`). More than one → `<company>-<roleslug>`. Never overwrite an
existing folder; if the slug exists and is a *different* role, use the two-part
form.

Region selects the phone number only. Use the **role's** location, not the
candidate's.

**Then open the posting in Chrome and read it yourself.** Navigate to the row's
`Link` and capture the JD into `job-description.md` **verbatim**. Not a summary —
the exact requirement phrasing is what the proof-point map keys off, and a
paraphrase degrades every bullet built from it. Use `get_page_text`; avoid a
web-fetch tool that summarises through a smaller model.

**If the `Link` is a board root, not a posting**, find the specific posting on
that board by role title before going further. If you cannot find it, that is a
blocker (R5) — flag it, leave the row at `To apply`, move to the next one. Never
build from a neighbouring posting (R3).

**Open the application form now, in the same pass, and enumerate every field** —
selects, comboboxes, radio groups, uploads, free-text boxes, eligibility and
declaration checkboxes. Two reasons, both load-bearing:

1. **R2: the form is part of the JD.** Append its fields to
   `job-description.md`. Track and area dropdowns routinely carry role taxonomy
   the posting body omits.
2. **The fill step (§7) needs the field list anyway.** Enumerating once here
   saves a second crawl and tells you up front whether the form is login-gated,
   multi-page, or asks for something on the never-fill list.

**Reading is not filling.** Opening a dropdown to read its options is fine.
Nothing that could post happens until §7, and submit never happens at all.

## 2. Decide the audience, record it

Pick the column from `master-profile.md` §5's proof-point map. Write it in
`notes.md` with one line of why. This single decision drives every override that
follows.

## 3. Tailor — edit, never regenerate

In `applications/<slug>/resume.tex`, `\renewcommand` **only** what changes.

- **§6 settled wordings get pasted, not improved.** If a bullet has a canonical
  form, use it verbatim.
- **Headings fixed by a truth rule are never retitled.** Check CLAUDE.md's
  truth-rules block before changing any `\h...`. Those titles were settled for a
  reason and the reason is usually that the alternative overclaims.
- `\renewcommand` a bullet block to **trim bullet count for page-fit or reorder
  for emphasis** — not to reword.
- **Optional blocks exist for exactly this.** Switch on the one that answers a
  specific JD line; leave the rest off. A block spent on an audience that won't
  read it is a wasted line.
- **Experience ALWAYS precedes Projects.** Every cut, every audience, no
  exceptions. `shared/blocks.tex` ships that order by default; if you override
  `\ResumeBody`, keep it. Reordering entries *within* a section is still fine.
- Reorder anything else by overriding `\ResumeBody` — renaming a section,
  dropping an entry, moving Education.
- **Rule 4b:** if the tailored bullet shares almost no words with the source,
  stop. That's regeneration, and it's what makes the page sound like someone
  else.
- **Never a headless entry.** Every `\h...` call needs a matching `\Bullets{...}`.
  A heading with dates and no bullets occupies a line and explains nothing — a
  cold reader has no idea what an organisation *is* from its name. If nothing
  earns even one real bullet, cut the whole entry. (The one exception: a heading
  whose own line already carries its entire content, such as a school with its
  grades in the role line.)

## 4. Build — the gates run themselves

```bash
./build.sh <slug>
```

`build.sh` runs `pipeline/preflight.py` automatically and exits non-zero on any
FAIL. Do not hand back a build with a FAIL.

| Gate | Rule | Level |
|---|---|---|
| one page | 1 | FAIL |
| page fill % + lines available | 2 | FAIL <90%, WARN <95% |
| orphan bullet tails <70% column | 3 | WARN |
| rejected wordings, truth-rule phrases | 4a | FAIL |
| semicolon splices | 4c | WARN |
| flagged vocabulary | 4d | WARN |
| wrong spelling variant | 4f | FAIL |

**A WARN is not a pass.** Fix it, or write one line in `notes.md` saying why it
stands. Silent WARNs are how drift returns.

**Fill loop:** the gate tells you how many lines are free. Add the next item in
§5's priority order, rebuild, repeat until PASS or the honest content runs out.
Never pad — the truth rules say a page that can't be filled honestly stays
slightly short, and that gets recorded in `notes.md`, not hidden.

**On an orphan tail within a word or two of 70%:** padding it over the line is
the wrong fix. Record it with the reason and move on. Rule 3 says prefer cutting
and never pad; a justified WARN is a good outcome.

Then **read the rendered PDF** and say the bullets aloud. The gates catch
geometry and vocabulary; they don't catch a sentence that's awkward to speak.

## 5. Evaluator — two passes, not one

Run `profile/evaluator-brief.md`: a fresh `general-purpose` subagent with **only**
the JD and the built PDF. No repo context, no notes, no `.tex`.

**If any finding changed the PDF, rebuild and dispatch a second fresh subagent**
against the new PDF — same brief, zero memory of the first. Report both scores
and the delta. Skip the second pass only if every finding was declined and the
PDF is unchanged.

Truth rules outrank the evaluator. It doesn't know what's true, so it will
sometimes call an honest claim thin. **Never inflate a claim because it asked.**
Record declined findings **with the reason** — a declined finding is a good
outcome; a silently dropped one is not.

## 6. Record the build

Fill every slot in `notes.md`. A blank slot means the step was skipped, and
that's the point — it's visible.

```
Audience:
Preflight: PASS / WARN (list) — after final build
Evaluator pass 1: __/100
Evaluator pass 2: __/100   (or: not run — no fixes were made)
Fixes taken:
Fixes declined (+ reason):
```

If the user rewrote any line by hand, add the before/after to `master-profile.md`
§6's ledger **this session, dated**, and add the rejected form to
`profile/lexicon.json` (Rule 4h). That table is why drift doesn't recur; it only
works if it gets fed.

## 7. Fill the live form

**A weak evaluator score never blocks this.** The evaluator is advice, not
authority — it doesn't know what's true. Fill the form regardless, report the
score, and let the user decide at review whether to send it. There is no
threshold and no auto-abort.

### Set up

Load the Chrome tools in **one** `ToolSearch` call:

```
select:mcp__claude-in-chrome__tabs_context_mcp,mcp__claude-in-chrome__navigate,
mcp__claude-in-chrome__computer,mcp__claude-in-chrome__read_page,
mcp__claude-in-chrome__tabs_create_mcp,mcp__claude-in-chrome__find,
mcp__claude-in-chrome__form_input,mcp__claude-in-chrome__file_upload,
mcp__claude-in-chrome__get_page_text
```

**One tab per application, and it stays open.** This is a deliberate exception to
the usual clean-up-your-tabs rule: the open filled tab *is* the deliverable. The
user comes along afterwards, reads it, and clicks submit. Never close an
application tab, and never close one from an earlier role in the same run.

### Fill Category A — from `application-facts.md`, never from memory

**Category A is everything the user has pre-declared.** Read
`profile/application-facts.md` and fill from it verbatim. Never re-ask what it
already records, never infer a value it doesn't state.

| Field group | Source | Trap |
|---|---|---|
| Name | §1 | Given-name-first on everything outgoing |
| Email, links | §1 | A generic "Website" field takes the personal domain if there is one, not the code-host URL |
| Phone | §1 | **Region-matched to the role**, not to where they live |
| Addresses | §1 | Term-time and home are different fields |
| Right to work | §2 | **Three distinct questions — never collapse them.** "Right to work?" / "sponsorship now?" / "sponsorship now *or in future*?" have different recorded answers |
| Education | §3 | Predicted vs. achieved classification is a per-application question — **ask** |
| Work history | §4 | Use the contract titles and confirmed months from the table, not the CV |
| CV upload | §5 | Attach `dist/<Name>-Resume-<Label>.pdf` via `file_upload` |
| MCQs | §6 | "Previously applied to this firm?" — **read it off the Notion tracker**, don't guess |
| Track / area dropdowns | the leaf | Pick the track this build was tailored for |

### Multi-page forms — go all the way to the edge

Most real ATS flows are several pages. **Advance through every page**, filling
each as you go, and stop on the final review/submit page with submit unclicked.
Click `Next` / `Continue` / `Save and continue` freely — those advance the form,
they don't send it.

Know what you're doing, though: on some ATSes `Next` persists a partial draft
server-side. That's acceptable and expected here — a saved draft is not an
application — but it means a half-filled form can be visible to the employer, so
finish the pages you start.

### Login-gated forms — pause, don't guess

- **Session already authenticated** → carry on normally.
- **Login or registration wall** → **stop.** Leave the tab parked on the login
  page and ask the user to log in. Continue on their say-so.

**Never create an account and never type a password** — not theirs, not a new
one. That is a hard prohibition, not a preference. If they'd rather skip a gated
application, that is their call to make, not yours to make silently.

### The never-fill list — leave blank, flag every one

These are standing decisions in `application-facts.md` §7, not oversights:

- **Category B** — why-this-firm, describe-a-time, anything needing a personal
  story or opinion. Leave the field **empty** and record the exact question text
  in the hand-back. Never draft into a live field: an unedited draft that slips
  through review goes out in their voice.
- **Cover letters** — theirs to write, even where the posting lists one as
  required. Flag it; don't draft it.
- **Referees** — never auto-filled, ever. They name them, having asked
  permission.
- **Demographic questions** — select "prefer not to say" wherever that option
  exists. Where it does **not** exist and the field is mandatory, stop and hand
  the form back.
- **Transcript · UCAS tariff · supervisor names and contacts** — deliberately
  blank, not missing.
- **Passport · national ID · NI/tax number · bank details · full DOB · any
  government identifier** — they type these themselves, always. They are
  deliberately not in `application-facts.md` and must never be entered here.

### Before you leave the tab

Screenshot the final state and read it back. Report what is actually on screen,
not what you intended to type — a `form_input` that silently failed on a React
combobox is the difference between an honest hand-back and a wrong one.

## 8. Mark it `Ready to submit`

Set the Notion row's `Status` once the PDF is gated **and** the form is filled,
using the row's `url` from `tracker.json`:

```bash
python3 pipeline/notion_push.py --table tracker --update \
  '{"page":"<row url from tracker.json>","properties":{"Status":"Ready to submit"}}'
```

It prints `update: 1 requested, 1 applied, 0 failed`. **A non-zero failure count
means the status did not change** — say so rather than reporting the row as done,
or it will look finished and never be picked up again.

That status is the whole idempotency mechanism:

- `To apply` — promoted, not built. The next `/resume-build` picks it up.
- `Ready to submit` — built, filled, waiting on their click.
- `Applied` — they sent it. **They set this, not you.**

Set it **only** when both halves are actually done. If the build passed its gates
but the form was gated, blocked, or half-filled, **leave the row at `To apply`**,
say so explicitly, and say why. A row wrongly marked `Ready to submit` looks
finished and will never be picked up again — exactly the silent-miss failure this
pipeline exists to prevent.

Also record the fill in `notes.md`:

```
Form URL:
Pages reached:        __ of __   (stopped at: ____)
Category A filled:    (list)
Left blank + why:     (Category B questions verbatim · referees · demographics ·
                       cover letter · gated fields)
Tab left open:        yes / no
Notion status set:    Ready to submit / left at To apply (why)
```

## 9. Hand back

Per role: the `dist/` path · the preflight line · **both evaluator scores with
the delta** · fixes taken vs. declined · the open tab · and the **exact list of
what they still have to do** — every Category B question in full, plus referees,
demographics, cover letter and anything gated.

Across the run: what was built, what was skipped and why, and anything left at
`To apply` with the reason. Never report a role as done when its form is
half-filled. **If the queue drain hit the batch cap**, say so explicitly and list
the remaining `To apply` rows with their scores.

---

## Hard rules

- **Never click submit. Never tick a certification or declaration checkbox.**
  This is the single most dangerous surface in the pipeline and there is no
  circumstance in which this skill crosses it. One-click apply flows get the same
  gate as everything else.
- **Never create an account, never enter a password.** Pause and hand back.
- **Never enter a government identifier, bank detail, or full DOB.**
- **One page.** Verify with `pdfinfo`, never macOS `mdls` (cached; has reported 1
  for a 2-page PDF). The gate does this for you.
- **Their voice.** One spelling variant, no semicolon splices, no JD nouns
  grafted onto their sentences, no word they wouldn't say aloud.
- **Never revert a line the user edited by hand** — flag it and leave it. An
  unexpected edit may mean the rule is out of date, not the edit.
- **Truth rules are absolute.** Read CLAUDE.md's truth-rules block before every
  build. If a detail is missing, **ask** — never fabricate to fill a line.
- **A failed extraction is a blocker, not a finding** (R5). If a form defeats the
  tooling, say "could not fill" and leave the row at `To apply`. Never report a
  blocked form as a finished one.
