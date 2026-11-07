#!/usr/bin/env python3
"""Archive public records listed in a trigger file into raw/, unchanged.

Trigger file: one fetch per line, tab-separated:  <path under raw/>  <url>
  - `{utc}` in the path becomes the fetch time, e.g. raw/city/pages/bsfm-status/{utc}.html
  - blank lines and lines starting with # are ignored
Every fetch (ok or not) is appended to raw/fetch-log.jsonl with UTC time, HTTP status, bytes and SHA-256.
Files over 95 MB are not stored (GitHub's limit is 100 MB); the log says so.
The stamping workflow then checksums and Bitcoin-timestamps everything stored.
"""
import hashlib
import json
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

MAX = 95 * 1024 * 1024
UA = "RWI-raw-archiver/1.0 (+https://rogerwilcoimagery.com/project/bearspaw.html)"


def fetch(url: str):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "*/*"})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=180) as r:
                return r.status, r.read(MAX + 1), r.headers.get("Content-Type", "")
        except urllib.error.HTTPError as e:
            return e.code, b"", ""
        except Exception as e:  # network hiccup: retry
            err = str(e)
            time.sleep(5 * (attempt + 1))
    return 0, err.encode(), "error"


def main(trigger: str) -> int:
    root = Path(__file__).resolve().parent.parent
    log = root / "raw" / "fetch-log.jsonl"
    log.parent.mkdir(parents=True, exist_ok=True)
    failed = 0
    for line in Path(trigger).read_text().splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        rel, url = [x.strip() for x in line.split("\t", 1)]
        now = datetime.now(timezone.utc)
        rel = rel.replace("{utc}", now.strftime("%Y-%m-%dT%H%MZ"))
        if not rel.startswith("raw/") or ".." in rel:
            print(f"skip (path must be under raw/): {rel}")
            continue
        status, body, ctype = fetch(url)
        rec = {"fetched_utc": now.strftime("%Y-%m-%dT%H:%M:%SZ"), "url": url, "path": rel, "http": status,
               "content_type": ctype}
        if status == 200 and len(body) <= MAX:
            out = root / rel
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_bytes(body)
            rec.update(bytes=len(body), sha256=hashlib.sha256(body).hexdigest())
        else:
            failed += 1
            rec.update(stored=False, note="too large" if len(body) > MAX else "not fetched")
        with log.open("a") as f:
            f.write(json.dumps(rec) + "\n")
        print(rec["http"], rec.get("bytes", "-"), rel)
    print(f"{failed} not stored")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "trigger/fetch.tsv"))
