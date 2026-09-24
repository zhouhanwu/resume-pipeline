#!/usr/bin/env python3
"""
preflight.py — mechanical gates for CLAUDE.md Rules 1-4.

Rules with a command attached get followed; rules that rely on judgement at the
end of a long context get skipped. A rule like "one page" survives because
`pdfinfo` answers it in a second; a rule like "fill the page" decays, because
judging fill by eye is unreliable — pages that read as "roughly full" measure in
the mid-80s. This script converts the judgement calls into numbers so they
behave like the one that already works.

Everything is measured on the BUILT PDF, not the .tex — the PDF is what ships,
and it needs no macro expansion to inspect. Wrap points, and therefore orphan
lines, only exist after rendering anyway.

The word-level gates read profile/lexicon.json and config.json, so they are
yours to edit without touching this file.

Usage:
    python3 pipeline/preflight.py dist/<Name>-Resume-<Company>.pdf
    python3 pipeline/preflight.py --json dist/...pdf     # machine-readable

Exit codes:  0 = no FAILs (WARNs may be present) · 1 = at least one FAIL
             2 = could not run (missing file, no pdftotext)
"""

import argparse
import collections
import json
import re
import os
import shutil
import subprocess
import sys

# ---------------------------------------------------------------- geometry --
# shared/preamble.tex: \usepackage[a4paper,margin=0.8cm]{geometry}
MARGIN_PT = 0.8 * 28.3465          # 0.8cm -> 22.68pt
LINE_PITCH_PT = 15.5               # measured median baseline pitch, 10pt CM
# Words on one visual line do not share an exact yMax: the bullet marker sits
# ~2pt off its text baseline, and a superscript (the R^2 in the property
# bullet) ~4pt above it. Cluster with a tolerance comfortably above both and
# well below the ~12pt minimum line pitch — at 3pt the R^2 split into its own
# pseudo-line and silently truncated the bullet it belonged to.
LINE_CLUSTER_TOL = 5.0

# Fill thresholds, calibrated against builds judged full or short by eye. Pages
# that read as "roughly full" routinely measure 84-89, which is the whole reason
# this is a number and not a look.
FILL_PASS = 95.0
FILL_WARN = 90.0

ORPHAN_MIN_RATIO = 0.70            # CLAUDE.md Rule 3's stated threshold

# ------------------------------------------------------------------ lexicon --
# The word gates are data, not code: profile/lexicon.json holds them and
# config.json picks the spelling variant. Both are written by /setup and are
# meant to be edited by hand as you learn what keeps creeping into your drafts.

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _load_json(path, what):
    try:
        with open(path) as fh:
            return json.load(fh)
    except FileNotFoundError:
        print("preflight: no %s — %s gates disabled" % (what, what), file=sys.stderr)
        return {}
    except ValueError as e:
        raise SystemExit("preflight: %s is not valid JSON — %s" % (what, e))


_LEX = _load_json(os.path.join(ROOT, "profile", "lexicon.json"), "profile/lexicon.json")
_CFG = _load_json(os.path.join(ROOT, "config.json"), "config.json")

# Rule 4d — WARN. Skills headers and terms of art are exempt by the rule itself.
BANNED_VOCAB = [w.lower() for w in _LEX.get("banned_vocab", {}).get("words", [])]

# Rule 4a + truth rules — FAIL. (bad wording, what to use instead)
REJECTED_WORDINGS = [(bad, fix) for bad, fix
                     in _LEX.get("rejected_wordings", {}).get("pairs", [])
                     if not bad.startswith("example-")]

# Rule 4f — direction comes from config.json. en-GB flags American spellings,
# en-US flags British ones, anything else turns the gate off.
_VARIANT = (_CFG.get("locale") or {}).get("spelling")
_GB_FROM_US = _LEX.get("spelling", {}).get("en_GB_from_en_US", {})
if _VARIANT == "en-GB":
    SPELLING_MAP, SPELLING_LABEL = dict(_GB_FROM_US), "British spelling"
elif _VARIANT == "en-US":
    SPELLING_MAP = {uk: us for us, uk in _GB_FROM_US.items()}
    SPELLING_LABEL = "American spelling"
else:
    SPELLING_MAP, SPELLING_LABEL = {}, "spelling gate off"

WORD_RE = re.compile(
    r'<word xMin="([\d.]+)" yMin="([\d.]+)" xMax="([\d.]+)" yMax="([\d.]+)">'
    r'(.*?)</word>')
PAGE_RE = re.compile(r'<page width="([\d.]+)" height="([\d.]+)"')
# Split on the page boundary so geometry gates read page 1 only. Without this a
# 2-page build reports the fill of page 1 *plus* page 2's words, and the
# overflow — the thing Rule 1 exists to catch — reads as a healthy 98% page.
PAGE_SPLIT_RE = re.compile(r'<page\b')


