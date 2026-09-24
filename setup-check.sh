#!/usr/bin/env bash
# ============================================================
#  setup-check.sh  —  is this machine ready to run the pipeline?
# ------------------------------------------------------------
#  ./setup-check.sh
#
#  /setup runs this first. Run it yourself any time something
#  stops working — it is faster than guessing which piece broke.
#
#  Exit 0 = everything required is present.
#  Exit 1 = at least one REQUIRED item is missing.
#  Optional items never fail the check; they limit what works.
# ============================================================
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MISSING=0

ok ()   { printf '  \033[32m✓\033[0m %-22s %s\n' "$1" "${2:-}"; }
bad ()  { printf '  \033[31m✗\033[0m %-22s %s\n' "$1" "$2"; MISSING=1; }
warn () { printf '  \033[33m!\033[0m %-22s %s\n' "$1" "$2"; }

echo ""
echo "  resume-pipeline — environment check"
echo "  ──────────────────────────────────────────────────────────────"

# ---- required ----------------------------------------------------------
if command -v python3 >/dev/null 2>&1; then
  ok "python3" "$(python3 --version 2>&1)"
else
  bad "python3" "not found — install Python 3.8 or newer"
fi

if command -v pdflatex >/dev/null 2>&1; then
  ok "pdflatex" "$(command -v pdflatex)"
else
  bad "pdflatex" "not found — macOS: brew install --cask mactex-no-gui
                         Debian/Ubuntu: sudo apt install texlive-latex-recommended"
fi

for tool in pdftotext pdfinfo; do
  if command -v "$tool" >/dev/null 2>&1; then
    ok "$tool" "$(command -v $tool)"
  else
    bad "$tool" "not found — this is poppler. macOS: brew install poppler
                         Debian/Ubuntu: sudo apt install poppler-utils"
  fi
done

if [ -f "$ROOT/config.json" ]; then
  if python3 -c "import json,sys; json.load(open(sys.argv[1]))" "$ROOT/config.json" 2>/dev/null; then
    NAME="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["identity"]["name"])' "$ROOT/config.json" 2>/dev/null)"
    IS_EX="$(python3 -c 'import json,sys; print("yes" if json.load(open(sys.argv[1])).get("_example") else "")' "$ROOT/config.json" 2>/dev/null)"
    if [ -n "$IS_EX" ]; then
      warn "config.json" "still the shipped example ($NAME) — run /setup"
    else
      ok "config.json" "$NAME"
    fi
  else
    bad "config.json" "present but not valid JSON"
  fi
else
  bad "config.json" "missing — run /setup, or copy config.example.json"
fi

# ---- optional: Notion --------------------------------------------------
echo ""
echo "  Notion (needed for /jobscan and the /resume-build queue)"

if [ -n "${NOTION_TOKEN:-}" ]; then
  ok "NOTION_TOKEN" "set in the environment"
elif [ -f "$ROOT/pipeline/.notion-token" ]; then
  PERM="$(stat -f '%Lp' "$ROOT/pipeline/.notion-token" 2>/dev/null || stat -c '%a' "$ROOT/pipeline/.notion-token" 2>/dev/null)"
  if [ "$PERM" = "600" ]; then
    ok "notion token file" "pipeline/.notion-token (0600)"
  else
    warn "notion token file" "pipeline/.notion-token is $PERM — needs chmod 600"
  fi
else
  warn "NOTION_TOKEN" "unset — see pipeline/NOTION-SETUP.md
                         note: it must be in ~/.zshenv, NOT ~/.zshrc"
fi

if [ -f "$ROOT/pipeline/notion_config.json" ]; then
  ok "notion_config.json" "present — verify with: python3 pipeline/notion_bootstrap.py --verify"
else
  warn "notion_config.json" "not created yet — run: python3 pipeline/notion_bootstrap.py --parent <page url>"
fi

# ---- optional: browser -------------------------------------------------
echo ""
echo "  Browser (needed to read live postings and fill forms)"
if [ -d "/Applications/Google Chrome.app" ] || command -v google-chrome >/dev/null 2>&1; then
  ok "Chrome" "installed"
else
  warn "Chrome" "not found — /jobscan and the form-fill step need it"
fi
warn "Chrome extension" "check by hand: the Claude for Chrome extension must be
                         installed and granted access to the sites you apply on"

# ---- summary -----------------------------------------------------------
echo "  ──────────────────────────────────────────────────────────────"
if [ "$MISSING" -eq 0 ]; then
  echo "  Ready. Next: run /setup in Claude Code, or ./build.sh --example base"
  echo ""
  exit 0
fi
echo "  Missing required tools above. Install them, then re-run."
echo ""
exit 1
