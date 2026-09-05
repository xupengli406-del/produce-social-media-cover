#!/usr/bin/env python3
"""Check measured cover-layout data, not aesthetic quality or image OCR."""

import argparse
import hashlib
import json
import math
from pathlib import Path
import struct
import sys


def require(condition, message):
    if not condition:
        raise ValueError(message)


def string(value, label):
    require(isinstance(value, str) and bool(value.strip()), f"{label}: expected nonempty text")
    return value


def rectangle(value, label):
    require(isinstance(value, list) and len(value) == 4, f"{label}: expected [x,y,w,h]")
    require(all(type(v) in (int, float) and math.isfinite(v) for v in value),
            f"{label}: coordinates must be finite numbers")
    require(value[2] > 0 and value[3] > 0, f"{label}: width/height must be positive")
    return value


def contains(outer, inner):
    x, y, w, h = outer
    a, b, c, d = inner
    return x <= a and y <= b and a + c <= x + w and b + d <= y + h


def overlaps(first, second):
    x, y, w, h = first
    a, b, c, d = second
    return x < a + c and a < x + w and y < b + d and b < y + h


def validate_manifest(data):
    """Return errors; coordinates and flow declarations must come from the renderer."""
    errors = []
    try:
        require(isinstance(data, dict), "manifest: expected object")
        canvas = data.get("canvas")
        require(isinstance(canvas, list) and len(canvas) == 2
                and all(type(v) is int and v > 0 for v in canvas),
                "canvas: expected two positive integers")
        safe = rectangle(data.get("safe_rect"), "safe_rect")
        require(contains([0, 0, *canvas], safe), "safe_rect: outside canvas")
        digest = data.get("image_sha256")
        require(isinstance(digest, str) and len(digest) == 64
                and all(c in "0123456789abcdef" for c in digest),
                "image_sha256: expected lowercase SHA256 of final PNG")
        keepouts = data.get("keepouts")
        require(isinstance(keepouts, list), "keepouts: expected array (empty is allowed)")
        seen = set()
        for zone in keepouts:
            require(isinstance(zone, dict), "keepout: expected object")
            key = string(zone.get("id"), "keepout.id")
            require(key not in seen, f"keepout: duplicate id {key}")
            seen.add(key)
            rect = rectangle(zone.get("rect"), f"keepout {key}")
            require(contains([0, 0, *canvas], rect), f"keepout {key}: outside canvas")
        blocks = data.get("blocks")
        require(isinstance(blocks, list) and bool(blocks), "blocks: expected nonempty array")
        seen = set()
        for block in blocks:
            require(isinstance(block, dict), "block: expected object")
            key = string(block.get("id"), "block.id")
            require(key not in seen, f"block: duplicate id {key}")
            seen.add(key)
            original = string(block.get("text"), f"{key}.text")
            require("\n" not in original and "\r" not in original,
                    f"{key}: keep layout line breaks in runs, not source text")
            atomic = block.get("atomic")
            require(isinstance(atomic, list), f"{key}.atomic: expected array")
            for word in atomic:
                string(word, f"{key}.atomic entry")
                require(word in original, f"{key}: atomic phrase {word!r} absent from source")
            runs = block.get("runs")
            require(isinstance(runs, list) and bool(runs), f"{key}.runs: expected nonempty array")
            ranges = []
            offset = 0
            for index, run in enumerate(runs):
                label = f"{key}.runs[{index}]"
                require(isinstance(run, dict), f"{label}: expected object")
                content = string(run.get("text"), f"{label}.text")
                flow = string(run.get("flow"), f"{label}.flow")
                line = run.get("line")
                require(type(line) is int and line >= 0, f"{label}.line: expected nonnegative integer")
                rect = rectangle(run.get("rect"), label)
                if not contains(safe, rect):
                    errors.append(f"{label}: text outside safe_rect")
                for zone in keepouts:
                    if overlaps(rect, zone["rect"]):
                        errors.append(f"{label}: text overlaps keepout {zone['id']}")
                ranges.append((offset, offset + len(content), (flow, line)))
                offset += len(content)
            if "".join(run["text"] for run in runs) != original:
                errors.append(f"{key}: runs do not exactly reproduce source text (order/omission/duplication)")
                continue
            for word in atomic:
                start = original.find(word)
                while start >= 0:
                    end = start + len(word)
                    flows = {flow for a, b, flow in ranges if a < end and start < b}
                    if len(flows) != 1:
                        errors.append(f"{key}: atomic phrase {word!r} at {start} split across lines/flows")
                    start = original.find(word, start + 1)
    except ValueError as exc:
        errors.append(str(exc))
    return errors


def validate_image(data, image_path):
    """Bind the manifest to its PNG; full image decoding remains a separate gate."""
    payload = image_path.read_bytes()
    require(len(payload) >= 24 and payload[:8] == b"\x89PNG\r\n\x1a\n"
            and payload[8:16] == b"\x00\x00\x00\rIHDR", "image: expected PNG with IHDR")
    size = list(struct.unpack(">II", payload[16:24]))
    require(size == data["canvas"], "image: PNG size does not match canvas")
    require(hashlib.sha256(payload).hexdigest() == data["image_sha256"],
            "image: SHA256 mismatch; stale manifest or changed image")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--image", required=True, type=Path)
    args = parser.parse_args()
    try:
        data = json.loads(args.manifest.read_text(encoding="utf-8"))
        errors = validate_manifest(data)
        if not errors:
            validate_image(data, args.image)
    except (ValueError, OSError, OverflowError) as exc:
        errors = [str(exc)]
    if errors:
        for error in errors:
            print(f"FAIL: {error}", file=sys.stderr)
        return 1
    print("PASS: declared text, atomic phrases, measured bounds and PNG binding.")
    print("Still required: actual image/thumbnail review; no OCR, semantic or aesthetic guarantee.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
