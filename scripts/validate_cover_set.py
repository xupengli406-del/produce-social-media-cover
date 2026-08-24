#!/usr/bin/env python3
"""Validate the standard PNG cover set without third-party dependencies."""

from __future__ import annotations

import argparse
import struct
from pathlib import Path


PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
EXPECTED = {
    "竖封面_3比4": (1242, 1660),
    "抖音封面_9比16": (1080, 1920),
    "横封面_4比3": (1600, 1200),
}


def png_size(path: Path) -> tuple[int, int]:
    with path.open("rb") as handle:
        if handle.read(8) != PNG_SIGNATURE:
            raise ValueError("not a PNG file")
        length = struct.unpack(">I", handle.read(4))[0]
        chunk_type = handle.read(4)
        if chunk_type != b"IHDR" or length < 8:
            raise ValueError("missing PNG IHDR")
        width, height = struct.unpack(">II", handle.read(8))
    return width, height


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a standard social cover set.")
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--topic", required=True)
    args = parser.parse_args()

    failures: list[str] = []
    for label, expected_size in EXPECTED.items():
        path = args.output_dir / f"{args.topic}_{label}.png"
        if not path.is_file():
            failures.append(f"missing: {path.name}")
            continue
        try:
            actual_size = png_size(path)
        except (OSError, ValueError, struct.error) as exc:
            failures.append(f"invalid: {path.name}: {exc}")
            continue
        if actual_size != expected_size:
            failures.append(
                f"wrong size: {path.name}: {actual_size[0]}x{actual_size[1]} "
                f"expected {expected_size[0]}x{expected_size[1]}"
            )

    if failures:
        for failure in failures:
            print(f"ERROR: {failure}")
        return 1

    print("OK: standard 3:4, 9:16, and 4:3 PNG cover set passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
