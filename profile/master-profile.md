# Master Career Profile — Alex Mercer

> **THIS IS THE WORKED EXAMPLE.** Everything below belongs to a fictional
> candidate and exists to show you the shape of the file. `/setup` replaces it
> entirely with yours, written from an interview about your own work.
>
> **Read it before you replace it.** This is the single most important file in
> the repo, and it is the one nobody else can write for you. Every bullet on
> every résumé this system produces is drawn from here, which means the quality
> ceiling of the output is set by the quality of this file and nothing else.
>
> The thing to notice is how much longer each entry is than the bullets that
> come out of it. That is deliberate. §3 holds the *full* context — what was
> hard, what you'd say if asked a follow-up, the numbers you can defend and the
> ones you can't — so that a tailoring pass has something to select from. An
> entry written at résumé length gives a tailoring pass nothing to do but
> reword, and rewording is the defect Rule 4 exists to stop.

**Last consolidated:** 2026-09-24

---

## 0. Identity, contact, and current status

- **Name:** Alex Mercer (given name first on everything outgoing)
- **Email:** alex.mercer@example.com
- **Links:** linkedin.com/in/alexmercer · github.com/alexmercer
- **Phone:** +44 7700 900142 (UK) · +353 20 915 0142 (IE)
- **Current status:** Penultimate-year BSc Computer Science & Statistics,
  University of Manchester. Graduating June 2027.
- **Right to work:** British citizen. No sponsorship required, now or in future.
- **Availability:** 8 June – 25 September 2026 (summer vacation).

## 1. Career aspirations & direction

### What I'm optimising for

Work where I can see the thing I built being used, and where somebody will tell
me when it's wrong. I'd rather be the person who finds out why a number is
wrong than the person who builds a model three layers removed from anyone using
it. That's a real preference, not modesty — the Northwind scanner bug was the
most satisfying month of my life so far.

Secondary: a team where I'm the least experienced person in the room. I learn
by being corrected, and I've had two years of that from the teaching side.

### Target roles — the honest split between *fit* and *positioning*

| Bucket | Honest read |
|---|---|
| **Data analyst / analytics engineer** | The owned floor. I have done this job, for money, and the Northwind bullets are all defensible in depth. |
| **Data science / applied ML intern** | Strong positioning. The bike-share project is real and the methodology is sound, but it was coursework with a clean dataset, and I should not pretend otherwise in an interview. |
| **Software engineering** | Stretch. I can write Python and Java and I've shipped something people used, but I have no systems-design depth and no production on-call experience. Applying, honestly framed, not leading with it. |
| **Quant research** | Not yet. No stochastic calculus, no C++. Listing it here so the ranking doesn't quietly drift toward it. |

## 2. Geographic preferences

1. **Manchester / Leeds** — home, no relocation cost, family nearby.
2. **London** — happy to, and where most of the roles are. Would need the
   salary to cover it; a summer internship at London rates usually does.
3. **Remote (UK)** — fine, though I'd rather not for a first internship.
4. **Dublin / EU** — open to it. British passport, so post-Brexit that means
   the employer handles a permit. Flag rather than filter.

## 3. Accomplishments in full

> The working rule for this section: write down everything, including the parts
> that don't fit on a page. What was hard, what broke, what you'd say if the
> interviewer asked a second question. A résumé bullet is a lossy compression
> of one of these entries — you cannot decompress what was never written down.

### Northwind Logistics — Data Analyst Intern (Leeds; Jun–Sep 2025)

**Scope.** 12-week paid internship in a 400-person regional logistics firm,
sitting with the operations team rather than in a data function. No other
analysts. Reported to the operations manager, who is not technical.

**What I actually did.**

- Inherited a weekly "delivery exception report" that two people rebuilt by
  hand every Monday morning in Excel, taking about four hours between them,
  ahead of the depot review meeting. Rebuilt it as a SQL view over the
  warehouse plus a scheduled job. It has run unattended since September 2025.
- While validating the rebuild against the manual version, found the two
  disagreed on about 60% of flagged exceptions. Traced it to one depot's
  handheld scanners being configured with a different timestamp convention, so
  scans that happened inside the delivery window were recorded as outside it.
  Those had been logged as driver error for the previous eight months —
  roughly 4,000 deliveries — and two drivers had been through performance
  conversations over it.
- Built a depot-level dashboard in Power BI. The thing I'd want an interviewer
  to ask about: I agreed every metric definition with the operations lead
  *before* building anything, because the depot already had numbers printed on
  a wall chart and a dashboard that disagreed with the wall would have been
  ignored entirely.
- Wrote the handover documentation the operations team still works from.

**What was hard.** Nobody could tell me what "on time" meant. Three people gave
three definitions, and all three were in use somewhere. Getting to one agreed
definition took three weeks and was most of the actual work — far more than the
SQL.

**Numbers I can defend:** four hours → zero, two people → nobody; 60% of flagged
exceptions misattributed; ~4,000 deliveries over eight months; runs unattended
since September 2025.
**Numbers I cannot:** any money figure. I was never shown the cost side, and I
should not estimate one on a CV.

