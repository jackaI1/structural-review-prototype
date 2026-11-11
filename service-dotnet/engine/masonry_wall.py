"""Masonry wall strip: axial capacity with eccentricity and reinforced flexure, CSA S304 style.

Scope: a solid rectangular wall strip (default 1000 mm wide), pinned top and bottom,
with an optional fully grouted reinforcement layer for the flexure check. Hollow units,
partial grouting and shear walls are not supported and are flagged. Units: mm, MPa, kN, kNm.
"""
import math

from hand_sheet import HandSheet, fmt

PHI_M = 0.6          # masonry resistance factor
PHI_S = 0.85         # reinforcement resistance factor
STRESS_BLOCK = 0.8   # masonry flexural stress block factor, assumed for this sheet
MAX_SLENDERNESS = 99
MAX_ECCENTRICITY_RATIO = 1 / 3

RANGES = {
    "t_mm": (90, 400, "wall thickness"),
    "h_mm": (500, 6000, "effective height, pinned ends"),
    "fm_mpa": (5, 25, "masonry compressive strength f'm"),
    "pf_kn": (0.001, 5000, "factored axial load per strip"),
}
OPTIONAL_RANGES = {
    "b_mm": (500, 4000, "strip width, default 1000"),
    "mf_knm": (0, 500, "factored out-of-plane moment"),
    "as_mm2": (0, 5000, "vertical reinforcement area per strip"),
    "d_mm": (30, 400, "effective depth to reinforcement"),
    "fy_mpa": (300, 500, "reinforcement yield strength"),
}


def _read(data):
    values, flags = {}, []
    for key, (low, high, label) in {**RANGES, **OPTIONAL_RANGES}.items():
        raw = data.get(key)
        if raw is None:
            if key in RANGES:
                flags.append(f"{label} ({key}) is missing.")
            continue
        if isinstance(raw, bool) or not isinstance(raw, (int, float)) or not math.isfinite(raw):
            flags.append(f"{label} ({key}) must be a finite number.")
            continue
        values[key] = float(raw)
        if not low <= raw <= high:
            flags.append(f"{label} ({key}) = {raw} is outside {low} to {high}.")
    if "as_mm2" in values and values["as_mm2"] > 0:
        for key in ("d_mm", "fy_mpa"):
            if key not in values:
                flags.append(f"{key} is needed for the reinforced flexure check.")
        if "d_mm" in values and "t_mm" in values and values["d_mm"] >= values["t_mm"]:
            flags.append("d_mm must be less than t_mm.")
    if values.get("as_mm2", 0) == 0 and values.get("mf_knm", 0) > 0:
        flags.append("Out-of-plane moment needs reinforcement (as_mm2 > 0); unreinforced "
                     "flexural tension is not checked here.")
    return values, flags


def _validity_flags(values):
    """Breaches of the limits where the reduction formulas stop applying."""
    flags = []
    r_g = values["t_mm"] / math.sqrt(12)
    if values["h_mm"] / r_g > MAX_SLENDERNESS:
        flags.append(f"Slenderness h/r = {values['h_mm'] / r_g:.1f} is above {MAX_SLENDERNESS}; "
                     "the slenderness reduction does not apply.")
    e_ratio = values.get("mf_knm", 0.0) / values["pf_kn"] * 1000 / values["t_mm"]
    if e_ratio > MAX_ECCENTRICITY_RATIO:
        flags.append(f"Eccentricity ratio e/t = {e_ratio:.2f} is above 1/3; "
                     "the eccentricity reduction does not apply.")
    return flags


