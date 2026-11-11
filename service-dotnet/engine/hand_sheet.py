"""Markdown hand-calculation sheets. Each check writes every formula, input, factor and result.

A reader can follow the sheet with a calculator: each row shows the formula, the numbers
put into it and the result. The sheet is text only and never includes uploaded content.
"""

DISCLAIMER = ("Portfolio and learning tool. Not for design or construction. A licensed "
              "engineer must check every formula and constant against the current standard.")


def fmt(value, digits=2):
    return f"{value:.{digits}f}"


class HandSheet:
    def __init__(self, title, code_basis):
        self.lines = [f"# {title}", "", f"Code basis: {code_basis}", "", f"> {DISCLAIMER}", ""]
        self._rows = []
        self._headers = None

    def _flush(self):
        if self._rows:
            self.lines.append("| " + " | ".join(self._headers) + " |")
            self.lines.append("|" + "|".join("---" for _ in self._headers) + "|")
            self.lines.extend("| " + " | ".join(row) + " |" for row in self._rows)
            self.lines.append("")
        self._rows = []
        self._headers = None

    def _table(self, headers, rows):
        self._flush()
        self._headers = headers
        self._rows = [[str(cell) for cell in row] for row in rows]
        self._flush()

    def section(self, title):
        self._flush()
        self.lines.extend([f"## {title}", ""])

    def inputs(self, rows):
        """rows: (symbol, meaning, value, unit)"""
        self.section("Inputs")
        self._table(["Symbol", "Meaning", "Value", "Unit"], rows)

    def factors(self, rows):
        """rows: (symbol, meaning, value, where it comes from)"""
        self.section("Resistance factors and constants")
        self._table(["Symbol", "Meaning", "Value", "Source in this sheet"], rows)

    def calc(self, rows):
        """rows: (symbol, formula, numbers, result, unit)"""
        self._table(["Symbol", "Formula", "Numbers", "Result", "Unit"], rows)

    def check(self, label, demand, capacity, passed, unit):
        verdict = "PASS" if passed else "FAIL"
        suffix = "" if unit == "-" else f" {unit}"
        self._table(["Check", "Demand", "Capacity", "Result"],
                    [[label, f"{fmt(demand)}{suffix}", f"{fmt(capacity)}{suffix}", verdict]])
        return passed

    def note(self, text):
        self.lines.extend([text, ""])

    def flagged(self, reasons):
        self.section("Not sized")
        self.note("These inputs are outside the range this check supports, so no result is given.")
        self.lines.extend(f"- {reason}" for reason in reasons)
        self.lines.append("")

    def markdown(self):
        self._flush()
        return "\n".join(self.lines).rstrip() + "\n"
