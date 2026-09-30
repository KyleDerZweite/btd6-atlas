#!/usr/bin/env python3
"""Derive conservative source-record structure from an unchanged capture.

This records field shapes, never gameplay values, file inventories, or hashes.
Observed nulls remain null-only; arrays without observed items remain empty-only.
It does not infer behavior, balance, numerical limits, or unseen alternatives.
Run `audit` to inspect counts or `generate` to write Profile contract documents.
Whole-number observations do not establish integer intent:

>>> observed = Shape("$type")
>>> observed.observe(2)
>>> observed.export()
{'type': 'number'}
>>> observed.observe(2.5)
>>> observed.export()
{'type': 'number'}
"""

import argparse
import json
import os
from pathlib import Path


NONFINITE = frozenset(("NaN", "Infinity", "-Infinity"))


class Shape:
    def __init__(self, discriminator):
        self.discriminator = discriminator
        self.scalars = set()
        self.string_tokens = set()
        self.free_string = False
        self.models = set()
        self.objects = {}
        self.arrays = False
        self.items = None

    def observe(self, value):
        if value is None:
            self.scalars.add("null")
        elif isinstance(value, bool):
            self.scalars.add("boolean")
        elif isinstance(value, (int, float)):
            self.scalars.add("number")
        elif isinstance(value, str):
            self.scalars.add("string")
            if value in NONFINITE:
                self.string_tokens.add(value)
            else:
                self.free_string = True
        elif isinstance(value, list):
            self.arrays = True
            for item in value:
                if self.items is None:
                    self.items = Shape(self.discriminator)
                self.items.observe(item)
        elif isinstance(value, dict):
            source = value.get(self.discriminator)
            if source is not None:
                if not isinstance(source, str) or not source:
                    raise ValueError("model discriminator must be a nonempty string")
                self.models.add(source)
            else:
                fields = self.objects.setdefault(tuple(sorted(value)), {})
                for name, item in value.items():
                    fields.setdefault(name, Shape(self.discriminator)).observe(item)
        else:
            raise ValueError(f"unsupported JSON value type: {type(value)}")

    def export(self):
        variants = []
        for scalar in sorted(self.scalars):
            variant = {"type": scalar}
            if scalar == "string" and not self.free_string:
                variant["enum"] = sorted(self.string_tokens)
            variants.append(variant)
        if self.models:
            variants.append({"type": "model", "models": sorted(self.models)})
        for keys, fields in sorted(self.objects.items()):
            variants.append({"type": "object", "fields": export_fields(fields)})
        if self.arrays:
            variants.append({"type": "array", "items": self.items.export()} if self.items
                            else {"type": "array", "maxItems": 0})
        if not variants:
            raise ValueError("cannot derive a shape without observed values")
        return variants[0] if len(variants) == 1 else {"anyOf": variants}


def export_fields(fields):
    return [{"field": name, "shape": shape.export()} for name, shape in sorted(fields.items())]


def matches(path, collection):
    prefix = collection["path"]
    return prefix == "." or path == prefix or path.startswith(prefix + "/")


def derive(data, profile, map_types):
    manifest = json.loads((profile / "manifest.json").read_text())
    documents = manifest["documents"]
    collections = json.loads((profile / documents["collections"]["file"]).read_text())["collections"]
    mechanics = json.loads((profile / documents["mechanics"]["file"]).read_text())
    discriminator = mechanics["typeIdentity"]["field"]
    models = {}
    counts = {"files": 0, "skippedFiles": 0, "instances": 0}

    def visit(value, detect=True):
        if isinstance(value, dict):
            if detect and discriminator in value:
                source = value[discriminator]
                if not isinstance(source, str) or not source:
                    raise ValueError("model discriminator must be a nonempty string")
                counts["instances"] += 1
                record = models.setdefault(source, {"fields": {}, "keys": None, "values": None})
                values = {key: item for key, item in value.items() if key != discriminator}
                if source in map_types:
                    for item in values.values():
                        if record["values"] is None:
                            record["values"] = Shape(discriminator)
                        record["values"].observe(item)
                else:
                    keys = tuple(sorted(values))
                    if record["keys"] is not None and record["keys"] != keys:
                        raise ValueError(f"inconsistent field set for {source}; review source variants or configure --map-type")
                    record["keys"] = keys
                    for name, item in values.items():
                        record["fields"].setdefault(name, Shape(discriminator)).observe(item)
            for item in value.values():
                visit(item)
        elif isinstance(value, list):
            for item in value:
                visit(item)

    for path in sorted(data.rglob("*.json")):
        relative = path.relative_to(data).as_posix()
        matched = [collection for collection in collections if matches(relative, collection)]
        active = [collection for collection in matched if collection.get("enabled", True)]
        if matched and not active:
            counts["skippedFiles"] += 1
            continue
        counts["files"] += 1
        detect = not active or any(c.get("typed", False) or c["idField"] != "@keys" for c in active)
        visit(json.loads(path.read_text()), detect)
    missing_maps = map_types - models.keys()
    if missing_maps:
        raise ValueError("configured map types were not observed: " + ", ".join(sorted(missing_maps)))
    contracts = []
    for source, record in sorted(models.items()):
        contract = {"sourceType": source, "fields": export_fields(record["fields"])}
        if source in map_types:
            if record["values"] is None:
                raise ValueError(f"cannot derive values of empty map {source}")
            contract["additionalFields"] = record["values"].export()
        contracts.append(contract)
    counts["sourceTypes"] = len(contracts)
    return contracts, counts