**Per-audience emphasis.** Analytics: the metric-definition negotiation.
DS/ML: the data-quality root-cause. SWE: the scheduled job and the handover doc,
though this is the weakest framing of the three.

### Ridgeline — Route Planning App for Hikers (Manchester; Jan–Nov 2025)

**Titling: "Co-Founder".** See Appendix A.1 — this is settled and it is not a
per-application choice.

**Scope.** Co-founded with one other student. Reached ~400 registered users and
~1,200 saved routes across ten months. Wound down in November 2025 when we both
ran out of time; it is not running now, so it is described in the past tense.

**What I actually did.**

- Designed the route-scoring heuristic: elevation gain, surface type, and
  daylight remaining against estimated pace. The part I'd defend in an
  interview is how I found out the first version was wrong — I walked the first
  twelve routes it suggested, and six of them were unwalkable in winter
  conditions because the surface data didn't distinguish a maintained path from
  a moorland trace.
- Diagnosed the sync failure that silently dropped saved routes. Users reported
  it as "the app forgot my route" with no pattern. Traced it to a cache key
  built from a local timestamp, so a device whose timezone shifted — or a user
  who crossed a boundary — got a key that never matched. Reproduced it by
  shifting the device clock forward a day. Support reports about lost routes
  went to zero.
- Ran a fortnightly call with eight regular users for six months. Shipped the
  two changes they asked for most. 30-day retention went from 22% to 41% across
  the quarter that followed.

**THE HONESTY CAVEAT, AND IT IS THE IMPORTANT PART OF THIS ENTRY.** The
application itself — React Native front end, the API, the auth — was built with
heavy AI assistance. I directed it, debugged it, and made every product
decision, but I did not write most of that code and I could not reproduce it
from scratch on a whiteboard. The two bullets above are deliberately about the
things I *reasoned* my way to: the heuristic and the sync diagnosis. Neither
depends on claiming I wrote the stack.

This is not false modesty. An interviewer who asks "walk me through your
architecture" will find out in ninety seconds, and the rest of the page dies
with it.

**Per-audience emphasis.** SWE/debugging: the sync bug, every time. Product:
the user calls and the retention number. DS/ML: weakest fit — the heuristic is
hand-tuned, not learned, and I should say so.

### Bike-Share Demand Forecasting (Manchester; Oct 2024 – Feb 2025)

**Titling: "Modelling and feature engineering, team of 4"** — my own wording,
verbatim. See Appendix A.2. It replaced "Machine Learning Engineer", which read
as a solo build.

**Scope.** Second-year group coursework. Four people. My scope was the modelling
and the feature engineering; the other three did data collection, the write-up
and the presentation.

**What I actually did.**

- Forecast hourly demand across 68 docking stations. Final model reached
  **0.81 R²** on a held-out month against a **0.63** seasonal-naive baseline.
- Built the feature set from weather, public-holiday and station-adjacency
  data. Adjacency — demand at the six nearest stations in the preceding hour —
  accounted for about a third of the improvement over the baseline. Weather
  accounted for almost none, which surprised all of us and is the most
  interesting thing in the project.
- Used rolling-origin cross-validation rather than naive k-fold, because a
  random fold on a time series leaks the future into the training set. Tuned
  with Optuna across 200 trials on a four-year hourly series.

**What was hard.** Convincing the group that the k-fold number in the first
draft — which was much better — was wrong rather than good. That took a
demonstration, not an argument.

**Honest limits.** Clean public dataset, no missing data to speak of, no
deployment, no monitoring. It is a well-executed coursework project and calling
it anything more invites a question I'd lose.

### University of Manchester — Undergraduate Teaching Assistant (Sep 2025 – present)

Weekly lab sessions for 30 first-year students on Python fundamentals; marking
against the department's rubric with individual written feedback. Rewrote the
recursion lab's worked examples after a third of the cohort stalled on the same
exercise two weeks running — the stated problem asked them to trace a call stack
before they'd been shown one.

### Manchester Data Science Society — Events Lead (Sep 2024 – Jun 2025)

Six-week practical workshop series on pandas and scikit-learn; attendance grew
15 → 60 across the run. Ran a careers evening with four alumni in data roles,
attended by 80 students from three departments.

### Academic

- **Year 1 average 78%** (First-Class), ranked **6th of 211**.
- Highest mark **91%** in Probability & Statistics.
- A-levels: Mathematics A*, Further Mathematics A*, Physics A.
- Relevant coursework: Machine Learning, Probability & Statistics, Algorithms &
  Data Structures, Databases, Linear Algebra.
- Manchester Hack 2025: 3rd of 47 teams, live-departures routing tool in 24h.

## 4. Things not yet on the résumé (or not fully written up)

Everything here is real and none of it currently earns a line. It lives here so
that when a JD makes one of them relevant, the detail already exists.

- **Homelab.** Run a small Debian server for backups and a Postgres instance I
  use for coursework. Relevant only to an infrastructure-flavoured JD.
- **Half-finished:** a scraper for council planning applications, abandoned at
  the point it needed a captcha solver. Worth mentioning in conversation as
  evidence of knowing when to stop, not on the page.
