# /// script
# requires-python = ">=3.10"
# dependencies = ["requests"]
# ///
"""Verify every reference in a survey corpus against the public registries.

Reads a CSV containing a `doi` and/or `arxiv_id` column (names configurable),
resolves each DOI through Crossref and each arXiv id through the arXiv API,
and writes `refs_verified.csv` next to the input. Any reference that fails to
resolve is reported loudly and the script exits nonzero: a failing reference
is fixed or removed, never shipped.

This is the survey's zero fabrication guarantee. Do not skip it.

Usage:
    uv run verify_refs.py data/papers.csv --mailto you@example.com
    uv run verify_refs.py corpus.csv --doi-col DOI --key-col slug
"""
from __future__ import annotations

import argparse
import csv
import sys
import time
import xml.etree.ElementTree as ET
from pathlib import Path

import requests

CROSSREF = "https://api.crossref.org/works/{doi}"
ARXIV = "https://export.arxiv.org/api/query?id_list={aid}"
ATOM = {"a": "http://www.w3.org/2005/Atom"}


def check_doi(doi: str, session: requests.Session) -> dict:
    # Retry transient refusals: a rate limited request is not a missing paper.
    r = None
    for attempt in range(4):
        try:
            r = session.get(CROSSREF.format(doi=doi), timeout=45)
            if r.status_code == 404:
                return {"status": "NOT_FOUND", "detail": "Crossref 404"}
            if r.status_code == 200:
                break
            if r.status_code in (429, 500, 502, 503):
                time.sleep(3 * (attempt + 1))
                continue
            return {"status": f"HTTP_{r.status_code}", "detail": ""}
        except requests.RequestException as exc:
            if attempt == 3:
                return {"status": "ERROR", "detail": str(exc)[:100]}
            time.sleep(3 * (attempt + 1))
    if r is None or r.status_code != 200:
        return {"status": "ERROR", "detail": "Crossref unreachable after retries"}
    m = r.json()["message"]
    year = (m.get("issued", {}).get("date-parts") or [[None]])[0][0]
    return {
        "status": "OK",
        "resolved_title": (m.get("title") or [""])[0],
        "resolved_year": year if year is not None else "",
        "resolved_venue": (m.get("container-title") or [""])[0],
    }


def check_arxiv(aid: str, session: requests.Session) -> dict:
    # arXiv throttles aggressively once a run has made many requests, and a
    # transient refusal is not evidence that the paper does not exist. Retry
    # with backoff before reporting a failure.
    r = None
    for attempt in range(4):
        try:
            r = session.get(ARXIV.format(aid=aid), timeout=45)
            if r.status_code == 200:
                break
            if r.status_code in (429, 500, 502, 503):
                time.sleep(3 * (attempt + 1))
                continue
            return {"status": f"HTTP_{r.status_code}", "detail": ""}
        except requests.RequestException as exc:
            if attempt == 3:
                return {"status": "ERROR", "detail": str(exc)[:100]}
            time.sleep(3 * (attempt + 1))
    if r is None or r.status_code != 200:
        return {"status": "ERROR", "detail": "arXiv unreachable after retries"}
    try:
        entry = ET.fromstring(r.text).find("a:entry", ATOM)
    except ET.ParseError:
        return {"status": "ERROR", "detail": "arXiv response parse failure"}
    title = entry.findtext("a:title", "", ATOM).strip() if entry is not None else ""
    # The API returns an entry titled "Error" for unknown ids.
    if not title or title == "Error":
        return {"status": "NOT_FOUND", "detail": "arXiv id not found"}
    pub = entry.findtext("a:published", "", ATOM)
    return {"status": "OK", "resolved_title": " ".join(title.split()),
            "resolved_year": pub[:4] if pub else "", "resolved_venue": "arXiv"}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("csv_path", type=Path, help="corpus CSV to verify")
    ap.add_argument("--mailto", default="", help="contact email for the Crossref polite pool")
    ap.add_argument("--doi-col", default="doi")
    ap.add_argument("--arxiv-col", default="arxiv_id")
    ap.add_argument("--key-col", default="key", help="row identifier column, if present")
    ap.add_argument("--year-col", default="year", help="year column for mismatch warnings")
    ap.add_argument("--sleep", type=float, default=0.4, help="seconds between requests")
    args = ap.parse_args()

    with args.csv_path.open(newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    if not rows:
        sys.exit(f"no rows in {args.csv_path}")

    session = requests.Session()
    ua = "almagest-literature-survey/1.0"
    if args.mailto:
        ua += f" (mailto:{args.mailto})"
    session.headers["User-Agent"] = ua

    out_rows: list[dict] = []
    failures: list[tuple[str, str, str]] = []
    warnings: list[str] = []
    n_ok = n_noid = 0

    for i, row in enumerate(rows):
        key = row.get(args.key_col) or f"row{i + 1}"
        doi = (row.get(args.doi_col) or "").strip()
        aid = (row.get(args.arxiv_col) or "").strip()

        if doi:
            res, ident, kind = check_doi(doi, session), doi, "doi"
        elif aid:
            res, ident, kind = check_arxiv(aid, session), aid, "arxiv"
        else:
            n_noid += 1
            out_rows.append({"key": key, "identifier": "", "kind": "none",
                             "status": "NO_IDENTIFIER", "resolved_title": "",
                             "resolved_year": "", "resolved_venue": "", "detail": ""})
            continue

        out_rows.append({"key": key, "identifier": ident, "kind": kind,
                         "status": res["status"],
                         "resolved_title": res.get("resolved_title", ""),
                         "resolved_year": res.get("resolved_year", ""),
                         "resolved_venue": res.get("resolved_venue", ""),
                         "detail": res.get("detail", "")})

        if res["status"] == "OK":
            n_ok += 1
            claimed = (row.get(args.year_col) or "").strip()
            resolved = str(res.get("resolved_year") or "")
            if claimed.isdigit() and resolved.isdigit() and abs(int(claimed) - int(resolved)) > 1:
                warnings.append(f"{key}: corpus year {claimed} vs resolved {resolved} ({ident})")
        else:
            failures.append((key, ident, res["status"]))
            print(f"  ! {res['status']:<12} {key}  {ident}")
        time.sleep(args.sleep)

    out_path = args.csv_path.parent / "refs_verified.csv"
    with out_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(out_rows[0].keys()))
        writer.writeheader()
        writer.writerows(out_rows)

    print(f"\n{'=' * 60}\nReference verification -> {out_path}")
    print(f"  resolved OK    : {n_ok}")
    print(f"  failed         : {len(failures)}")
    print(f"  no identifier  : {n_noid}  (may not be cited as verified)")
    print(f"  total rows     : {len(rows)}")
    for w in warnings:
        print(f"  year mismatch  : {w}")

    if failures:
        print("\nFAILED, fix or remove before publication:")
        for key, ident, status in failures:
            print(f"  {key:<30} {ident:<45} {status}")
        sys.exit(1)


if __name__ == "__main__":
    main()
