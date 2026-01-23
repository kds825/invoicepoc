from __future__ import annotations
import argparse
import subprocess
import sys
from pathlib import Path
from typing import Iterator, Optional

def iter_pdfs(folder: Path) ->Iterator[Path]:
    if not folder.exists():
        return
    for ext in ("*.pdf", "*.PDF"):
        for p in folder.glob(ext):
            if p.is_file():
                yield p

def run_one(
    pdf_path: Path,
    doc_type: str,
    max_pages: Optional[int],
    save_sap: bool,
    out_dir : Path,
)-> bool:
    cmd = [
        sys.executable,
        "main.py",
        "--pdf",
        str(pdf_path),
        "--type",
        doc_type,
        "--out-dir",
        str(out_dir),
        "--prefix",
        pdf_path.stem,
    ]
    if max_pages is not None:
        cmd += ["--max-pages", str(max_pages)]
    if save_sap:
        cmd += ["--save-sap"]

    print(f'\n=== RUN {doc_type} | {pdf_path.name} ===')
    proc = subprocess.run(cmd, capture_output = True, text=True)

    if proc.returncode !=0:
        print("[FAIL]", pdf_path)
        if proc.stdout:
            print(proc.stdout)
        if proc.stderr:
            print(proc.stderr)
        return False
    
    if proc.stdout:
        print(proc.stdout.strip())
    return True

def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--samples-root", default = "samples", help = "samples root folder")
    p.add_argument("--ci-folder", default = "commercial invoice", help = "CI folder name under samples/")
    p.add_argument("--bl-folder", default="BL", help="BL folder name under samples/")
    p.add_argument("--max-pages", type=int, default=None)
    p.add_argument("--save-sap", action="store_true")
    p.add_argument("--out-dir", default="output/batch")
    args = p.parse_args()

    samples_root = Path(args.samples_root)
    ci_dir = samples_root / args.ci_folder
    bl_dir = samples_root / args.bl_folder

    base_out_dir = Path(args.out_dir)
    (base_out_dir/"import_invoice").mkdir(parents=True, exist_ok = True)
    (base_out_dir/"bl").mkdir(parents = True, exist_ok = True)

    ok=0
    fail=0

    for pdf in iter_pdfs(ci_dir):
        if run_one(
            pdf_path = pdf,
            doc_type="import_invoice",
            max_pages = args.max_pages,
            save_sap = args.save_sap,
            out_dir = base_out_dir / "import_invoice"
        ):
            ok += 1
        else: 
            fail += 1
    
    for pdf in iter_pdfs(bl_dir):
        if run_one(
            pdf_path=pdf,
            doc_type = "bl",
            max_pages = args.max_pages,
            save_sap = args.save_sap,
            out_dir=base_out_dir / "bl"
        ):
            ok += 1
        else:
            fail += 1

    print(f"\nDone. ok={ok}, fail={fail}")
    if fail:
        raise SystemExit(1)

if __name__ =="__main__":
    main()        
    