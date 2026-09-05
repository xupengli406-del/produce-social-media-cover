#!/usr/bin/env python3
"""Synthetic regression cases; no personal media or environment-specific paths."""

import copy
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest
import zlib

from validate_typography import validate_image, validate_manifest


def fixture():
    return {
        "canvas": [300, 400], "image_sha256": "0" * 64,
        "safe_rect": [10, 10, 280, 380],
        "keepouts": [{"id": "face", "rect": [100, 200, 100, 100]}],
        "blocks": [{"id": "title", "text": "你会把它当成家人吗？", "atomic": ["家人"],
                    "runs": [{"text": "你会把它当成", "flow": "top", "line": 0,
                              "rect": [20, 20, 200, 35]},
                             {"text": "家人吗？", "flow": "bottom", "line": 1,
                              "rect": [20, 70, 160, 45]}]}],
    }


def synthetic_png(width=300, height=400):
    def chunk(kind, payload):
        return struct.pack(">I", len(payload)) + kind + payload + struct.pack(">I", zlib.crc32(kind + payload))
    raw = (b"\x00" + b"\xff\xff\xff" * width) * height
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b""))


class TypographyTests(unittest.TestCase):
    def test_valid_semantic_line_break(self):
        self.assertEqual(validate_manifest(fixture()), [])

    def test_style_fragments_in_same_flow_are_allowed(self):
        data = fixture()
        runs = data["blocks"][0]["runs"]
        runs[1]["text"] = "家"
        runs[1]["rect"] = [20, 70, 40, 45]
        runs.append({"text": "人吗？", "flow": "bottom", "line": 1, "rect": [60, 70, 120, 45]})
        self.assertEqual(validate_manifest(data), [])

    def test_scattered_word_and_cross_line_word_fail(self):
        for different_flow in (True, False):
            with self.subTest(different_flow=different_flow):
                data = fixture()
                runs = data["blocks"][0]["runs"]
                runs[1]["text"] = "家"
                runs.append({"text": "人吗？", "flow": "separate" if different_flow else "bottom",
                             "line": 1 if different_flow else 2, "rect": [200, 130, 50, 40]})
                self.assertTrue(any("atomic phrase" in e for e in validate_manifest(data)))

    def test_exact_copy_rejects_omission_duplication_and_reordering(self):
        for text in ("家人吗", "家家人吗？", "人家吗？"):
            with self.subTest(text=text):
                data = fixture()
                data["blocks"][0]["runs"][1]["text"] = text
                self.assertTrue(any("exactly reproduce" in e for e in validate_manifest(data)))

    def test_intentional_single_character_is_allowed(self):
        data = fixture()
        block = data["blocks"][0]
        block.update(text="赞", atomic=["赞"], runs=[block["runs"][0]])
        block["runs"][0]["text"] = "赞"
        self.assertEqual(validate_manifest(data), [])

    def test_every_occurrence_of_atomic_phrase_is_checked(self):
        data = fixture()
        block = data["blocks"][0]
        block["text"] = "家人家人"
        block["runs"][0]["text"] = "家人家"
        block["runs"][1]["text"] = "人"
        self.assertTrue(any("at 2 split" in e for e in validate_manifest(data)))

    def test_number_unit_and_english_name_are_protected(self):
        for word, pieces in (("15分钟", ["15", "分钟"]), ("OpenAI", ["Open", "AI"])):
            with self.subTest(word=word):
                data = fixture()
                block = data["blocks"][0]
                block.update(text=word, atomic=[word])
                for run, piece in zip(block["runs"], pieces):
                    run["text"] = piece
                self.assertTrue(any("atomic phrase" in e for e in validate_manifest(data)))

    def test_safe_area_overflow(self):
        data = fixture()
        data["blocks"][0]["runs"][0]["rect"] = [0, 20, 200, 35]
        self.assertTrue(any("outside safe_rect" in e for e in validate_manifest(data)))

    def test_face_overlap(self):
        data = fixture()
        data["blocks"][0]["runs"][0]["rect"] = [90, 190, 30, 30]
        self.assertTrue(any("overlaps keepout face" in e for e in validate_manifest(data)))

    def test_malformed_inputs_fail_closed(self):
        samples = [None, {}, [], fixture(), fixture(), fixture(), fixture(), fixture(), fixture()]
        samples[3]["blocks"] = []
        samples[4]["blocks"][0]["runs"][0]["rect"][0] = float("nan")
        samples[5]["canvas"] = [True, 400]
        samples[6]["blocks"][0]["atomic"] = ["不存在"]
        samples[7]["blocks"][0]["runs"][0]["rect"][2] = -1
        samples[8]["blocks"].append(copy.deepcopy(samples[8]["blocks"][0]))
        for sample in samples:
            with self.subTest(sample=repr(sample)[:90]):
                self.assertTrue(validate_manifest(sample))

    def test_png_binding_and_cli(self):
        with tempfile.TemporaryDirectory(prefix="cover-typography-test-") as directory:
            root = Path(directory)
            image = root / "synthetic.png"
            manifest = root / "layout.json"
            image.write_bytes(synthetic_png())
            data = fixture()
            data["image_sha256"] = hashlib.sha256(image.read_bytes()).hexdigest()
            manifest.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
            validate_image(data, image)
            command = [sys.executable, str(Path(__file__).with_name("validate_typography.py")),
                       str(manifest), "--image", str(image)]
            result = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("no OCR", result.stdout)
            image.write_bytes(synthetic_png(301, 400))
            result = subprocess.run(command, capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("size does not match", result.stderr)
            image.write_bytes(synthetic_png() + b"changed")
            result = subprocess.run(command, capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("SHA256 mismatch", result.stderr)
            manifest.write_text("{broken", encoding="utf-8")
            self.assertNotEqual(subprocess.run(command, capture_output=True).returncode, 0)


if __name__ == "__main__":
    unittest.main()