def unescape(s):
    return (s.replace("&amp;", "&").replace("&lt;", "<")
             .replace("&gt;", ">").replace("&quot;", '"').replace("&apos;", "'"))


# ------------------------------------------------------------------ parsing --
def extract(pdf):
    """-> (page_w, page_h, [line]) for PAGE 1 ONLY.

    line = dict(y, xmin, xmax, text, bullet_start).
    """
    xml = subprocess.run(["pdftotext", "-bbox", pdf, "-"],
                         capture_output=True, text=True).stdout
    pm = PAGE_RE.search(xml)
    if not pm:
        raise RuntimeError(f"no page geometry in {pdf} — is it a valid PDF?")
    page_w, page_h = float(pm.group(1)), float(pm.group(2))

    # Geometry gates describe the page the screener sees first. On an
    # overflowing build the rest is a defect to fix, not content to measure.
    chunks = PAGE_SPLIT_RE.split(xml)
    page1 = chunks[1] if len(chunks) > 1 else xml

    words = [(float(a), float(b), float(c), float(d), unescape(e))
             for a, b, c, d, e in WORD_RE.findall(page1)]
    if not words:
        raise RuntimeError(f"no text extracted from {pdf}")

    # Group into visual lines. The bullet marker renders ~2pt off its text
    # baseline, so cluster on yMax with a tolerance rather than exact match.
    buckets = []
    for w in sorted(words, key=lambda w: w[3]):
        for b in buckets:
            if abs(b[0] - w[3]) <= LINE_CLUSTER_TOL:
                b[1].append(w)
                break
        else:
            buckets.append((w[3], [w]))

    lines = []
    for _, ws in buckets:
        ws = sorted(ws, key=lambda w: w[0])
        glyphs = [w for w in ws if w[4].strip() in ("•", "·")]
        body = [w for w in ws if w not in glyphs]
        if not body:
            continue
        # Key the line on its widest-set baseline, not the first word clustered
        # into it — otherwise a superscript drags the reported y upward.
        lines.append({
            "y": max(w[3] for w in body),
            "xmin": min(w[0] for w in body),
            "xmax": max(w[2] for w in body),
            "text": " ".join(w[4] for w in body),
            "bullet_start": bool(glyphs),
        })
    lines.sort(key=lambda l: l["y"])
    return page_w, page_h, lines


def bullets_from(lines):
    """Collect each bullet as its ordered list of visual lines."""
    out, cur = [], None
    for ln in lines:
        if ln["bullet_start"]:
            if cur:
                out.append(cur)
            cur = [ln]
        elif cur is not None:
            # A continuation line shares the bullet's text indent. Anything
            # further left is a new heading/section and closes the bullet.
            if abs(ln["xmin"] - cur[0]["xmin"]) < 1.0:
                cur.append(ln)
            else:
                out.append(cur)
                cur = None
    if cur:
        out.append(cur)
    return out


# -------------------------------------------------------------------- gates --
def gate_pages(pdf):
    out = subprocess.run(["pdfinfo", pdf], capture_output=True, text=True).stdout
    m = re.search(r"^Pages:\s+(\d+)", out, re.M)
    n = int(m.group(1)) if m else -1
    if n == 1:
        return "PASS", "Pages: 1", {"pages": n}
    return "FAIL", f"Pages: {n} — Rule 1 is non-negotiable, cut and rebuild", {"pages": n}


def gate_fill(page_h, lines):
    top, bottom = MARGIN_PT, page_h - MARGIN_PT
    last = max(l["y"] for l in lines)
    pct = (last - top) / (bottom - top) * 100
    room = max(0, int((bottom - last) / LINE_PITCH_PT))
    d = {"fill_pct": round(pct, 1), "lines_available": room}
    if pct >= FILL_PASS:
        return "PASS", f"{pct:.1f}% full", d
    level = "WARN" if pct >= FILL_WARN else "FAIL"
    return level, (f"{pct:.1f}% full — room for ~{room} more line(s). "
                   f"Rule 2: add the next item in the §5 priority order"), d


def gate_orphans(bullets):
    hits = []
    for b in bullets:
        if len(b) < 2:
            continue                      # single-line bullets cannot orphan
        col_left, col_right = b[0]["xmin"], max(l["xmax"] for l in b)
        # Column right edge is the widest line in the bullet (a wrapped line
        # runs to the margin), so ratio is measured against that.
        width = col_right - col_left
        if width <= 0:
            continue
        last = b[-1]
        ratio = (last["xmax"] - col_left) / width
        if ratio < ORPHAN_MIN_RATIO:
            hits.append({"ratio": round(ratio * 100, 1),
                         "tail": last["text"][:60],
                         "bullet": b[0]["text"][:50]})
    if not hits:
        return "PASS", "no orphan tails", {"orphans": []}
    msg = "; ".join(f'{h["ratio"]:.0f}% "{h["tail"]}"' for h in hits[:3])
    if len(hits) > 3:
        msg += f" (+{len(hits)-3} more)"
    return "WARN", f"{len(hits)} bullet(s) end short of {ORPHAN_MIN_RATIO:.0%}: {msg}", \
           {"orphans": hits}


