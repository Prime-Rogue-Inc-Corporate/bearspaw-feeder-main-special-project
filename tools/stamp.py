#!/usr/bin/env python3
"""Checksums and Bitcoin timestamps for everything in this repo (Roger Wilco Imagery, RWI-SP-002 Bearspaw special project).

  python3 tools/stamp.py sums      write SHA256SUMS for every tracked data/output file
  python3 tools/stamp.py stamp     OpenTimestamps-stamp every file that has no proof for its current hash (needs network)
  python3 tools/stamp.py upgrade   upgrade pending proofs once the calendars have anchored them in a Bitcoin block
  python3 tools/stamp.py verify    check SHA256SUMS and that every listed file has a proof for its current hash

Proofs live in proofs/<path>.ots; proofs/index.json records path, sha256, stamped time (UTC), status and Bitcoin block.
A changed file is stamped again; the old proof is kept as proofs/<path>.<first 12 hex of old sha256>.ots, so every
published version stays provable. Anyone can check a file with:  ots verify proofs/<path>.ots -f <path>
"""
import hashlib, json, os, re, shutil, subprocess, sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKIP_DIRS = {".git", ".github", "proofs"}
SKIP_FILES = {"SHA256SUMS"}
INDEX = ROOT / "proofs" / "index.json"


def files():
    out = []
    for p in sorted(ROOT.rglob("*")):
        rel = p.relative_to(ROOT)
        if p.is_file() and rel.parts[0] not in SKIP_DIRS and rel.name not in SKIP_FILES and "__pycache__" not in rel.parts:
            out.append(rel.as_posix())
    return out


def sha(p):
    h = hashlib.sha256()
    with open(ROOT / p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def load():
    return json.loads(INDEX.read_text()) if INDEX.exists() else {"files": {}}


def save(ix):
    INDEX.parent.mkdir(exist_ok=True)
    INDEX.write_text(json.dumps(ix, indent=1, sort_keys=True) + "\n")


def now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def cmd_sums():
    lines = [f"{sha(p)}  {p}" for p in files()]
    (ROOT / "SHA256SUMS").write_text("\n".join(lines) + "\n")
    print(f"SHA256SUMS: {len(lines)} files")


def cmd_stamp():
    ix = load()
    todo = []
    for p in files() + ["SHA256SUMS"]:
        h = sha(p)
        e = ix["files"].get(p)
        if e and e["sha256"] == h:
            continue
        proof = ROOT / "proofs" / (p + ".ots")
        if e and proof.exists():  # keep the proof of the earlier version
            old = proof.with_name(f"{Path(p).name}.{e['sha256'][:12]}.ots")
            shutil.move(proof, old)
            ix.setdefault("superseded", []).append(dict(path=p, sha256=e["sha256"], proof=old.relative_to(ROOT).as_posix(),
                                                        stamped_utc=e.get("stamped_utc"), status=e.get("status"),
                                                        bitcoin_block=e.get("bitcoin_block")))
        todo.append((p, h))
    if not todo:
        print("nothing to stamp")
        return
    for p, h in todo:
        subprocess.run(["ots", "stamp", str(ROOT / p)], check=True)
        dst = ROOT / "proofs" / (p + ".ots")
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(ROOT / p) + ".ots", dst)
        ix["files"][p] = dict(sha256=h, stamped_utc=now(), status="pending", bitcoin_block=None)
        print("stamped", p)
    save(ix)


def cmd_upgrade():
    ix = load()
    changed = False
    for p, e in ix["files"].items():
        if e.get("status") == "confirmed":
            continue
        proof = ROOT / "proofs" / (p + ".ots")
        if not proof.exists():
            continue
        r = subprocess.run(["ots", "upgrade", str(proof)], capture_output=True, text=True)
        bak = Path(str(proof) + ".bak")
        if bak.exists():
            bak.unlink()
        info = subprocess.run(["ots", "info", str(proof)], capture_output=True, text=True).stdout
        m = re.findall(r"BitcoinBlockHeaderAttestation\((\d+)\)", info)
        if m:
            e.update(status="confirmed", bitcoin_block=int(min(map(int, m))), confirmed_seen_utc=now())
            changed = True
            print("confirmed", p, "block", e["bitcoin_block"])
        elif r.returncode:
            print("pending", p)
    if changed:
        save(ix)


def cmd_verify():
    ix = load()
    bad = 0
    listed = {}
    for ln in (ROOT / "SHA256SUMS").read_text().splitlines():
        h, p = ln.split("  ", 1)
        listed[p] = h
    for p in files():
        h = sha(p)
        if listed.get(p) != h:
            print("SHA256SUMS mismatch:", p)
            bad += 1
        e = ix["files"].get(p)
        if not e or e["sha256"] != h or not (ROOT / "proofs" / (p + ".ots")).exists():
            print("no proof for current version:", p)
            bad += 1
    print("verify:", "OK" if not bad else f"{bad} problem(s)")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    {"sums": cmd_sums, "stamp": cmd_stamp, "upgrade": cmd_upgrade, "verify": cmd_verify}[sys.argv[1]]()
