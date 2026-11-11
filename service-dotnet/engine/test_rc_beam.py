"""Hand-worked numbers for the concrete beam check, plus out-of-range and failure cases.

Expected values were worked by hand from the formulas in rc_beam.py (not copied from the
code's output). Example: b=300, h=500, d=450, As=1500 mm2, f'c=30 MPa, fy=400 MPa.
  alpha1 = 0.85 - 0.0015*30 = 0.805;  beta1 = 0.97 - 0.0025*30 = 0.895
  a = 0.85*1500*400 / (0.65*0.805*30*300) = 108.30 mm;  c = 108.30 / 0.895 = 121.0 mm
  Mr = 0.85*1500*400*(450 - 108.30/2) / 1e6 = 201.88 kNm
  Vc = 0.65*0.21*sqrt(30)*300*405 / 1000 = 90.84 kN   (dv = max(405, 360) = 405 mm)
  Vs = 0.85*200*400*405*cot(42 deg)/200 / 1000 = 152.93 kN   (cot 42 = 1.1106)
"""
import unittest

import rc_beam

EXAMPLE = {"b_mm": 300, "h_mm": 500, "d_mm": 450, "as_mm2": 1500, "fc_mpa": 30,
           "fy_mpa": 400, "mf_knm": 150, "vf_kn": 120, "av_mm2": 200, "s_mm": 200}


def passed_names(result):
    return {check["name"]: check["passed"] for check in result["checks"]}


class RcBeamWorkedExampleTests(unittest.TestCase):
    def setUp(self):
        self.result = rc_beam.check(EXAMPLE)

    def test_example_passes_all_checks(self):
        self.assertEqual(self.result["status"], "pass")
        self.assertTrue(all(check["passed"] for check in self.result["checks"]))

    def test_flexure_numbers_match_hand_calculation(self):
        sheet = self.result["sheet"]
        self.assertIn("| a | φs As fy / (φc α1 f'c b) |", sheet)
        self.assertIn("| 108.3 | mm |", sheet)
        self.assertIn("| 201.9 | kNm |", sheet)
        self.assertIn("| c/d | neutral axis depth ratio | 121.0 / 450 | 0.269 | - |", sheet)

    def test_shear_numbers_match_hand_calculation(self):
        sheet = self.result["sheet"]
        self.assertIn("| Vc | φc β λ √f'c b dv |", sheet)
        self.assertIn("| 90.8 | kN |", sheet)
        self.assertIn("| Vs | φs Av fy dv cot θ / s |", sheet)
        self.assertIn("| 152.9 | kN |", sheet)
        self.assertIn("| Vr | min(Vc + Vs, Vmax) |", sheet)
        self.assertIn("| 243.8 | kN |", sheet)

    def test_sheet_lists_every_check_and_disclaimer(self):
        sheet = self.result["sheet"]
        for label in ("Mr ≥ Mf", "c/d ≤ 0.5", "Mr ≥ Mmin", "Vr ≥ Vf", "Av ≥ Av,min", "s ≤ s,max"):
            self.assertIn(label, sheet)
        self.assertIn("not for design or construction", sheet.lower())


class RcBeamFailureTests(unittest.TestCase):
    def test_moment_above_capacity_fails(self):
        result = rc_beam.check({**EXAMPLE, "mf_knm": 300})
        self.assertEqual(result["status"], "fail")
        self.assertFalse(passed_names(result)["Factored moment resistance"])

    def test_heavy_steel_fails_neutral_axis_limit(self):
        # As = 4000 mm2 gives c/d = 0.717, above 0.5.
        result = rc_beam.check({**EXAMPLE, "as_mm2": 4000})
        self.assertEqual(result["status"], "fail")
        self.assertFalse(passed_names(result)["Neutral axis ratio c/d"])

    def test_no_stirrups_needed_when_shear_is_low(self):
        result = rc_beam.check({k: v for k, v in EXAMPLE.items()
                                if k not in ("av_mm2", "s_mm")} | {"vf_kn": 30})
        self.assertEqual(result["status"], "pass")

    def test_no_stirrups_fails_when_shear_needs_them(self):
        # Vc = 90.8 kN, so 0.5 Vc = 45.4 kN; 120 kN needs stirrups.
        result = rc_beam.check({k: v for k, v in EXAMPLE.items()
                                if k not in ("av_mm2", "s_mm")})
        self.assertEqual(result["status"], "fail")

    def test_stirrups_too_small_fail_minimum_area(self):
        # Av,min = 0.06 * sqrt(30) * 300 * 200 / 400 = 49.3 mm2
        result = rc_beam.check({**EXAMPLE, "av_mm2": 20})
        self.assertFalse(passed_names(result)["Minimum stirrup area"])

    def test_spacing_above_limit_fails(self):
        # s,max = min(0.7 * 405, 600) = 283.5 mm
        result = rc_beam.check({**EXAMPLE, "s_mm": 400})
        self.assertFalse(passed_names(result)["Maximum stirrup spacing"])


class RcBeamOutOfRangeTests(unittest.TestCase):
    def assertFlagged(self, data, fragment):
        result = rc_beam.check(data)
        self.assertEqual(result["status"], "flagged")
        self.assertEqual(result["checks"], [])
        self.assertTrue(any(fragment in flag for flag in result["flags"]), result["flags"])
        self.assertIn("Not sized", result["sheet"])
        self.assertNotIn("Mr ≥ Mf", result["sheet"])

    def test_concrete_strength_below_range_is_flagged(self):
        self.assertFlagged({**EXAMPLE, "fc_mpa": 15}, "fc_mpa")

    def test_concrete_strength_above_range_is_flagged(self):
        self.assertFlagged({**EXAMPLE, "fc_mpa": 95}, "fc_mpa")

    def test_steel_grade_outside_range_is_flagged(self):
        self.assertFlagged({**EXAMPLE, "fy_mpa": 600}, "fy_mpa")

    def test_depth_not_less_than_height_is_flagged(self):
        self.assertFlagged({**EXAMPLE, "d_mm": 500}, "less than overall depth")

    def test_boolean_is_not_a_number(self):
        self.assertFlagged({**EXAMPLE, "b_mm": True}, "must be a finite number")

    def test_nan_is_flagged(self):
        self.assertFlagged({**EXAMPLE, "mf_knm": float("nan")}, "mf_knm")

    def test_missing_required_input_is_flagged(self):
        data = {k: v for k, v in EXAMPLE.items() if k != "as_mm2"}
        self.assertFlagged(data, "as_mm2")

    def test_stirrup_area_without_spacing_is_flagged(self):
        data = {k: v for k, v in EXAMPLE.items() if k != "s_mm"}
        self.assertFlagged(data, "both av_mm2 and s_mm")

    def test_shallow_section_is_flagged(self):
        # d must be at least 0.6 h
        self.assertFlagged({**EXAMPLE, "d_mm": 250}, "at least 0.6 times h_mm")


if __name__ == "__main__":
    unittest.main()
