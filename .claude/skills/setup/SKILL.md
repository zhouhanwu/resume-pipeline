---
name: setup
description: Onboard a new user to the résumé pipeline — check the toolchain, interview them about their career, and write config.json, profile/master-profile.md, profile/application-facts.md, profile/lexicon.json, CLAUDE.md's truth rules and shared/blocks.tex from their answers, then create their Notion tables and do one real end-to-end build. Use when someone has just cloned this repo, says "set up", "/setup", "get me started", or when config.json still carries "_example": true.
---

# setup — the front door

**Run this before anything else in this repo.** Nobody should have to read the
codebase to use it. They should have to answer questions about their own life,
which they can do.

## What you are actually doing

The repo ships with a complete fictional candidate so it builds on clone. Your
job is to replace that candidate with a real one — not by asking them to fill in
templates, but by **interviewing them and writing the files yourself.**

The hard part is not `config.json`. It is `profile/master-profile.md`: a deep,
honest, per-audience knowledge base of everything they have done. That file is
the asset; every résumé this system produces is a lossy compression of it. An
hour spent here is worth more than every other hour combined, and no amount of
good tooling downstream compensates for a thin one.

**Read `profile/HOW-TO.md` before you start.** Phase 3 below is that file's
Loop 1, run once per entry on their CV.

---

## Ground rules for the whole run

- **One question at a time, in plain language.** Never present a form. Never ask
  them to edit JSON. If you find yourself explaining what a `\renewcommand` is,
  you have gone wrong.
- **Never invent a fact about them.** Not a metric, not a date, not a job title.
  If they don't remember a number, write "not recorded" and move on — that is a
  true statement and a fabricated number is not. `profile/master-profile.md`
  Appendix C exists to hold exactly these gaps.
- **Write as you go, not at the end.** Each phase commits its output to disk
  before the next begins. A session that runs out of room mid-interview must not
  lose the interview. This applies inside a phase too, not just between phases:
  in phases 1, 4 and 5, write each answer into `config.json` /
  `application-facts.md` / the truth-rules block as it's given, rather than
  holding everything in your head until the phase's last question — a phase cut
  short should lose at most one unanswered question, not the whole phase.
- **Their words, not yours.** When they describe an accomplishment, keep their
  phrasing. The entire voice doctrine (Rule 4) depends on the knowledge base
  being in their voice, and this is the moment that voice enters the system.
- **Tell them roughly how long is left** at each phase boundary. A 40-minute
  interview that arrives unannounced feels like an interrogation.

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

Write it after **every** phase — that covers phases 0, 1, 2, 4, 5, 6, 7, 8.
Phase 3 is the one long enough to lose mid-phase, so it gets finer-grained
tracking: `entries` (written once, in phase 2) is the full agenda;
`phase3_done` and `phase3_sections_done` grow one item at a time, as each
entry or §-section is actually written to `master-profile.md` — see Phase 3
below. Don't wait for the whole phase to finish before writing these; that
defeats the point.

On invocation, read the state file first. If `completed` shows phases already
done, say which, and start at the first incomplete one rather than beginning
again. For phase 3 specifically, also read `phase3_done` and
`phase3_sections_done` and diff them against what's actually in
`master-profile.md` §3 — the state file is a record of what you *meant* to
write, not proof that you did, so a mismatch means trust the file on disk and
correct the state. Resume phase 3 from the first entry not in `phase3_done`,
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
  command the script printed and wait. There is no point interviewing someone
  for 40 minutes and then discovering they can't build a PDF.
- **Chrome and the Chrome extension are not required to finish setup.** They are
  required for `/jobscan` and for form-filling later. Note it and carry on.

Record `0-environment`.

## Phase 1 — Identity

Short, factual, five minutes. Ask for:

- Full name, and how it should appear on the page (given name first on
  everything outgoing).
- Email, LinkedIn, GitHub, personal site if any.
- Which **regions** they apply into, and a phone number for each. Explain in one
  line why: the region only ever selects the phone number, and a UK role wants a
  UK number.
- **Spelling variant** — `en-GB` or `en-US`. Frame it as consistency, not
  nationality.

> **If they choose `en-US`, warn them now:** the shipped example content is
> written in British English, so `./build.sh --example base` will FAIL the
> spelling gate until phase 6 replaces that content with theirs. That is the
> gate working, not a broken repo. Say it before they see it and wonder.

Write `config.json`: fill `identity`, `regions`, `locale`. **Delete the
`_example` and `_example_note` keys** — that is what unlocks `./build.sh`.

Leave `rank`, `sources` and `queue` at their defaults for now; phase 7 revisits
`sources`.

Then confirm it works:

```bash
python3 pipeline/gen_identity.py
```

Record `1-identity`.

## Phase 2 — Ingest

