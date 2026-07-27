# /// script
# requires-python = ">=3.10"
# ///
"""Compile the survey report with whatever TeX engine the machine has.

Tries latexmk, then tectonic, then xelatex, then pdflatex. Direct engines run
twice so cross references settle. Prints the page count from the engine log,
or from pdfinfo when available. When no engine exists it exits cleanly with
instructions, so the survey can still deliver the .tex source.

Usage:
    uv run compile_report.py report.tex
"""
from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path


def run(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=300)


def page_count(pdf: Path, log_text: str) -> str:
    if shutil.which("pdfinfo"):
        try:
            out = run(["pdfinfo", str(pdf)], pdf.parent).stdout
            m = re.search(r"Pages:\s+(\d+)", out)
            if m:
                return m.group(1)
        except (subprocess.SubprocessError, OSError):
            pass
    m = re.search(r"\((\d+) pages?", log_text)
    return m.group(1) if m else "unknown"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("tex_path", type=Path, help="the .tex file to compile")
    args = ap.parse_args()

    tex = args.tex_path.resolve()
    if not tex.exists():
        sys.exit(f"not found: {tex}")
    cwd, pdf = tex.parent, tex.with_suffix(".pdf")

    plans: list[tuple[str, list[list[str]]]] = []
    if shutil.which("latexmk"):
        plans.append(("latexmk", [["latexmk", "-pdf", "-interaction=nonstopmode",
                                   "-halt-on-error", tex.name]]))
    if shutil.which("tectonic"):
        plans.append(("tectonic", [["tectonic", tex.name]]))
    for engine in ("xelatex", "pdflatex"):
        if shutil.which(engine):
            once = [engine, "-interaction=nonstopmode", "-halt-on-error", tex.name]
            plans.append((engine, [once, once]))  # twice, for references

    if not plans:
        print("No TeX engine found (looked for latexmk, tectonic, xelatex, pdflatex).")
        print("Deliver the .tex and figures; the user can compile with, for example:")
        print(f"  latexmk -pdf {tex.name}")
        print("TeX Live: https://tug.org/texlive/  or  tectonic: https://tectonic-typesetting.github.io/")
        sys.exit(0)

    name, commands = plans[0]
    print(f"engine: {name}")
    log = ""
    for cmd in commands:
        try:
            proc = run(cmd, cwd)
        except subprocess.TimeoutExpired:
            sys.exit(f"{name} timed out after 300 s")
        log = proc.stdout + proc.stderr
        if proc.returncode != 0:
            # Surface the actual TeX error lines, not the whole log.
            errors = [ln for ln in log.splitlines() if ln.startswith("!")]
            print("\n".join(errors[:12]) or log[-2500:])
            sys.exit(f"{name} failed with exit code {proc.returncode}")

    if not pdf.exists():
        sys.exit(f"{name} reported success but {pdf.name} was not produced")

    pages = page_count(pdf, log)
    print(f"wrote {pdf}  ({pages} pages)")
    if pages.isdigit() and not 4 <= int(pages) <= 6:
        print(f"note: target is about 5 pages, this is {pages}; see references/report.md squeeze rule")


if __name__ == "__main__":
    main()
