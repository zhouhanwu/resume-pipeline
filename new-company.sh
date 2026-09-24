#!/usr/bin/env bash
# ============================================================
#  new-company.sh  —  scaffold a new application folder
# ------------------------------------------------------------
#  Usage:
#    ./new-company.sh <company> <region>
#
#  <region> is any key from config.json's "regions" — it selects the phone
#  number on the page and nothing else. Use the ROLE's location, not yours.
#
#  Example:
#    ./new-company.sh acmecapital uk
#
#  Creates applications/<company>/ containing:
#    resume.tex          inherits the shared base; override blocks here
#    job-description.md  paste the JD for reference
#    notes.md            status / deadline / tailoring tracker
#
#  Then:  tailor resume.tex  ->  ./build.sh <company>
# ============================================================
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

CONFIG="$ROOT/config.json"
[ -f "$CONFIG" ] || { echo "No config.json. Run /setup first." >&2; exit 1; }

REGIONS="$(python3 -c 'import json,sys; print(" ".join(sorted(json.load(open(sys.argv[1]))["regions"]["phones"])))' "$CONFIG")"

raw="${1:-}"; region="${2:-}"
if [ -z "$raw" ] || [ -z "$region" ]; then
  echo "Usage: ./new-company.sh <company> <region>" >&2
  echo "Regions configured: $REGIONS" >&2; exit 1
fi
case " $REGIONS " in
  *" $region "*) ;;
  *) echo "Unknown region '$region'. config.json has: $REGIONS" >&2; exit 1 ;;
esac

# The override list below is read off shared/blocks.tex, so it always names the
# blocks you actually have rather than a list that drifts out of date.
HEADINGS="$(grep -oE '\\newcommand\{\\h[A-Za-z]+\}' "$ROOT/shared/blocks.tex" 2>/dev/null \
            | sed 's/.*{\\/\\/; s/}//' | tr '\n' ' ')"
BULLETS="$(grep -oE '\\newcommand\{\\x[A-Za-z]+\}' "$ROOT/shared/blocks.tex" 2>/dev/null \
            | sed 's/.*{\\/\\/; s/}//' | tr '\n' ' ')"

slug="$(printf '%s' "$raw" | tr '[:upper:] ' '[:lower:]-' | tr -cd 'a-z0-9-')"
dir="$ROOT/applications/$slug"
label="$(tr '[:lower:]' '[:upper:]' <<< "${slug:0:1}")${slug:1}"

if [ -e "$dir" ]; then
  echo "applications/$slug already exists — not overwriting." >&2; exit 1
fi
mkdir -p "$dir"

# resume.tex — inherits everything; you override only what you tailor.
# printf (not echo) so backslash sequences like \begin are preserved.
{
  printf '%s\n' "% ============================================================"
  printf '%s\n' "%  APPLICATION: $label"
  printf '%s\n' "%  Region: $region   |   Created $(date +%Y-%m-%d)"
  printf '%s\n' "% ------------------------------------------------------------"
  printf '%s\n' "%  Inherits the shared base (shared/blocks.tex). Override ONLY"
  printf '%s\n' "%  the blocks you want to tailor, then run: ./build.sh $slug"
  printf '%s\n' "%"
  printf '%s\n' "%  Available blocks to \\renewcommand (from shared/blocks.tex):"
  printf '%s\n' "%    Headings: $HEADINGS"
  printf '%s\n' "%    Bullets:  $BULLETS"
  printf '%s\n' "%    Layout:   \\ResumeBody  (reorder or drop whole sections)"
  printf '%s\n' "%"
  printf '%s\n' "%  Blocks carrying a SETTLED wording (master-profile.md section 6) are inherited"
  printf '%s\n' "%  as-is. \\renewcommand them to trim bullet count for page-fit or to reorder"
  printf '%s\n' "%  for emphasis — never to reword from scratch. Rewording every application"
  printf '%s\n' "%  is how five different versions of the same bullet end up in circulation."
  printf '%s\n' "% ============================================================"
  printf '%s\n' '\def\TargetRegion{'"$region"'}'
  printf '%s\n' '\input{../../shared/preamble.tex}'
  printf '%s\n' '\input{../../shared/blocks.tex}'
  printf '%s\n' ''
  printf '%s\n' '% ===== Your overrides go here. Example: ====='
  printf '%s\n' '% \renewcommand{\xFirstProject}{%'
  printf '%s\n' '%   \resumeItem{...tailored bullet...}'
  printf '%s\n' '%   \resumeItem{...tailored bullet...}'
  printf '%s\n' '% }'
  printf '%s\n' ''
  printf '%s\n' '\begin{document}\ResumeBody\end{document}'
} > "$dir/resume.tex"

