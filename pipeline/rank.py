#!/usr/bin/env python3
"""
Rank job postings and decide which ones are new to the Notion tracker.

Deterministic on purpose. The mechanical components (recency, geography, visa)
are computed here so they cannot drift between runs. The two judgement
components — fit and p_admission — are supplied by Claude per posting and
recorded in the archive so a later run can be audited against an earlier one.

THE TRACKER IS THE SOURCE OF TRUTH, NOT seen.json.
`is_new` is derived from an export of the Notion Application Tracker passed via
--known. seen.json survives only as a first-seen date ledger. The inversion
matters: if the ledger decided what was new, a sweep that stamped keys but
failed to write the Notion rows would silently skip those openings on every
later run — they would look already-seen with nothing to show for them. With the
tracker authoritative, a lost write is self-correcting. No row means still new,
so it gets offered again.

Three ordering rules follow from that, and breaking any one reopens the bug:
  1. seen.json is committed AFTER the Notion rows exist, never during ranking.
  2. Every run is archived to pipeline/runs/ before anything downstream can fail.
  3. Running without --known is refused: an unreachable tracker reads as "empty",
     which would mark every posting new and duplicate the entire board.

Usage:
    # step 5 — rank against the live tracker, archive, emit ranked.json
    cat postings.json | python3 pipeline/rank.py --known tracker.json > ranked.json

    # step 6 — ONLY after the Notion rows are confirmed written
    echo '["key1","key2"]' | python3 pipeline/rank.py --commit-seen

    cat postings.json | python3 pipeline/rank.py --known tracker.json --today 2026-08-04
    python3 pipeline/rank.py --selftest

--known takes a JSON array of tracker rows; url/Link and role/Role are the
fields that matter. Keys are recomputed here with canonical_key rather than
supplied pre-built, so the two sides cannot drift apart.

Input: JSON array. Each posting:
    company        str   required
    role           str   required
    url            str   required
    location       str   London|Singapore|Europe|Hong Kong|China|US|Remote
    opened         str   "YYYY-MM-DD" or null
    closes         str   "YYYY-MM-DD" or null
    sponsors_visa  bool  or null (null = not stated)
    source         list  ["Trackr", ...]
    cycle          str   Summer|Off Cycle  (drives OFF_CYCLE_UPLIFT)
    fit            float 0..1   Claude's judgement vs master-profile s1/s5
    p_admission    float 0..1   Claude's judgement
    eligible       bool         false only if a STATED hard bar is failed
    eligibility_note str
    requires       list  ["CV", "Cover letter", ...]
    min_degree     str   BSc|Masters|PhD|Not stated — the LOWEST qualification
                         the JD accepts. Carried through to the Notion
                         "Min Degree" column; not scored here, but PhD is a
                         stated bar so it should come with eligible: false.

Weights come from config.json ("rank"), defaulting to p_admission 35, fit 25,
recency 20, visa 10, geography 10. Failing a stated eligibility bar multiplies
the total by 0.1 — it never filters the row out. Rank, don't filter: a bad role
scored 22 is a signal you can correct, a bad role silently dropped is not.
"""

import json
import sys
import os
import re
import tempfile
from datetime import date, datetime

# ------------------------------------------------------------------ config --
# Scoring is yours to tune — geography especially, which is personal. Edit
# config.json's "rank" block rather than this file, so an upstream change to
# rank.py never silently resets your weights.
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

_DEFAULTS = {
    "weights": {"p_admission": 35.0, "fit": 25.0, "recency": 20.0,
                "visa": 10.0, "geography": 10.0},
    "geography_points": {"london": 10.0, "remote": 7.0, "europe": 6.0, "us": 4.0},
    "geography_default": 3.0,
    "off_cycle_uplift": 1.35,
    "ineligible_multiplier": 0.1,
}


def _rank_config():
    try:
        with open(os.path.join(_ROOT, "config.json")) as fh:
            user = (json.load(fh) or {}).get("rank") or {}
    except (OSError, ValueError):
        user = {}
    out = dict(_DEFAULTS)
    for key, default in _DEFAULTS.items():
        value = user.get(key, default)
        if isinstance(default, dict) and isinstance(value, dict):
            value = {k: v for k, v in value.items() if not k.startswith("_")}
        out[key] = value
    return out


_CFG = _rank_config()

