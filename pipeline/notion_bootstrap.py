#!/usr/bin/env python3
"""
notion_bootstrap.py — create the two tables the pipeline needs, once.

    python3 pipeline/notion_bootstrap.py --parent <notion page url or id>
    python3 pipeline/notion_bootstrap.py --verify        # check an existing setup
    python3 pipeline/notion_bootstrap.py --parent <url> --dry-run

Reads pipeline/notion_schema.json, creates "Application Tracker (postings)"
and "Target Companies (watch list)" as child databases of the page you name,
links them with a two-way relation, and writes pipeline/notion_config.json
with the ids every other script reads.

Before running it you need, once:

  1. An integration at notion.so/my-integrations with Read + Update + Insert
     content capabilities. Copy its Internal Integration Secret (starts `ntn_`).
  2. That secret in $NOTION_TOKEN — see pipeline/NOTION-SETUP.md, and note the
     .zshenv-not-.zshrc trap, which is the one that actually catches people.
  3. A page in your workspace to hold the two tables (call it "Jobs"), shared
     with the integration via ... -> Connections -> Connect to -> <your
     integration>. Its URL is what --parent takes.

Safe to re-run. It refuses to create a table when notion_config.json already
names one that still resolves, so a half-finished run resumes instead of
producing a second copy.
"""

import argparse
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import notion_io as n  # noqa: E402

SCHEMA_FILE = os.path.join(HERE, "notion_schema.json")
CONFIG_FILE = os.path.join(HERE, "notion_config.json")

ID_RE = re.compile(r"([0-9a-fA-F]{32})")


# ----------------------------------------------------------------- helpers --

def parse_page_id(raw):
    """Accept a full Notion URL, a dashed id, or a bare 32-char id."""
    compact = raw.strip().replace("-", "")
    hit = ID_RE.search(compact)
    if not hit:
        raise SystemExit(
            "could not find a Notion id in %r.\n"
            "Paste the page URL from your browser — it ends in the 32-character id."
            % raw)
    h = hit.group(1).lower()
    return "%s-%s-%s-%s-%s" % (h[0:8], h[8:12], h[12:16], h[16:20], h[20:32])


def load_schema():
    with open(SCHEMA_FILE) as fh:
        return json.load(fh)


def load_config():
    if not os.path.exists(CONFIG_FILE):
        return {}
    with open(CONFIG_FILE) as fh:
        return json.load(fh)


def save_config(cfg):
    with open(CONFIG_FILE, "w") as fh:
        json.dump(cfg, fh, indent=2)
        fh.write("\n")
    print("wrote %s" % os.path.relpath(CONFIG_FILE, os.path.dirname(HERE)))


def prop_payload(spec):
    """One entry of a Notion `properties` body. Relations are added later."""
    t = spec["type"]
    if t in ("title", "rich_text", "url", "date", "number", "checkbox", "email",
             "phone_number", "people", "files"):
        return {t: {}}
    if t in ("select", "multi_select"):
        return {t: {"options": [{"name": o} for o in spec.get("options", [])]}}
    raise SystemExit("unsupported property type in notion_schema.json: %s" % t)


def title_payload(text):
    return [{"type": "text", "text": {"content": text}}]


# ------------------------------------------------------------------ create --

def create_table(parent_id, table, dry_run=False):
    """Create one database. Returns {'database_id':..., 'data_source_id':...}."""
    props = {}
    for name, spec in table["properties"].items():
        if spec["type"] == "relation":
            continue                      # second pass, once both tables exist
        props[name] = prop_payload(spec)

    body_new = {
        "parent": {"type": "page_id", "page_id": parent_id},
        "title": title_payload(table["label"]),
        "initial_data_source": {"properties": props},
    }
    if dry_run:
        print("  would create %-34s %d properties"
              % (table["label"], len(props)))
        return None

    try:
        out = n.request("POST", "/databases", body_new, n.API_VERSION)
        ds = (out.get("data_sources") or [{}])[0].get("id")
        return {"database_id": out["id"], "data_source_id": ds or out["id"]}
    except n.NotionError as e:
        if e.code not in (400, 404):
            raise
        # Workspace predates the 2025-09-03 data-source API.
        body_old = {
            "parent": {"type": "page_id", "page_id": parent_id},
            "title": title_payload(table["label"]),
            "properties": props,
        }
        out = n.request("POST", "/databases", body_old, n.FALLBACK_API_VERSION)
        return {"database_id": out["id"], "data_source_id": out["id"]}