# job-description.md
{
  printf '%s\n' "# Job Description — $label"
  printf '%s\n' ""
  printf '%s\n' "_Paste the job description here for reference while tailoring resume.tex._"
  printf '%s\n' ""
  printf '%s\n' "- Role:"
  printf '%s\n' "- Team:"
  printf '%s\n' "- Key requirements:"
  printf '%s\n' "- Keywords to mirror:"
} > "$dir/job-description.md"

# notes.md — the audit trail. Every slot below is REQUIRED; a blank slot is
# visible evidence a step was skipped, which is the entire point of the shape.
{
  printf '%s\n' "# $label"
  printf '%s\n' ""
  printf '%s\n' "- **Region:** $(printf '%s' "$region" | tr '[:lower:]' '[:upper:]')"
  printf '%s\n' "- **Status:** _not started / built / form filled / applied / OA / interview / offer / rejected_"
  printf '%s\n' "- **Deadline:** _TBD_"
  printf '%s\n' "- **Portal / link:** _TBD_"
  printf '%s\n' "- **Audience:** _which reader this cut is for_ — drives every override (master-profile.md section 5)"
  printf '%s\n' ""
  printf '%s\n' "## Tailoring rationale"
  printf '%s\n' ""
  printf '%s\n' "_What was emphasised, what was dropped, and why. Name the JD line each"
  printf '%s\n' "override answers._"
  printf '%s\n' ""
  printf '%s\n' "- "
  printf '%s\n' ""
  printf '%s\n' "## Build gates"
  printf '%s\n' ""
  printf '%s\n' "_From \`./build.sh $slug\` (runs pipeline/preflight.py). A WARN is not a pass:"
  printf '%s\n' "fix it or justify it on the line below._"
  printf '%s\n' ""
  printf '%s\n' "- **Preflight:** _PASS / WARN (list which, and why each stands)_"
  printf '%s\n' "- **Page fill:** _\`__%\`_"
  printf '%s\n' ""
  printf '%s\n' "## Adversarial review (profile/evaluator-brief.md)"
  printf '%s\n' ""
  printf '%s\n' "_Two passes are mandatory whenever a finding changed the PDF (CLAUDE.md"
  printf '%s\n' "Rule 5). A pre-fix score alone doesn't tell you the fixes worked._"
  printf '%s\n' ""
  printf '%s\n' "- **Pass 1:** _\`__/100\`_ —"
  printf '%s\n' "- **Pass 2:** _\`__/100\`_ (delta: _\`__\`_) — _or: not run, no fixes were made_"
  printf '%s\n' "- **Fixes taken:**"
  printf '%s\n' "- **Fixes declined (+ reason):**"
  printf '%s\n' ""
  printf '%s\n' "## To-do"
  printf '%s\n' "- [ ] Tailor resume.tex (§6 canonical wordings pasted, not re-derived)"
  printf '%s\n' "- [ ] Build + all preflight gates PASS"
  printf '%s\n' "- [ ] Evaluator pass 1"
  printf '%s\n' "- [ ] Evaluator pass 2 (if any fix was applied)"
  printf '%s\n' "- [ ] Fill Category A form fields (profile/application-facts.md)"
  printf '%s\n' "- [ ] (Optional) cover letter: cp ../../shared/cover-letter-template.tex cover-letter.tex"
  printf '%s\n' "- [ ] **You submit — never automated**"
} > "$dir/notes.md"

echo "Created applications/$slug/ (region: $region)"
echo "  resume.tex  job-description.md  notes.md"
echo "Next: tailor applications/$slug/resume.tex, then ./build.sh $slug"
