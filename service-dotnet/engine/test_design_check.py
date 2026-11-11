"""Command line behaviour and the committed example sheets, which must match the code."""
import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

import design_check

ENGINE = Path(__file__).resolve().parent
EXAMPLES = ENGINE / "examples"
DOCS = ENGINE.parents[1] / "docs" / "design-sheets"


def run_cli(*args):
    stdout, stderr = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
        code = design_check.main(list(args))
    return code, stdout.getvalue(), stderr.getvalue()


class CommandLineTests(unittest.TestCase):
    def setUp(self):
        self._dir = tempfile.TemporaryDirectory()
        self.tmp = Path(self._dir.name)

    def tearDown(self):
        self._dir.cleanup()

    def write_json(self, data):
        path = self.tmp / "input.json"
        path.write_text(json.dumps(data), encoding="utf-8")
        return str(path)

    def test_passing_beam_writes_sheet_and_exits_zero(self):
        out = self.tmp / "beam.md"
        code, _, err = run_cli("rc-beam", str(EXAMPLES / "rc-beam-b1.json"), "--out", str(out))
        self.assertEqual(code, 0)
        self.assertIn("pass", err)
        self.assertIn("Reinforced concrete beam check", out.read_text(encoding="utf-8"))

    def test_passing_wall_writes_sheet_and_exits_zero(self):
        out = self.tmp / "wall.md"
        code, _, _ = run_cli("masonry-wall", str(EXAMPLES / "masonry-wall-w1.json"), "--out", str(out))
        self.assertEqual(code, 0)
        self.assertIn("Masonry wall strip check", out.read_text(encoding="utf-8"))

    def test_failing_input_exits_one(self):
        path = self.write_json({"t_mm": 190, "h_mm": 2800, "fm_mpa": 10, "pf_kn": 2000})
        code, out, _ = run_cli("masonry-wall", path)
        self.assertEqual(code, 1)
        self.assertIn("Pr ≥ Pf", out)

    def test_out_of_range_input_exits_three_and_reports_no_result(self):
        path = self.write_json({"b_mm": 300, "h_mm": 500, "d_mm": 450, "as_mm2": 1500,
                                "fc_mpa": 15, "fy_mpa": 400, "mf_knm": 100})
        code, out, err = run_cli("rc-beam", path)
        self.assertEqual(code, 3)
        self.assertIn("Not sized", out)
        self.assertIn("1 input(s) outside the supported range", err)

    def test_unreadable_file_exits_two_without_echoing_content(self):
        path = self.tmp / "bad.json"
        path.write_text("SECRET-TEXT not json", encoding="utf-8")
        code, out, err = run_cli("rc-beam", str(path))
        self.assertEqual(code, 2)
        self.assertNotIn("SECRET", out + err)

    def test_json_that_is_not_an_object_exits_two(self):
        path = self.write_json([1, 2, 3])
        code, _, _ = run_cli("masonry-wall", path)
        self.assertEqual(code, 2)


class CommittedSheetTests(unittest.TestCase):
    """The sheets in docs/ are generated from examples/. Regenerate them if this fails."""

    def assertSheetCurrent(self, check, example, sheet_name):
        data = json.loads((EXAMPLES / example).read_text(encoding="utf-8"))
        generated = design_check.CHECKS[check](data)["sheet"]
        committed = (DOCS / sheet_name).read_text(encoding="utf-8")
        self.assertEqual(committed, generated,
                         f"Regenerate with: python3 design_check.py {check} "
                         f"examples/{example} --out ../../docs/design-sheets/{sheet_name}")

    def test_beam_sheet_is_current(self):
        self.assertSheetCurrent("rc-beam", "rc-beam-b1.json", "rc-beam-b1.md")

    def test_wall_sheet_is_current(self):
        self.assertSheetCurrent("masonry-wall", "masonry-wall-w1.json", "masonry-wall-w1.md")


if __name__ == "__main__":
    unittest.main()