- **Reading:** working through *Designing Data-Intensive Applications*. Not a
  claim; a thing to talk about.

## 5. Positioning / narrative

### The story I tell about myself

"I like finding out why a number is wrong." Northwind is the proof, Ridgeline's
sync bug is the second proof, and the bike-share k-fold argument is the third.
Three independent instances of the same trait is a narrative; one is an anecdote.

### Core strengths (claim confidently)

- Tracing a data problem to its actual cause rather than its symptom.
- Working with non-technical people to agree what a number means before building.
- Sound time-series methodology, and knowing why it matters.

### Weaknesses / gaps I'm honest about

- **No production engineering.** Nothing I've built has been on-call.
- **AI-assisted stack on Ridgeline.** Addressed by leading with reasoning wins.
- **No C++, no deep maths.** Rules out quant research honestly, for now.

### Proof-point-to-audience matching (the core tailoring rule)

**This table is what Rule 2's "priority order" means.** Read the JD, pick the
column, fill from the top of that column down.

| Audience | Anchor (full 3 bullets) | Second | Third | Cut first |
|---|---|---|---|---|
| **Data / analytics** | Northwind | Ridgeline (user + retention) | Bike-share (2 bullets) | Hackathon line |
| **DS / applied ML** | Bike-share | Northwind | Ridgeline | Society |
| **SWE / systems** | Ridgeline (+ `\xRidgelineDebug`) | Northwind (job + handover) | Bike-share (1 bullet) | Hackathon line |
| **Breadth / rotational** | Northwind | Society + TA | Ridgeline | Bike-share 3rd bullet |

## 6. Résumé / writing preferences

### Canonical wordings — the ledger

**Rule 4a: paste these, don't re-derive them.** When a line gets rewritten by
hand, the before/after lands here in the same session, dated, and the rejected
form goes into `profile/lexicon.json` so the gate catches it next time. This
table is the mechanism that stops wording drift; it is worthless if it isn't fed.

| Date | Rejected | Settled wording | Why |
|---|---|---|---|
| 2026-02-11 | "reaching 0.81 R²" | **"achieving 0.81 R² on a held-out month"** | "Reaching" implies a target was set beforehand. It wasn't. |
| 2026-02-11 | "tuned hyperparameters" | **"optimised hyperparameters with Optuna"** | Names the tool; "tuned" reads as manual fiddling. |
| 2026-02-11 | "not naive k-fold, removing look-ahead bias" | **"instead of naive k-fold to remove look-ahead bias"** | My own phrasing. The comma version was a splice. |
| 2026-03-02 | "built a full-stack hiking app" | **"co-founded a hiking route planner"** | Truth rule A.1. The build claim is the one that fails. |
| 2026-03-02 | "Machine Learning Engineer" | **"Modelling and feature engineering, team of 4"** | Truth rule A.2. Read as a solo build. |
| 2026-05-19 | "identified that 60% of exceptions…" | **"traced 60% of flagged exceptions to…"** | "Traced" is the verb I use out loud. |

### Words that are mine — do not "improve" these

*traced*, *achieving*, *optimised*, *rebuilt*, *agreed*, *co-founded*. A
tailoring pass that smooths these into something more standard has made the page
worse.

### Words to keep out

Kept in `profile/lexicon.json` so the gate enforces them. Beyond the generic
list: I never say *spearheaded*, *drove*, or *owned the end-to-end*.

---

## Appendix A — Framing rules (truth rules)

**These override every other consideration, including filling the page.**

**A.1 — Ridgeline: "Co-Founder", never a solo-build claim.** He co-founded it;
that part is plainly true. The stack was heavily AI-assisted, so bullets lead
with own-reasoning wins and never imply he wrote it alone. Allowed:
"co-founded", "designed the route-scoring heuristic", "diagnosed". Forbidden:
"built a full-stack app", "architected", any line count, any framework name
presented as personally-written code.

**A.2 — Bike-share: "Modelling and feature engineering, team of 4".** Verbatim.
Never retitle to anything that implies a solo build.

**A.3 — "Classifier" / "applied ML", never "production ML".** Nothing here has
run in production.

**A.4 — Never fabricate a detail to fill a line.** If a detail is missing, ask.

## Appendix B — Skills inventory, with honest ownership tags

| Skill | Level | Would I defend it in a technical interview? |
|---|---|---|
| Python (pandas, NumPy, scikit-learn) | Strong | Yes |
| SQL | Strong | Yes — including window functions and query plans |
| Java | Moderate | Coursework only. Yes for syntax, no for design. |
| R | Basic | One module. On the page only if the JD names it. |
| Power BI | Moderate | Yes, from Northwind |
| PyTorch | Learning | **Labelled "(learning)" on the page. Do not remove that label.** |
| Docker | Basic | "(basic)" stays. I can run one, not debug one. |
| Git, Linux, LaTeX | Working | Yes |

## Appendix C — Known data gaps (don't fabricate these)

- No money figure for the Northwind saving. Never estimate one.
- Ridgeline's user numbers are from our own analytics and were never audited.
  "~400 registered users" is the honest phrasing; "400 active users" is not.
- Final-year module choices aren't confirmed yet. Don't list them.
