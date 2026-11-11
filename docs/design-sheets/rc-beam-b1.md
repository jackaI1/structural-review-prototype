# Reinforced concrete beam check

Code basis: CSA A23.3, simplified rectangular stress block and shear method

> Portfolio and learning tool. Not for design or construction. A licensed engineer must check every formula and constant against the current standard.

## Inputs

| Symbol | Meaning | Value | Unit |
|---|---|---|---|
| b | width of beam | 300 | mm |
| h | overall depth | 500 | mm |
| d | effective depth to tension steel | 450 | mm |
| As | tension steel area | 1500 | mm² |
| f'c | concrete strength | 30.0 | MPa |
| fy | steel yield strength | 400 | MPa |
| Mf | factored moment | 150.0 | kNm |
| Vf | factored shear (optional) | 120.0 | kN |
| Av | stirrup area per spacing (optional) | 200 | mm² |
| s | stirrup spacing (optional) | 200 | mm |

## Resistance factors and constants

| Symbol | Meaning | Value | Source in this sheet |
|---|---|---|---|
| φc | concrete resistance factor | 0.65 | fixed in this sheet |
| φs | steel resistance factor | 0.85 | fixed in this sheet |
| λ | density factor, normal weight | 1.00 | fixed in this sheet |
| β (shear) | shear factor, simplified method | 0.21 | fixed in this sheet |
| θ | diagonal crack angle, simplified method | 42° | fixed in this sheet |

## 1. Stress block

| Symbol | Formula | Numbers | Result | Unit |
|---|---|---|---|---|
| α1 | 0.85 − 0.0015 f'c, not less than 0.67 | 0.85 − 0.0015 × 30.0 | 0.805 | - |
| β1 | 0.97 − 0.0025 f'c, not less than 0.67 | 0.97 − 0.0025 × 30.0 | 0.895 | - |

## 2. Flexure

| Symbol | Formula | Numbers | Result | Unit |
|---|---|---|---|---|
| a | φs As fy / (φc α1 f'c b) | 0.85 × 1500 × 400 / (0.65 × 0.805 × 30.0 × 300) | 108.3 | mm |
| c | a / β1 | 108.3 / 0.895 | 121.0 | mm |
| c/d | neutral axis depth ratio | 121.0 / 450 | 0.269 | - |
| Mr | φs As fy (d − a/2) | 0.85 × 1500 × 400 × (450 − 108.3/2) / 1e6 | 201.9 | kNm |

| Check | Demand | Capacity | Result |
|---|---|---|---|
| Mr ≥ Mf | 150.00 kNm | 201.88 kNm | PASS |

| Check | Demand | Capacity | Result |
|---|---|---|---|
| c/d ≤ 0.5 | 0.27 | 0.50 | PASS |

## 3. Minimum flexural strength

| Symbol | Formula | Numbers | Result | Unit |
|---|---|---|---|---|
| fr | 0.6 λ √f'c | 0.6 × 5.477 | 3.286 | MPa |
| S | b h² / 6, uncracked section | 300 × 500² / 6 | 12500000 | mm³ |
| Mcr | fr S / 1e6 | 3.286 × 12500000 / 1e6 | 41.08 | kNm |
| Mmin | lesser of 1.2 Mcr and 1.33 Mf | min(1.2 × 41.08, 1.33 × 150.0) | 49.30 | kNm |

| Check | Demand | Capacity | Result |
|---|---|---|---|
| Mr ≥ Mmin | 49.30 kNm | 201.88 kNm | PASS |

## 4. Shear

| Symbol | Formula | Numbers | Result | Unit |
|---|---|---|---|---|
| dv | max(0.9 d, 0.72 h) | max(0.9 × 450, 0.72 × 500) | 405.0 | mm |
| Vc | φc β λ √f'c b dv | 0.65 × 0.21 × 5.477 × 300 × 405.0 / 1000 | 90.8 | kN |
| Vmax | 0.25 φc f'c b dv | 0.25 × 0.65 × 30.0 × 300 × 405.0 / 1000 | 592.3 | kN |

| Symbol | Formula | Numbers | Result | Unit |
|---|---|---|---|---|
| cot θ | 1 / tan θ | 1 / tan 42° | 1.111 | - |
| Vs | φs Av fy dv cot θ / s | 0.85 × 200 × 400 × 405.0 × 1.111 / 200 / 1000 | 152.9 | kN |
| Vr | min(Vc + Vs, Vmax) | min(90.8 + 152.9, 592.3) | 243.8 | kN |
| Av,min | 0.06 √f'c b s / fy | 0.06 × 5.477 × 300 × 200 / 400 | 49.3 | mm² |
| s,max | lesser of 0.7 dv and 600 mm | min(0.7 × 405.0, 600) | 283.5 | mm |

| Check | Demand | Capacity | Result |
|---|---|---|---|
| Vr ≥ Vf | 120.00 kN | 243.77 kN | PASS |

| Check | Demand | Capacity | Result |
|---|---|---|---|
| Av ≥ Av,min | 49.30 mm² | 200.00 mm² | PASS |

| Check | Demand | Capacity | Result |
|---|---|---|---|
| s ≤ s,max | 200.00 mm | 283.50 mm | PASS |

## Result

**All checks pass.**
