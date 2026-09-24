#!/usr/bin/env bash
# ============================================================
#  build.sh  —  compile application resumes (+ cover letters)
# ------------------------------------------------------------
#  Usage:
#    ./build.sh                 build every application in applications/
#    ./build.sh acme globex     build only the named applications
#    ./build.sh base            build the untailored base preview
#    ./build.sh --no-check ...  skip the preflight gates (fast iteration only)
#
#  Output (upload-ready) in dist/, named from config.json:
#    dist/<YourName>-Resume-<Company>.pdf
#    dist/<YourName>-CoverLetter-<Company>.pdf  (if cover-letter.tex exists)
#
#  Every resume build runs pipeline/preflight.py — the mechanical gates for
#  CLAUDE.md Rules 1-4 (one page, page fill, orphan lines, settled wordings,
#  semicolon splices, vocabulary, spelling variant). The gates hang off the
#  build because the build is the one step that can't be skipped: you need the
#  PDF, so you cannot forget to run them. A rule with a command attached gets
#  followed; a rule left to end-of-context judgement does not.
# ============================================================
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APPS="$ROOT/applications"
SHARED="$ROOT/shared"
DIST="$ROOT/dist"
TMP="$ROOT/.build"
CONFIG="$ROOT/config.json"

[ -f "$CONFIG" ] || { echo "No config.json. Run /setup, or copy config.example.json." >&2; exit 1; }

# Identity comes from config.json — nothing about you is hardcoded here.
NAME="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["identity"]["file_name"])' "$CONFIG")"
IS_EXAMPLE="$(python3 -c 'import json,sys; print("1" if json.load(open(sys.argv[1])).get("_example") else "")' "$CONFIG")"

mkdir -p "$DIST" "$TMP"

# Regenerate shared/identity.tex so a config.json edit always reaches the page.
python3 "$ROOT/pipeline/gen_identity.py"

RUN_CHECKS=1
ALLOW_EXAMPLE=0
GATE_FAILURES=()

titlecase () { printf '%s' "$(tr '[:lower:]' '[:upper:]' <<< "${1:0:1}")${1:1}"; }

# preflight <pdf> <label> — mechanical gates for Rules 1-4. Never aborts the
# run (a multi-application build must not stop at the first offender); records
# the failure and lets the final summary carry it.
preflight () {
  local pdf="$1" label="$2"
  [ "$RUN_CHECKS" -eq 1 ] || return 0
  if [ ! -f "$ROOT/pipeline/preflight.py" ]; then
    echo "    ! pipeline/preflight.py missing — gates skipped" >&2; return 0
  fi
  if ! python3 "$ROOT/pipeline/preflight.py" "$pdf"; then
    GATE_FAILURES+=("$label")
  fi
}

# run_latex <workdir> <jobname> <source-or-jobspec...>
run_latex () {
  local workdir="$1" job="$2"; shift 2
  local pass
  # TEXINPUTS lets \input{identity.tex} resolve from any working directory,
  # so the same preamble compiles from applications/<slug>/ and from shared/.
  for pass in 1 2; do
    if ! ( cd "$workdir" && TEXINPUTS="$SHARED:${TEXINPUTS:-}" \
             pdflatex -interaction=nonstopmode -halt-on-error \
             -jobname="$job" -output-directory="$TMP" "$@" ) >/dev/null 2>&1; then
      echo "  ✗ LaTeX error building '$job'. Last 25 log lines:" >&2
      tail -n 25 "$TMP/$job.log" >&2 || true
      return 1
    fi
  done
}

build_app () { # <company-folder-name>
  local app="$1"
  local dir="$APPS/$app"
  if [ ! -f "$dir/resume.tex" ]; then
    echo "  ! No applications/$app/resume.tex — skipping." >&2; return 0
  fi
  local label job
  # Optional: applications/<app>/label overrides the auto-titlecased name in the
  # output filename (e.g. "yc" -> "YC" instead of "Yc"). One line, no spaces.
  if [ -s "$dir/label" ]; then
    label="$(head -n1 "$dir/label" | tr -d '[:space:]')"
  else
    label="$(titlecase "$app")"
  fi
  echo "==> $label"

  # Resume (always)
  job="$NAME-Resume-$label"
  run_latex "$dir" "$job" "resume.tex"
  cp "$TMP/$job.pdf" "$DIST/"
  echo "    -> dist/$job.pdf"
  preflight "$DIST/$job.pdf" "$label"

  # Cover letter (only if present)
  if [ -f "$dir/cover-letter.tex" ]; then
    job="$NAME-CoverLetter-$label"
    run_latex "$dir" "$job" "cover-letter.tex"
    cp "$TMP/$job.pdf" "$DIST/"
    echo "    -> dist/$job.pdf"
  fi
}

build_base () {
  echo "==> Base (untailored preview)"
  local job="$NAME-Resume-Base"
  run_latex "$SHARED" "$job" "master.tex"
  cp "$TMP/$job.pdf" "$DIST/"
  echo "    -> dist/$job.pdf"
  preflight "$DIST/$job.pdf" "Base"
}

# Resolve targets.
targets=()
for arg in "$@"; do
  case "$arg" in
    --no-check) RUN_CHECKS=0 ;;
    --example)  ALLOW_EXAMPLE=1 ;;
    *)          targets+=("$arg") ;;
  esac
done
# Guard: config.json still holds the shipped example persona. Building in that
# state produces a fictional person's CV, which is never what you want unless
# you are looking at the worked example on purpose.
if [ -n "$IS_EXAMPLE" ] && [ "$ALLOW_EXAMPLE" -eq 0 ]; then
  echo "config.json is still the shipped example (\"_example\": true)." >&2
  echo "" >&2
  echo "  Run /setup in Claude Code to fill it with your own details," >&2
  echo "  or ./build.sh --example example-corp to see the worked example build." >&2
  exit 1
fi

if [ "${#targets[@]}" -eq 0 ]; then
  if compgen -G "$APPS/*/resume.tex" >/dev/null; then
    for d in "$APPS"/*/; do targets+=("$(basename "$d")"); done
  else
    echo "No applications found in applications/. Create one with ./new-company.sh" >&2
    exit 0
  fi
fi

for t in "${targets[@]}"; do
  case "$t" in
    base) build_base ;;
    *)    build_app "$t" ;;
  esac
done

echo ""
if [ "$RUN_CHECKS" -eq 1 ] && [ "${#GATE_FAILURES[@]}" -gt 0 ]; then
  echo "✗ preflight FAILED for: ${GATE_FAILURES[*]}"
  echo "  Fix the failing gates and rebuild. Do not ship or hand these back."
  echo "  (Rule 2's escape hatch still applies: if the honest content genuinely"
  echo "   does not fill the page, record that in notes.md and move on.)"
  exit 1
fi

if [ "$RUN_CHECKS" -eq 1 ]; then
  echo "✓ preflight passed for all builds in this run."
else
  echo "! preflight SKIPPED (--no-check). Re-run without it before shipping."
fi
