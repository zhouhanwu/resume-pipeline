---
name: setup
description: Onboard a new user to the résumé pipeline — check the toolchain, read their CV, ask a handful of questions, and write config.json, profile/master-profile.md, profile/application-facts.md, profile/lexicon.json, CLAUDE.md's truth rules and shared/blocks.tex from what they gave you, then do one real end-to-end build. Use when someone has just cloned this repo, says "set up", "/setup", "get me started", or when config.json still carries "_example": true.
---

# setup — the front door

**Run this before anything else in this repo.** Nobody should have to read the
codebase to use it. They hand over their CV, answer a few questions, and get
working files.

## What you are actually doing

The repo ships with a complete fictional candidate so it builds on clone. Your
job is to replace that candidate with a real one — **by reading what they give
you and writing the files yourself**, not by interviewing them.

`profile/master-profile.md` is the asset; every résumé this system produces is a
lossy compression of it. It does not have to be complete on day one.
`profile/HOW-TO.md` Loop 1 deepens it one entry at a time, whenever they do
something new or an application needs more. A thin entry is fine; a setup nobody
finishes is not.

**Read `profile/HOW-TO.md` before you start.**

---

## Ground rules for the whole run

- **Ask as little as possible.** The whole run needs about five questions (listed
  per phase below). If the CV or a previous answer already says it, don't ask it.
  If a detail wouldn't change a bullet or a form field this week, don't ask it —
  write "not recorded" and move on. Anything not asked now gets asked once, the
  first time a form needs it.
- **Trust what they give you.** Take the CV and their answers at face value. Do
  not probe whether a claim is defensible, whether they "really" built something,
  whether a number is audited, or what was hard. If they volunteer a constraint
  ("it was a team of four", "that grade is predicted", "that was unpaid"), record
  it as a truth rule. If they don't, don't go looking.
- **Infer, then let them correct you.** Spelling variant from the CV, skills from
  their projects, the words that are theirs from their own phrasing, which roles
  fit which audience — infer it, write it, and mention it in one line.
- **One question at a time.** Never present a form. Never ask them to edit JSON.
  If you find yourself explaining what a `\renewcommand` is, you have gone wrong.
- **Never invent a fact about them.** Not a metric, not a date, not a job title.
  A gap recorded as "not recorded" is true; a filled gap is not.
  `profile/master-profile.md` Appendix C exists to hold exactly these gaps.
- **Write as you go, not at the end.** Each phase commits its output to disk
  before the next begins, so a session that ends early loses nothing.
- **Their words, not yours.** Keep the CV's phrasing. The voice doctrine (Rule 4)
  depends on the knowledge base being in their voice.

## Resuming

Track progress in `.setup-state.json` at the repo root:

```json
{
  "completed": ["0-environment", "1-identity"],
  "entries": ["Acme internship", "Bike-share", "Ridgeline"],
  "phase3_done": ["Acme internship"],
  "phase3_sections_done": ["§1"],
  "updated": "2026-09-24"
}
```

Write it after **every** phase.
Phase 2 is the one long enough to lose mid-phase, so it gets finer-grained
tracking: `entries` (written once, in phase 1) is the full agenda;
`phase3_done` and `phase3_sections_done` grow one item at a time, as each
entry or §-section is actually written to `master-profile.md` — see Phase 2
below. Don't wait for the whole phase to finish before writing these; that
defeats the point.

On invocation, read the state file first. If `completed` shows phases already
done, say which, and start at the first incomplete one rather than beginning
again. For phase 2 specifically, also read `phase3_done` and
`phase3_sections_done` and diff them against what's actually in
`master-profile.md` §3 — the state file is a record of what you *meant* to
write, not proof that you did, so a mismatch means trust the file on disk and
correct the state. Resume phase 2 from the first entry not in `phase3_done`,
and tell the person which entries are already captured so they don't repeat
themselves. If `.setup-state.json` doesn't exist, this is a fresh run.

`/setup <phase>` re-runs one phase by name, for someone who wants to redo just
the truth rules or just the Notion step.

---

## Phase 0 — Environment

```bash
./setup-check.sh
```

Read its output back in one or two sentences — don't paste it.

- **A required item missing is a hard stop.** Give them the exact install
  command the script printed and wait. There is no point going further if they
  can't build a PDF.
- **Chrome and the Chrome extension are not required to finish setup.** They are
  required for `/jobscan` and for form-filling later. Note it and carry on.

Record `0-environment`.

## Phase 1 — CV and identity *(question 1)*