WEIGHTS = {k: float(v) for k, v in _CFG["weights"].items()}
GEOGRAPHY_POINTS = {k.lower(): float(v) for k, v in _CFG["geography_points"].items()}
GEOGRAPHY_DEFAULT = float(_CFG["geography_default"])
INELIGIBLE_MULTIPLIER = float(_CFG["ineligible_multiplier"])

# Off-cycle roles draw far fewer applicants than the summer campus programmes —
# they sit outside the standard calendar and often want immediate availability.
# Applied mechanically so it cannot drift between runs; capped at the weight.
#
# CAVEAT the digest must surface: off-cycle usually means a term-time
# commitment. A higher score here is about odds, not feasibility — check the
# dates against your own availability before promoting the row.
OFF_CYCLE_UPLIFT = float(_CFG["off_cycle_uplift"])

RECENCY_FULL_DAYS = 3      # <=72h scores full marks
RECENCY_ZERO_DAYS = 21     # decays to zero here
CLOSING_SOON_DAYS = 14     # a near deadline floors recency
CLOSING_SOON_FLOOR = 15.0

SEEN_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "seen.json")
ARCHIVE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "runs")


def _parse_date(value):
    if not value:
        return None
    try:
        return datetime.strptime(str(value).strip(), "%Y-%m-%d").date()
    except ValueError:
        return None


def _norm(s):
    return re.sub(r"[^a-z0-9]+", "", (s or "").lower())


def canonical_key(posting):
    """Dedupe key. Prefer the ATS URL — the same role reaches us from several
    sources with different identifiers, but the ATS path is stable.

    The role is ALWAYS part of the key, including for ATS URLs. One posting can
    contain several distinct roles: one "Internships" posting can hold both a
    Quant Developer and a Core Technology track, and a bank's can hold a whole
    division tree. Keying on the posting alone silently collapses those leaves
    into one — which would defeat the leaf-level indexing this pipeline exists
    to do. Cross-source title variance is tolerable here because the ATS id
    already pins company and posting; the leaf names come from the form's own
    option labels and are stable.
    """
    url = (posting.get("url") or "").split("?")[0].split("#")[0].rstrip("/")
    role = _norm(posting.get("role"))
    m = re.search(r"greenhouse\.(?:io|eu)/(?:embed/job_app\?for=)?([^/]+)/jobs/(\d+)", url)
    if m:
        return "greenhouse:%s:%s:%s" % (m.group(1).lower(), m.group(2), role)
    m = re.search(r"lever\.co/([^/]+)/([0-9a-f-]{36})", url)
    if m:
        return "lever:%s:%s:%s" % (m.group(1).lower(), m.group(2), role)
    return "n:%s:%s:%s" % (_norm(posting.get("company")), role, _norm(posting.get("location")))


def recency_points(opened, closes, today):
    """Full marks inside 72h, linear decay to zero at 21 days. A deadline
    within 14 days floors the score — an old posting about to close is still
    urgent."""
    pts = 0.0
    d = _parse_date(opened)
    if d is not None:
        age = (today - d).days
        if age < 0:
            age = 0
        if age <= RECENCY_FULL_DAYS:
            pts = WEIGHTS["recency"]
        elif age < RECENCY_ZERO_DAYS:
            span = RECENCY_ZERO_DAYS - RECENCY_FULL_DAYS
            pts = WEIGHTS["recency"] * (1.0 - (age - RECENCY_FULL_DAYS) / float(span))
    c = _parse_date(closes)
    if c is not None:
        left = (c - today).days
        if 0 <= left <= CLOSING_SOON_DAYS:
            pts = max(pts, CLOSING_SOON_FLOOR)
    return round(pts, 2)


def visa_points(sponsors_visa):
    """Never a gate. Sponsorship is treated as negotiable, so an explicit
    'no' costs points rather than removing the row."""
    if sponsors_visa is True:
        return WEIGHTS["visa"]
    if sponsors_visa is False:
        return 0.0
    return WEIGHTS["visa"] / 2.0          # not stated


def geography_points(location):
    """Unlisted locations get geography_default rather than zero — a city you
    have not ranked yet is unknown, not unwanted."""
    return GEOGRAPHY_POINTS.get((location or "").strip().lower(), GEOGRAPHY_DEFAULT)


def _clamp01(x):
    try:
        x = float(x)
    except (TypeError, ValueError):
        return 0.0
    return 0.0 if x < 0 else (1.0 if x > 1 else x)


