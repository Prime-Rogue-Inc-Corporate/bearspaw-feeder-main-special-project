#!/usr/bin/env python3
"""Archive the City of Calgary's daily water demand charts into raw/city/daily-demand/, unchanged.

During a feeder main shutdown the City posts one chart a day on its water restrictions page, as an image named
`daily-demand-<mon>-<day>.jpg`. The page links only the newest one or two, so each day's chart has to be collected by name.

Each run tries, in this order:
  1. every demand chart linked on the restrictions page;
  2. the names for the last DAYS days (Calgary time);
  3. every name or URL listed in trigger/demand-backfill.txt (blank lines and lines starting with # are ignored).

A chart is stored only if it is new, or if its bytes differ from the copy last stored from the same URL (the City can
replace an image under the same name). Stored files are named `{utc}-<name>` and logged in raw/fetch-log.jsonl with UTC
time, HTTP status, bytes and SHA-256. A name that does not exist (HTTP 404) is not logged: most guesses miss.
Any other failure is logged. The stamping workflow then checksums and Bitcoin-timestamps what was stored.
"""
import hashlib
import json
import re
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

PAGE = "https://www.calgary.ca/emergencies/feeder-main-repair/make-every-drop-count.html"
BASE = "https://www.calgary.ca/content/dam/www/uep/water/publishingimages/2026-bsfm/"
DAYS = 10
UA = "RWI-raw-archiver/1.0 (+https://rogerwilcoimagery.com/project/bearspaw.html)"
LINK = re.compile(r'/content/dam/[^"\'\s>]*daily-demand[^"\'\s>]*\.(?:jpe?g|png)', re.I)
MAGIC = (b"\xff\xd8\xff", b"\x89PNG")


def get(url: str):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "*/*"})
    err = ""
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                return r.status, r.read(), r.headers.get("Content-Type", "")
        except urllib.error.HTTPError as e:
            return e.code, b"", ""
        except Exception as e:  # network hiccup: retry
            err = str(e)
            time.sleep(5 * (attempt + 1))
    return 0, err.encode(), "error"


def candidates(root: Path):
    urls = []
    status, body, _ = get(PAGE)
    if status == 200:
        urls += ["https://www.calgary.ca" + m.group(0) for m in LINK.finditer(body.decode("utf-8", "replace"))]
    else:
        print(f"page not read (HTTP {status}); going by name only")
    today = datetime.now(ZoneInfo("America/Edmonton")).date()
    for back in range(DAYS):
        d = today - timedelta(days=back)
        urls.append(f"{BASE}daily-demand-{d.strftime('%b').lower()}-{d.day}.jpg")
    backfill = root / "trigger" / "demand-backfill.txt"
    if backfill.exists():
        for line in backfill.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#"):
                urls.append(line if line.startswith("http") else BASE + line)
    seen, out = set(), []
    for u in urls:
        if u not in seen:
            seen.add(u)
            out.append(u)
    return out


def main() -> int:
    root = Path(__file__).resolve().parent.parent
    log = root / "raw" / "fetch-log.jsonl"
    last = {}  # url -> sha256 of the copy last stored
    if log.exists():
        for line in log.read_text().splitlines():
            try:
                r = json.loads(line)
            except ValueError:
                continue
            if r.get("sha256") and r.get("url"):
                last[r["url"]] = r["sha256"]
    stored = 0
    for url in candidates(root):
        now = datetime.now(timezone.utc)
        status, body, ctype = get(url)
        name = url.rsplit("/", 1)[-1]
        if status == 404:
            print("404", name)
            continue
        rec = {"fetched_utc": now.strftime("%Y-%m-%dT%H:%M:%SZ"), "url": url, "http": status, "content_type": ctype}
        if status == 200 and body.startswith(MAGIC):
            h = hashlib.sha256(body).hexdigest()
            if last.get(url) == h:
                print("same", name)
                continue
            rel = f"raw/city/daily-demand/{now.strftime('%Y-%m-%dT%H%MZ')}-{name}"
            out = root / rel
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_bytes(body)
            rec.update(path=rel, bytes=len(body), sha256=h)
            if url in last:
                rec["note"] = "replaces an earlier copy from the same URL; the earlier file is kept"
            last[url] = h
            stored += 1
            print("stored", rel)
        else:
            rec.update(path=None, stored=False, note="not an image" if status == 200 else "not fetched")
            print(status, "not stored", name)
        with log.open("a") as f:
            f.write(json.dumps(rec) + "\n")
        time.sleep(1)
    print(f"{stored} stored")
    return 0


if __name__ == "__main__":
    sys.exit(main())
