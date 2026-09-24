# Adversarial review — the gate every résumé passes before it ships

Required by CLAUDE.md Rule 5. Runs **after** the final build passes Rules 1–4.

The point is a reader who knows nothing. Every other check in this repo is done by
someone who knows what the candidate meant, what the master profile says, and which
claims were deliberately kept small. A real screener knows none of that. They see
one page, cold, next to two hundred others. This step buys that reader.

---

## How to run it

Spawn a **fresh `general-purpose` subagent**. It gets exactly two things: the job
description and the built PDF. Nothing else.

Fill the four placeholders and send the prompt below verbatim.

- `<COMPANY>` / `<ROLE>` — from `job-description.md`
- `<JD>` — the full job description text, pasted inline
- `<PDF>` — absolute path to the file in `dist/`
- `<POOL>` — one line on the realistic applicant pool and odds for this role and
  cycle (e.g. "~3,000 applicants for ~20 summer analyst seats; most are
  penultimate-year maths/CS students from target universities"). Say if it's a
  guess.

**Do not** pass it the company folder, `notes.md`, `master-profile.md`,
`CLAUDE.md`, or the `.tex`. Those tell it what was intended; the whole value is
that it can only see what landed.

---

## The prompt

> You are screening CVs for the **<ROLE>** position at **<COMPANY>**. <POOL>
>
> Your job is to protect a small number of interview slots. Your default is
> reject. Most CVs you see are competent and forgettable, and competent and
> forgettable is a reject.
>
> The job description:
>
> <JD>
>
> The CV: read `<PDF>`.
>
> Read **only** that PDF. Do not open any other file in the repository, and do
> not go looking for context about the candidate — no notes, no profile
> documents, no source files, no web searches. You know what a screener knows:
> one page and the job spec. If something on the page is unclear or
> unverifiable, that *is* the finding — say so rather than resolving it.
>
> Work through it in this order.
>
> **1. The ten-second pass.** Before analysing anything, react. You have skimmed
> the top third and nothing else. Forward or bin? Say which, in one sentence,
> and name the thing that decided it. Be honest even if the honest answer is "the
> university and the predicted grade carried it and I read nothing else."
>
> **2. The two-minute pass.** Now read the whole page as a hiring manager. What
> is this candidate's argument for this job? Does the page make that argument, or
> does it make a different one and leave you to connect it? What is the strongest
> line on the page, and the weakest?
>
> **3. The ten-minute pass.** Now be the technical reviewer who would interview
> them. For each substantive claim: could this person defend it under questioning,
> or does the wording hide the fact that they can't? Flag every line where you
> would ask a question the candidate probably cannot answer. Flag every claim that
> sounds larger than the work underneath it — you cannot verify it, so say what
> your suspicion is and what you would ask.
>
> **4. Writing check.** Quote every line that reads as AI-generated,
> written-to-order, or corporate. Specific tells: two unrelated facts fused with a
> semicolon; nouns that echo the job description rather than the work; vocabulary
> a twenty-year-old would not say out loud; every bullet the same shape and
> length; a purpose clause welded to the end of every sentence. Quote the line and
> say what is wrong with it. If a line reads genuinely human and specific, quote
> that too — it is useful to know what is working.
>
> **5. Score it out of 100.**
>
> | # | Dimension | Weight |
> |---|---|---|
> | 1 | Relevance to *this* job spec | 25 |
> | 2 | Evidence quality — metrics, specificity, verifiability | 20 |
> | 3 | Credibility — does anything smell inflated or padded | 15 |
> | 4 | Differentiation against the realistic applicant pool | 15 |
> | 5 | Technical depth for this audience | 10 |
> | 6 | Writing — does it read as human | 10 |
> | 7 | Layout, scannability, use of the page | 5 |
>
> Give each dimension its score, one line of reasoning, and the total.
>
> Interpretation: **85+** submit · **80–84** strong, one or two fixes ·
> **75–79** needs reframing before it goes out · **70–74** first-draft quality ·
> **<70** would not survive your screen.
>
> **6. Interview probability.** Give a number, and say what the ceiling is —
> the score this CV could reach if every fixable thing were fixed, and what
> structural facts (year of study, no prior name-brand internship, whatever you
> see) cap it regardless of editing.
>
> **7. The three fixes.** Ranked by how many points each is worth. Be concrete —
> name the line and what should replace it. Then name anything you would **cut**:
> a line earning less than the space it occupies.
>
> Constraints on your output: no preamble, no encouragement, no praise sandwich.
> If you would reject this CV, say so in your first sentence. Do not soften a
> finding because the candidate is a student — say the CV is weak for the role
> where it is, and say what would fix it.

---

## Reading the verdict

The evaluator is deliberately ignorant. That is the design, and it has a cost:

- **It does not know what is true.** It will sometimes read an honest, deliberately
  small claim as thin, and push toward a bigger one. The truth rules in CLAUDE.md
  and master-profile.md Appendix A **outrank it, always.** Never inflate a claim
  because the review asked for it.
- **It does not know what was cut and why.** A "missing" item is often a
  deliberate omission — a language left off the Skills line because it isn't
  strong enough to defend, a project kept back for the interview, a short
  programme listed without a forward claim. Check `notes.md` before treating an
  omission as an oversight.
- **It does not know which wordings the candidate chose themselves.** The canonical
  wordings in master-profile.md §6 are settled. If the evaluator wants to rewrite
  one, the answer is no — record it as a declined finding and move on.
- **Its writing findings are the most reliable part.** It has no stake in the
  prose and no memory of drafting it. If it quotes a line as AI-sounding, it is
  usually right, and that line usually violates Rule 4.

Report back: the score, the ten-second verdict, the fixes taken, and —
explicitly — the fixes **declined** with the reason. A declined finding with a
stated reason is a good outcome. A finding silently dropped is not.

## After fixes are applied — re-run, don't guess

If any finding led to a change in the PDF, the review is **not done** until the
rebuilt PDF is scored again. Rebuild, re-verify `Pages: 1`, then spawn a **second
fresh subagent** — this brief, verbatim, zero memory of the first pass — against
the new PDF. Report **both scores, pre-fix → post-fix, with the delta**, not just
the first one captioned "not re-run." An unverified pre-fix score doesn't tell
you whether the fixes actually worked. Reporting pass 1 alone, captioned "not
re-run", is the most common way this step decays. Skip the second pass only when
every finding was declined and the PDF is unchanged from the first pass.
