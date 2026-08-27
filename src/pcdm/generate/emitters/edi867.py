"""Emit X12 867 interchanges and flattened CSV."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from pcdm.generate.config import DefectConfig


def write_edi867_files(landing: Path, shipments: pd.DataFrame, defects: DefectConfig) -> None:
    raw_dir = landing / "edi867"
    flat_dir = landing / "edi867_flat"
    raw_dir.mkdir(parents=True, exist_ok=True)
    flat_dir.mkdir(parents=True, exist_ok=True)
    quarantine = landing / "quarantine" / "edi867"
    quarantine.mkdir(parents=True, exist_ok=True)

    if shipments.empty:
        return

    # Flatten always
    shipments.to_csv(flat_dir / "edi867_flat.csv", index=False)

    # Group into interchanges by report_date + wholesaler
    for (report_date, wholesaler), g in shipments.groupby(["report_date", "wholesaler_id"]):
        icn = f"{str(report_date).replace('-', '')}{wholesaler[-1]}"
        version = "004010" if wholesaler.endswith("A") else "005010"
        mismatch = defects.is_on("segment_mismatch") and (hash(icn) % 200 == 0)
        content = _build_x12(g, icn=icn, version=version, force_mismatch=mismatch)
        fname = f"867_{wholesaler}_{str(report_date).replace('-', '')}.edi"
        target = quarantine if mismatch else raw_dir
        (target / fname).write_text(content, encoding="utf-8")

    # Duplicate file delivery ~1%
    if defects.is_on("duplicate_file") and len(list(raw_dir.glob("*.edi"))) > 0:
        first = next(raw_dir.glob("*.edi"))
        dup = raw_dir / (first.stem + "_DUP.edi")
        dup.write_text(first.read_text(encoding="utf-8"), encoding="utf-8")


def _build_x12(g: pd.DataFrame, *, icn: str, version: str, force_mismatch: bool) -> str:
    # Element separator *, segment terminator ~
    segs = []
    segs.append(f"ISA*00*          *00*          *ZZ*SENDER         *ZZ*RECEIVER       *240101*1200*U*{version[2:5]}*{icn.zfill(9)}*0*P*>~")
    segs.append(f"GS*PT*SENDER*RECEIVER*20240101*1200*1*X*{version}~")
    segs.append("ST*867*0001~")
    segs.append(f"BPT*00*{g.iloc[0]['report_id']}*{str(g.iloc[0]['report_date']).replace('-', '')}*RS~")
    segs.append("N1*SU*SYNTHO PHARMA*91*MFG001~")
    segs.append(f"N1*BY*{g.iloc[0]['wholesaler_id']}*91*{g.iloc[0]['wholesaler_id']}~")
    line_count = 0
    for _, r in g.iterrows():
        line_count += 1
        segs.append(f"PTD*{r['transfer_type_code']}**{int(r['line_number'])}~")
        segs.append(f"LIN**N4*{r['ndc11']}~")
        qty_code = "61" if r["is_return"] else "39"
        segs.append(f"QTY*{qty_code}*{abs(r['quantity']):.4f}*{r['quantity_uom']}~")
        segs.append(f"CTP**WAC*{r['unit_price_wac']:.4f}~")
        segs.append(f"DTM*011*{str(r['ship_date']).replace('-', '')}~")
        segs.append(f"REF*IV*{r['invoice_number']}~")
        segs.append(f"N1*ST*{r['shipto_name']}*ZI*{r['shipto_dea'] or ''}~")
        segs.append(f"N3*{r['shipto_address']}~")
        segs.append(f"N4*{r['shipto_city']}*{r['shipto_state']}*{r['shipto_zip']}~")
        if r.get("shipto_hin"):
            segs.append(f"REF*HI*{r['shipto_hin']}~")
    ctt_count = line_count if not force_mismatch else line_count + 5
    segs.append(f"CTT*{ctt_count}~")
    # SE01 = segment count in ST including ST and SE
    # Build first then fix SE
    body_without_se = segs[2:]  # from ST
    # temporary
    se_count = len(body_without_se) + 1  # + SE itself
    if force_mismatch:
        se_count = se_count + 3
    segs.append(f"SE*{se_count}*0001~")
    segs.append("GE*1*1~")
    segs.append(f"IEA*1*{icn.zfill(9)}~")
    return "".join(segs)
