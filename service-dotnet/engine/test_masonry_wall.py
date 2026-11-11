"""Hand-worked numbers for the masonry wall check, plus limits and failure cases.

Example: t=190 mm, b=1000 mm, h=2800 mm, f'm=10 MPa, Pf=250 kN, Mf=5 kNm.
  r = 190 / sqrt(12) = 54.85 mm;  h/r = 51.0 (limit 99)
  Rs = 1 - (2800 / (140 * 54.85))^2 = 0.8670
  e = 5 / 250 * 1000 = 20 mm;  e/t = 0.105 (limit 1/3);  Re = 1 - 2*20/190 = 0.7895
  Pr = 0.6 * 10 * 190000 * 0.8670 * 0.7895 / 1000 = 780.3 kN
Reinforced flexure with As = 500 mm2/m, d = 140 mm, fy = 400 MPa:
  a = 0.85*500*400 / (0.6*0.8*10*1000) = 35.42 mm
  Mr = 0.85*500*400*(140 - 35.42/2) / 1e6 = 20.79 kNm
"""
import unittest

import masonry_wall

EXAMPLE = {"t_mm": 190, "b_mm": 1000, "h_mm": 2800, "fm_mpa": 10, "pf_kn": 250,
           "mf_knm": 5, "as_mm2": 500, "d_mm": 140, "fy_mpa": 400}


def passed_names(result):
    return {check["name"]: check["passed"] for check in result["checks"]}


class MasonryWorkedExampleTests(unittest.TestCase):
    def setUp(self):
        self.result = masonry_wall.check(EXAMPLE)

    def test_example_passes(self):
        self.assertEqual(self.result["status"], "pass")

    def test_axial_numbers_match_hand_calculation(self):
        sheet = self.result["sheet"]
        self.assertIn("| h/r | h / r | 2800 / 54.85 | 51.0 | - |", sheet)
        self.assertIn("| Rs | 1 − (h / (140 r))² |", sheet)
        self.assertIn("| 0.8670 | - |", sheet)
        self.assertIn("| e | Mf / Pf | 5.00 / 250.0 × 1000 | 20.0 | mm |", sheet)
        self.assertIn("| 780.3 | kN |", sheet)

    def test_reinforced_flexure_numbers_match_hand_calculation(self):
        sheet = self.result["sheet"]
        self.assertIn("| a | φs As fy / (φm α f'm b) |", sheet)
        self.assertIn("| 35.42 | mm |", sheet)
        self.assertIn("| 20.79 | kNm |", sheet)


class MasonryFailureTests(unittest.TestCase):
    def test_axial_load_above_capacity_fails(self):
        result = masonry_wall.check({**EXAMPLE, "pf_kn": 1100})
        self.assertEqual(result["status"], "fail")
        self.assertFalse(passed_names(result)["Axial resistance"])

    def test_moment_above_reinforced_capacity_fails(self):
        # As = 200 mm2/m: a = 14.17 mm, Mr = 0.85*200*400*(140 - 7.08)/1e6 = 9.04 kNm.
        # Mf = 15 kNm keeps e/t = 0.32 under 1/3, so the check is reached.
        result = masonry_wall.check({**EXAMPLE, "as_mm2": 200, "mf_knm": 15})
        self.assertEqual(result["status"], "fail")
        self.assertFalse(passed_names(result)["Reinforced flexure"])

    def test_zero_moment_needs_no_reinforcement(self):
        result = masonry_wall.check({"t_mm": 190, "h_mm": 2800, "fm_mpa": 10, "pf_kn": 250})
        self.assertEqual(result["status"], "pass")
        self.assertIn("Flexure not required", passed_names(result))


class MasonryOutOfRangeTests(unittest.TestCase):
    def assertFlagged(self, data, fragment):
        result = masonry_wall.check(data)
        self.assertEqual(result["status"], "flagged")
        self.assertEqual(result["checks"], [])
        self.assertTrue(any(fragment in flag for flag in result["flags"]), result["flags"])
        self.assertIn("Not sized", result["sheet"])

    def test_slender_wall_is_flagged_not_sized(self):
        # h/r = 6000 / (90/sqrt(12)) = 231, above 99
        self.assertFlagged({"t_mm": 90, "h_mm": 6000, "fm_mpa": 10, "pf_kn": 100},
                           "does not apply")

    def test_large_eccentricity_is_flagged_not_sized(self):
        # e = 100 kNm / 250 kN = 400 mm, e/t = 2.1, above 1/3
        self.assertFlagged({**EXAMPLE, "mf_knm": 100}, "e/t")

    def test_masonry_strength_out_of_range_is_flagged(self):
        self.assertFlagged({**EXAMPLE, "fm_mpa": 40}, "fm_mpa")

    def test_thickness_out_of_range_is_flagged(self):
        self.assertFlagged({**EXAMPLE, "t_mm": 600}, "t_mm")

    def test_missing_axial_load_is_flagged(self):
        data = {k: v for k, v in EXAMPLE.items() if k != "pf_kn"}
        self.assertFlagged(data, "pf_kn")

    def test_string_input_is_flagged(self):
        self.assertFlagged({**EXAMPLE, "h_mm": "2800"}, "must be a finite number")

    def test_reinforced_moment_without_steel_is_flagged(self):
        self.assertFlagged({**EXAMPLE, "as_mm2": 0}, "needs reinforcement")

    def test_reinforcement_depth_not_less_than_thickness_is_flagged(self):
        self.assertFlagged({**EXAMPLE, "d_mm": 200}, "less than t_mm")


if __name__ == "__main__":
    unittest.main()
