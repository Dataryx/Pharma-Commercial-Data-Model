"""X12 867 parser — delimiters from ISA, CTT/SE validation, quarantine on failure."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass
class ParseResult:
    ok: bool
    lines: list[dict]
    reason: str | None = None
    interchange_control_number: str | None = None


def parse_867(text: str) -> ParseResult:
    if not text.startswith("ISA"):
        return ParseResult(False, [], "missing_ISA")
    if len(text) < 106:
        return ParseResult(False, [], "ISA_too_short")
    element_sep = text[3]
    segment_term = text[105]
    segments = [s for s in text.split(segment_term) if s]
    if not segments or not segments[0].startswith("ISA"):
        return ParseResult(False, [], "bad_ISA")

    isa_elems = segments[0].split(element_sep)
    icn = isa_elems[13] if len(isa_elems) > 13 else None

    parsed_lines: list[dict] = []
    current: dict | None = None
    header = {
        "interchange_control_number": icn,
        "group_control_number": None,
        "transaction_set_control_number": None,
        "report_id": None,
        "report_date": None,
        "report_purpose_code": None,
        "wholesaler_id": None,
    }
    se_declared = None
    ctt_lines = None

    for seg in segments:
        elems = seg.split(element_sep)
        tag = elems[0]
        if tag == "GS":
            header["group_control_number"] = elems[6] if len(elems) > 6 else None
        if tag == "ST":
            header["transaction_set_control_number"] = elems[2] if len(elems) > 2 else None
        if tag == "BPT":
            header["report_purpose_code"] = elems[1] if len(elems) > 1 else None
            header["report_id"] = elems[2] if len(elems) > 2 else None
            header["report_date"] = elems[3] if len(elems) > 3 else None
        if tag == "N1" and len(elems) > 1 and elems[1] == "BY":
            header["wholesaler_id"] = elems[2] if len(elems) > 2 else None
        if tag == "PTD":
            if current:
                parsed_lines.append(current)
            current = {
                **header,
                "line_number": int(elems[3]) if len(elems) > 3 and str(elems[3]).isdigit() else len(parsed_lines) + 1,
                "transfer_type_code": elems[1] if len(elems) > 1 else None,
                "ndc11": None,
                "quantity": None,
                "quantity_uom": None,
                "unit_price_wac": None,
                "ship_date": None,
                "invoice_number": None,
                "shipto_name": None,
                "shipto_dea": None,
                "shipto_hin": None,
                "shipto_address": None,
                "shipto_city": None,
                "shipto_state": None,
                "shipto_zip": None,
                "is_return": elems[1] == "RE" if len(elems) > 1 else False,
            }
        elif tag == "LIN" and current is not None:
            for i, e in enumerate(elems):
                if e == "N4" and i + 1 < len(elems):
                    current["ndc11"] = elems[i + 1]
        elif tag == "QTY" and current is not None:
            current["quantity"] = float(elems[2]) if len(elems) > 2 else None
            current["quantity_uom"] = elems[3] if len(elems) > 3 else None
            if len(elems) > 1 and elems[1] == "61":
                current["is_return"] = True
                if current["quantity"]:
                    current["quantity"] = -abs(current["quantity"])
        elif tag == "CTP" and current is not None and len(elems) > 3:
            try:
                current["unit_price_wac"] = float(elems[3])
            except ValueError:
                current["unit_price_wac"] = None
        elif tag == "DTM" and current is not None and len(elems) > 2 and elems[1] == "011":
            current["ship_date"] = elems[2]
        elif tag == "REF" and current is not None and len(elems) > 2:
            if elems[1] == "IV":
                current["invoice_number"] = elems[2]
            if elems[1] == "HI":
                current["shipto_hin"] = elems[2]
        elif tag == "N1" and current is not None and len(elems) > 1 and elems[1] == "ST":
            current["shipto_name"] = elems[2] if len(elems) > 2 else None
            current["shipto_dea"] = elems[4] if len(elems) > 4 else None
        elif tag == "N3" and current is not None and len(elems) > 1:
            current["shipto_address"] = elems[1]
        elif tag == "N4" and current is not None:
            current["shipto_city"] = elems[1] if len(elems) > 1 else None
            current["shipto_state"] = elems[2] if len(elems) > 2 else None
            current["shipto_zip"] = elems[3] if len(elems) > 3 else None
        elif tag == "CTT":
            ctt_lines = int(elems[1]) if len(elems) > 1 and elems[1].isdigit() else None
        elif tag == "SE":
            se_declared = int(elems[1]) if len(elems) > 1 and elems[1].isdigit() else None

    if current:
        parsed_lines.append(current)

    if se_declared is not None:
        st_idx = next(i for i, s in enumerate(segments) if s.startswith("ST" + element_sep) or s == "ST" or s.startswith("ST*"))
        se_idx = next(i for i, s in enumerate(segments) if s.startswith("SE" + element_sep) or s.startswith("SE*"))
        actual_se = se_idx - st_idx + 1
        if actual_se != se_declared:
            return ParseResult(False, [], f"SE_mismatch declared={se_declared} actual={actual_se}", icn)

    if ctt_lines is not None and ctt_lines != len(parsed_lines):
        return ParseResult(False, [], f"CTT_mismatch declared={ctt_lines} actual={len(parsed_lines)}", icn)

    return ParseResult(True, parsed_lines, None, icn)


def parse_directory(raw_dir: Path, quarantine_dir: Path) -> list[dict]:
    quarantine_dir.mkdir(parents=True, exist_ok=True)
    all_lines: list[dict] = []
    for path in sorted(raw_dir.glob("*.edi")):
        text = path.read_text(encoding="utf-8")
        result = parse_867(text)
        if not result.ok:
            dest = quarantine_dir / path.name
            dest.write_text(text, encoding="utf-8")
            (quarantine_dir / (path.name + ".reason.txt")).write_text(result.reason or "", encoding="utf-8")
            continue
        for line in result.lines:
            line["_source_file"] = path.name
            all_lines.append(line)
    return all_lines
