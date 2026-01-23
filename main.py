from __future__ import annotations
import argparse
import json
from pathlib import Path
from typing import Any, Dict

from src.vision.gpt_vision import extract_json_from_pdf
from src.parsing.response_parser import parse_bl, parse_import_invoice
from src.outputs.sap_mapper import map_bl_to_sap_payload, map_import_invoice_to_sap_payload

def read_json(path: str) -> Dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))

def write_json(path: str, data: Dict[str, Any]) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--pdf", required=True)
    p.add_argument("--type", required=True, choices=["bl", "import_invoice"])
    p.add_argument("--max-pages", type=int, default=None)
    p.add_argument("--save-sap", action="store_true")
    p.add_argument("--out-dir", default="output")
    p.add_argument("--prefix", default=None, help="output filename prefix (optional)")

    args = p.parse_args()
    
    pdf_stem = Path(args.pdf).stem
    prefix = args.prefix or pdf_stem
    out_dir = Path(args.out_dir)

    if args.type == "bl":
        schema = read_json("config/bl_schema.json")
        extracted = extract_json_from_pdf(
            pdf_path=args.pdf,
            schema=schema,
            doc_type="Bill of Lading (B/L)",
            max_pages=args.max_pages
        )
        bl_model = parse_bl(extracted)
        normalized = bl_model.model_dump()

        out_file = str(out_dir /f"{prefix}_bl_extracted.json")
        write_json(out_file, normalized)
        print(f"[OK] extracted saved: {out_file}")

        if args.save_sap:
            sap_payload = map_bl_to_sap_payload(bl_model)
            sap_file = str(out_dir / f"{prefix}_bl_sap_payload.json")
            write_json(sap_file, sap_payload)
            print(f"[OK] sap payload saved: {sap_file}")

    else:
        schema = read_json("config/import_invoice_schema.json")
        extracted = extract_json_from_pdf(
            pdf_path=args.pdf,
            schema=schema,
            doc_type="Import Invoice (수입 인보이스)",
            max_pages=args.max_pages
        )
        inv_model = parse_import_invoice(extracted)
        normalized = inv_model.model_dump()

        out_file = str(out_dir / f"{prefix}_import_invoice_extracted.json")
        write_json(out_file, normalized)
        print(f"[OK] extracted saved: {out_file}")

        if args.save_sap:
            sap_payload = map_import_invoice_to_sap_payload(inv_model)
            sap_file = str(out_dir / f"{prefix}_import_invoice_sap_payload.json")
            write_json(sap_file, sap_payload)
            print(f"[OK] sap payload saved: {sap_file}")

if __name__ == "__main__":
    main()