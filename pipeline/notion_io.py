#!/usr/bin/env python3
"""
Notion REST I/O for the jobscan / resume-build pipeline.

WHY THIS EXISTS. The MCP Notion tools route every row through the
conversation: the payload goes up, an equally large confirmation comes back. On
the 15 Sep jobscan that was ~100k of a ~327k-token run just to write 95 rows —
roughly 30% of the whole sweep spent echoing JSON. These scripts do the same
reads and writes over the public REST API, print only counts and failures, and
leave the row data in files on disk.

ON THE "read through views, never SQL" RULE. That rule
exists because the MCP tool's *SQL mode* returned stale rows against a
`collection://`. This is not SQL mode. It is the same REST API the Notion UI
and the MCP view mode both read from, paginated to exhaustion, so it sees the
same rows a view sees. Two things preserve the rule's intent:

  1. Both views this pipeline reads are UNFILTERED (tracker `All`, Target
     Companies `Default view`), so querying the data source directly returns the
     same set. If either view ever gains a filter, this equivalence breaks and
     the scripts must be revisited.
  2. Pagination is not optional here and not left to a caller — query_all()
     loops the cursor to exhaustion internally and cannot return a partial page.

AUTH. Never pass a token on the command line and never paste one into a
conversation. Resolution order:
    1. $NOTION_TOKEN
    2. pipeline/.notion-token  (must be chmod 600)
See pipeline/NOTION-SETUP.md.

Stdlib only, to match rank.py.
"""

import json
import os
import ssl
import sys
import time
import urllib.error
import urllib.request

API = "https://api.notion.com/v1"
API_VERSION = "2025-09-03"          # data-source era; falls back automatically
FALLBACK_API_VERSION = "2022-06-28"  # database-era

HERE = os.path.dirname(os.path.abspath(__file__))
TOKEN_FILE = os.path.join(HERE, ".notion-token")
CONFIG_FILE = os.path.join(HERE, "notion_config.json")

# Notion's published limit is ~3 requests/second averaged. Creating a full
# jobscan batch is ~100 sequential POSTs, so pace rather than get throttled.
MIN_INTERVAL = 0.34
MAX_RETRIES = 5

_last_call = [0.0]


# --------------------------------------------------------------------------
# auth + config
# --------------------------------------------------------------------------

def token():
    t = os.environ.get("NOTION_TOKEN", "").strip()
    if t:
        return t
    if os.path.exists(TOKEN_FILE):
        mode = os.stat(TOKEN_FILE).st_mode & 0o777
        if mode & 0o077:
            raise SystemExit(
                "refusing to read %s: mode is %o, group/world readable.\n"
                "  chmod 600 %s" % (TOKEN_FILE, mode, TOKEN_FILE))
        with open(TOKEN_FILE) as fh:
            t = fh.read().strip()
        if t:
            return t
    raise SystemExit(
        "no Notion token found.\n"
        "  export NOTION_TOKEN=ntn_...   (preferred)\n"
        "  or write it to %s and chmod 600 that file\n"
        "See pipeline/NOTION-SETUP.md." % TOKEN_FILE)


def config():
    if not os.path.exists(CONFIG_FILE):
        raise SystemExit("missing %s" % CONFIG_FILE)
    with open(CONFIG_FILE) as fh:
        return json.load(fh)


# --------------------------------------------------------------------------
# transport
# --------------------------------------------------------------------------

def _sleep_for_rate_limit():
    gap = time.time() - _last_call[0]
    if gap < MIN_INTERVAL:
        time.sleep(MIN_INTERVAL - gap)
    _last_call[0] = time.time()


