# Research protocol — finding and indexing roles before a résumé gets built

The failure mode this exists to stop: **stopping when there's enough to write a
confident answer, rather than when the source is exhausted.** The counter is to
replace judgement about sufficiency with a checklist about enumeration. Count
things. State the count.

Read this before recommending which roles to apply to, not after.

---

## The rules

**R1 — Enumerate, don't sample.** Never recommend from a partial list. For each
company, obtain the *complete* role list and state the number. A job-board row is
a discovery signal that a company is hiring — it is never the role list. A
tracker showing one role at a firm that has fourteen open is the normal case,
not the exception.

**R2 — The application form is part of the job description.** Open it before
concluding. Track selectors, area preferences, eligibility questions and required
attachments routinely carry role taxonomy that the posting body omits — a single
"Internships" posting can be two or four distinct roles, distinguishable only
inside a form dropdown.

**R3 — Cite the posting you are recommending, not a neighbour.** Record the
posting ID next to every quoted requirement. If the target posting is thin and
you are inferring from a sibling or a full-time equivalent, write "inferring from
<id>" in the output itself. A proxy must never become the source silently.
Quoting a full-time spec as though it were the internship produces a
recommendation built on requirements that don't apply.

**R4 — Quote to the end of the sentence.** Truncating at a clause boundary can
invert meaning. "We primarily work with Python, C++ and Rust" cut before "*but we
care more about how you think than the languages you've used*" turns a soft
preference into a hard barrier.

**R5 — A failed extraction is a blocker, not a finding.** If a page defeats a
tool — popup, lazy load, CSP, permission gate, wrong DOM node — report "could not
extract" and retry with a different tool. Never convert it into "nothing relevant
there." **Apply this most strictly when you already have an independent reason to
want to skip that company**; a convenient narrative is exactly when this fails.

**R6 — Exhaust lazy lists.** Boards paginate, virtualise, or hide behind "Show
more". Loop the control to exhaustion and confirm the loaded count matches the
stated count before reading. A board can report "56 open jobs" and render twelve
until a button is clicked five times.

**R7 — Rank on role fit. Constraints are flags, not filters.** Visa sponsorship,
location, language, deadline and relocation get surfaced as notes for the
candidate to weigh. Never use one to silently demote or drop a role. They decide
what is negotiable — and for internships, sponsorship often is.

**R8 — Verify a disqualifier before it disqualifies.** If a reason for skipping
is checkable, check it or don't use it. A wrong reason sitting next to three
sound ones contaminates all four.

**R9 — Separate verified from inferred, and say what you failed to get.** Every
line of a recommendation should be traceable to something actually read. An
explicit "I could not retrieve X" is a good outcome; a silent gap is not.

**R10 — Score against master-profile §1, not generic prestige.** §1 already ranks
*fit* against *positioning* and names which bucket is the owned floor and which
is aspirational. Apply that ranking without being asked. A well-matched role at
an unglamorous firm outranks a poorly-matched one at a famous firm, and the
profile says so explicitly.

**R11 — Check for a per-firm application cap before spending a slot**, and record
it in `notes.md`. Where a cap exists, *which* roles to spend it on is a decision
to surface, never to make alone.

**R12 — Ask the constraint questions early, not after building.** Whether a cap
is real, whether an application is already submitted, whether relocation is
acceptable — these change the ranking and cost nothing to ask up front.

**R13 — Never re-filter the user's own filters.** A saved filter on a job source
*is* the curation. Applying a second filter on top silently overrides the
candidate's judgement and — worse — hides what was discarded, so they cannot
correct you. This also breaks R7: a low-relevance role should sink on score,
visibly, not vanish before anyone sees it.

**R14 — Assert page state, never assume it.** Single-page apps restore prior
pagination, filters and scroll position across visits. A sweep that assumes it
starts at page 1 will silently miss page 1 — and page 1 is where the newest
postings are. Always click to the first page explicitly, then iterate, and log
per-page row counts so a missing page is visible.

**R15 — Reconcile against the source's own count.** Every paginated source states
a total. Compare your unique count to it and **report the gap**, never absorb it.
A dedupe key of `company||title` will collapse the same role in two cities into
one row; if location matters to the candidate — and it usually does — the key
must include it.

