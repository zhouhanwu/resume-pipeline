#!/usr/bin/env python3
"""
Pull whole Notion tables to disk. Prints counts, never rows.

    python3 pipeline/notion_pull.py --out-dir /tmp/scratch
    python3 pipeline/notion_pull.py --out-dir /tmp/scratch --queue

Writes tracker.json in the flat shape rank.py's canonical_key() and both
skills already expect, so it is a drop-in replacement for the MCP view read.

--queue additionally prints the `To apply` / `Ready to submit` standing queue,
which is what resume-build §0 and jobscan §9 need, without either skill having
to pull row data through the conversation.

Exit codes: 0 ok, 1 blocked (a partial read is a blocker under research-protocol
R5, so any failure here is non-zero and loud).
"""

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import notion_io as N


TERMINAL = ("Applied", "Rejected", "Withdrawn", "Abandoned", "Offer",
            "Hirevue", "Coding assessment", "Completed Coding Assessment")


def pull(name, source, out_dir, verbose):
    def progress(kind, pages, rows):
        if verbose:
            sys.stderr.write("  %s: page %d, %d rows\n" % (name, pages, rows))

    raw, endpoint = N.query_all(source, progress=progress)
    rows = [N.flatten(p) for p in raw]
    path = os.path.join(out_dir, "%s.json" % name)
    with open(path, "w") as fh:
        json.dump(rows, fh)
    print("%-8s %4d rows  ->  %s   [%s endpoint]"
          % (name, len(rows), path, endpoint))
    return rows


def print_queue(rows):
    def score(r):
        s = r.get("Score")
        return s if isinstance(s, (int, float)) else -1

    buckets = {}
    for r in rows:
        buckets.setdefault(r.get("Status") or "(none)", []).append(r)

    print("\nstanding queue")
    for status in ("To apply", "Ready to submit"):
        got = sorted(buckets.get(status, []), key=score, reverse=True)
        print("  %-16s %d" % (status, len(got)))
        for r in got:
            print("      %-28s %-52s score %s  first seen %s"
                  % ((r.get("Company") or "")[:28],
                     (r.get("Role") or "")[:52],
                     r.get("Score") if r.get("Score") is not None else "-",
                     r.get("date:First Seen:start") or "-"))

    counts = {k: len(v) for k, v in sorted(buckets.items())}
    print("  all statuses     %s" % json.dumps(counts))


def print_stale(rows, today):
    stale = [r for r in rows
             if (r.get("Status") in ("Discovered", "To apply"))
             and r.get("date:Closes:start")
             and r["date:Closes:start"] < today]
    if not stale:
        return
    print("\nclosed but still open-status (%d) — candidates for archiving:" % len(stale))
    for r in stale:
        print("      %-24s %-46s closed %s  [%s]"
              % ((r.get("Company") or "")[:24], (r.get("Role") or "")[:46],
                 r["date:Closes:start"], r.get("Status")))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--queue", action="store_true",
                    help="also print the To apply / Ready to submit queue")
    ap.add_argument("--stale", metavar="YYYY-MM-DD",
                    help="also list open rows whose Closes date has passed")
    ap.add_argument("--verbose", action="store_true", help="per-page progress to stderr")
    args = ap.parse_args()

    os.makedirs(args.out_dir, exist_ok=True)
    cfg = N.config()

    try:
        rows = pull("tracker", cfg["tracker"], args.out_dir, args.verbose)
    except Exception as e:
        print("BLOCKED pulling tracker: %s" % e, file=sys.stderr)
        return 1

    if args.queue:
        print_queue(rows)
    if args.stale:
        print_stale(rows, args.stale)
    return 0


if __name__ == "__main__":
    sys.exit(main())
