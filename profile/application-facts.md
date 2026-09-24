# Application facts — the answer set every form asks for

> **THIS IS THE WORKED EXAMPLE.** `/setup` replaces it with yours.
>
> **What this file is for.** Every application form asks the same forty
> questions. Deciding each one once, here, means `/resume-build` can fill a form
> without asking you anything, and means the answers are consistent across every
> application instead of being improvised at 1am.
>
> **Read it before filling any field, and never re-ask what it already records.**
>
> **What is deliberately NOT here, and never will be:** passport number,
> national ID, NI / tax number, bank details, full date of birth, driving
> licence, any government identifier. The candidate types those himself, every
> time. They are not in this file, and no skill in this repo may enter one.

**Last updated:** 2026-09-24

---

## 1. Identity and contact

| Field | Answer | Trap |
|---|---|---|
| Full name | **Alex Mercer** | Given name first on everything outgoing |
| Preferred name | Alex | |
| Email | alex.mercer@example.com | The same one on the CV. Always. |
| Phone (UK roles) | +44 7700 900142 | **Region-matched to the ROLE, not to where you are** |
| Phone (IE/EU roles) | +353 20 915 0142 | |
| Term-time address | 14 Oxford Road, Manchester M13 9PL | Different field from home address |
| Home address | 8 Beckett Lane, Leeds LS6 2AT | |
| LinkedIn | linkedin.com/in/alexmercer | |
| GitHub | github.com/alexmercer | |
| Generic "Website" / "Personal website" | github.com/alexmercer | If you have a personal domain, it goes here instead of the GitHub URL |

## 2. Right to work — three questions, three answers

**These are three different questions and forms ask them separately. Never
collapse them.** Getting this wrong is one of the few form errors that gets an
application auto-rejected.

| Question as asked | Answer |
|---|---|
| "Do you have the right to work in the UK?" | **Yes** |
| "Will you now require sponsorship for employment visa status?" | **No** |
| "Will you in the future require sponsorship?" | **No** |
| "Are you legally authorised to work in the EU?" | **No** — British citizen, post-Brexit. An employer permit would be needed. |
| Nationality | British |
| Visa type held | n/a — citizen |

## 3. Education

| Field | Answer |
|---|---|
| University | University of Manchester |
| Degree | BSc Computer Science & Statistics |
| Start / expected end | September 2024 / June 2027 |
| Year of study (2026/27) | Penultimate |
| Expected graduation year | 2027 |
| Current classification | **First-class (predicted)** — see note below |
| Year 1 average | 78% |
| A-levels | Mathematics A*, Further Mathematics A*, Physics A |
| GCSEs | 9 subjects, grades 9–7 (specifics on request) |
| UCAS tariff | **Leave blank.** Flag it; the candidate fills it. |

> **"Predicted First" is a per-application toggle — ask.** Some forms want a
> predicted classification and some ask for an achieved one. A predicted grade
> stated as achieved is a lie on a form you signed. When a form is ambiguous,
> ask rather than guess.

## 4. Work history — as forms want it

Forms want month precision and the title as it appeared on the contract, which
is not always the title on the CV. Use this table, not the CV.

| Employer | Title on contract | From | To | Location |
|---|---|---|---|---|
| Northwind Logistics | Data Analyst Intern | Jun 2025 | Sep 2025 | Leeds, UK |
| University of Manchester | Undergraduate Teaching Assistant | Sep 2025 | Present | Manchester, UK |

**Ridgeline is not employment.** It was a co-founded side project with no
contract and no salary. On a work-history form it goes under "other experience"
if there is such a section, and is left off if there isn't. Never listed as
employment.

## 5. Documents

| Document | Path | Note |
|---|---|---|
| CV | `dist/AlexMercer-Resume-<Company>.pdf` | The tailored one for *this* application |
| Cover letter | `dist/AlexMercer-CoverLetter-<Company>.pdf` | **Only if the candidate wrote one** — see §7 |
| Transcript | **Leave blank.** Flag it. | |
| Portfolio | github.com/alexmercer | |

## 6. Standard multiple-choice answers

| Question | Answer |
|---|---|
| How did you hear about this role? | Company website (unless a specific source applies) |
| Have you previously applied to this firm? | **Read it off the Notion tracker. Never guess.** |
| Have you previously been employed by this firm? | No |
| Do you have any family employed here? | No |
| Earliest start date | 8 June 2026 |
| Latest end date | 25 September 2026 |
| Willing to relocate? | Yes |
| Require any adjustments for interview? | No |
| Notice period | None |
| Expected salary | **Leave blank** where possible; "negotiable" where mandatory |

## 7. What is never auto-filled — leave blank, flag every one

These are standing decisions, not oversights. Each one gets left empty and
reported back in full.

- **Category B questions** — "why this firm", "describe a time when", anything
  needing a personal story or an opinion. Leave the field **empty** and record
  the exact question text in the hand-back. Never draft into a live field: an
  unedited draft that slips through review goes out in the candidate's name.
- **Cover letters.** The candidate writes these. Even where the posting lists
  one as required. Flag it; don't draft it.
- **Referees.** Never auto-filled, ever. The candidate names them, having asked
  permission first.
- **Demographic questions.** Select "prefer not to say" wherever that option
  exists. Where it does **not** exist and the field is mandatory, stop and hand
  the form back.
- **Transcript · UCAS tariff · supervisor names and contacts** — deliberately
  blank, not missing.
- **Passport · national ID · NI/tax number · bank details · full DOB · any
  government identifier** — the candidate types these himself, always.
- **Account creation and passwords.** Never create an account, never type a
  password. Pause and hand back.
- **The submit button, and any certification or declaration checkbox.** No
  exceptions, including one-click apply flows.

## 8. Referees

Two are usually asked for. Both have agreed in principle, but **permission is
asked again per application**, because being listed on eleven forms without
knowing is how a good reference turns into a bad one.

1. Operations manager, Northwind Logistics — direct supervisor for the
   internship. *Contact details held by the candidate; not recorded here.*
2. Personal tutor, University of Manchester. *Same.*

## 9. Per-firm notes that recur

Where a specific employer needs a specific answer, record it here as you
discover it — an application portal that rejects a particular date format, a
firm that asks an unusual eligibility question, a graduate scheme with its own
definition of "penultimate year".

| Firm | Note | Recorded |
|---|---|---|
| _(example)_ Example Corp | Asks the three right-to-work questions separately on one page; answer each individually | 2026-09-24 |

## Fill-me checklist

Before a form is handed back as finished, every one of these has an answer or an
explicit flag:

- [ ] Name, email, region-matched phone
- [ ] Both addresses, if both fields exist
- [ ] Three right-to-work questions, answered separately
- [ ] Education block, with the predicted-classification question asked if ambiguous
- [ ] Work history from §4's table, not from the CV
- [ ] CV uploaded — the tailored one for this application
- [ ] Every MCQ in §6
- [ ] Track / area dropdown set to the track this build was tailored for
- [ ] Every §7 item left blank **and named in the hand-back**
- [ ] Screenshot of the final state, read back before leaving the tab
