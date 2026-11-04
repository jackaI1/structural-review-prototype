"""Synthetic inputs only; literal expectations independently calculated."""
import io
import unittest

from pypdf import PdfWriter
from pypdf.generic import DictionaryObject, NameObject, DecodedStreamObject
from review import review


def pdf(text="", encrypted=False):
    writer = PdfWriter()
    page = writer.add_blank_page(width=612, height=792)
    font = DictionaryObject({NameObject("/Type"): NameObject("/Font"),
                             NameObject("/Subtype"): NameObject("/Type1"),
                             NameObject("/BaseFont"): NameObject("/Helvetica")})
    page[NameObject("/Resources")] = DictionaryObject({
        NameObject("/Font"): DictionaryObject({NameObject("/F1"): font})})
    stream = DecodedStreamObject()
    stream.set_data(("BT /F1 10 Tf 40 700 Td (" + text + ") Tj ET").encode("ascii"))
    page[NameObject("/Contents")] = stream
    if encrypted:
        writer.encrypt("test-only")
    output = io.BytesIO()
    writer.write(output)
    return output.getvalue()


class ReviewTests(unittest.TestCase):
    def test_extracts_schedule_and_illustrative_demands(self):
        result = review(pdf("BEAM B1 SPAN_M=4 TRIBUTARY_M=3 LOAD_KPA=2.5"))
        self.assertEqual(result["pageCount"], 1)
        member = result["members"][0]
        self.assertEqual(member["id"], "B1")
        self.assertEqual(member["lineLoadKnPerM"], 7.5)
        self.assertEqual(member["momentKnM"], 15)
        self.assertEqual(member["reactionKn"], 15)
        self.assertTrue(result["requiresEngineerApproval"])
        self.assertEqual(result["mode"], "synthetic-demo")
        self.assertEqual(len(result["sha256"]), 64)

    def test_unannotated_drawing_needs_input_and_has_no_fabricated_members(self):
        result = review(pdf("Fictional plan without a schedule"))
        self.assertEqual(result["members"], [])
        self.assertTrue(result["warnings"])
        self.assertTrue(result["requiresEngineerApproval"])

    def test_rejects_malformed_and_encrypted_pdf(self):
        for data in (b"%PDF-not-a-document", pdf(encrypted=True)):
            with self.subTest(data=data[:10]), self.assertRaises(ValueError):
                review(data)

    def test_rejects_invalid_member_values_and_duplicate_ids(self):
        for text in (
            "BEAM B1 SPAN_M=0 TRIBUTARY_M=3 LOAD_KPA=2.5",
            "BEAM B1 SPAN_M=-4 TRIBUTARY_M=3 LOAD_KPA=2.5",
            "BEAM B1 SPAN_M=nan TRIBUTARY_M=3 LOAD_KPA=2.5",
            "BEAM B1 SPAN_M=101 TRIBUTARY_M=3 LOAD_KPA=2.5",
            "BEAM B1 SPAN_M=4 TRIBUTARY_M=3 LOAD_KPA=2.5 BEAM B1 SPAN_M=5 TRIBUTARY_M=2 LOAD_KPA=3",
        ):
            with self.subTest(text=text), self.assertRaises(ValueError):
                review(pdf(text))

    def test_rejects_too_many_pages(self):
        writer = PdfWriter()
        for _ in range(51):
            writer.add_blank_page(width=612, height=792)
        output = io.BytesIO()
        writer.write(output)
        with self.assertRaises(ValueError):
            review(output.getvalue())


if __name__ == "__main__":
    unittest.main()
