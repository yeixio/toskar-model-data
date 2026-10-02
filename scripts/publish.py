#!/usr/bin/env python3
"""Validate an aggregate snapshot and lay it out in this repository.

    publish.py SNAPSHOT.json

Writes ratings/summary.json (the latest snapshot), one file per model
configuration under models/<model>/, and snapshots/<date>.json. The snapshot
must match schema/ratings-v1.schema.json; nothing is written otherwise.
"""
import json
import pathlib
import re
import sys

import jsonschema

ROOT = pathlib.Path(__file__).resolve().parent.parent
SAFE = re.compile(r"^[a-z0-9][a-z0-9._-]*$")


def main(path: str) -> int:
    snap = json.loads(pathlib.Path(path).read_text())
    schema = json.loads((ROOT / "schema" / "ratings-v1.schema.json").read_text())
    jsonschema.validate(snap, schema)

    # Belt and braces: nothing per person, and no small cohorts.
    for m in snap["models"]:
        for c in m["cohorts"]:
            if c["tier"] == "exact" or c["ratings"] < snap["min_ratings"]:
                raise SystemExit(f"refusing to publish a small or exact cohort in {m['model']}")

    def write(rel: str, data) -> None:
        p = ROOT / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")

    write("ratings/summary.json", snap)
    date = snap["generated_at"][:10]
    write(f"snapshots/{date}.json", snap)

    keep = set()
    for m in snap["models"]:
        if not SAFE.match(m["model"]):
            raise SystemExit(f"unsafe model id {m['model']!r}")
        name = "-".join(x.lower() for x in (m["quantization"], m["runtime"], m["backend"], m["format"]))
        rel = f"models/{m['model']}/{name}.json"
        keep.add(ROOT / rel)
        write(rel, {"schema_version": snap["schema_version"], "generated_at": snap["generated_at"],
                    "prior": snap["prior"], "weight": snap["weight"], "min_ratings": snap["min_ratings"], **m})
    # A configuration no longer published (its ratings were removed) goes.
    for old in (ROOT / "models").glob("*/*.json"):
        if old not in keep:
            old.unlink()
    for d in (ROOT / "models").glob("*"):
        if d.is_dir() and not any(d.iterdir()):
            d.rmdir()
    print(f"published {len(snap['models'])} configurations for {date}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