Ask them to give you whatever they already have: a current CV (PDF or Word), a
LinkedIn export, a GitHub profile, an old cover letter. Any of it.

Read it. Extract the skeleton — every education entry, job, project, society,
award — and **read the list back to them for confirmation and additions.**
People routinely leave off the thing that turns out to be their best entry,
usually because it wasn't paid.

If they have nothing at all, that is fine: ask them to list everything they'd
put on a CV, in any order, and work from that.

Write nothing to `master-profile.md` yet. This phase produces the agenda for
phase 3. Record `2-ingest`, and write the confirmed list of entries into the
state file's `entries` array (initialise `phase3_done` and
`phase3_sections_done` as empty arrays) so a resumed run knows what remains.

## Phase 3 — The interview *(the important one)*

**Budget: 3–6 minutes per entry. Say so up front.** For each entry from phase 2,
work through `profile/HOW-TO.md`'s Loop 1:

1. **Scope.** What was theirs, what was the team's, how many people, who they
   reported to.
2. **What they actually did.** Methods and tools, named. Push for specifics — "I
   analysed data" is not yet an entry.
3. **Numbers.** Every metric they have. Then the question that matters:
   **"which of these could you defend if someone pushed on it?"** Record
   defensible and non-defensible separately. This distinction is what stops a
   confident number from reaching a page it can't survive.
4. **What was hard.** The single most valuable question in this phase and the
   one most often skipped. The hard part is what an interviewer asks about, and
   it is almost never the part that sounds impressive.
5. **Per-audience emphasis.** Which kind of reader would care about which part.

Write each entry into `profile/master-profile.md` §3 **as you finish it**, in
their words, at full length. Do not compress to résumé length — that is phase 6's
job, and an entry written short leaves a later tailoring pass nothing to do but
reword. **The moment an entry is written, append its name to `phase3_done` in
the state file and save it** — don't batch this until the end of the phase;
the whole point is that a session ending mid-interview still knows what's
already captured.

Then §1 (what they're optimising for, and the honest fit-vs-positioning split
across role types), §2 (geography), §4 (things not yet résumé-worthy), §5 (the
narrative and the **proof-point-to-audience map**, which is the table Rule 2's
priority order actually reads), Appendix B (skills with honest ownership tags —
"would you defend this in a technical interview?"), Appendix C (known gaps).
**Same rule: append the section label ("§1", "§2", "Appendix B", ...) to
`phase3_sections_done` as soon as it's written**, not at the end.

Record `3-interview` only once every entry is in `phase3_done` and every
section above is in `phase3_sections_done`. If the session ends before that,
leave `3-interview` off `completed` — the per-entry and per-section progress
already saved is what a resumed run reads to pick up where this one stopped.

## Phase 4 — Truth rules *(the one worth stealing)*

Go back through every entry from phase 3 and ask the honesty questions outright.
This front-loads something that otherwise takes months of builds to surface, and
it is the phase most likely to change what ends up on their page.

For each entry, ask whichever apply:

- **"You said you *built* this — did you write the code, or integrate, configure
  and direct it?"** AI-assisted and heavily-templated work is extremely common
  now and is not shameful. What is fatal is a build claim that collapses under
  "walk me through your architecture."
- **"Was this solo or a team? What was yours specifically?"**
- **"Is this title the one on your contract, or the one that describes the
  work?"** They are often different, and forms want the contract one.
- **"Has this shipped to real users, or is it coursework?"** Dictates
  "classifier"/"applied ML" versus "production".
- **"Is this employment, or a project?"** An unpaid co-founded venture is not
  employment on a work-history form.
- **"Where did this number come from — your own analytics, or something
  audited?"** Changes the honest phrasing, usually by one word.
- **"Is this grade achieved or predicted?"**

For every answer that constrains a claim, write **two** things:

1. A rule in `CLAUDE.md`'s truth-rules block — **replace everything between the
   `<!-- BEGIN TRUTH RULES -->` and `<!-- END TRUTH RULES -->` markers**, and
   mirror it into `master-profile.md` Appendix A. Each rule names the claim, the
   allowed wording, and the forbidden wording.
2. An entry in `profile/lexicon.json` under `rejected_wordings.pairs`, as
   `["the forbidden phrase", "what to use instead"]`, so the build gate catches
   it mechanically rather than relying on anyone remembering. **Remove the
   placeholder `example-overclaim` pair.**

Also ask: **"which words do you actually use?"** Record them in §6 under "words
that are mine" so no later pass smooths them away. And **"which words make you
wince?"** — add those to `lexicon.json`'s `banned_vocab.words`.

Record `4-truth-rules`.

## Phase 5 — Application facts

Work through `profile/application-facts.md`'s nine sections as an interview.
Most are quick; three need care:

