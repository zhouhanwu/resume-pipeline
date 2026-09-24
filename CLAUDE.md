# CLAUDE.md — résumé system

Read `profile/HOW-TO.md` (the two working loops) and `profile/master-profile.md`
(the knowledge base every bullet is written from) before tailoring anything.
**§6 of master-profile.md is not optional reading — it holds the canonical
wordings the candidate has settled, and Rule 4 below exists because they keep
getting re-derived instead of reused.** `README.md` explains the inheritance
mechanics; `profile/evaluator-brief.md` is the adversarial review every build
must pass; **`profile/research-protocol.md` governs finding and indexing roles —
read it before recommending which jobs to apply to, not after.**
`profile/application-facts.md` holds the decided answers every form asks for —
read it before filling any field, and never re-ask what it already records.

Sensitive identifiers (passport, national ID, tax/NI number, bank details, full
date of birth) are deliberately **not** in it. The candidate types those
himself, always.

> **First time here?** Don't read this file top to bottom. Run `/setup` — it
> interviews you, writes `profile/master-profile.md` and
> `profile/application-facts.md` from your answers, and fills in the truth-rules
> section below with your own. Come back to this file afterwards, when the rules
> have something to point at.

---

## Rule 0 — The gates run on every build. Read them.

`./build.sh <company>` runs `pipeline/preflight.py` and **exits non-zero on any
FAIL**. It measures Rules 1, 2, 3, 4a, 4c, 4d and 4f mechanically. Do not
re-derive these by hand, and do not hand back a build with a FAIL.

**A WARN is not a pass.** Fix it, or record one line in `notes.md` saying why it
stands. Silent WARNs are how drift returns.

Why this exists: a rule with a command attached gets followed. A rule left to
end-of-context judgement gets skipped — not through carelessness, but because
by the time a long tailoring session reaches the end, the judgement that was
sharp at the start is gone. Rule 1 has `pdfinfo` behind it and holds every time.
Rules 2 and 5 were judgement calls and held about half the time, until they got
a number attached too. The rules below are unchanged; they now have commands.

## Rule 1 — ONE PAGE. Strict, non-negotiable.

Every résumé fits on a single page. Two pages is a defect. The `pages` gate
checks this on every build. To verify by hand:

```bash
pdfinfo dist/<Name>-Resume-<Company>.pdf | grep Pages   # must read: Pages: 1
```

On macOS, do **not** use `mdls -name kMDItemNumberOfPages` — it is cached and
has reported 1 page for a 2-page PDF.

## Rule 2 — FILL THE PAGE. Also strict.

A one-page résumé that runs three-quarters down the page is wasted space and a
wasted application. **Always fill the page with as much content as it will hold,
in priority order.** Rules 1 and 2 are a pair: the target is a page that is full
*and* does not spill.

**Priority order = relevance to this specific job**, using the proof-point map in
master-profile.md §5. Fill from the top of that map down:

1. The anchor proof points for this audience — give them their full 3 bullets.
2. Third bullets on the next-strongest entries.
3. Lower-priority entries restored with at least one real bullet each.
4. Optional blocks that exist for exactly this purpose.

Never fill with padding, filler adjectives, or restated bullets. If the page has
room, there is always a *real* accomplishment in master-profile.md that earns the
line. If nothing relevant is left, widen an existing bullet with genuine detail
(a method, a constraint, a number) — not with words.

**The build loop:** build → read the gate report → if the `fill` gate is short it
tells you **how many lines are free**; add the next item in priority order and
rebuild. If it tips to 2 pages, cut the lowest-priority item and rebuild. Iterate
until `fill` passes and `Pages: 1`. Expect several passes. This is normal, not a
sign of a problem.

Thresholds: **FAIL below 90%**, WARN below 95%, PASS at 95%+. Judging fill by eye
is unreliable — pages that read as "roughly full" routinely measure 84–89%. The
worked example in `applications/example-corp/notes.md` shows one such page and
the rebuild that fixed it.

## Rule 2b — Experience before Projects. Always.

**The Experience section always precedes the Projects section** — every cut,
every audience, no per-application exception. `shared/blocks.tex` ships that
order in the default `\ResumeBody`; an application that overrides `\ResumeBody`
keeps it. Reordering *entries within* a section for emphasis (Rule 2's priority
order) is unaffected.

