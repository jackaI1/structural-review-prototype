# Masonry wall strip check

Code basis: CSA S304, slenderness and eccentricity reduction, simplified

> Portfolio and learning tool. Not for design or construction. A licensed engineer must check every formula and constant against the current standard.

## Inputs

| Symbol | Meaning | Value | Unit |
|---|---|---|---|
| t | wall thickness | 190 | mm |
| b | strip width | 1000 | mm |
| h | effective height, pinned ends | 2800 | mm |
| f'm | masonry compressive strength | 10.0 | MPa |
| Pf | factored axial load | 250.0 | kN |
| Mf | factored out-of-plane moment | 5.00 | kNm |
| As | vertical reinforcement per strip | 500 | mm² |
| d | effective depth to reinforcement | 140 | mm |
| fy | reinforcement yield strength | 400 | MPa |

## Resistance factors and constants

| Symbol | Meaning | Value | Source in this sheet |
|---|---|---|---|
| φm | masonry resistance factor | 0.60 | fixed in this sheet |
| φs | reinforcement resistance factor | 0.85 | fixed in this sheet |
| α | masonry stress block factor, flexure | 0.80 | assumed, check S304 |
| h/r limit | maximum slenderness | 99 | fixed in this sheet |
| e/t limit | maximum eccentricity ratio | 1/3 | fixed in this sheet |

## 1. Geometry and slenderness

| Symbol | Formula | Numbers | Result | Unit |
|---|---|---|---|---|
| Ae | b t | 1000 × 190 | 190000 | mm² |
| r | t / √12 | 190 / √12 | 54.85 | mm |
| h/r | h / r | 2800 / 54.85 | 51.0 | - |
| Rs | 1 − (h / (140 r))² | 1 − (2800 / (140 × 54.85))² | 0.8670 | - |

## 2. Axial capacity with eccentricity

| Symbol | Formula | Numbers | Result | Unit |
|---|---|---|---|---|
| e | Mf / Pf | 5.00 / 250.0 × 1000 | 20.0 | mm |
| e/t | e / t | 20.0 / 190 | 0.105 | - |
| Re | 1 − 2e / t, compression zone of the wall | 1 − 2 × 20.0 / 190 | 0.7895 | - |
| Pr | φm f'm Ae Rs Re | 0.60 × 10.0 × 190000 × 0.8670 × 0.7895 / 1000 | 780.3 | kN |

| Check | Demand | Capacity | Result |
|---|---|---|---|
| Pr ≥ Pf | 250.00 kN | 780.33 kN | PASS |

## 3. Reinforced flexure

| Symbol | Formula | Numbers | Result | Unit |
|---|---|---|---|---|
| a | φs As fy / (φm α f'm b) | 0.85 × 500 × 400 / (0.60 × 0.80 × 10.0 × 1000) | 35.42 | mm |
| Mr | φs As fy (d − a/2) / 1e6 | 0.85 × 500 × 400 × (140 − 35.42/2) / 1e6 | 20.79 | kNm |

| Check | Demand | Capacity | Result |
|---|---|---|---|
| Mr ≥ Mf | 5.00 kNm | 20.79 kNm | PASS |

## Result

**All checks pass.**
