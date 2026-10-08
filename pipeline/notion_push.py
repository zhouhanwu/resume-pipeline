#!/usr/bin/env python3
"""
Write Notion rows from a file on disk. Prints a reconcile line, never payloads.

    # create posting rows (jobscan step 6)
    python3 pipeline/notion_push.py --table tracker --create rows.json \
        --receipts /tmp/scratch/receipts.json

    # set one row's status (resume-build step 8)
    python3 pipeline/notion_push.py --table tracker --update \
        '{"page":"https://app.notion.com/p/<id>","properties":{"Status":"Ready to submit"}}'

INPUT for --create: a JSON array of
    {"properties": {<flat dict, same shape jobscan already builds>},
     "content":    "optional page body text"}

RECONCILE AND RESUME. Every successful create is appended to the receipts file
immediately, keyed by rank.py's canonical_key(). Re-running the same --create
with the same --receipts skips rows already written, so a run that dies at row
60 of 95 is resumed, not duplicated. This is the failure class where —
rows stamped as done that were never written — inverted: nothing is recorded
until Notion confirms it.

Exit codes: 0 all rows written, 1 some failed (names them), 2 bad input.
"""

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import notion_io as N

try:
    from rank import canonical_key
except Exception:                                    # pragma: no cover
    def canonical_key(p):                            # minimal stand-in
        return "%s|%s|%s" % (p.get("company"), p.get("role"), p.get("location"))


def row_key(row):
    p = row.get("properties", {})
    return canonical_key({"url": p.get("Link"), "role": p.get("Role"),
                          "company": p.get("Company"), "location": p.get("Location")})


def load_receipts(path):
    if path and os.path.exists(path):
        with open(path) as fh:
            try:
                return json.load(fh)
            except ValueError:
                return {}
    return {}


def save_receipts(path, receipts):
    if not path:
        return
    tmp = path + ".tmp"
    with open(tmp, "w") as fh:
        json.dump(receipts, fh, indent=1)
    os.replace(tmp, path)


def do_create(source, schema, rows, receipts_path):
    receipts = load_receipts(receipts_path)
    created, skipped, failed = [], [], []

    for i, row in enumerate(rows, 1):
        key = row_key(row)
        if key in receipts:
            skipped.append(key)
            continue
        try:
            page_id, url = N.create_page(source, schema, row)
            receipts[key] = url
            created.append(key)
            save_receipts(receipts_path, receipts)   # durable after every row
        except Exception as e:
            label = "%s / %s" % (row.get("properties", {}).get("Company", "?"),
                                 row.get("properties", {}).get("Role", "?"))
            failed.append((label, str(e)))
        if i % 25 == 0:
            sys.stderr.write("  ... %d/%d\n" % (i, len(rows)))

    print("create: %d requested, %d written, %d already present, %d failed"
          % (len(rows), len(created), len(skipped), len(failed)))
    if failed:
        print("\nFAILED — these rows do NOT exist in Notion:")
        for label, err in failed:
            print("   %-52s %s" % (label[:52], err[:110]))
    if receipts_path:
        print("receipts: %s (%d keys)" % (receipts_path, len(receipts)))
        print("keys written this run, for rank.py --commit-seen:")
        print(json.dumps(created))
    return 1 if failed else 0


def do_update(source, schema, updates):
    ok, failed = 0, []
    for u in updates:
        ref = u.get("page") or u.get("url") or u.get("id")
        if not ref:
            failed.append(("(no page ref)", "update entry needs page/url/id"))
            continue
        try:
            N.update_page(N._relation_id(ref), u.get("properties", {}), schema)
            ok += 1
        except Exception as e:
            failed.append((ref, str(e)))
    print("update: %d requested, %d applied, %d failed" % (len(updates), ok, len(failed)))
    for ref, err in failed:
        print("   %-52s %s" % (str(ref)[:52], str(err)[:110]))
    return 1 if failed else 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--table", choices=["tracker"], required=True)
    ap.add_argument("--create", metavar="FILE", help="JSON array of rows to create")
    ap.add_argument("--receipts", metavar="FILE",
                    help="resume/idempotency ledger; strongly recommended with --create")
    ap.add_argument("--update", metavar="JSON", help="one inline update object")
    ap.add_argument("--update-file", metavar="FILE", help="JSON array of update objects")
    ap.add_argument("--dry-run", action="store_true",
                    help="validate payloads against the live schema, write nothing")
    args = ap.parse_args()

    if not (args.create or args.update or args.update_file):
        print("nothing to do: pass --create, --update or --update-file", file=sys.stderr)
        return 2

    source = N.config()[args.table]
    schema = N.get_schema(source)

    if args.create:
        with open(args.create) as fh:
            rows = json.load(fh)
        if not isinstance(rows, list):
            print("--create file must be a JSON array", file=sys.stderr)
            return 2
        if args.dry_run:
            bad = 0
            for row in rows:
                try:
                    N.to_properties(row.get("properties", {}), schema)
                except Exception as e:
                    bad += 1
                    print("   INVALID %-40s %s"
                          % (str(row.get("properties", {}).get("Role", "?"))[:40], e))
            print("dry-run: %d rows, %d would fail validation" % (len(rows), bad))
            return 1 if bad else 0
        if not args.receipts:
            sys.stderr.write("warning: no --receipts; a partial failure will not "
                             "be resumable without duplicating rows\n")
        return do_create(source, schema, rows, args.receipts)

    updates = []
    if args.update:
        updates.append(json.loads(args.update))
    if args.update_file:
        with open(args.update_file) as fh:
            updates.extend(json.load(fh))
    if args.dry_run:
        for u in updates:
            N.to_properties(u.get("properties", {}), schema)
        print("dry-run: %d updates validate" % len(updates))
        return 0
    return do_update(source, schema, updates)


if __name__ == "__main__":
    sys.exit(main())