- **§2 right to work — three separate questions.** "Do you have the right to
  work?", "do you need sponsorship now?", and "will you need sponsorship in
  future?" have different answers and forms ask them separately. Collapsing them
  is one of the few form errors that gets an application auto-rejected.
- **§4 work history** — contract titles and confirmed months, which are often
  not what the CV says.
- **§7 what is never auto-filled.** Read the list to them and confirm each. If
  they want something added — a question they'd always rather answer themselves
  — add it. This list is a standing instruction to `/resume-build`, so it needs
  to be theirs.

**Do not ask for, and never record:** passport number, national ID, NI or tax
number, bank details, full date of birth, driving licence. Say plainly that
these are deliberately excluded and they will type them on each form
themselves.

Record `5-application-facts`.

## Phase 6 — Résumé content

Now turn the knowledge base into `shared/blocks.tex`.

**Map, don't compose.** Where they have an existing CV, take its lines and
rewrite them into the `\h`/`\x` macro structure, keeping their phrasing. Rule 4b
applies to onboarding exactly as it applies to tailoring: if your bullet shares
almost no words with what they wrote, you have regenerated it.

Where they have no CV, compose from the phase-3 entry — and then **flag every
composed line explicitly** and have them read it. A bullet they have not
approved is not in their voice yet.

Structure it as the shipped example does:

- `\h<Name>` heading and `\x<Name>` bullets per entry, replacing the example's.
- Month-precise dates.
- Two or three optional blocks for page-fill — the ones that answer a specific
  kind of JD line rather than a general one.
- `\ResumeBody` with **Experience before Projects**, and **no headless
  entries**: every `\h...` call needs a matching `\Bullets{...}`.

Record any wording they settle during this phase in §6's ledger, dated. That
table starts being useful the moment it has one row.

Record `6-resume-content`.

## Phase 7 — Notion

Only needed for `/jobscan` and for `/resume-build`'s queue. **A user who only
wants to tailor résumés by hand can skip this entirely** — say so, and if they
skip, note it in the state file and go to phase 8.

Walk them through `pipeline/NOTION-SETUP.md`:

1. Create an integration at notion.so/my-integrations with Read, Update and
   Insert content capabilities.
2. Put the secret in `$NOTION_TOKEN`. **Flag the `.zshenv`-not-`.zshrc` trap
   explicitly** — a token in `.zshrc` works when they type commands themselves
   and is invisible to every script run from a non-interactive shell, so the
   pipeline fails with "no Notion token found" while their own terminal looks
   fine. This one costs people an hour.
3. Create a page to hold the tables (call it "Jobs") and connect the integration
   to it.

**Never ask them to paste the token into the conversation.** They set it in
their own shell; you verify it exists, not what it is.

Then:

```bash
python3 pipeline/notion_bootstrap.py --parent "<their page url>"
```

It creates both tables, links them, writes `pipeline/notion_config.json` and
verifies. If a relation could not be added automatically it says so — tell them
which column to add by hand.

Then ask about **sources** and write `config.json`'s `sources` block. Be honest
here: the watch list is the spine, and the two aggregators the repo knows about
are UK-internship-specific and login-gated. For most people the right answer is
watch-list-only plus their own target companies. Offer to seed the Target
Companies table with the firms they name.

Record `7-notion`.

## Phase 8 — First build, end to end

Prove the whole loop before leaving them alone with it.

Ask for **one real job posting** they're interested in. Then:

```bash
./new-company.sh <slug> <region>
```

Capture the JD verbatim into `job-description.md`, tailor `resume.tex` per
`CLAUDE.md` Rules 2–4, and:

```bash
./build.sh <slug>
```

**Run the fill loop in front of them.** It will take several passes, and seeing
that is the point — it teaches the iteration that the docs only describe. Narrate
what each gate is telling you.

Then run one evaluator pass from `profile/evaluator-brief.md` and report the
score honestly, including anything you declined and why.

Finally, delete the shipped example so it can't be mistaken for their own:

```bash
rm -rf applications/example-corp
```

Record `8-first-build`.

## Phase 9 — Hand back

Tell them, briefly:

- **What was written** — the files, and that `master-profile.md` is the one that
  matters.
- **What is still blank**, and what would fill it. Appendix C's gaps especially.
- **The two commands they will actually use:** `/jobscan` to find roles,
  `/resume-build` to build and fill applications. Plus the third one nobody
  thinks of: *tell Claude when you do something new*, which is Loop 1 and the
  only thing that keeps the knowledge base from going stale.
- **The boundary:** this system never clicks submit, never creates an account,
  never types a password, and never enters a government identifier. They do
  those.

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
- **Don't skip phase 4.** It is tempting — it feels like an interrogation about
  claims the person just made proudly. It is also the phase that stops a page
  collapsing in an interview, and the whole reason the truth rules exist.