def p_admission_points(p_admission, cycle):
    pts = _clamp01(p_admission) * WEIGHTS["p_admission"]
    if (cycle or "").strip().lower().replace("-", " ") in ("off cycle", "offcycle"):
        pts = min(pts * OFF_CYCLE_UPLIFT, WEIGHTS["p_admission"])
    return round(pts, 2)


def score_posting(posting, today):
    breakdown = {
        "p_admission": p_admission_points(posting.get("p_admission"), posting.get("cycle")),
        "fit": round(_clamp01(posting.get("fit")) * WEIGHTS["fit"], 2),
        "recency": recency_points(posting.get("opened"), posting.get("closes"), today),
        "visa": visa_points(posting.get("sponsors_visa")),
        "geography": geography_points(posting.get("location")),
    }
    total = sum(breakdown.values())
    eligible = posting.get("eligible", True)
    if eligible is False:
        total *= INELIGIBLE_MULTIPLIER
    out = dict(posting)
    out["score"] = round(total, 1)
    out["score_breakdown"] = breakdown
    out["key"] = canonical_key(posting)
    return out


def load_seen(path=SEEN_PATH):
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r") as fh:
            return json.load(fh)
    except (ValueError, IOError):
        # A corrupt store must not silently look like "nothing seen before",
        # which would re-notify everything. Fail loudly instead.
        raise SystemExit("seen.json is unreadable — fix or delete it before running")


def save_seen(seen, path=SEEN_PATH):
    tmp = path + ".tmp"
    with open(tmp, "w") as fh:
        json.dump(seen, fh, indent=1, sort_keys=True)
    os.replace(tmp, path)


def load_known(path):
    """Build the already-tracked key set from an export of the Notion
    Application Tracker.

    Keys are computed HERE, with canonical_key, from the tracker's own Link and
    Role fields — never accepted pre-built from the caller. Two sides computing
    keys by different routes is exactly how a dedupe store stops matching
    without anyone noticing.

    Returns {key: page_id-or-None}. Rows you created by hand are included
    like any other: they are in the tracker, so they are not new. That is the
    property seen.json could never have, since hand-made rows never entered it.
    """
    with open(path, "r") as fh:
        rows = json.load(fh)
    if not isinstance(rows, list):
        raise SystemExit("--known expects a JSON array of tracker rows")
    known = {}
    for row in rows:
        posting = {
            "url": row.get("url") or row.get("Link") or "",
            "role": row.get("role") or row.get("Role") or "",
            "company": row.get("company") or row.get("Company") or "",
            "location": row.get("location") or row.get("Location") or "",
        }
        known[canonical_key(posting)] = row.get("page_id") or row.get("id")
    return known


def commit_seen(keys, today, path=SEEN_PATH):
    """Stamp keys into the first-seen ledger.

    Called at step 6, after the Notion rows exist — never at step 5 during
    ranking, which is the bug this ordering exists to prevent. Only pass keys whose rows came
    back confirmed; a key committed for a row that was never written is the
    original bug rebuilt by hand.
    """
    seen = load_seen(path)
    stamp = today.isoformat()
    added = 0
    for k in keys:
        if k not in seen:
            seen[k] = stamp
            added += 1
    save_seen(seen, path)
    return added


def archive_run(ranked, today, directory=ARCHIVE_DIR):
    """Persist the full ranked array before anything downstream can fail.

    The scores and the fit / p_admission judgements previously existed only on
    stdout, so a run that died after ranking left nothing to replay or audit —
    which is why a sweep lost this way is unrecoverable beyond a list of keys.
    Existing archives are never overwritten.
    """
    if not os.path.isdir(directory):
        os.makedirs(directory)
    base = today.isoformat()
    path = os.path.join(directory, base + ".json")
    n = 2
    while os.path.exists(path):
        path = os.path.join(directory, "%s.%d.json" % (base, n))
        n += 1
    with open(path, "w") as fh:
        json.dump(ranked, fh, indent=1)
    return path


def run(postings, today, seen, known):
    """Rank, and decide is_new against the tracker contents in `known`.

    is_new is tracker-derived, NOT seen-derived. seen.json only supplies the
    original discovery date, so a posting re-offered after a lost write keeps
    its real first_seen instead of looking brand new.
    """
    ranked = [score_posting(p, today) for p in postings]
    stamp = today.isoformat()
    for r in ranked:
        r["is_new"] = r["key"] not in known
        r["first_seen"] = seen.get(r["key"], stamp)
        r["notion_page_id"] = known.get(r["key"])
    ranked.sort(key=lambda r: (-r["score"], r["company"]))
    return ranked


