# Example Corp — Data Analyst Intern, Operations Analytics

> **The worked example.** This is what a finished `notes.md` looks like. Every
> slot is filled, because a blank slot is visible evidence that a step was
> skipped — that is the entire point of the shape. Delete this folder once you
> have one of your own.

- **Region:** UK
- **Status:** _worked example — not a real application_
- **Deadline:** rolling
- **Portal / link:** https://example.com/careers/data-analyst-intern
- **Audience:** operations analytics — SQL and data-quality root-causing, explicitly
  not modelling depth. The posting says so in its own words: "we care more about
  this than about modelling depth."

## Tailoring rationale

Every override reorders or trims. None rewrites. The bullets that survive are
word-for-word the ones in `shared/blocks.tex`.

- **Northwind leads Experience.** It is the only entry that is literally this
  job. Its scanner-configuration bullet answers the JD's "evidence you can find
  the real cause of a problem rather than describing the symptom" directly.
- **`\xNorthwindDash` kept.** The JD lists a BI tool under nice-to-have, and the
  bullet's real content is agreeing metric definitions with operations staff
  first — which is a different JD line ("work directly with operations staff to
  agree metric definitions before building anything").
- **`\xRidgelineDebug` switched on.** This block exists for exactly this JD
  sentence. It is the strongest own-reasoning claim in the file and it is not
  spent on audiences who won't read it.
- **Bike-share trimmed to two bullets.** The dropped one is the rolling-origin
  CV / Optuna line — genuinely the best line in the file, and the wrong line for
  this reader. Trimmed, not reworded: the wording is settled, so it stays intact
  in `blocks.tex` for the audiences that want it.
- **`\xEduCompetition` cut, then restored.** See the build gates below.

## Build gates

From `./build.sh example-corp` (runs `pipeline/preflight.py`). A WARN is not a
pass: fix it or justify it on the line below.

- **Preflight:** WARN (orphans) — justified below. Everything else PASS.
- **Page fill:** `95.2%`

**The fill loop, as it actually ran.** First build with `\xEduCompetition` cut
came back at **92.9%, three lines free**. Restoring it took the page to
**95.2%**. That is the loop: build, read the number, add the next item in
priority order, rebuild. It is worth noticing that the 92.9% page looked
completely full to the eye — pages that read as "roughly full" routinely measure
in the high 80s, which is the whole reason this gate is a number.

**Orphans WARN — why it stands.** Two bullet tails land at 67% and 69% against a
70% threshold. Both are within a word of the line. Pushing them over would mean
adding words that carry no information purely to satisfy the gate, and the rule
itself says to prefer cutting and never to pad. Cutting either one costs a real
detail (the wall-chart reconciliation; the quarter the retention change was
measured over). Recorded and left. This is the escape hatch working as intended
— not a gate being ignored.

## Adversarial review (profile/evaluator-brief.md)

Two passes are mandatory whenever a finding changed the PDF. A pre-fix score
alone doesn't tell you the fixes worked.

- **Pass 1:** `_not run — this is a fictional posting_`
- **Pass 2:** `_not run_`
- **Fixes taken:** —
- **Fixes declined (+ reason):** —

> On a real build both scores go here with the delta. The evaluator is a fresh
> subagent that sees only the JD and the built PDF — no repo context, no notes,
> no `.tex`. Its verdict is advice, not authority: it does not know what is
> true, so it will sometimes call an honest claim thin. Record the declines with
> their reasons. **Never inflate a claim because the evaluator asked for it.**

## Form fill

- **Form URL:** https://example.com/careers/data-analyst-intern
- **Pages reached:** _n/a — fictional posting_
- **Category A filled:** name, email, phone (+44, region-matched), CV upload,
  university / degree / graduation year, the three right-to-work questions
  answered separately, preferred start date
- **Left blank + why:**
  - "Why Example Corp?" (200 words) — **Category B**, yours to write
  - "Describe a time you found the cause of a problem" (200 words) — **Category B**
  - Referees — never auto-filled, and you ask permission first
  - Ethnicity / gender / disability — "prefer not to say" where offered
  - Certification checkbox — never ticked by the skill
- **Tab left open:** yes — the filled tab *is* the deliverable
- **Notion status set:** _n/a_

## To-do

- [x] Tailor resume.tex (settled wordings pasted, not re-derived)
- [x] Build + all preflight FAIL gates clear; WARNs justified above
- [ ] Evaluator pass 1
- [ ] Evaluator pass 2 (if any fix was applied)
- [ ] Fill Category A form fields (profile/application-facts.md)
- [ ] (Optional) cover letter: `cp ../../shared/cover-letter-template.tex cover-letter.tex`
- [ ] **You submit — never automated**