## Rule 2c — No headless entries.

Never render an entry as a heading and dates with zero bullets under it. A cold
reader cannot tell what an organisation or project *is* from its name alone; a
bare heading occupies a line and explains nothing, which is worse than not
listing the entry at all. If an entry cannot earn even one real bullet, cut the
whole entry.

The one exception is an entry whose heading line already carries its entire
content — a school with its grades in the role line, for instance. Nothing is
missing there. The rule targets headings that raise a question they don't answer.

## Rule 3 — No orphan lines in bullets.

If a bullet wraps and leaves only a **few words alone on the final line**, that is
a defect: it burns a full line of vertical space to carry two or three words, and
it looks sloppy. **Cut words until the bullet ends flush on the previous line** —
or, if the content genuinely deserves the space, add real detail until the last
line is substantially full.

Prefer cutting. Tighten by deleting filler ("in order to", "successfully",
"various", "leveraged", "utilised"), collapsing phrases, and dropping adjectives
that carry no information. Never cut a metric or a defensible technical noun to
win the line — cut the connective tissue around them.

The same applies to the Skills lines and the Education coursework line: a
coursework list that spills two words onto a second line should lose a course, not
gain a line.

Line breaks depend on the rendered width, so a bullet's wrap point is only
knowable after `./build.sh` — never eyeball this from the `.tex`. The `orphans`
gate measures it on the built PDF and reports each offending tail with its
percentage.

The threshold: the last line of a wrapped bullet should fill **≥70% of the column
width**. Below that, cut.

**When a tail lands within a word or two of the threshold**, padding it over the
line is the wrong fix — that is adding words that carry no information purely to
satisfy a gate, which this rule exists to prevent. Record it in `notes.md` with
the reason and move on. A justified WARN is a good outcome; a silent one is not.

## Rule 4 — The candidate's voice, not Claude's.

The résumé has to sound like the person who will sit in the interview. Every
bullet in `shared/blocks.tex` and every wording in master-profile.md §6 is
theirs. **Tailoring means editing their line. It does not mean composing a
replacement.**

This is the rule that gets broken most often, so it has teeth:

**4a — Settled wordings are reused verbatim.** master-profile.md §6 carries a
table of canonical wordings the candidate chose themselves. Re-deriving one of
those from scratch is the exact defect this rule exists to stop. Read §6 before
writing a single `\renewcommand`. If a bullet has a settled wording, paste it;
don't improve it.

**4b — Diff, don't regenerate.** Open the block you're overriding and *edit* it:
reorder the clauses, swap the emphasised noun, cut what this reader won't care
about, add one real detail from master-profile.md. If the tailored bullet shares
almost no words with the source bullet, stop — that's regeneration, and
regeneration is what makes the page sound like someone else wrote it.

**4c — One idea per bullet. No semicolon splices.** Fusing two independent facts
with a semicolon (`"…in Gephi; nominated for the departmental prize"`) is a
page-fitting trick, not a sentence. Two facts = two bullets, or cut the weaker
fact. A semicolon is legitimate only inside a list that already has commas.

**4d — No word they wouldn't say out loud.** Before keeping a noun or verb in a
bullet, check it appears somewhere in their own writing (blocks.tex,
master-profile.md, a bullet they edited). The list in `profile/lexicon.json`
starts generic — *leveraged*, *utilised*, *stakeholder alignment*, *robust
solution*, *comprehensive*, *seamless*, *proven track record*, *demonstrated
ability to*, *played a key role in*, *worked closely with* — and you add to it
every time you catch one creeping back in.

Equally: record the words that **are** theirs and must not be "fixed". Every
candidate has a handful of verbs they actually use, and a tailoring pass that
smooths them into something more standard has made the page worse.

This governs **bullet prose only.** Skills-line headers and technical terms of
art are exempt — "ML/Data Frameworks" is a category label, and "Huber loss for
robustness to price outliers" is a real statement about a loss function. The test
is whether the word is doing work or doing impression management.

**4e — Don't launder JD vocabulary into their sentences.** Keyword matching
belongs in Skills and coursework, where it's honest. Grafting the JD's nouns onto
their accomplishments produces lines like *"designed the model validation
protocol"* — which reads as written-to-order, and which they cannot say in an
interview without sounding like a brochure.