def request(method, path, body=None, version=API_VERSION):
    """One API call, with pacing, 429 honouring and retry on 5xx/transport."""
    url = path if path.startswith("http") else API + path
    data = json.dumps(body).encode() if body is not None else None
    headers = {
        "Authorization": "Bearer " + token(),
        "Notion-Version": version,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    ctx = ssl.create_default_context()
    last = None
    for attempt in range(MAX_RETRIES):
        _sleep_for_rate_limit()
        req = urllib.request.Request(url, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=60, context=ctx) as r:
                return json.loads(r.read().decode())
        except urllib.error.HTTPError as e:
            raw = e.read().decode("utf-8", "replace")
            if e.code == 429:
                wait = float(e.headers.get("Retry-After", "1")) + 0.5
                time.sleep(wait)
                last = ("429", raw)
                continue
            if 500 <= e.code < 600:
                time.sleep(1.5 * (attempt + 1))
                last = (str(e.code), raw)
                continue
            # 4xx other than 429 is a real error — surface the API's own message
            try:
                msg = json.loads(raw).get("message", raw)
            except Exception:
                msg = raw
            raise NotionError(e.code, msg)
        except (urllib.error.URLError, ssl.SSLError, TimeoutError) as e:
            time.sleep(1.5 * (attempt + 1))
            last = ("transport", repr(e))
            continue
    raise NotionError(0, "gave up after %d attempts: %s" % (MAX_RETRIES, last))


class NotionError(Exception):
    def __init__(self, code, message):
        self.code = code
        self.message = message
        Exception.__init__(self, "HTTP %s: %s" % (code, message))


# --------------------------------------------------------------------------
# id helpers
# --------------------------------------------------------------------------

def dashless(page_id):
    return (page_id or "").replace("-", "")


def page_url(page_id):
    """Match the shape the MCP tools returned, so downstream code is unchanged."""
    return "https://app.notion.com/p/" + dashless(page_id)


# --------------------------------------------------------------------------
# reading
# --------------------------------------------------------------------------

def query_all(source, progress=None):
    """Every row of a table, paginated to exhaustion. Never returns a partial read.

    `source` is a dict from notion_config.json with `data_source_id` and
    `database_id`. Tries the data-source endpoint first (2025-09-03) and falls
    back to the database endpoint (2022-06-28) if the workspace predates it.
    Returns (rows, endpoint_used).
    """
    attempts = []
    if source.get("data_source_id"):
        attempts.append(("data_source",
                         "/data_sources/%s/query" % source["data_source_id"],
                         API_VERSION))
    if source.get("database_id"):
        attempts.append(("database",
                         "/databases/%s/query" % source["database_id"],
                         FALLBACK_API_VERSION))

    first_error = None
    for kind, path, version in attempts:
        rows = []
        cursor = None
        pages = 0
        try:
            while True:
                body = {"page_size": 100}
                if cursor:
                    body["start_cursor"] = cursor
                out = request("POST", path, body, version=version)
                rows.extend(out.get("results", []))
                pages += 1
                if progress:
                    progress(kind, pages, len(rows))
                if not out.get("has_more"):
                    break
                cursor = out.get("next_cursor")
                if not cursor:
                    # has_more true with no cursor is a broken read, not an end
                    raise NotionError(0, "has_more=true with no next_cursor "
                                         "after %d rows" % len(rows))
            return rows, kind
        except NotionError as e:
            first_error = first_error or e
            if e.code in (400, 404) and kind == "data_source":
                continue   # workspace may predate data sources; try database
            raise
    raise first_error or SystemExit("no queryable id in config for this table")


def get_schema(source):
    """{property name: notion type} — needed to build write payloads."""
    if source.get("data_source_id"):
        try:
            out = request("GET", "/data_sources/%s" % source["data_source_id"])
            return {k: v.get("type") for k, v in out.get("properties", {}).items()}
        except NotionError as e:
            if e.code not in (400, 404):
                raise
    out = request("GET", "/databases/%s" % source["database_id"],
                  version=FALLBACK_API_VERSION)
    return {k: v.get("type") for k, v in out.get("properties", {}).items()}


# --------------------------------------------------------------------------
# flatten: REST page -> the flat dict shape the MCP tools produced
# --------------------------------------------------------------------------

def _plain(rich):
    return "".join(x.get("plain_text", "") for x in (rich or []))


def flatten(page):
    """REST page object -> flat dict.

    Deliberately reproduces the MCP tools' shape so tracker.json and
    targets.json stay drop-in for rank.py, canonical_key() and both skills:
    multi_select and relation come back as JSON *strings*, dates explode into
    `date:NAME:start` / `:end` / `:is_datetime`, and `url` is the page URL.

    Empty values follow the MCP tools' own convention exactly, because callers
    rely on it: an empty select / multi-select / relation / number is an ABSENT
    key, not an empty one. Emitting `"[]"` for an empty relation would be
    truthy and would silently flip any `if row.get("Target Company"):` test.
    Title, rich_text and url always appear, empty string included.
    """
    flat = {"url": page_url(page.get("id"))}
    for name, prop in (page.get("properties") or {}).items():
        t = prop.get("type")
        v = prop.get(t)
        if t == "title":
            flat[name] = _plain(v)
        elif t == "rich_text":
            flat[name] = _plain(v)
        elif t in ("select", "status"):
            if v and v.get("name"):
                flat[name] = v["name"]
        elif t == "multi_select":
            if v:
                flat[name] = json.dumps([o.get("name") for o in v])
        elif t == "number":
            if v is not None:
                flat[name] = v
        elif t in ("url", "email", "phone_number"):
            flat[name] = v or ""
        elif t == "checkbox":
            flat[name] = bool(v)
        elif t == "relation":
            if v:
                flat[name] = json.dumps([page_url(o.get("id")) for o in v])
        elif t == "people":
            if v:
                flat[name] = json.dumps([o.get("id") for o in v])
        elif t == "date":
            start = (v or {}).get("start") if v else None
            end = (v or {}).get("end") if v else None
            if start:
                flat["date:%s:start" % name] = start
            if end:
                flat["date:%s:end" % name] = end
            flat["date:%s:is_datetime" % name] = 1 if (start and "T" in start) else 0
        elif t == "formula":
            f = v or {}
            flat[name] = f.get(f.get("type"), "")
        elif t in ("created_time", "last_edited_time"):
            flat[name] = v
        # rollups, files and unsupported types are intentionally skipped —
        # nothing in this pipeline reads them.
    return flat


# --------------------------------------------------------------------------
# to_properties: flat dict -> REST properties
# --------------------------------------------------------------------------

def _as_list(value):
    """Accept a JSON string, a real list, or a bare string."""
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        s = value.strip()
        if s.startswith("["):
            try:
                return json.loads(s)
            except ValueError:
                pass
        return [s] if s else []
    return [value]


def _relation_id(ref):
    """Accept a page URL, a bare id, dashed or not."""
    ref = (ref or "").strip()
    if "/" in ref:
        ref = ref.rstrip("/").split("/")[-1]
    ref = ref.split("?")[0]
    return dashless(ref)


def to_properties(flat, schema):
    """Flat dict (same shape jobscan already builds) -> REST properties.

    Unknown keys raise rather than being silently dropped — a typo'd property
    name that vanishes is exactly the kind of quiet half-write this pipeline's
    reconcile step exists to catch.
    """
    props = {}
    dates = {}
    for key, value in flat.items():
        if key == "url":
            continue
        if key.startswith("date:"):
            parts = key.split(":")
            if len(parts) != 3:
                raise ValueError("malformed date key %r" % key)
            _, name, field = parts
            dates.setdefault(name, {})[field] = value
            continue
        t = schema.get(key)
        if t is None:
            raise ValueError("no such property %r in this table "
                             "(have: %s)" % (key, ", ".join(sorted(schema))))
        if value is None:
            props[key] = {t: None}
        elif t == "title":
            props[key] = {"title": [{"text": {"content": str(value)}}]}
        elif t == "rich_text":
            props[key] = {"rich_text": [{"text": {"content": str(value)}}]}
        elif t in ("select", "status"):
            props[key] = {t: {"name": str(value)}} if str(value) else {t: None}
        elif t == "multi_select":
            props[key] = {"multi_select": [{"name": n} for n in _as_list(value) if n]}
        elif t == "number":
            props[key] = {"number": None if value == "" else float(value)}
        elif t in ("url", "email", "phone_number"):
            props[key] = {t: str(value) or None}
        elif t == "checkbox":
            props[key] = {"checkbox": value in (True, "__YES__", "true", 1)}
        elif t == "relation":
            props[key] = {"relation": [{"id": _relation_id(r)}
                                       for r in _as_list(value) if r]}
        else:
            raise ValueError("property %r has type %r, which this script does "
                             "not write" % (key, t))

    for name, fields in dates.items():
        start = fields.get("start")
        if not start:
            continue
        d = {"start": start}
        if fields.get("end"):
            d["end"] = fields["end"]
        props[name] = {"date": d}
    return props


# --------------------------------------------------------------------------
# writing
# --------------------------------------------------------------------------

def _parent(source):
    if source.get("data_source_id"):
        return {"type": "data_source_id",
                "data_source_id": source["data_source_id"]}, API_VERSION
    return {"type": "database_id",
            "database_id": source["database_id"]}, FALLBACK_API_VERSION


def _content_blocks(text):
    """Plain paragraphs. Notion caps a rich_text chunk at 2000 chars."""
    blocks = []
    for para in str(text).split("\n\n"):
        para = para.strip()
        if not para:
            continue
        for i in range(0, len(para), 1900):
            blocks.append({
                "object": "block",
                "type": "paragraph",
                "paragraph": {"rich_text": [
                    {"type": "text", "text": {"content": para[i:i + 1900]}}]},
            })
    return blocks[:100]


def create_page(source, schema, row):
    """row = {"properties": {...flat...}, "content": "optional body text"}"""
    parent, version = _parent(source)
    body = {"parent": parent,
            "properties": to_properties(row.get("properties", {}), schema)}
    content = row.get("content")
    if content:
        body["children"] = _content_blocks(content)
    out = request("POST", "/pages", body, version=version)
    return out.get("id"), page_url(out.get("id"))


def update_page(page_id, flat, schema):
    props = to_properties(flat, schema)
    out = request("PATCH", "/pages/%s" % dashless(page_id), {"properties": props})
    return out.get("id")
