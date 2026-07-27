# The report

About 5 pages of LaTeX that let a newcomer navigate the field in one sitting: what is being solved,
who did it best, what the data really is, and where the field is building toward. Start from
`assets/template.tex`, which compiles standalone and marks every slot with `% ALMAGEST:` comments.

## Page budget

| Page | Content |
|---|---|
| 1 | Title, one paragraph abstract, the TLDR box: 8 to 12 bullets a domain expert scans in a minute. Corpus line: N papers, window, how many DOI verified, how many read at full text |
| 2 | What the field solves for, and the taxonomy: method families against tasks, with the evolution figure |
| 3 | Who did it best: the comparison table plus the decision relevant figure, with validity caveats stated inline, and one paragraph on the dominant metric and what it hides |
| 4 | Data and ground truth provenance: where training data comes from, label quality, the coverage gap matrix |
| 5 | Hypotheses (3 to 5, from future work sections plus verified gaps), outlook, verification notes, references |

Squeeze rule: when content overflows, cut prose before cutting tables, cut tables before cutting
figures, and never cut the verification notes.

## The comparison table

The core of page 3. Columns: paper, method, evaluation protocol, headline metric, and a caveat
column. Rules: booktabs only (`\toprule`, `\midrule`, `\bottomrule`), no vertical rules, group rows
by evaluation protocol so incomparable numbers are never visually adjacent, bold nothing except the
single result the text argues is strongest, and footnote every asterisk. If no two papers measured
the same thing the same way, say exactly that and rank nothing.

## Hypotheses section format

Numbered list, three lines each: **H1.** One sentence claim. One sentence of evidence with citation.
*Falsified if:* the experiment that would kill it. No hedging padding: the falsification line is what
makes it useful.

## References

Bibliography entries only for works present in `data/refs_verified.csv` as resolved. Format each
entry with a clickable DOI: `\href{https://doi.org/DOI}{doi:DOI}`. Works without a resolved
identifier are not cited; if one is essential, name it in prose with an explicit unverified flag.
The template uses plain `thebibliography`, no biber or natbib dependency.

## Verification notes subsection

Short, mandatory, on page 5: how many records were abstract only, which claims are negative findings
worded as "not found in this scan", any citation corrected or dropped during verification, and the
statement that all metrics are as self reported by their authors.

## Compiling

```bash
uv run scripts/compile_report.py report.tex
```

Tries `latexmk`, then `tectonic`, then `xelatex`, then `pdflatex`, runs twice for references, and
prints the page count. Target 5 pages, accept 4 to 6. If no engine exists the script says so and
exits cleanly: deliver `report.tex` plus the `figures/` directory and the one line compile command
for the user's machine.

## Template conventions

Packages used are TeX Live universal: geometry, booktabs, graphicx, xcolor, microtype, hyperref. The
TLDR box is a `tcolorbox` free construction from `\fcolorbox` and a `minipage`. Figures include as
PDF vectors from `figures/`. Margins and type size are set for density without crowding: change them
only to hold the page budget.
