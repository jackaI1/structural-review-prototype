# Structural Review Prototype

From permit drawings to a checked load path. This prototype cut a **four-hour** structural review to **ten minutes**, with an engineer verifying every step.

https://github.com/user-attachments/assets/2c35d8c2-6d67-4bd0-a4c0-d416f84e945b

*The demo uses a fictional house and synthetic data. No real drawings appear.*

## What it does

Residential gravity design starts from a set of architectural drawings. Usually an engineer traces by hand how every roof and floor load travels down to the foundation, then sizes each member along the way. The prototype automates that workflow:

1. **Finds every member.** It extracts the framing linework from the drawing PDFs: trusses, girder trusses, beams, lintels, posts and walls.
2. **Classifies every depiction.** Different drafters draw the same member in different ways. The program interprets them from the geometry, without relying on labels.
3. **Builds the house.** Each floor's framing plan is stacked into one 3D structural model.
4. **Traces the loads.** Roof and floor loads flow member by member down to the foundation, and the totals are checked to balance.
5. **Tests every member.** Each post and beam is checked against its demand, and failing members are flagged.
6. **Proposes the fix.** The program suggests a member that passes, and the engineer accepts it in one click.

Before any calculation, the engineer reviews and approves the program's interpretation of the drawings. The engineer stays in charge of every result.

## Results

- **Four hours to ten minutes** for a residential gravity review.
- Combines PDF extraction, member interpretation and sizing, with engineer-in-the-loop verification.

## Why there's no code

I built this prototype during my engineering co-op. The source code, the internal design methods and the project drawings it was developed on are confidential and belong to the firm, so this repository only shows the project. The video recreates the workflow on a fictional house with simplified, illustrative values. It is not engineering output.

## More

- Other projects with public code are on my [GitHub profile](https://github.com/jackaI1).
- I'm happy to walk through the architecture and design decisions in an interview.
