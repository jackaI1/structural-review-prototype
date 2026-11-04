"""Create a fictional one-page framing plan; no third-party drawing data."""
from pathlib import Path
from pypdf import PdfWriter
from pypdf.generic import DictionaryObject, NameObject, DecodedStreamObject


def make_sample(destination):
    writer = PdfWriter()
    page = writer.add_blank_page(width=612, height=792)
    page[NameObject("/Resources")] = DictionaryObject({
        NameObject("/Font"): DictionaryObject({NameObject("/F1"): DictionaryObject({
            NameObject("/Type"): NameObject("/Font"),
            NameObject("/Subtype"): NameObject("/Type1"),
            NameObject("/BaseFont"): NameObject("/Helvetica"),
        })})})
    commands = ["0.12 0.22 0.30 rg", "BT /F1 20 Tf 48 730 Td (FICTIONAL FRAMING PLAN) Tj ET",
                "BT /F1 11 Tf 48 705 Td (Synthetic workflow fixture - not for construction) Tj ET",
                "0.12 0.22 0.30 RG 2 w 90 420 400 220 re S",
                "0.1 0.5 0.5 RG 5 w 90 530 m 490 530 l S",
                "BT /F1 12 Tf 260 545 Td (B1 - 4 m) Tj ET"]
    for x in range(110, 490, 40):
        commands.append(f"0.6 0.65 0.7 RG 0.8 w {x} 420 m {x} 640 l S")
    for y, text in [(370, "SYNTHETIC MEMBER SCHEDULE"),
                    (345, "BEAM B1 SPAN_M=4 TRIBUTARY_M=3 LOAD_KPA=2.5"),
                    (300, "Simply supported beam; uniform illustrative gravity load."),
                    (280, "Expected: w = 7.5 kN/m; M = 15 kN m; R = 15 kN."),
                    (240, "All interpretation and results require engineer approval."),
                    (220, "No section selection, load combinations or code checks."),
                    (100, "Generated from source in engine/make_sample.py. No real project data.")]:
        commands.append(f"BT /F1 10 Tf 48 {y} Td ({text}) Tj ET")
    stream = DecodedStreamObject()
    stream.set_data("\n".join(commands).encode("ascii"))
    page[NameObject("/Contents")] = stream
    writer.add_metadata({"/Title": "Synthetic framing workflow fixture", "/Author": "Public demo generator"})
    with open(destination, "wb") as output:
        writer.write(output)


if __name__ == "__main__":
    make_sample(Path(__file__).resolve().parent.parent / "samples/synthetic-framing.pdf")