Ask for their CV (PDF or Word) in the first real message, plus a LinkedIn or
GitHub link if they like. Any other material — old cover letter, project
write-ups — is welcome but not required. With no CV at all, ask them to list
everything they'd put on one, in any order, and work from that.

Read it and take from it, without asking: full name, email, links, spelling
variant (`en-GB` / `en-US`, from the CV's own spelling), and every education
entry, job, project, society and award.

**The one question:** *"Which regions do you apply into, and what phone number
goes with each?"* One line of why: the region only ever selects the phone number,
and a UK role wants a UK number. If the CV already shows a number and they
apply in one region, don't ask.

Tell them in a sentence what you read off the CV (name, spelling variant, the
list of entries) so they can correct it. That is a confirmation, not a quiz.

> **If the spelling is `en-US`, say so now:** the shipped example content is
> written in British English, so `./build.sh --example base` will FAIL the
> spelling gate until phase 5 replaces that content with theirs. That is the
> gate working, not a broken repo.

Write `config.json`: fill `identity`, `regions`, `locale`. **Delete the
`_example` and `_example_note` keys** — that is what unlocks `./build.sh`. Leave
`rank`, `sources` and `queue` at their defaults; phase 6 revisits `sources`.

```bash
python3 pipeline/gen_identity.py
```

Write the entry list into `.setup-state.json`'s `entries`. Record `1-identity`.

## Phase 2 — Knowledge base *(question 2)*

Write `profile/master-profile.md` yourself from the CV. §3 gets one entry per
item, **in the CV's words**, at the length the CV gives it — no interview, no
follow-ups. Append each name to `phase3_done` as it's written.

**The one question:** *"Which roles are you going for — and is there anything the
CV undersells or leaves off, like unpaid work, projects or numbers?"* Add
whatever they say as entries or details, in their words.

Then draft the rest without asking: §1 (what they're optimising for, and a
fit-vs-positioning split), §2 (geography), §4 (things not yet résumé-worthy), §5
(the narrative and the **proof-point-to-audience map**, which Rule 2's priority
order actually reads), Appendix B (skills, from their projects and CV) and
Appendix C (gaps, i.e. anything marked "not recorded"). Append each section label
to `phase3_sections_done` as it's written.

Record `2-knowledge-base` once every entry and section is written.

## Phase 3 — Truth rules *(no questions)*

Write these from what they have already told you. Do not interrogate.

If the CV or their answers state a constraint on a claim — a team size, a
predicted grade, an unpaid or co-founded venture, AI-assisted work, a title that
differs from the work — turn each into:

1. A rule in `CLAUDE.md`'s truth-rules block — **replace everything between the
   `<!-- BEGIN TRUTH RULES -->` and `<!-- END TRUTH RULES -->` markers**, and
   mirror it into `master-profile.md` Appendix A. Each rule names the claim, the
   allowed wording, and the forbidden wording.
2. An entry in `profile/lexicon.json` under `rejected_wordings.pairs`, as
   `["the forbidden phrase", "what to use instead"]`, so the build gate catches it
   mechanically.

**Remove the placeholder `example-overclaim` pair either way.** If they stated no
constraints, the block holds just "claims are exactly what the CV states; add a
rule here the first time something needs pinning", and `/resume-build` keeps
working from that.

Lift "words that are mine" from their CV into §6 yourself. Words they dislike get
added to `lexicon.json`'s `banned_vocab.words` the first time a build trips one
(HOW-TO's Loop 2).

Record `3-truth-rules`.

## Phase 4 — Application facts *(question 3)*

Fill `profile/application-facts.md` from the CV: §1 identity and contact, §3
education, §4 work history (CV titles and dates). Leave everything the CV doesn't
give — addresses, start and end dates, notice period, referees, GCSEs, transcript,
per-firm notes — as the literal text "not recorded". `/resume-build` asks the first
time a form needs one and writes the answer back, so each is asked at most once.

**The one question:** *"Do you have the right to work in [each region], and will
you need visa sponsorship — now, or later?"* This is the single form answer that
can get an application auto-rejected, and it can't be read off a CV. Record it as
the three separate answers forms ask for (right to work / sponsorship now /
sponsorship in future); they are never collapsed.

For §7 (**what is never auto-filled**), keep the shipped list as it stands and tell
them in one sentence: cover letters, referees, demographic questions and any
government ID are never filled, and nothing is ever submitted. They can add to it
any time.

**Do not ask for, and never record:** passport number, national ID, NI or tax
number, bank details, full date of birth, driving licence. One sentence: these are
deliberately excluded and they type them on each form themselves.

Record `4-application-facts`.

## Phase 5 — Résumé content *(no questions)*

Turn the knowledge base into `shared/blocks.tex`.

**Map, don't compose.** Take the CV's lines and rewrite them into the `\h`/`\x`
macro structure, keeping their phrasing. Rule 4b applies to onboarding exactly as
it applies to tailoring: if your bullet shares almost no words with what they
wrote, you have regenerated it. Where there is no CV, compose from the §3 entry
and list those lines in the hand-back as composed.

Structure it as the shipped example does:

- `\h<Name>` heading and `\x<Name>` bullets per entry, replacing the example's.
- Month-precise dates.
- Two or three optional blocks for page-fill — the ones that answer a specific
  kind of JD line rather than a general one.
- `\ResumeBody` with **Experience before Projects**, and **no headless
  entries**: every `\h...` call needs a matching `\Bullets{...}`.

Record `5-resume-content`.

## Phase 6 — Sources and Notion *(question 4)*

Only needed for `/jobscan` and for `/resume-build`'s queue. **A user who only
wants to tailor résumés by hand can skip this entirely** — say so, and if they
skip, note it in the state file and go to phase 7.

**The one question:** *"Which job-listing pages should `/jobscan` look at? Paste
the URL of each — for example a saved Trackr or Jorb AI search with your filters
set. Skip if none yet."* Write each into `config.json` as
`{"name": "...", "url": "..."}` under `sources.urls`. These URLs are the **only**
thing `/jobscan` ever looks at.

If they gave URLs, set up the Notion tracker (the table that remembers what has
been found, promoted, built and sent). Check whether `$NOTION_TOKEN` is set —
check that it exists, never ask for its value:

- **Set:** have them create a page called "Jobs" and connect their integration to
  it (`pipeline/NOTION-SETUP.md` has the clicks), then run
  `python3 pipeline/notion_bootstrap.py --parent "<their page url>"`.
- **Not set:** don't walk them through it now. Record `6-notion: deferred` and
  tell them `/setup notion` finishes it when they want job scanning. If they later
  create the token, flag the `.zshenv`-not-`.zshrc` trap: a token in `.zshrc` is
  invisible to every script Claude runs.

**Never ask them to paste the token into the conversation.**

Record `6-sources`.

## Phase 7 — First build *(question 5)*

Prove the whole loop before leaving them alone with it.

**The one question:** *"Paste one job posting you're interested in (URL or text)."*
Then:

```bash
./new-company.sh <slug> <region>
```

Capture the JD verbatim into `job-description.md`, tailor `resume.tex` per
`CLAUDE.md` Rules 2–4, and:

```bash
./build.sh <slug>
```

Run the fill loop in front of them and narrate what each gate says in a line. It
takes several passes; that is normal. Then run one evaluator pass from
`profile/evaluator-brief.md` and report the score honestly, including anything you
declined and why.

Finally, delete the shipped example so it can't be mistaken for their own:

```bash
rm -rf applications/example-corp
```

Record `7-first-build`.

## Phase 8 — Hand back

Tell them, briefly:

- **What was written** — the files, and that `master-profile.md` is the one that
  matters.
- **What is still blank** — anything "not recorded" in `application-facts.md`,
  Appendix C's gaps, and anything deferred (Notion). None of it blocks a build:
  those get asked once, when a form first needs them. List any bullets you
  composed rather than took from their CV.
- **The two commands they will actually use:** `/jobscan` to scan the URLs in
  `config.json` for roles, and `/resume-build` to build and fill applications.
  Plus the third one nobody thinks of: *tell Claude when you do something new*,
  which is Loop 1 and the only thing that keeps the knowledge base from going
  stale.
- **The boundary:** this system never clicks submit, never creates an account,
  never types a password, and never enters a government identifier. They do those.

Suggest they read `profile/HOW-TO.md` once, now that the files have something in
them. Not before.

---

## Hard rules

- **Never fabricate a fact about the user.** A gap recorded is correct; a gap
  filled by invention is a lie on a document they will sign.
- **Never ask for or store a government identifier, bank detail, full DOB or
  password.** Not in `application-facts.md`, not in the state file, not
  anywhere.
- **Never ask them to paste an API token into the conversation.**
- **Write after every phase.** An interview lost to a full context window is the
  worst failure this skill has, because it is the one people don't come back
  from.
- **Don't add questions.** If you're about to ask something not listed above,
  write "not recorded" or your best inference instead.
