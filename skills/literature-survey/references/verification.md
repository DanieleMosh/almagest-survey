# Verification

The rules that keep a survey honest: evidence levels, reference verification, open access
acquisition, negative findings, and the metric inflation checklist.

## Evidence levels

Record per paper how much you actually read, and let that bound what you claim:

| Level | You read | You may state |
|---|---|---|
| `full-text` | the paper | internal details: architecture specifics, dataset sizes, protocol, caveats |
| `abstract` | abstract only | headline claims, marked as provisional where they matter |
| `metadata` | title and record only | existence, venue, year, topic. Nothing internal |

Most of a typical corpus will be abstract level, because major publishers block scripted access even
for open access articles. That is fine: say so in the report rather than papering over it.

**Peer review status is a separate axis from evidence level.** In fast moving computational fields the
frontier lives on arXiv months or years before journal publication, and excluding preprints would
misrepresent the state of the art. Include them, but record the status: keep an `arxiv_id` alongside
`doi`, mark records that exist only as preprints, and state the preprint share in the report. A result
that has not been peer reviewed can still be the most important in the corpus, and the reader is
entitled to know which is which.

## Reference verification

Run after corpus assembly, and again after any edit that touches identity columns:

```bash
uv run scripts/verify_refs.py data/papers.csv --mailto you@example.com
```

What it does: resolves every `doi` against Crossref (polite pool via your mailto), every `arxiv_id`
against the arXiv API, writes `data/refs_verified.csv`, warns when the resolved year disagrees with
the corpus year by more than one, and exits nonzero on any failure. A failing reference is fixed or
removed, never shipped. Rows with no identifier are counted and reported: they are papers you found
but could not confirm, and the report must not cite them as verified.

## Open access acquisition recipe

No bundled script: write a small fetcher per survey, following these rules.

**Routes that historically work for scripted clients**, in priority order: arXiv (`arxiv.org/pdf/ID`),
Europe PMC full text XML (`ebi.ac.uk/europepmc/webservices/rest/PMCID/fullTextXML`, structured, often
better than PDF), Copernicus journals, Springer (`link.springer.com/content/pdf/DOI.pdf` for open
articles), Nature portfolio (`nature.com/articles/ID.pdf`), Frontiers, government and university
repositories, and the OpenAlex `best_oa_location.pdf_url` as a general fallback. A last resort that
often works: search the arXiv API by title for a preprint of a paywalled paper, accepting only strong
title matches.

**Routes that historically block scripted clients** even for gold open access: ScienceDirect and MDPI
(bot protection challenge pages). Do not attempt to bypass bot protection, ever. Routes drift in both
directions, so test 2 or 3 during recon rather than trusting this table.

**Validation rule**: a 200 response with a `.pdf` name is not a PDF. Check the magic bytes and run
`pdftotext -l 1` on every download; count a paper as acquired only if text extraction succeeds.

**MANIFEST.md**: every paper appears once, either retrieved (with source) or not retrieved (with DOI
link and reason). When paywalled papers carry evidence the report depends on, open the manifest with
a priority request list for interlibrary loan: author, year, title, journal, DOI, plus the specific
fields to extract from each once obtained. Exclude any reference that failed verification, with a
note, so nobody spends a request on a paper that may not exist.

## Negative findings protocol

"No published work does X" is the highest value claim a survey makes and the easiest to get wrong.
Before printing one: have the overseer attack it with fresh queries, then either confirm it through a
targeted sweep of the relevant index, or downgrade the wording to "no published work found in this
scan". Absence of search results is never proof of absence. Corrections discovered late go in the
report's verification notes, visibly, not silently.

## Metric inflation checklist

Apply before declaring any paper the best performer:

1. **Split type.** Random splits on spatially, temporally, or structurally correlated data leak;
   expect large metric drops under blocked or grouped splits. Prefer papers reporting the harder
   protocol, and say when the winner used the easy one.
2. **Class or value imbalance.** Accuracy on rare event tasks is close to meaningless; check what the
   base rate is. Rebalanced training data makes accuracy incomparable to the native distribution.
3. **Non comparability.** Different test sets, preprocessing, or label definitions make cross paper
   metric tables indicative at best. Never rank papers on a metric they did not measure the same way.
4. **Decision relevance.** Prefer metrics tied to the downstream decision (capture rate, cost
   weighted error, calibration) over generic ones, and lead the report with those when any paper
   provides them.
5. **Forward validation.** The rarest and strongest evidence: the model's predictions tested on new
   experiments, sites, or samples. Papers with it deserve headline placement even when their
   retrospective metrics look ordinary.
6. **Self reported values.** Every metric in the corpus is as reported by its authors. Note this once
   in the report rather than implying independent reproduction.