def format_contract(contract):
    # One field per line keeps large captures reviewable without huge schema files.
    compact = lambda value: json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    lines = ["    {", '      "sourceType": ' + json.dumps(contract["sourceType"]) + ",", '      "fields": [']
    fields = contract["fields"]
    lines.extend("        " + compact(field) + ("," if i + 1 < len(fields) else "") for i, field in enumerate(fields))
    lines.append("      ]" + ("," if "additionalFields" in contract else ""))
    if "additionalFields" in contract:
        lines.append('      "additionalFields": ' + compact(contract["additionalFields"]))
    lines.append("    }")
    return "\n".join(lines)


def generate(contracts, output, revision, chunk_bytes):
    directory = output / "model-contracts"
    directory.mkdir(parents=True, exist_ok=True)
    chunks = []
    current = []
    size = 32
    for contract in contracts:
        encoded = format_contract(contract)
        length = len(encoded.encode()) + 2
        if length + 32 > chunk_bytes:
            raise ValueError("a single contract exceeds --chunk-bytes")
        if current and size + length > chunk_bytes:
            chunks.append(current)
            current, size = [], 32
        current.append(encoded)
        size += length
    if current:
        chunks.append(current)
    paths = []
    for index, chunk in enumerate(chunks, 1):
        name = f"models-{index:03d}.json"
        paths.append("model-contracts/" + name)
        (directory / name).write_text('{\n  "contracts": [\n' + ",\n".join(chunk) + "\n  ]\n}\n")
    for obsolete in directory.glob("models-*.json"):
        if "model-contracts/" + obsolete.name not in paths:
            obsolete.unlink()
    catalog = {
        "requireContracts": True,
        "includes": paths,
        "contracts": [],
        "provenance": {
            "captureRevision": revision,
            "method": "Conservative structural derivation from all active capture records; reviewed map types use value shapes instead of entry keys.",
            "limitations": [
                "Observed structure only; does not establish behavior semantics, balance, or engine implementation.",
                "Every recorded field is required. Unexpected fields and unobserved model types fail.",
                "Null-only fields accept only null; arrays with no observed elements accept only empty arrays.",
                "Numerical ranges, integer intent, and gameplay strings are not inferred. All observed JSON numbers use number shapes; named nonfinite tokens retain explicit string alternatives.",
                "New captures or previously unseen variants require review and an explicit contract revision."
            ]
        }
    }
    (output / "model-contracts.json").write_text(json.dumps(catalog, indent=2) + "\n")
    return len(chunks)


def existing_map_types(catalog):
    """Resolve each include beside its containing document.

    >>> import tempfile
    >>> with tempfile.TemporaryDirectory() as temporary:
    ...     root = Path(temporary)
    ...     (root / "parts").mkdir()
    ...     _ = (root / "catalog.json").write_text('{"includes":["parts/index.json"]}')
    ...     _ = (root / "parts/index.json").write_text('{"includes":["values.json"]}')
    ...     _ = (root / "parts/values.json").write_text('{"contracts":[{"sourceType":"Map","fields":[],"additionalFields":{"type":"number"}}]}')
    ...     assert existing_map_types(root / "catalog.json") == {"Map"}
    """
    root = catalog.parent.resolve()
    visited = set()
    active = set()
    result = set()

    def visit(path):
        path = path.resolve()
        if not path.is_relative_to(root):
            raise ValueError("model-contract include escapes catalog directory")
        if path in active:
            raise ValueError("model-contract include cycle")
        if path in visited:
            return
        if len(active) >= 64:
            raise ValueError("model-contract include depth exceeds 64")
        active.add(path)
        document = json.loads(path.read_text())
        for contract in document.get("contracts", []):
            if not contract["fields"] and "additionalFields" in contract:
                result.add(contract["sourceType"])
        for include in document.get("includes", []):
            relative = Path(include)
            normalized = os.path.normpath(include)
            if not include or relative.is_absolute() or normalized == ".." or normalized.startswith("../"):
                raise ValueError("model-contract include must be a local relative path")
            visit(path.parent / relative)
        active.remove(path)
        visited.add(path)

    visit(catalog)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("audit", "generate"), nargs="?", default="audit")
    parser.add_argument("--game-data", required=True, type=Path)
    parser.add_argument("--profile", required=True, type=Path)
    parser.add_argument("--map-type", action="append", default=[], help="Exact source discriminator of a reviewed dynamic dictionary; repeat as needed")
    parser.add_argument("--map-types-from", type=Path, help="Reuse reviewed dynamic dictionary types from an existing contract catalog")
    parser.add_argument("--output", type=Path, help="Destination Profile directory (required for generate)")
    parser.add_argument("--capture-revision", help="Capture revision recorded in provenance (required for generate)")
    parser.add_argument("--chunk-bytes", type=int, default=95000)
    args = parser.parse_args()
    if args.command == "generate" and (args.output is None or not args.capture_revision):
        parser.error("generate requires --output and --capture-revision")
    map_types = set(args.map_type)
    if args.map_types_from:
        map_types.update(existing_map_types(args.map_types_from))
    contracts, counts = derive(args.game_data, args.profile, map_types)
    if args.command == "generate":
        counts["chunks"] = generate(contracts, args.output, args.capture_revision, args.chunk_bytes)
    print(json.dumps(counts, indent=2))


if __name__ == "__main__":
    main()
