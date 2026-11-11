# Concrete beam and masonry wall checks

This note gives the method behind the two checks in `service-dotnet/engine/`:
`rc_beam.py` for a reinforced concrete beam and `masonry_wall.py` for a masonry wall
strip. Each check writes a Markdown sheet listing every formula, input, factor and
result. The examples are in `docs/design-sheets/`.

## Status of the constants

I did not have a licensed copy of CSA A23.3 or CSA S304. The formulas are the standard
textbook forms, and every constant is printed in the sheet beside the result so an
engineer can compare it with the standard. Nothing here should be used for design until
that comparison is done.

## Concrete beam (`rc_beam.py`)

Scope: one singly reinforced rectangular section, normal-weight concrete, tension bars
only, and optional stirrups. Concrete strength 20 to 80 MPa, steel 300 to 500 MPa.

Flexure:

- Stress block: α1 = 0.85 − 0.0015 f'c (not below 0.67), β1 = 0.97 − 0.0025 f'c
  (not below 0.67).
- Depth of the stress block a = φs As fy / (φc α1 f'c b), with φc = 0.65 and φs = 0.85.
- Neutral axis c = a / β1. The check requires c/d ≤ 0.5, a limit used here for a
  ductile section.
- Moment resistance Mr = φs As fy (d − a/2). Must be at least Mf.
- Minimum strength: Mr ≥ the lesser of 1.2 Mcr and 1.33 Mf, where Mcr = 0.6 √f'c b h²/6.

Shear, simplified method for members with minimum transverse steel:

- Effective shear depth dv = max(0.9 d, 0.72 h).
- Concrete part Vc = φc β √f'c b dv, with β = 0.21.
- Steel part Vs = φs Av fy dv cot θ / s, with θ = 42°.
- Resistance Vr = min(Vc + Vs, Vmax), where Vmax = 0.25 φc f'c b dv.
- Minimum stirrups Av ≥ 0.06 √f'c b s / fy, and spacing s ≤ min(0.7 dv, 600 mm).
- Without stirrups the check passes only when Vf ≤ 0.5 Vc.

Not covered: continuous or multi-span beams, compression steel, T-beams, axial load,
torsion, deflection and cracking limits, and anchorage.

## Masonry wall strip (`masonry_wall.py`)

Scope: a solid rectangular strip, 1000 mm wide by default, pinned at top and bottom.
Hollow units, partial grouting and shear walls are not covered.

Axial with eccentricity:

- Radius of gyration r = t / √12, slenderness h/r.
- Slenderness reduction Rs = 1 − (h / (140 r))², with h/r ≤ 99 required.
- Eccentricity e = Mf / Pf. Requires e/t ≤ 1/3.
- Compression zone reduction Re = 1 − 2e/t. This is a simplification: it counts only the
  part of the wall section still in compression.
- Axial resistance Pr = φm f'm Ae Rs Re, with φm = 0.6 and Ae = b t.

Reinforced flexure (optional vertical bars):

- Stress block a = φs As fy / (φm α f'm b), with α = 0.8 assumed.
- Moment resistance Mr = φs As fy (d − a/2). Must be at least Mf.
- An out-of-plane moment with no reinforcement is flagged, because unreinforced flexural
  tension is not checked here.

Cases where the reduction formulas stop applying (h/r above 99, e/t above 1/3) are
reported as **not sized**, not as a failure.

## Out-of-range inputs

Each input has a range. A value outside the range, a missing required value, a non-number
or a true/false value is listed under **Not sized** and no result is produced. The
command returns exit code 3 for this case, so a script can tell it apart from a failing
design (exit 1) or an unreadable file (exit 2).

## Running

```sh
python3 service-dotnet/engine/design_check.py rc-beam service-dotnet/engine/examples/rc-beam-b1.json
python3 service-dotnet/engine/design_check.py masonry-wall service-dotnet/engine/examples/masonry-wall-w1.json --out wall.md
```

The tests in `test_rc_beam.py`, `test_masonry_wall.py` and `test_design_check.py` run in
the existing review-service workflow. `test_design_check.py` also fails if the committed
sheets in `docs/design-sheets/` no longer match the code.