def _selftest():
    # Pin the shipped defaults. The selftest checks the scoring LOGIC, so it
    # must not depend on whatever weights the current config.json happens to
    # carry — otherwise tuning your own geography breaks the test suite.
    global WEIGHTS, GEOGRAPHY_POINTS, GEOGRAPHY_DEFAULT, OFF_CYCLE_UPLIFT
    global INELIGIBLE_MULTIPLIER
    WEIGHTS = dict(_DEFAULTS["weights"])
    GEOGRAPHY_POINTS = dict(_DEFAULTS["geography_points"])
    GEOGRAPHY_DEFAULT = _DEFAULTS["geography_default"]
    OFF_CYCLE_UPLIFT = _DEFAULTS["off_cycle_uplift"]
    INELIGIBLE_MULTIPLIER = _DEFAULTS["ineligible_multiplier"]

    today = date(2026, 8, 4)
    cases = [
        # fresh London posting, strong on both judgement axes, visa unstated.
        # 35 + 25 + 20 recency + 5 visa-unstated + 10 London = 95
        (dict(company="A", role="R", url="https://job-boards.greenhouse.io/x/jobs/1",
              location="London", opened="2026-08-03", closes=None, sponsors_visa=None,
              fit=1.0, p_admission=1.0, eligible=True), 95.0),
        # same but ineligible -> multiplied down, still present
        (dict(company="B", role="R", url="u2", location="London", opened="2026-08-03",
              closes=None, sponsors_visa=None, fit=1.0, p_admission=1.0, eligible=False), 9.5),
        # 21 days old -> recency exhausted
        (dict(company="C", role="R", url="u3", location="London", opened="2026-07-14",
              closes=None, sponsors_visa=True, fit=0.0, p_admission=0.0, eligible=True), 20.0),
        # old but closing in 10 days -> floored at 15
        (dict(company="D", role="R", url="u4", location="US", opened="2026-06-01",
              closes="2026-08-14", sponsors_visa=False, fit=0.0, p_admission=0.0,
              eligible=True), 19.0),  # closing-soon floor 15 + US geography 4
        # off-cycle uplift: 0.5*35 = 17.5 -> *1.35 = 23.63, +20 rec +5 visa +10 geo
        (dict(company="E", role="R", url="u5", location="London", opened="2026-08-04",
              closes=None, sponsors_visa=None, fit=0.0, p_admission=0.5,
              cycle="Off Cycle", eligible=True), 58.6),
        # uplift must cap at the weight: 1.0*35 = 35 -> capped 35, not 47.25
        (dict(company="F", role="R", url="u6", location="London", opened="2026-08-04",
              closes=None, sponsors_visa=None, fit=0.0, p_admission=1.0,
              cycle="Off Cycle", eligible=True), 70.0),
        # summer cycle gets no uplift
        (dict(company="G", role="R", url="u7", location="London", opened="2026-08-04",
              closes=None, sponsors_visa=None, fit=0.0, p_admission=0.5,
              cycle="Summer", eligible=True), 52.5),
    ]
    ok = True
    for posting, expected in cases:
        got = score_posting(posting, today)["score"]
        flag = "ok " if abs(got - expected) < 0.05 else "FAIL"
        if flag == "FAIL":
            ok = False
        print("%s %s expected %.1f got %.1f" % (flag, posting["company"], expected, got))

    def check(label, cond):
        nonlocal_ok.append(bool(cond))
        print("%s %s" % ("ok " if cond else "FAIL", label))

    nonlocal_ok = []

    # same posting, same role, different host + query string -> one key
    a = canonical_key(dict(url="https://job-boards.greenhouse.io/examplecapital/jobs/4255974?gh_src=Trackr",
                           role="Core Technology Internship"))
    b = canonical_key(dict(url="https://boards.greenhouse.io/examplecapital/jobs/4255974",
                           role="Core Technology Internship"))
    check("dedupe across hosts and query strings", a == b)

    # REGRESSION: one posting, two tracks -> two keys.
    # One "Internships" posting can hold a Quant Developer and a Core
    # Technology. Keying on the posting alone collapsed them into one row and
    # silently lost a leaf.
    c = canonical_key(dict(url="https://job-boards.greenhouse.io/examplecapital/jobs/4255974",
                           role="Quant Developer Internship"))
    check("leaf collision: two tracks at one posting stay distinct", a != c)

    # fragments must not create a phantom second key
    d = canonical_key(dict(url="https://job-boards.greenhouse.io/examplecapital/jobs/4255974#core",
                           role="Core Technology Internship"))
    check("URL fragments ignored", a == d)

    # undated posting must score (recency 0), not crash
    undated = score_posting(dict(company="U", role="R", url="u9", location="London",
                                 opened=None, closes=None, sponsors_visa=None,
                                 fit=0.0, p_admission=0.0, eligible=True), today)
    check("undated posting scores without crashing", undated["score_breakdown"]["recency"] == 0.0)

    # is_new comes from the tracker, not the seen ledger
    p = [dict(company="S", role="R", url="https://jobs.lever.co/x/11111111-2222-3333-4444-555555555555",
              location="London", opened="2026-08-04", fit=0.5, p_admission=0.5, eligible=True)]
    k = canonical_key(p[0])
    check("posting absent from the tracker is new", run(list(p), today, {}, {})[0]["is_new"])
    check("posting already in the tracker is not new",
          not run(list(p), today, {}, {k: "page-1"})[0]["is_new"])

    # REGRESSION: a sweep stamped keys into seen.json and never
    # wrote the Notion rows. Because is_new was seen-derived, those openings
    # would have been skipped for good. seen must NEVER suppress a posting the
    # tracker does not actually have.
    lost = run(list(p), today, {k: "2026-08-05"}, {})
    check("lost write self-heals: seen but untracked is still new", lost[0]["is_new"])
    check("re-offered posting keeps its original first_seen",
          lost[0]["first_seen"] == "2026-08-05")

    # the tracker side must build keys through canonical_key too, or the two
    # sides stop matching on cosmetic host/query differences
    fd, known_path = tempfile.mkstemp(suffix=".json")
    with os.fdopen(fd, "w") as fh:
        json.dump([{"Link": "https://boards.greenhouse.io/examplecapital/jobs/4255974?src=x",
                    "Role": "Core Technology Internship"}], fh)
    kn = load_known(known_path)
    os.unlink(known_path)
    check("tracker export keys match sweep keys across host variants", a in kn)

    # committing must not touch rows that were never written
    fd, seen_path = tempfile.mkstemp(suffix=".json")
    os.close(fd)
    os.unlink(seen_path)
    commit_seen(["written-key"], today, path=seen_path)
    after = load_seen(seen_path)
    os.unlink(seen_path)
    check("commit_seen stamps only the keys it is given",
          list(after) == ["written-key"] and after["written-key"] == "2026-08-04")

    ok = ok and all(nonlocal_ok)
    print("SELFTEST", "PASSED" if ok else "FAILED")
    return 0 if ok else 1


