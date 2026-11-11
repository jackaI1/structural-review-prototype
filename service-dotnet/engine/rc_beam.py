"""Reinforced concrete rectangular beam: flexure and shear, simplified CSA A23.3 method.

Scope: one singly reinforced rectangular section, normal-weight concrete, tension bars
only, and stirrups as the only shear reinforcement. Inputs outside these limits are
flagged and not sized. Units: mm, MPa, kN, kNm.
"""
import math

from hand_sheet import HandSheet, fmt

PHI_C = 0.65          # concrete resistance factor
PHI_S = 0.85          # steel resistance factor
SHEAR_BETA = 0.21     # shear factor, simplified method with minimum transverse steel
SHEAR_THETA_DEG = 42.0
MAX_NEUTRAL_RATIO = 0.5   # c/d limit used here for a ductile section

# name: (lower, upper, label) for every number the check accepts
RANGES = {
    "b_mm": (150, 1000, "width"),
    "h_mm": (200, 1200, "overall depth"),
    "d_mm": (120, 1150, "effective depth"),
    "as_mm2": (1, 10000, "tension steel area"),
    "fc_mpa": (20, 80, "concrete strength f'c"),
    "fy_mpa": (300, 500, "steel yield strength"),
    "mf_knm": (0, 1000, "factored moment"),
}
OPTIONAL_RANGES = {
    "vf_kn": (0, 1000, "factored shear"),
    "av_mm2": (1, 2000, "stirrup area per spacing"),
    "s_mm": (50, 600, "stirrup spacing"),
}


def _read(data):
    """Return (values, flags). Any missing, non-numeric or out-of-range input is a flag."""
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
    if not flags:
        if not values["d_mm"] < values["h_mm"]:
            flags.append("Effective depth d_mm must be less than overall depth h_mm.")
        if not 0.6 * values["h_mm"] <= values["d_mm"]:
            flags.append("Effective depth d_mm must be at least 0.6 times h_mm.")
        if ("av_mm2" in values) != ("s_mm" in values):
            flags.append("Give both av_mm2 and s_mm for stirrups, or neither.")
    return values, flags


