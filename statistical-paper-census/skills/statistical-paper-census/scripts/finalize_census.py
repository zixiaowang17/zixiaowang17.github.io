#!/usr/bin/env python3
"""Derive demand metrics and dependency-safe order for a census v4 artifact."""

from __future__ import annotations

import argparse
import json
import os
import tempfile
from pathlib import Path

from census_metrics import DERIVED_FIELDS, MetricsError, derive_metrics
from validate_census import validate
from canonical_dependencies import canonical_dependencies
from publication_contract import attach_inventory


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--inventory", type=Path, required=True, help="Independently inspected theorem inventory")
    args = parser.parse_args()

    if args.inventory.resolve() == args.output.resolve():
        parser.error("output must not overwrite the source inventory")

    data = json.loads(args.input.read_text(encoding="utf-8"))
    for item in data.get("interfaces", []):
        for field in (*DERIVED_FIELDS, "rank", "paper_count", "central_use_count"):
            item.pop(field, None)
    try:
        attach_inventory(data, args.inventory, args.output)
        edges = canonical_dependencies(data)
        for item in data.get("interfaces", []):
            item["dependencies"] = edges[item["interface_id"]]
        derive_metrics(data)
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(f"ERROR: {error}")
        return 1

    args.output.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix='.' + args.output.name + '-', dir=args.output.parent)
    temporary = Path(name)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as stream:
            stream.write(json.dumps(data, ensure_ascii=False, indent=2) + '\n')
            stream.flush(); os.fsync(stream.fileno())
        errors = validate(temporary)
        if errors:
            for error in errors: print(f"ERROR: {error}")
            return 1
        os.replace(temporary, args.output)
    finally:
        temporary.unlink(missing_ok=True)
    print(f"{args.output}: finalized and passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