def main():
    args = sys.argv[1:]
    if "--selftest" in args:
        sys.exit(_selftest())
    today = date.today()
    if "--today" in args:
        today = _parse_date(args[args.index("--today") + 1]) or today

    # step 6: stamp the ledger for rows that are now confirmed in Notion
    if "--commit-seen" in args:
        keys = json.load(sys.stdin)
        if not isinstance(keys, list):
            raise SystemExit("--commit-seen expects a JSON array of keys on stdin")
        added = commit_seen(keys, today)
        sys.stderr.write("seen.json: %d new key(s) committed, %d supplied\n"
                         % (added, len(keys)))
        return

    if "--known" in args:
        known = load_known(args[args.index("--known") + 1])
    elif "--no-known-check" in args:
        # Deliberate escape hatch. Everything will look new.
        known = {}
    else:
        raise SystemExit(
            "refusing to run without --known.\n"
            "is_new is derived from the Notion tracker, so an unreachable or "
            "unexported tracker would read as empty, mark every posting new, and "
            "duplicate the whole board. Export the Application Tracker and pass "
            "--known <path>, or pass --no-known-check if you actually mean it."
        )

    postings = json.load(sys.stdin)
    seen = load_seen()
    ranked = run(postings, today, seen, known)
    # archived before stdout, so a downstream failure still leaves the run on disk
    path = archive_run(ranked, today)
    n_new = sum(1 for r in ranked if r["is_new"])
    sys.stderr.write(
        "ranked %d posting(s): %d new, %d already tracked (%d known keys)\n"
        "archived -> %s\n"
        "reconcile: %d Notion row(s) must exist before --commit-seen\n"
        % (len(ranked), n_new, len(ranked) - n_new, len(known), path, n_new))
    json.dump(ranked, sys.stdout, indent=1)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