def check(data):
    """Check a beam. Returns status, checks (name, passed) and the Markdown sheet."""
    values, flags = _read(data)
    sheet = HandSheet("Reinforced concrete beam check",
                      "CSA A23.3, simplified rectangular stress block and shear method")
    sheet.inputs([
        ("b", "width of beam", fmt(values.get("b_mm", 0), 0), "mm"),
        ("h", "overall depth", fmt(values.get("h_mm", 0), 0), "mm"),
        ("d", "effective depth to tension steel", fmt(values.get("d_mm", 0), 0), "mm"),
        ("As", "tension steel area", fmt(values.get("as_mm2", 0), 0), "mm²"),
        ("f'c", "concrete strength", fmt(values.get("fc_mpa", 0), 1), "MPa"),
        ("fy", "steel yield strength", fmt(values.get("fy_mpa", 0), 0), "MPa"),
        ("Mf", "factored moment", fmt(values.get("mf_knm", 0), 1), "kNm"),
        ("Vf", "factored shear (optional)", fmt(values.get("vf_kn", 0), 1), "kN"),
        ("Av", "stirrup area per spacing (optional)", fmt(values.get("av_mm2", 0), 0), "mm²"),
        ("s", "stirrup spacing (optional)", fmt(values.get("s_mm", 0), 0), "mm"),
    ])
    if flags:
        sheet.flagged(flags)
        return {"status": "flagged", "flags": flags, "checks": [], "sheet": sheet.markdown()}

    b, h, d = values["b_mm"], values["h_mm"], values["d_mm"]
    a_s, fc, fy, mf = values["as_mm2"], values["fc_mpa"], values["fy_mpa"], values["mf_knm"]
    sheet.factors([
        ("φc", "concrete resistance factor", fmt(PHI_C), "fixed in this sheet"),
        ("φs", "steel resistance factor", fmt(PHI_S), "fixed in this sheet"),
        ("λ", "density factor, normal weight", "1.00", "fixed in this sheet"),
        ("β (shear)", "shear factor, simplified method", fmt(SHEAR_BETA), "fixed in this sheet"),
        ("θ", "diagonal crack angle, simplified method", fmt(SHEAR_THETA_DEG, 0) + "°",
         "fixed in this sheet"),
    ])
    checks = []

    # Flexure
    sheet.section("1. Stress block")
    alpha1 = max(0.85 - 0.0015 * fc, 0.67)
    beta1 = max(0.97 - 0.0025 * fc, 0.67)
    sheet.calc([
        ("α1", "0.85 − 0.0015 f'c, not less than 0.67", f"0.85 − 0.0015 × {fmt(fc, 1)}",
         fmt(alpha1, 3), "-"),
        ("β1", "0.97 − 0.0025 f'c, not less than 0.67", f"0.97 − 0.0025 × {fmt(fc, 1)}",
         fmt(beta1, 3), "-"),
    ])

    sheet.section("2. Flexure")
    a_depth = PHI_S * a_s * fy / (PHI_C * alpha1 * fc * b)
    neutral = a_depth / beta1
    neutral_ratio = neutral / d
    m_r = PHI_S * a_s * fy * (d - a_depth / 2) / 1e6
    sheet.calc([
        ("a", "φs As fy / (φc α1 f'c b)",
         f"{fmt(PHI_S)} × {fmt(a_s, 0)} × {fmt(fy, 0)} / ({fmt(PHI_C)} × {fmt(alpha1, 3)} × "
         f"{fmt(fc, 1)} × {fmt(b, 0)})", fmt(a_depth, 1), "mm"),
        ("c", "a / β1", f"{fmt(a_depth, 1)} / {fmt(beta1, 3)}", fmt(neutral, 1), "mm"),
        ("c/d", "neutral axis depth ratio", f"{fmt(neutral, 1)} / {fmt(d, 0)}",
         fmt(neutral_ratio, 3), "-"),
        ("Mr", "φs As fy (d − a/2)",
         f"{fmt(PHI_S)} × {fmt(a_s, 0)} × {fmt(fy, 0)} × ({fmt(d, 0)} − {fmt(a_depth, 1)}/2) / 1e6",
         fmt(m_r, 1), "kNm"),
    ])
    checks.append(("Factored moment resistance", sheet.check(
        "Mr ≥ Mf", mf, m_r, m_r >= mf, "kNm")))
    checks.append(("Neutral axis ratio c/d", sheet.check(
        "c/d ≤ 0.5", neutral_ratio, MAX_NEUTRAL_RATIO, neutral_ratio <= MAX_NEUTRAL_RATIO, "-")))

    sheet.section("3. Minimum flexural strength")
    f_r = 0.6 * math.sqrt(fc)
    s_mod = b * h ** 2 / 6
    m_cr = f_r * s_mod / 1e6
    m_req = min(1.2 * m_cr, 1.33 * mf)
    sheet.calc([
        ("fr", "0.6 λ √f'c", f"0.6 × {fmt(math.sqrt(fc), 3)}", fmt(f_r, 3), "MPa"),
        ("S", "b h² / 6, uncracked section", f"{fmt(b, 0)} × {fmt(h, 0)}² / 6",
         fmt(s_mod, 0), "mm³"),
        ("Mcr", "fr S / 1e6", f"{fmt(f_r, 3)} × {fmt(s_mod, 0)} / 1e6", fmt(m_cr, 2), "kNm"),
        ("Mmin", "lesser of 1.2 Mcr and 1.33 Mf",
         f"min(1.2 × {fmt(m_cr, 2)}, 1.33 × {fmt(mf, 1)})", fmt(m_req, 2), "kNm"),
    ])
    checks.append(("Minimum flexural strength", sheet.check(
        "Mr ≥ Mmin", m_req, m_r, m_r >= m_req, "kNm")))

    # Shear
    sheet.section("4. Shear")
    d_v = max(0.9 * d, 0.72 * h)
    cot_theta = 1 / math.tan(math.radians(SHEAR_THETA_DEG))
    v_c = PHI_C * SHEAR_BETA * math.sqrt(fc) * b * d_v / 1000
    v_max = 0.25 * PHI_C * fc * b * d_v / 1000
    sheet.calc([
        ("dv", "max(0.9 d, 0.72 h)", f"max(0.9 × {fmt(d, 0)}, 0.72 × {fmt(h, 0)})",
         fmt(d_v, 1), "mm"),
        ("Vc", "φc β λ √f'c b dv", f"{fmt(PHI_C)} × {fmt(SHEAR_BETA)} × {fmt(math.sqrt(fc), 3)} × "
         f"{fmt(b, 0)} × {fmt(d_v, 1)} / 1000", fmt(v_c, 1), "kN"),
        ("Vmax", "0.25 φc f'c b dv", f"0.25 × {fmt(PHI_C)} × {fmt(fc, 1)} × {fmt(b, 0)} × "
         f"{fmt(d_v, 1)} / 1000", fmt(v_max, 1), "kN"),
    ])
    vf = values.get("vf_kn", 0.0)
    if "av_mm2" in values:
        av, s = values["av_mm2"], values["s_mm"]
        v_s = PHI_S * av * fy * d_v * cot_theta / s / 1000
        v_r = min(v_c + v_s, v_max)
        av_min = 0.06 * math.sqrt(fc) * b * s / fy
        s_max = min(0.7 * d_v, 600)
        sheet.calc([
            ("cot θ", "1 / tan θ", f"1 / tan {fmt(SHEAR_THETA_DEG, 0)}°", fmt(cot_theta, 3), "-"),
            ("Vs", "φs Av fy dv cot θ / s",
             f"{fmt(PHI_S)} × {fmt(av, 0)} × {fmt(fy, 0)} × {fmt(d_v, 1)} × {fmt(cot_theta, 3)} / "
             f"{fmt(s, 0)} / 1000", fmt(v_s, 1), "kN"),
            ("Vr", "min(Vc + Vs, Vmax)", f"min({fmt(v_c, 1)} + {fmt(v_s, 1)}, {fmt(v_max, 1)})",
             fmt(v_r, 1), "kN"),
            ("Av,min", "0.06 √f'c b s / fy", f"0.06 × {fmt(math.sqrt(fc), 3)} × {fmt(b, 0)} × "
             f"{fmt(s, 0)} / {fmt(fy, 0)}", fmt(av_min, 1), "mm²"),
            ("s,max", "lesser of 0.7 dv and 600 mm", f"min(0.7 × {fmt(d_v, 1)}, 600)",
             fmt(s_max, 1), "mm"),
        ])
        checks.append(("Shear resistance with stirrups", sheet.check(
            "Vr ≥ Vf", vf, v_r, v_r >= vf, "kN")))
        checks.append(("Minimum stirrup area", sheet.check(
            "Av ≥ Av,min", av_min, av, av >= av_min, "mm²")))
        checks.append(("Maximum stirrup spacing", sheet.check(
            "s ≤ s,max", s, s_max, s <= s_max, "mm")))
    else:
        transverse_needed = vf > 0.5 * v_c
        sheet.note("No stirrups given. This sheet accepts an unstirruped beam only when "
                   "Vf ≤ 0.5 Vc.")
        checks.append(("Shear without stirrups", sheet.check(
            "Vf ≤ 0.5 Vc", vf, 0.5 * v_c, not transverse_needed, "kN")))

    passed = all(result for _, result in checks)
    sheet.section("Result")
    sheet.note("**All checks pass.**" if passed else
               "**At least one check fails.** Increase steel, depth or stirrups and run again.")
    return {"status": "pass" if passed else "fail", "flags": [],
            "checks": [{"name": name, "passed": result} for name, result in checks],
            "sheet": sheet.markdown()}
