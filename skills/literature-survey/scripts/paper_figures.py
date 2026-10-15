# /// script
# requires-python = ">=3.10"
# dependencies = ["pillow"]
# ///
"""Find, preview and crop figure panels from the retrieved open access PDFs.

Three subcommands, used in this order:

    # 1. list every figure caption and the page it sits on
    uv run paper_figures.py find papers/

    # 2. render chosen pages as small previews with a 50 pt grid, to pick boxes by eye
    uv run paper_figures.py preview papers/smith2025.pdf 2 5 --out figures/snapshots/_preview

    # 3. crop every box in a spec file into figures/snapshots/<name>.png
    uv run paper_figures.py crop figures/snapshots/panels.csv

The spec CSV has columns: name,key,page,x0,y0,x1,y1,caption
Boxes are in PDF points (1/72 in) from the top left corner, which is exactly what the
preview grid shows, so no resolution conversion is ever needed. `key` names
papers/<key>.pdf. `caption` is a one line description that the report caption reuses.

Needs poppler (pdftoppm, pdftotext, pdfinfo) on PATH. Previews draw the grid with Pillow; the
script falls back to plain renders without the grid when Pillow is missing.
"""
from __future__ import annotations

import argparse
import csv
import re
import shutil
import subprocess
import sys
from pathlib import Path

CAPTION = re.compile(r"^\s*(Fig\.|Figure|FIG\.?)\s*(\d+)\s*[.:|]?\s*(.*)$")


def need(tool: str) -> None:
    if shutil.which(tool) is None:
        sys.exit(f"error: {tool} not found; install poppler (brew install poppler / apt install poppler-utils)")


def pages(pdf: Path) -> int:
    out = subprocess.run(["pdfinfo", str(pdf)], capture_output=True, text=True, errors="replace").stdout
    m = re.search(r"Pages:\s+(\d+)", out)
    return int(m.group(1)) if m else 0


def page_size(pdf: Path, page: int) -> tuple[float, float]:
    out = subprocess.run(["pdfinfo", "-f", str(page), "-l", str(page), str(pdf)],
                         capture_output=True, text=True, errors="replace").stdout
    m = re.search(r"Page\s+\d+\s+size:\s+([\d.]+) x ([\d.]+)", out) or re.search(r"Page size:\s+([\d.]+) x ([\d.]+)", out)
    return (float(m.group(1)), float(m.group(2))) if m else (612.0, 792.0)


def cmd_find(args: argparse.Namespace) -> None:
    need("pdftotext")
    for pdf in sorted(Path(args.papers).glob("*.pdf")):
        hits = []
        for p in range(1, pages(pdf) + 1):
            txt = subprocess.run(["pdftotext", "-layout", "-f", str(p), "-l", str(p), str(pdf), "-"],
                                 capture_output=True, text=True, errors="replace").stdout
            for line in txt.splitlines():
                m = CAPTION.match(line)
                if m and len(m.group(3)) > 8:
                    hits.append(f"  p{p:<3} Fig {m.group(2):<3} {m.group(3).strip()[:110]}")
        if hits:
            print(pdf.stem)
            print("\n".join(dict.fromkeys(hits)))


def cmd_preview(args: argparse.Namespace) -> None:
    need("pdftoppm")
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    dpi = 72  # one pixel per point, so the grid labels are box coordinates
    for page in args.pages:
        stem = out / f"{Path(args.pdf).stem}_p{page}"
        subprocess.run(["pdftoppm", "-r", str(dpi), "-f", str(page), "-l", str(page), "-singlefile", "-png",
                        str(args.pdf), str(stem)], check=True)
        try:
            from PIL import Image, ImageDraw
        except ImportError:
            print(f"{stem}.png (no grid: Pillow missing)")
            continue
        im = Image.open(f"{stem}.png").convert("RGB")
        d = ImageDraw.Draw(im)
        for v in range(0, max(im.size), 50):
            d.line([(v, 0), (v, im.height)], fill=(255, 0, 0) if v % 100 == 0 else (255, 170, 170), width=1)
            d.line([(0, v), (im.width, v)], fill=(255, 0, 0) if v % 100 == 0 else (255, 170, 170), width=1)
            if v % 100 == 0:
                d.text((v + 2, 2), str(v), fill=(200, 0, 0))
                d.text((2, v + 2), str(v), fill=(200, 0, 0))
        im.save(f"{stem}.png")
        print(f"{stem}.png")


def cmd_crop(args: argparse.Namespace) -> None:
    need("pdftoppm")
    spec = Path(args.spec)
    root = Path(args.root) if args.root else spec.parent.parent.parent
    out = spec.parent
    rows = list(csv.DictReader(open(spec)))
    for r in rows:
        pdf = root / "papers" / f"{r['key']}.pdf"
        page = int(r["page"])
        x0, y0, x1, y1 = (float(r[k]) for k in ("x0", "y0", "x1", "y1"))
        w, h = page_size(pdf, page)
        if not (0 <= x0 < x1 <= w and 0 <= y0 < y1 <= h):
            sys.exit(f"error: box for {r['name']} falls outside the {w:.0f}x{h:.0f} pt page")
        s = args.dpi / 72
        subprocess.run(["pdftoppm", "-r", str(args.dpi), "-f", str(page), "-l", str(page), "-singlefile", "-png",
                        "-x", str(int(x0 * s)), "-y", str(int(y0 * s)),
                        "-W", str(int((x1 - x0) * s)), "-H", str(int((y1 - y0) * s)),
                        str(pdf), str(out / r["name"])], check=True)
        print(f"{r['name']}.png  <- {r['key']} p{page}")
    print(f"{len(rows)} panels written to {out}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    f = sub.add_parser("find", help="list figure captions per paper and page")
    f.add_argument("papers")
    f.set_defaults(fn=cmd_find)
    p = sub.add_parser("preview", help="render pages at 72 dpi with a 50 pt grid")
    p.add_argument("pdf")
    p.add_argument("pages", nargs="+", type=int)
    p.add_argument("--out", default="figures/snapshots/_preview")
    p.set_defaults(fn=cmd_preview)
    c = sub.add_parser("crop", help="crop every box listed in a spec CSV")
    c.add_argument("spec")
    c.add_argument("--root", help="survey root containing papers/ (default: inferred from spec path)")
    c.add_argument("--dpi", type=int, default=220)
    c.set_defaults(fn=cmd_crop)
    args = ap.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
