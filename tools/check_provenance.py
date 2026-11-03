"""Checks that every audio, image and post in this repo has a provenance record in provenance.json.

    python -P tools/check_provenance.py            # structure check; lists what is still a placeholder
    python -P tools/check_provenance.py --release  # also fails on anything that is not cleared to ship
    python -P tools/check_provenance.py --sync     # adds records for new files, refreshes changed hashes

A record says where a file came from and under what terms Serin may use it:

    "images/meditations/sleep.jpg": {
      "source":  original | generated-code | ai-generated | third-party | unknown,
      "license": "owned", an SPDX id such as "CC0-1.0", or "unknown",
      "created": "2026-10-07",
      "status":  placeholder | final,       # final = cleared to ship
      "sha256":  "...",                      # of the file; text files are hashed with LF line endings
      "tool":    "...",                      # ai-generated, generated-code: what made it
      "plan":    "paid" | "free",            # ai-generated: the plan it was made on
      "url":     "...",                      # third-party: where it came from
      "notes":   "..."
    }

The hash is there so a file cannot be swapped for another one while its record keeps saying "final":
change a file and the check fails until you review its record and run --sync.
"""

import argparse
import datetime
import hashlib
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "provenance.json"
ASSET_DIRS = ("audio", "images", "posts")
TEXT_SUFFIXES = {".md", ".txt", ".json"}

SOURCES = {"original", "generated-code", "ai-generated", "third-party", "unknown"}
STATUSES = {"placeholder", "final"}
PLANS = {"paid", "free"}
REFERENCE = re.compile(r"^(?:%s)/\S+\.\w+$" % "|".join(ASSET_DIRS))
DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def asset_files():
    found = []
    for folder in ASSET_DIRS:
        for path in (ROOT / folder).rglob("*"):
            if path.is_file() and not path.name.startswith("."):
                found.append(path.relative_to(ROOT).as_posix())
    return sorted(found)


def digest(rel):
    data = (ROOT / rel).read_bytes()
    if pathlib.PurePosixPath(rel).suffix in TEXT_SUFFIXES:
        data = data.replace(b"\r\n", b"\n")  # a Windows checkout may have converted the line endings
    return hashlib.sha256(data).hexdigest()


def references(node):
    """Every asset path content.json points at."""
    if isinstance(node, str):
        return {node} if REFERENCE.match(node) else set()
    if isinstance(node, list):
        node = dict(enumerate(node))
    if isinstance(node, dict):
        return set().union(*(references(v) for v in node.values()), set())
    return set()


def load_manifest():
    if not MANIFEST.exists():
        return {}
    return json.loads(MANIFEST.read_text(encoding="utf-8")).get("assets", {})


def save_manifest(assets):
    ordered = {path: assets[path] for path in sorted(assets)}
    MANIFEST.write_text(json.dumps({"assets": ordered}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def check(assets, release):
    errors, warnings = [], []
    files = set(asset_files())

    for rel in sorted(files - assets.keys()):
        errors.append(f"{rel}: no record in provenance.json (run --sync, then fill it in)")
    for rel in sorted(assets.keys() - files):
        errors.append(f"{rel}: has a record but the file is gone")

    content = json.loads((ROOT / "content.json").read_text(encoding="utf-8"))
    used = references(content)
    for rel in sorted(used - files):
        errors.append(f"{rel}: content.json points at it but the file does not exist")
    for rel in sorted(files - used):
        warnings.append(f"{rel}: not used by content.json")

    for rel in sorted(files & assets.keys()):
        record = assets[rel]
        problems = []
        if record.get("source") not in SOURCES:
            problems.append(f"source must be one of {sorted(SOURCES)}")
        if not record.get("license"):
            problems.append("license is missing")
        if record.get("status") not in STATUSES:
            problems.append(f"status must be one of {sorted(STATUSES)}")
        if not DATE.match(str(record.get("created", ""))):
            problems.append("created must be YYYY-MM-DD")
        if record.get("sha256") != digest(rel):
            problems.append("the file changed since its record was written; review the record, then run --sync")
        if record.get("source") == "ai-generated":
            if not record.get("tool"):
                problems.append("ai-generated needs `tool`")
            if record.get("plan") not in PLANS:
                problems.append("ai-generated needs `plan` (paid or free)")
        if record.get("source") == "third-party" and not record.get("url"):
            problems.append("third-party needs `url`")
        errors += [f"{rel}: {p}" for p in problems]

        if record.get("status") != "final":
            (errors if release else warnings).append(f"{rel}: still a placeholder")
        if release:
            if record.get("source") == "unknown" or record.get("license") == "unknown":
                errors.append(f"{rel}: source or license is unknown")
            if record.get("source") == "ai-generated" and record.get("plan") == "free":
                errors.append(f"{rel}: made on a free plan; regenerate it on a plan whose terms allow commercial use")
    return errors, warnings


def sync(assets):
    for rel in asset_files():
        if rel not in assets:
            assets[rel] = {"source": "unknown", "license": "unknown",
                           "created": datetime.date.today().isoformat(), "status": "placeholder",
                           "sha256": digest(rel), "notes": ""}
            print(f"added   {rel}: fill in source and license")
        elif assets[rel].get("sha256") != digest(rel):
            assets[rel]["sha256"] = digest(rel)
            if assets[rel].get("status") == "final":
                assets[rel]["status"] = "placeholder"  # a changed file has to be cleared again
            print(f"updated {rel}: hash refreshed; check its record and set status back to final")
    save_manifest(assets)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--release", action="store_true", help="fail on anything that is not cleared to ship")
    parser.add_argument("--sync", action="store_true", help="add records for new files and refresh changed hashes")
    args = parser.parse_args()

    assets = load_manifest()
    if args.sync:
        sync(assets)
        return 0

    errors, warnings = check(assets, args.release)
    for line in warnings:
        print(f"warning: {line}")
    for line in errors:
        print(f"error:   {line}")
    shipped = sum(1 for r in assets.values() if r.get("status") == "final")
    print(f"{len(assets)} assets, {shipped} cleared to ship, {len(errors)} errors, {len(warnings)} warnings")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