**4f — One spelling variant, consistently.** Set `locale.spelling` in
`config.json` to `en-GB` or `en-US` and the gate enforces it. The point is
consistency, not nationality: a page that mixes both reads as careless.

**4g — Read the built PDF and say the bullets aloud.** Not the `.tex`. If a
sentence would be awkward to speak in an interview, it's wrong on the page.

**4h — The wording ledger.** Whenever the candidate rewrites a line by hand, add
the before/after to the §6 canonical-wordings table **in the same session**, with
the date, and add the rejected form to `profile/lexicon.json` so the gate catches
it next time. That table is the mechanism that stops this drifting back; it is
worthless if it isn't fed.

## Rule 5 — Every résumé gets adversarially reviewed before it ships.

After the final build passes Rules 1–4, run the evaluation in
`profile/evaluator-brief.md`: a **fresh subagent with no memory, no access to
this repo's context files, and nothing but the JD and the built PDF.** It reads
the page the way a screener with 200 CVs and 15 interview slots does, scores it
out of 100, and says what would get it binned.

Non-negotiables for that agent:

- It must **not** read CLAUDE.md, master-profile.md, notes.md, or the `.tex`. It
  grades what is on the page, not what was intended.
- It is told to be brutal and to default to reject. Encouraging output is a
  failed review.
- Its verdict is **advice, not authority.** It doesn't know what's true, so it
  will sometimes call an honest claim thin or push toward a claim the truth rules
  forbid. Report its score and its findings, act on the ones that are fair, and
  say plainly which ones are being ignored and why. **Never inflate a claim
  because the evaluator asked for it.**
- **If any finding led to a fix, the review isn't done until it's re-run.**
  Rebuild, re-verify `Pages: 1`, then dispatch a **second fresh subagent** —
  same brief, same rules, zero memory of the first pass — against the rebuilt
  PDF. A score you didn't re-check is a guess, not a result. Skip the second
  pass only when every finding was declined and nothing changed.

Hand back: the PDF path, **both scores (pre-fix → post-fix) with the delta**,
and the fixes taken vs. declined.

---

## Truth rules — these override everything above

Filling the page never justifies inflating a claim. If the honest version of the
content does not fill the page, the page stays slightly short.

**`/setup` writes this section from the honesty questions it asks in phase 4.**
Until it has run, the entries below belong to the worked example and are here to
show you the shape. Each one names a specific claim and the exact wording that
is and isn't allowed.

<!-- BEGIN TRUTH RULES — /setup rewrites everything between these markers -->

- **Ridgeline titling — "Co-Founder", on every cut.** He *did* co-found it; that
  was never the risk. The risk is the **engineering** claim: the stack was
  heavily AI-assisted, so lead with own-reasoning wins (the sync-bug root-cause,
  the route-scoring heuristic) and never imply he built it alone. "Co-Founder" is
  truthful. "Built a full-stack app" is not.
- **Bike-share titling — "Modelling and feature engineering, team of 4"**, the
  candidate's own wording, verbatim. It replaces "Machine Learning Engineer",
  which read as a solo build. It was a four-person team and his scope was the
  modelling — which is still the whole claim the bullets rest on.
- **"Classifier" / "applied ML"**, never "production ML."
- Never fabricate a detail to fill a line. If a detail is missing, **ask.**

<!-- END TRUTH RULES -->

The pattern these share, and the one `/setup` is trying to elicit from you: each
rule names a claim that is *almost* true, and pins the wording to the version
that survives a follow-up question. An interviewer who asks "so what did you
build?" should get an answer that matches the page.

## Working style

- Blunt, specific assessments. No hedged menus of options.
- **Surface all doubts before building.** Once a decision is made, execute and
  don't relitigate it.
- Iterate on the candidate's drafts; don't regenerate them from scratch. This
  applies to individual sentences, not just documents — see Rule 4b.
- Strip copy until it stops sounding corporate. High allergy to LinkedIn voice.
- **Never revert a line the candidate has edited by hand — flag it and leave
  it.** If an unexpected edit appears to break a rule above, say so and stop
  there; the rule may be the thing that is out of date, not the edit. This
  matters more than it sounds: a rule written three months ago about a project
  that has since changed shape will confidently flag a correction as a
  violation.