def add_relation(source, target, prop_name, synced_name, dry_run=False):
    """Add one relation column, dual if the workspace allows it."""
    if dry_run:
        print("  would link %s -> %s" % (prop_name, target["label"]))
        return

    def patch(version, path, ref_key, ref_id, dual):
        rel = {"type": "dual_property",
               "dual_property": {}} if dual else {"type": "single_property",
                                                  "single_property": {}}
        rel[ref_key] = ref_id
        return n.request("PATCH", path, {"properties": {prop_name: {"relation": rel}}},
                         version)

    ds = source.get("data_source_id")
    attempts = []
    if ds:
        attempts.append((n.API_VERSION, "/data_sources/%s" % ds,
                         "data_source_id", target["data_source_id"]))
    attempts.append((n.FALLBACK_API_VERSION, "/databases/%s" % source["database_id"],
                     "database_id", target["database_id"]))

    last = None
    for version, path, ref_key, ref_id in attempts:
        for dual in (True, False):
            try:
                patch(version, path, ref_key, ref_id, dual)
                kind = "two-way" if dual else "one-way"
                print("  linked %-16s -> %-34s (%s)"
                      % (prop_name, target["label"], kind))
                return
            except n.NotionError as e:
                last = e
                if e.code not in (400, 404):
                    raise
    print("  ! could not add the %s relation: %s" % (prop_name, last))
    print("    Add it by hand in Notion (a Relation column pointing at %s)."
          % target["label"])


# ------------------------------------------------------------------ verify --

def verify(cfg):
    """Prove both tables resolve and every schema column is present."""
    schema = load_schema()
    ok = True
    for key in ("tracker", "targets"):
        if key not in cfg:
            print("  %-8s MISSING from notion_config.json" % key)
            ok = False
            continue
        try:
            live = n.get_schema(cfg[key])
        except Exception as e:                       # noqa: BLE001
            print("  %-8s UNREACHABLE — %s" % (key, e))
            print("           Is the integration connected to this table?")
            ok = False
            continue
        want = set(schema[key]["properties"])
        missing = sorted(want - set(live))
        print("  %-8s ok  %2d columns  (%s)" % (key, len(live), cfg[key]["label"]))
        if missing:
            print("           missing: %s" % ", ".join(missing))
            ok = False
    return ok


# -------------------------------------------------------------------- main --

def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--parent", help="Notion page URL or id to create the tables under")
    ap.add_argument("--verify", action="store_true", help="check an existing setup and exit")
    ap.add_argument("--dry-run", action="store_true", help="say what would happen, write nothing")
    args = ap.parse_args()

    cfg = load_config()

    if args.verify or (not args.parent and cfg):
        if not cfg:
            raise SystemExit("no notion_config.json yet — run with --parent first.")
        print("verifying %s" % os.path.relpath(CONFIG_FILE, os.path.dirname(HERE)))
        ok = verify(cfg)
        if ok:
            print("\nBoth tables resolve. Next: python3 pipeline/notion_pull.py "
                  '--out-dir /tmp/notion-check --queue')
        raise SystemExit(0 if ok else 1)

    if not args.parent:
        raise SystemExit("need --parent <notion page url>  (or --verify)")

    n.token()                                  # fail early and clearly if unset
    parent_id = parse_page_id(args.parent)
    schema = load_schema()

    print("creating tables under page %s" % parent_id)
    made = {}
    for key in ("tracker", "targets"):
        if key in cfg:
            try:
                n.get_schema(cfg[key])
                print("  %-8s already exists — keeping %s" % (key, cfg[key]["label"]))
                made[key] = cfg[key]
                continue
            except Exception:                  # noqa: BLE001
                print("  %-8s recorded but unreachable — recreating" % key)
        result = create_table(parent_id, schema[key], args.dry_run)
        if result is None:
            continue
        result["label"] = schema[key]["label"]
        made[key] = result
        print("  %-8s created  %s" % (key, schema[key]["label"]))

    if args.dry_run:
        print("\ndry run — nothing was written.")
        return

    for key in ("tracker", "targets"):
        for name, spec in schema[key]["properties"].items():
            if spec["type"] != "relation":
                continue
            other = spec["to"]
            if key in made and other in made:
                add_relation(made[key], made[other], name,
                             spec.get("synced_name", ""))

    out = {"_comment": "Written by notion_bootstrap.py. Table ids only — no "
                       "secrets. The token lives in $NOTION_TOKEN or "
                       "pipeline/.notion-token."}
    out.update(made)
    save_config(out)

    print("\nverifying")
    if verify(out):
        print("\nDone. Next:")
        print("  python3 pipeline/notion_pull.py --out-dir /tmp/notion-check --queue")


if __name__ == "__main__":
    main()
