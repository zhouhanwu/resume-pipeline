# How this résumé system works

Two loops. Everything else is detail.

```
  LOOP 1  "I did something new"      ->  update the knowledge base
  LOOP 2  "I'm applying to <company>" ->  produce a tailored PDF
```

Loop 1 is the one people skip, and skipping it is why systems like this decay.
The knowledge base is the asset. The résumés are disposable outputs.

---

## LOOP 1 — "I did something new" (update the knowledge base)

Say what happened, in whatever detail you have. Claude files it.

1. **Into the right section of `profile/master-profile.md`** — §3 for a real
   accomplishment, §4 for something not yet résumé-worthy, Appendix B for a
   skill, §0 for a status change.

2. **Preserve the FULL context.** This is the whole point of the loop, and the
   place it goes wrong. Record:
   - the role and the scope — what was yours, what was the team's
   - every method and tool, named
   - every number, and separately, **which numbers you could defend under
     questioning and which you couldn't**
   - what was *hard*. This is the most valuable thing in the entry and the one
     most often left out. The hard part is what an interviewer asks about.
   - the per-audience emphasis: which reader would care about which part

   An entry written at résumé length gives a later tailoring pass nothing to do
   but reword, and rewording is exactly what Rule 4 forbids. Write it long.

3. **Apply the framing rules (Appendix A).** Flag anything needing an accuracy
   caveat: AI-assisted vs. personally written, prospective vs. actual
   employment, team output vs. your scope, a metric from your own analytics vs.
   an audited one.

   **This is where truth rules get made.** If the new accomplishment contains a
   claim that is *almost* true, stop and pin the wording now, while the facts
   are fresh — add it to Appendix A and to `profile/lexicon.json`. Six weeks
   later, at the end of a long tailoring session, nobody remembers that the
   stack was AI-assisted.

4. **If it changes a default fact everyone should inherit** — a job title, a
   date, a fixed metric — also update `shared/blocks.tex`, so it flows into
   every future application automatically.

5. **Update the `Last consolidated` date** at the top of master-profile.md.

Don't fabricate or upgrade claims. If a detail is missing, **ask** — never
invent one to complete a sentence.

---

## LOOP 2 — "I'm applying to <company>" (produce a tailored PDF)

This is what `/resume-build` automates. The manual version, for when you want to
do it yourself:

0. **If the role is still being chosen,** follow `profile/research-protocol.md`
   first. A job-board row is a company signal, never the role list — enumerate
   the company's actual board and open the application form before deciding.

1. **Capture the role.**
   ```bash
   ./new-company.sh <company> <region>
   ```
   Then paste the JD into `applications/<company>/job-description.md`
   **verbatim**. Not a summary. The exact requirement phrasing is what the
   proof-point map keys off, and a paraphrase degrades every bullet built from
   it. While you're there, enumerate the application form's fields into the same
   file — the form is part of the job description, and its dropdowns routinely
   carry role taxonomy the posting body omits.

2. **Decide the audience** — which of master-profile §5's columns this reader
   sits in — and write it in `notes.md` with one line of why. This single
   decision drives every override that follows.

3. **Tailor.** In `applications/<company>/resume.tex`, `\renewcommand` **only**
   what changes.
   - §6 settled wordings get pasted, not improved.
   - Reorder and trim. Don't reword. If your tailored bullet shares almost no
     words with the source bullet, you regenerated it — start again.
   - Optional blocks exist for exactly this: switch on the one that answers a
     JD line, leave the rest off.
   - Experience always precedes Projects.

4. **Build, and let the gates run.**
   ```bash
   ./build.sh <company>
   ```
   Read the report. Fix every FAIL. For each WARN, either fix it or write one
   line in `notes.md` saying why it stands. Then **read the rendered PDF and say
   the bullets aloud** — the gates catch geometry and vocabulary, not a sentence
   that's awkward to speak.

5. **Adversarial review.** Run `profile/evaluator-brief.md`. If any finding
   changed the PDF, rebuild and run it **again**, fresh. Report both scores.

6. **Record it** in `notes.md`. Every slot filled. A blank slot means the step
   was skipped, and that visibility is the point.

7. **Fill the form.** From `profile/application-facts.md`, never from memory.
   Everything in its §7 gets left blank and named in the hand-back.

8. **You submit.** Always. No skill in this repo clicks that button.

---

## Build commands

```bash
./setup-check.sh                    # verify the toolchain before anything else
./new-company.sh <company> <region> # scaffold an application folder
./build.sh <company>                # build + run the gates
./build.sh                          # build every application
./build.sh base                     # the untailored all-defaults preview
./build.sh --no-check <company>     # skip gates (fast iteration only)
pdfinfo dist/<file>.pdf | grep Pages
python3 pipeline/preflight.py --json dist/<file>.pdf
```

## Where everything lives

| Path | What it is |
|---|---|
| `profile/master-profile.md` | The knowledge base. The asset. |
| `profile/application-facts.md` | Every form answer, decided once |
| `profile/lexicon.json` | The word gates — yours to grow |
| `profile/evaluator-brief.md` | The cold adversarial read |
| `profile/research-protocol.md` | How roles get found and indexed |
| `profile/pipeline-design.md` | Why the pipeline is shaped this way |
| `shared/blocks.tex` | Every résumé entry, once |
| `config.json` | Identity, locale, scoring weights, sources |
| `applications/<slug>/` | One folder per application |
| `dist/` | Built PDFs — what you actually upload |