def check(data):
    values, flags = _read(data)
    if not flags:
        flags = _validity_flags(values)
    sheet = HandSheet("Masonry wall strip check",
                      "CSA S304, slenderness and eccentricity reduction, simplified")
    sheet.inputs([
        ("t", "wall thickness", fmt(values.get("t_mm", 0), 0), "mm"),
        ("b", "strip width", fmt(values.get("b_mm", 1000), 0), "mm"),
        ("h", "effective height, pinned ends", fmt(values.get("h_mm", 0), 0), "mm"),
        ("f'm", "masonry compressive strength", fmt(values.get("fm_mpa", 0), 1), "MPa"),
        ("Pf", "factored axial load", fmt(values.get("pf_kn", 0), 1), "kN"),
        ("Mf", "factored out-of-plane moment", fmt(values.get("mf_knm", 0), 2), "kNm"),
        ("As", "vertical reinforcement per strip", fmt(values.get("as_mm2", 0), 0), "mm²"),
        ("d", "effective depth to reinforcement", fmt(values.get("d_mm", 0), 0), "mm"),
        ("fy", "reinforcement yield strength", fmt(values.get("fy_mpa", 400), 0), "MPa"),
    ])
    if flags:
        sheet.flagged(flags)
        return {"status": "flagged", "flags": flags, "checks": [], "sheet": sheet.markdown()}

    t, b, h = values["t_mm"], values.get("b_mm", 1000.0), values["h_mm"]
    fm, pf = values["fm_mpa"], values["pf_kn"]
    mf = values.get("mf_knm", 0.0)
    sheet.factors([
        ("φm", "masonry resistance factor", fmt(PHI_M), "fixed in this sheet"),
        ("φs", "reinforcement resistance factor", fmt(PHI_S), "fixed in this sheet"),
        ("α", "masonry stress block factor, flexure", fmt(STRESS_BLOCK), "assumed, check S304"),
        ("h/r limit", "maximum slenderness", str(MAX_SLENDERNESS), "fixed in this sheet"),
        ("e/t limit", "maximum eccentricity ratio", "1/3", "fixed in this sheet"),
    ])
    checks = []

    sheet.section("1. Geometry and slenderness")
    a_e = b * t
    r_g = t / math.sqrt(12)
    slenderness = h / r_g
    r_s = 1 - (h / (140 * r_g)) ** 2
    sheet.calc([
        ("Ae", "b t", f"{fmt(b, 0)} × {fmt(t, 0)}", fmt(a_e, 0), "mm²"),
        ("r", "t / √12", f"{fmt(t, 0)} / √12", fmt(r_g, 2), "mm"),
        ("h/r", "h / r", f"{fmt(h, 0)} / {fmt(r_g, 2)}", fmt(slenderness, 1), "-"),
        ("Rs", "1 − (h / (140 r))²", f"1 − ({fmt(h, 0)} / (140 × {fmt(r_g, 2)}))²", fmt(r_s, 4), "-"),
    ])

    sheet.section("2. Axial capacity with eccentricity")
    e_mm = mf / pf * 1000
    e_ratio = e_mm / t
    r_e = 1 - 2 * e_mm / t
    p_r = PHI_M * fm * a_e * r_s * r_e / 1000
    sheet.calc([
        ("e", "Mf / Pf", f"{fmt(mf, 2)} / {fmt(pf, 1)} × 1000", fmt(e_mm, 1), "mm"),
        ("e/t", "e / t", f"{fmt(e_mm, 1)} / {fmt(t, 0)}", fmt(e_ratio, 3), "-"),
        ("Re", "1 − 2e / t, compression zone of the wall",
         f"1 − 2 × {fmt(e_mm, 1)} / {fmt(t, 0)}", fmt(r_e, 4), "-"),
        ("Pr", "φm f'm Ae Rs Re",
         f"{fmt(PHI_M)} × {fmt(fm, 1)} × {fmt(a_e, 0)} × {fmt(r_s, 4)} × {fmt(r_e, 4)} / 1000",
         fmt(p_r, 1), "kN"),
    ])
    checks.append(("Axial resistance", sheet.check(
        "Pr ≥ Pf", pf, p_r, p_r >= pf, "kN")))

    sheet.section("3. Reinforced flexure")
    as_mm2 = values.get("as_mm2", 0.0)
    if as_mm2 > 0:
        d_mm, fy = values["d_mm"], values.get("fy_mpa", 400.0)
        a_depth = PHI_S * as_mm2 * fy / (PHI_M * STRESS_BLOCK * fm * b)
        m_r = PHI_S * as_mm2 * fy * (d_mm - a_depth / 2) / 1e6
        sheet.calc([
            ("a", "φs As fy / (φm α f'm b)",
             f"{fmt(PHI_S)} × {fmt(as_mm2, 0)} × {fmt(fy, 0)} / ({fmt(PHI_M)} × "
             f"{fmt(STRESS_BLOCK)} × {fmt(fm, 1)} × {fmt(b, 0)})", fmt(a_depth, 2), "mm"),
            ("Mr", "φs As fy (d − a/2) / 1e6",
             f"{fmt(PHI_S)} × {fmt(as_mm2, 0)} × {fmt(fy, 0)} × ({fmt(d_mm, 0)} − "
             f"{fmt(a_depth, 2)}/2) / 1e6", fmt(m_r, 2), "kNm"),
        ])
        checks.append(("Reinforced flexure", sheet.check(
            "Mr ≥ Mf", mf, m_r, m_r >= mf, "kNm")))
    else:
        sheet.note("No reinforcement given. The flexure check is not needed when Mf is zero.")
        checks.append(("Flexure not required", sheet.check(
            "Mf = 0", mf, 0, mf == 0, "kNm")))

    passed = all(result for _, result in checks)
    sheet.section("Result")
    sheet.note("**All checks pass.**" if passed else
               "**At least one check fails.** Thicken the wall, add reinforcement or reduce the load.")
    return {"status": "pass" if passed else "fail", "flags": [],
            "checks": [{"name": name, "passed": result} for name, result in checks],
            "sheet": sheet.markdown()}
