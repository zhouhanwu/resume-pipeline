# resume-pipeline

A job-application system that runs inside [Claude Code](https://claude.com/claude-code).
It finds roles, tailors a one-page résumé for each one, checks the page
mechanically, has a cold reader tear it apart, and fills in the application
form — then stops and hands it to you to send.

**It never clicks submit.** That part is yours, deliberately and permanently.

```
  /jobscan          →  you promote what you want  →  /resume-build
  find + rank roles     (selection is yours)          tailor + gate + fill form
                                                      → you vet and submit
```

---

## Start here

```bash
git clone <this repo> && cd resume-pipeline
./setup-check.sh          # is this machine ready?
claude                    # then, in Claude Code:
/setup
```

**`/setup` is the front door and it does the work.** It checks your toolchain,
reads your existing CV, asks you a handful of questions, and writes every file this system needs — your knowledge base,
your form answers, your honesty rules, your résumé content, your Notion tracker.
You never edit JSON and you never read the codebase.

You can stop and resume; it tracks which phases are done.

**Want to see it work first?** The repo ships with a complete fictional
candidate, so it builds on clone:

```bash
./build.sh --example base            # the untailored preview
./build.sh --example example-corp    # a finished, tailored application
```

Then read `applications/example-corp/` — the JD, the tailoring decisions in
`resume.tex`, and the audit trail in `notes.md`. That folder is the best
explanation of what this system does.

## Requirements

| | |
|---|---|
| **Required** | Python 3.8+, `pdflatex` (MacTeX / TeX Live), `poppler` (`pdftotext`, `pdfinfo`) |
| **For form-filling and live postings** | Chrome + the Claude for Chrome extension |
| **For `/jobscan` and the build queue** | A Notion account (free tier is fine) |

`./setup-check.sh` tells you which of these you're missing and the command to
fix it.

You can use this system with **none** of the optional pieces — writing JDs by
hand and running `./build.sh` — and it still does the part that matters most.

## What's actually in here

### The idea

Most résumé tooling optimises the wrong thing. It makes it fast to produce many
documents, when the actual constraint is that **one good page requires knowing a
lot about yourself and being honest about it.**

So the centre of this repo is not the LaTeX. It is
`profile/master-profile.md`: a long, uncompressed record of everything you've
done — every metric, which ones you could defend under questioning, what was
*hard*, and which kind of reader cares about which part. Every résumé this
system produces is a lossy compression of that file. Tooling downstream cannot
improve on a thin one.

`/setup` exists because writing that file from a blank page is miserable, and
answering questions about your own work is not.

### The gates

Rules that are written down get followed while attention is fresh and skipped
when it isn't. So every rule that can be measured, is — on the built PDF, on
every build:

| Gate | What it catches |
|---|---|
| **one page** | Two pages is a defect. `pdfinfo`, not a cached metadata read. |
| **page fill** | A page that stops three-quarters down is a wasted application. Judging this by eye fails: pages that read as "roughly full" measure 84–89%. |
| **orphan tails** | A bullet whose last line carries three words burns a whole line. |
| **settled wordings** | Wordings you already chose, being silently re-derived. |
| **truth rules** | Claims you've explicitly ruled out — the important one. |
| **semicolon splices** | Two facts fused into one sentence to win a line. |
| **vocabulary** | *leveraged*, *stakeholder alignment*, *proven track record*. |
| **spelling variant** | One of en-GB or en-US, consistently. |

`./build.sh` exits non-zero on any FAIL. A WARN is not a pass — fix it, or write
one line in `notes.md` saying why it stands.

### The truth rules

The part most worth stealing even if you never run the rest.

During setup you get asked, for every project: *"you said you built this — did
you write the code, or integrate and configure it?"* *"Was this solo or a team?"*
*"Is that number from your own analytics or something audited?"*

Each answer that constrains a claim becomes a rule in `CLAUDE.md` **and** a
mechanical check in `profile/lexicon.json`. After that, a tailoring pass
physically cannot promote you: the build fails.

This matters because the failure mode isn't lying. It's that "co-founded a
startup where I directed an AI-assisted build" compresses, over three tailoring
passes, into "built a full-stack application" — and then an interviewer says
"walk me through your architecture" and the whole page dies with it.

### The adversarial review

Before anything ships, a **fresh agent with no memory and no access to this
repo** gets the job description and the built PDF, and nothing else. It's told
to be brutal and to default to reject. It scores the page out of 100 and says
what would bin it.

If any of its findings change the PDF, a **second** fresh agent scores the
rebuild. You get both numbers and the delta, because a score you didn't re-check
is a guess.

Its verdict is advice, not authority. It doesn't know what's true, so it will
sometimes call an honest claim thin and push you toward one the truth rules
forbid. Declining a finding, with the reason written down, is a good outcome.

### The boundaries

Hard-coded, not configurable:

- **Never clicks submit**, and never ticks a certification checkbox. Including
  one-click apply flows — being one click from sending is a reason for more
  caution, not less.
- **Never creates an account or types a password.**
- **Never enters a government identifier, bank detail or full date of birth.**
  These are deliberately not stored anywhere in the repo.
- **Never writes your "why this firm" answers.** Those are left blank and handed
  back to you with the question text, because an unedited draft that slips
  through review goes out in your voice.
- **Never writes your cover letter.** Same reason, more so.

## Layout

```
CLAUDE.md                  the doctrine — the rules every build follows
config.json                you: name, regions, locale, scoring weights, sources
profile/
  master-profile.md        THE ASSET. Everything you've done, uncompressed.
  application-facts.md     every form answer, decided once
  lexicon.json             the word gates — yours to grow
  evaluator-brief.md       the cold adversarial read
  research-protocol.md     how roles get found without fooling yourself
  pipeline-design.md       why it's shaped this way
  HOW-TO.md                the two working loops
shared/blocks.tex          every résumé entry, written once, inherited everywhere
applications/<slug>/       one folder per application: JD, overrides, audit trail
pipeline/                  Notion I/O, ranking, the gates
dist/                      built PDFs — what you upload
```

An application inherits every block and `\renewcommand`s only what it tailors.
Fix a date in one place and it flows into every future application.

## The loop people skip

Tell Claude when you do something new — a project, a metric, a job. It files the
full context into `master-profile.md`, asks the honesty questions while the facts
are fresh, and updates the shared blocks if it changes a default.

Everything else here is machinery for turning that file into pages. None of it
improves the source material. A knowledge base that stops being fed produces
worse résumés every month, and the tooling will not tell you that's happening.

## Licence

MIT — see [LICENSE](LICENSE). Built by [Zhouhan Wu](https://github.com/zhouhanwu).

If you use it and something is confusing, that's a bug in the setup flow rather
than in you; issues welcome.