**R16 — Validate parsed values against their expected set, not just for
emptiness.** A column-misaligned row produces confident nonsense that passes
every non-empty check. If a value isn't in the known option set for that field,
flag the row rather than filing it. The same applies to dates: a parser built on
one format will silently misclassify rows written in another, and a value that
fails to parse is a flag, not a null.

---

## Established tool facts

Recorded so the exploration doesn't have to repeat.

### Resolving a company to its ATS — never guess the token

Guessing Greenhouse/Lever tokens from a company name has a measured hit rate of
roughly **1 in 8**. Don't do it.

The method that works, about 2–4 calls per company:

1. Open the company's careers page in Chrome (`<company>.com/careers`, or search).
2. Scan every outbound link's hostname for an ATS signature: `greenhouse`,
   `lever`, `ashby`, `workday`, `smartrecruiters`, `teamtailor`, `recruitee`,
   `personio`, `eightfold`, `icims`, `taleo`, `successfactors`, `tal.net`,
   `smartr.me`.
3. The homepage often has none — the listings sit one click deeper behind
   "Search roles" or "Browse all jobs". Follow that, then re-scan.
4. Extract the token from the path (`greenhouse.io/<token>/`, `lever.co/<co>/`).

The failure this prevents: a company whose name resolves to nothing on Greenhouse
or Lever may simply be on a less common ATS, and no amount of token-guessing will
find it. One link-scan will.

**This is a pipeline function, not a manual one.** Resolve on first encounter,
cache the result in the Target Companies row's `ATS` and `Board Token` columns,
and only re-resolve when a board 404s.

### Reaching job boards

| Source | Behaviour |
|---|---|
| Greenhouse | Public JSON, no auth: `boards-api.greenhouse.io/v1/boards/<token>/jobs` and `/jobs/<id>?content=true` for the full body. EU boards live at `job-boards.eu.greenhouse.io`; the matching EU API host may not resolve — page-scrape those. |
| Lever | Public JSON, no auth: `api.lever.co/v0/postings/<company>?mode=json`. Postings carry `lists` (requirements) and `descriptionPlain`. |
| Ashby | Public JSON, no auth: `api.ashbyhq.com/posting-api/job-board/<token>`. |
| SmartRecruiters | Public JSON, no auth: `api.smartrecruiters.com/v1/companies/<token>/postings?limit=100&offset=N`. |
| Workable | Public JSON, no auth: `apply.workable.com/api/v1/widget/accounts/<token>?details=true`. |
| Workday | Public JSON, no auth: `POST https://<tenant>.<host>/wday/cxs/<tenant>/<site>/jobs`, body `{"appliedFacets":{},"limit":20,"offset":N,"searchText":""}`. **See the two quirks below — both silently truncate a sweep.** |
| Eightfold | Modal on load — close it, then loop "Show More Positions". `get_page_text` can target the wrong node; use `document.body.innerText`. |
| Custom boards | Chrome only. Content often sits behind modals and form dropdowns. |
| Aggregators behind Cloudflare | Frequently **403** to server-side fetch and require Chrome. |

**Workday has two quirks that each look like a clean result:**

1. **`limit` must be exactly 20.** `limit=50` and `limit=100` return zero rows —
   not an error, an empty `jobPostings`. A loop that breaks on an empty page ends
   instantly and reports a complete-looking sweep of nothing.
2. **`total` is only meaningful on the first page.** Every later page returns
   `total: 0` while still carrying real rows. An `offset >= total` break
   condition therefore stops after page 2. The tell is several unrelated boards
   all reporting exactly the same round number of postings. Read `total` once
   from page 0, then paginate until a genuinely empty page.

**Fetch large payloads inside Chrome, not with a summarising web-fetch tool.**
A tool that summarises a page through a small model will quietly drop the exact
requirement phrasing the proof-point map keys off.

---

## Done-check before recommending

Do not produce a recommendation until every line here has an answer:

- [ ] For every company considered: the **complete** role list, with a count
- [ ] For every recommended role: the application form opened and its fields read
- [ ] Every quoted requirement carries its posting ID
- [ ] Every quote runs to the end of its sentence
- [ ] Every failed extraction named explicitly, not absorbed
- [ ] Paginated sources reconciled against their own stated totals
- [ ] Constraints surfaced as flags, with nothing silently filtered out
- [ ] Per-firm application caps checked and recorded