def gate_splices(bullets):
    hits = []
    for b in bullets:
        text = " ".join(l["text"] for l in b)
        if ";" not in text:
            continue
        # Rule 4c allows a semicolon inside a list that already has commas.
        head = text.split(";")[0]
        if head.count(",") >= 2:
            continue
        hits.append(text[:90])
    if not hits:
        return "PASS", "no semicolon splices", {"splices": []}
    return "WARN", (f"{len(hits)} possible splice(s) — Rule 4c, two facts in one "
                    f"sentence: " + " | ".join(f'"{h}"' for h in hits[:2])), \
           {"splices": hits}


def gate_vocab(lines):
    if not BANNED_VOCAB:
        return "PASS", "no vocabulary list configured", {"vocab": []}
    page = " ".join(l["text"] for l in lines).lower()
    hits = [w for w in BANNED_VOCAB if w in page]
    if not hits:
        return "PASS", "no flagged vocabulary", {"vocab": []}
    return "WARN", (f"Rule 4d — {', '.join(repr(h) for h in hits)}. "
                    f"Exempt only if a Skills header or a term of art"), {"vocab": hits}


def gate_spelling(lines):
    if not SPELLING_MAP:
        return "PASS", SPELLING_LABEL, {"spelling": []}
    page = " ".join(l["text"] for l in lines)
    hits = []
    for wrong, right in SPELLING_MAP.items():
        if re.search(rf"\b{wrong}\b", page, re.I):
            hits.append(f"{wrong}→{right}")
    if not hits:
        return "PASS", SPELLING_LABEL, {"spelling": []}
    return "FAIL", f"Rule 4f — {', '.join(hits)}", {"spelling": hits}


def gate_canonical(lines):
    if not REJECTED_WORDINGS:
        return "PASS", "no settled wordings recorded yet", {"canonical": []}
    page = " ".join(l["text"] for l in lines).lower()
    hits = [(bad, fix) for bad, fix in REJECTED_WORDINGS if bad.lower() in page]
    if not hits:
        return "PASS", "no rejected wordings", {"canonical": []}
    return "FAIL", ("Rule 4a / truth rules — " +
                    "; ".join(f'"{b}" ({f})' for b, f in hits)), \
           {"canonical": [b for b, _ in hits]}


# --------------------------------------------------------------------- main --
def run(pdf):
    page_w, page_h, lines = extract(pdf)
    bullets = bullets_from(lines)
    return [
        ("pages",     "Rule 1  one page",      gate_pages(pdf)),
        ("fill",      "Rule 2  fill the page", gate_fill(page_h, lines)),
        ("orphans",   "Rule 3  no orphan tails", gate_orphans(bullets)),
        ("canonical", "Rule 4a settled wording", gate_canonical(lines)),
        ("splices",   "Rule 4c one idea/bullet", gate_splices(bullets)),
        ("vocab",     "Rule 4d your vocabulary", gate_vocab(lines)),
        ("spelling",  "Rule 4f spelling variant", gate_spelling(lines)),
    ]


def main():
    ap = argparse.ArgumentParser(description="Mechanical gates for CLAUDE.md Rules 1-4.")
    ap.add_argument("pdf")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    args = ap.parse_args()

    for tool in ("pdftotext", "pdfinfo"):
        if not shutil.which(tool):
            print(f"preflight: {tool} not found (brew install poppler)", file=sys.stderr)
            return 2
    try:
        results = run(args.pdf)
    except Exception as e:                                  # noqa: BLE001
        print(f"preflight: {e}", file=sys.stderr)
        return 2

    fails = [k for k, _, (lvl, _, _) in results if lvl == "FAIL"]
    warns = [k for k, _, (lvl, _, _) in results if lvl == "WARN"]

    if args.json:
        print(json.dumps({
            "pdf": args.pdf,
            "fails": fails, "warns": warns,
            "gates": {k: {"level": lvl, "detail": msg, **data}
                      for k, _, (lvl, msg, data) in results},
        }, indent=2))
        return 1 if fails else 0

    mark = {"PASS": "✓", "WARN": "!", "FAIL": "✗"}
    name = args.pdf.split("/")[-1]
    print(f"\n  preflight — {name}")
    print("  " + "─" * 66)
    for _, label, (lvl, msg, _) in results:
        print(f"  {mark[lvl]} {label:26s} {msg}")
    print("  " + "─" * 66)
    if fails:
        print(f"  {len(fails)} FAIL, {len(warns)} WARN — fix the FAILs before shipping.\n")
    elif warns:
        print(f"  0 FAIL, {len(warns)} WARN — fix, or justify each in notes.md.\n")
    else:
        print("  all gates pass.\n")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
