# Manual setup

**You probably don't need this file.** Run `/setup` in Claude Code and it does
all of the below by interviewing you.

This is the fallback: for when a `/setup` phase fails, when you'd rather do it
by hand, or when you want to know exactly what got written and where.

---

## 0. Prerequisites

```bash
./setup-check.sh
```

| Tool | Install | Needed for |
|---|---|---|
| Python 3.8+ | preinstalled on macOS; `apt install python3` | everything |
| `pdflatex` | macOS: `brew install --cask mactex-no-gui`<br>Debian: `apt install texlive-latex-recommended` | building the PDF |
| `pdftotext`, `pdfinfo` | macOS: `brew install poppler`<br>Debian: `apt install poppler-utils` | the gates |
| Chrome + Claude for Chrome | [claude.com](https://claude.com) | reading live postings, filling forms |
| Notion account | free tier | `/jobscan`, the build queue |

MacTeX is a large download. `mactex-no-gui` is the smaller one and is enough.

## 1. `config.json`

Copy the example and edit:

```bash
cp config.example.json config.json
```

Then:

- **Delete the `_example` and `_example_note` keys.** While `_example` is true,
  `build.sh` refuses to build anything but the worked example — that guard
  exists so nobody accidentally uploads a fictional person's CV.
- Fill `identity`: `name`, `file_name` (used in the PDF filename, no spaces),
  `email`, `links`.
- Fill `regions.phones` with one entry per region you apply into. The region key
  is what you pass to `./new-company.sh`, and it only ever selects the phone
  number on the page.
- Set `locale.spelling` to `"en-GB"` or `"en-US"` — or `null` to turn the
  spelling gate off. Consistency is the point.

  > Note: the shipped example content is British English. If you set `en-US`
  > before replacing it in step 5, `./build.sh --example base` will FAIL the
  > spelling gate. That's the gate working correctly on content that isn't
  > yours yet.
- Leave `rank`, `sources` and `queue` alone until you have a reason.

Check it took:

```bash
python3 pipeline/gen_identity.py    # writes shared/identity.tex
```

Nothing about you is hardcoded in any `.tex` file; that script regenerates
`shared/identity.tex` from `config.json` before every build.

## 2. `profile/master-profile.md` — the actual work

**This is the file that determines output quality, and it is the one nobody can
write for you.** Read the shipped example first — the fictional candidate's
version shows the shape and, more usefully, shows how much longer each entry is
than the bullets that come out of it.

For each thing you've done, record:

- **Scope** — what was yours, what was the team's, how many people
- **What you actually did** — methods and tools, named specifically
- **Numbers** — and separately, **which ones you could defend if pushed**
- **What was hard** — the most valuable line in the entry, and the one most
  often left out. It's what interviewers ask about.
- **Per-audience emphasis** — which reader cares about which part

Then §1 (what you're optimising for; the honest split between roles you *fit*
and roles you're *positioning* for), §2 (geography), §5 (the
**proof-point-to-audience map** — the table that decides what goes on which
version of the page), §6 (the canonical-wordings ledger), Appendix A (truth
rules), Appendix B (skills with honest ownership tags), Appendix C (known gaps).

Write it long. An entry written at résumé length leaves a later tailoring pass
nothing to do but reword, and rewording is exactly what the voice rules forbid.

## 3. `profile/application-facts.md`

Every answer every form asks for, decided once. Work through all nine sections.

Three need care:

- **§2 right to work is three separate questions** — "do you have the right to
  work?", "do you need sponsorship now?", "will you need sponsorship in future?"
  Forms ask them separately and they have different answers. Collapsing them is
  one of the few form errors that triggers an automatic rejection.
- **§4 work history** wants contract titles and confirmed months, which often
  differ from what's on your CV.
- **§7 is the never-fill list** — read it and make it yours. It's a standing
  instruction to `/resume-build`.

**Do not put a passport number, national ID, NI/tax number, bank detail or full
date of birth in this file.** They're excluded on purpose. You type those on
each form yourself.

## 4. `CLAUDE.md` truth rules and `profile/lexicon.json`

Replace everything between the `<!-- BEGIN TRUTH RULES -->` and
`<!-- END TRUTH RULES -->` markers in `CLAUDE.md` with your own.

A truth rule names a claim that is *almost* true and pins the wording to the
version that survives a follow-up question. Ask yourself, per project:

- Did I write this code, or direct and configure it?
- Solo or a team — and what was mine?
- Is this the contract title or the descriptive one?
- Shipped to real users, or coursework?
- Is that number audited, or from my own analytics?
- Achieved grade, or predicted?

For each rule, also add the forbidden phrasing to `profile/lexicon.json` under
`rejected_wordings.pairs` as `["forbidden phrase", "use this instead"]`, so the
build gate catches it mechanically. Delete the placeholder `example-overclaim`
pair.

While you're in there: add the words that make you wince to
`banned_vocab.words`, and record the words that are genuinely yours in
`master-profile.md` §6, so no later pass smooths them away.

## 5. `shared/blocks.tex`

Replace the example candidate's entries with yours.

- `\h<Name>` = heading line, `\x<Name>` = its bullets. One pair per entry.
- Take the lines from your existing CV and rewrite them into this structure,
  keeping your phrasing. Don't compose from scratch if you don't have to.
- Month-precise dates.
- Define two or three **optional** blocks — bullets that answer one specific
  kind of JD line — and leave them out of the default `\ResumeBody`. They're
  what you add when the fill gate says a line is free.
- In `\ResumeBody`: **Experience before Projects**, and **no headless entries**
  (every `\h...` needs a matching `\Bullets{...}`).

Then:

```bash
./build.sh base
```

and iterate until `Pages: 1` and fill ≥95%. Expect several passes; that's normal.

## 6. Notion (optional)

Full instructions in [`pipeline/NOTION-SETUP.md`](pipeline/NOTION-SETUP.md).
Short version:

```bash
# 1. Create an integration at notion.so/my-integrations (Read/Update/Insert)
# 2. export NOTION_TOKEN='ntn_...' in ~/.zshenv  — NOT ~/.zshrc, see below
# 3. Create a "Jobs" page and connect the integration to it
python3 pipeline/notion_bootstrap.py --parent "<your Jobs page URL>"
python3 pipeline/notion_pull.py --out-dir /tmp/check --queue
```

> **The `.zshenv` trap.** Claude Code's Bash tool spawns a non-interactive
> shell, and zsh only reads `.zshrc` for interactive ones. A token in `.zshrc`
> works when you type commands yourself and is invisible to every script Claude
> runs. This costs people an hour; don't let it cost you one.

Then seed the **Target Companies** table with firms you'd actually work for, at
`Watch Status = Active`. `/jobscan`'s coverage is exactly that list plus any
aggregators you enable in `config.json` — a company on neither never appears.

## 7. Clean up the example

Once you've built something of your own:

```bash
rm -rf applications/example-corp
```

## 8. Check your work

```bash
./setup-check.sh                    # no warnings about the example config
./build.sh base                     # Pages: 1, fill >=95%, no FAILs
python3 pipeline/rank.py --selftest # SELFTEST PASSED
python3 pipeline/notion_bootstrap.py --verify   # if you did step 6
```

Then read [`profile/HOW-TO.md`](profile/HOW-TO.md) — now that the files have
something in them, it will make sense.
