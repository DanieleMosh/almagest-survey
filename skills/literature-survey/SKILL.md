---
name: literature-survey
description: Run a rigorous state of the art literature survey on any STEM topic and deliver a compiled PDF report of about 5 pages. Opens by converging with the user on how deep and granular the survey should go, then produces a DOI verified corpus CSV, open access PDFs with a request manifest, Tufte style seaborn figures, and testable hypotheses mined from the future work sections of the surveyed papers. Use whenever the user asks to survey a field, review the literature, map the state of the art, find who did it best, compare methods or benchmarks across papers, understand what a research area is solving for, or scope the open problems in a topic. Trigger on phrases like "survey the SOTA", "literature review", "state of the art of X", "what is the research on X", "who is leading in X", "map the field".
---

# Literature survey

Survey a STEM field the way a careful research scientist would: harvest in parallel, verify every
reference, refuse to guess, and end with a short document that says what is solved, who did it best,
and what to try next.

**The one rule that matters:** never state a fact you have not verified. A blank cell is useful; a
plausible fabricated number is a defect that propagates into the reader's work.

## Deliverables

```
<topic>-survey/
  report.pdf            the deliverable, about 5 pages
  report.tex            source, filled from assets/template.tex
  data/scope.md         the agreed scope contract, written before harvesting
  data/papers.csv       corpus, single source of truth for every count
  data/refs_verified.csv verification result per reference
  papers/               retrieved open access PDFs
  papers/MANIFEST.md    every paper: retrieved, or blocked with a DOI link
  figures/              4 to 6 figures, regenerated from papers.csv
  scripts/make_figures.py
```

## Phase 0, scope by convergence

A survey aimed at the wrong altitude is wasted work: a request for "AI in medicine" and a request for
"uncertainty calibration in histopathology foundation models" need entirely different corpora. So do
not guess the depth. Converge on it.

**Loop `AskUserQuestion` until you can pass the readiness test below.** Treat it as exploration: each
round should teach you something that reshapes the next question, rather than filling slots in a form.
Usually 2 or 3 rounds, rarely 1, occasionally 4. Each round is at most 4 questions, and each question
must be one whose answer changes what you would harvest. Stop as soon as the test passes: further
questions are then friction, not rigor.

**Round 1, locate the altitude.** Offer the topic at 3 or 4 levels, from field down to specific
problem. Asking directly how deep to go (a broad map, a focused survey, a deep dive on one problem) is
a fine opening move when you are still orienting: attach a rough corpus size to each level so the
tradeoff is legible. Once you know enough to name real sub areas, prefer naming them, because a user
recognizes their own problem faster than they classify its abstraction level, and their wording tells
you the field's vocabulary. Ask in the same round what is explicitly out of scope, since exclusions
are usually sharper in the user's mind than inclusions.

**Round 2, resolve what round 1 exposed.** Typically: which sub problems or method families are in
scope, time window (default: last 5 years, weighted to the last 2), emphasis (build oriented,
academic, or commercial), and corpus size (default 40 to 60 verified papers). Where you can infer an
answer confidently from round 1, state your assumption in the option text instead of asking again.

**Further rounds only for genuine ambiguity**, for example a term that names two different research
communities, or a scope whose plausible readings differ by an order of magnitude in corpus size.

### The readiness test

Proceed only when you can write all five of these down without hedging:

1. **One sentence** describing exactly what the survey covers, at a granularity a domain expert would
   call neither vague nor overly narrow.
2. **The taxonomy axes** you will populate: method family, task, data modality, evaluation metric.
3. **Three or four concrete search queries** you expect to be productive, in the field's own vocabulary.
4. **What is out of scope**, stated as explicitly as what is in scope.
5. **A named example paper** that clearly belongs, and one adjacent paper that clearly does not.

If any of the five is still fuzzy, that fuzziness is your next question. Write the five into
`data/scope.md` before harvesting, and treat it as the contract the corpus is judged against: a paper
that does not fit the sentence does not enter the corpus without an explicit scope amendment.

## Phase 1, recon before mass harvest

Cheap checks that stop expensive mistakes:

1. Environment: `uv`, `pdftotext`, and a TeX engine. Missing TeX is not fatal, see phase 8.
2. Resolve 1 or 2 seed papers through Crossref or OpenAlex. Confirm the field's vocabulary and the
   venues that matter.
3. Empirically test 2 or 3 PDF routes for this field's dominant publishers. Routes drift, so test
   rather than assume. See `references/verification.md`.
4. Fix the taxonomy dimensions now: method family, task, data modality, evaluation metric. Every
   agent will populate these columns, so they must be decided before the harvest, not after.
5. Sanity check the scope against reality. If a seed query at the agreed rung returns far more or far
   fewer papers than `data/scope.md` predicts, the rung was wrong: go back to the user with one
   corrective question rather than harvesting a corpus that is unusably broad or nearly empty.

## Phase 2, parallel harvest with a coordinator and an overseer

Speed comes from parallelism. Trust comes from the overseer. Full prompt templates are in
`references/methodology.md`.

**Coordinator (you, the main session).** Split the topic into 2 to 4 strands plus one strand for
data, benchmarks, and infrastructure. Launch them as background agents **in a single message** so
they run concurrently. Write the identical record schema into every agent prompt. When they return,
you merge, deduplicate by DOI, and resolve disagreements. Never delegate the merge or the final
judgment.

**Survey agents.** Each returns structured records per paper: what the method solves for, output
shape, training data provenance, metric and value, evaluation protocol, and **the paper's own stated
future work**. Unverifiable fields come back tagged `[UNVERIFIED]`, never guessed.

**Overseer.** After the merge, launch one auditor agent that has not seen the harvest prompts. It
independently re samples DOIs, attacks every negative claim ("no work exists on X") with fresh
targeted queries, sweeps for contradictions between strands, and answers "which sub field, venue, or
modality did nobody cover". Its findings return to you as corrections or as a follow up mini strand.
Overseer output never writes to the corpus directly.

Budget note: agents consume the session web search budget quickly. The metadata APIs (Crossref,
OpenAlex, Semantic Scholar, arXiv) keep working after it is exhausted, so lean on them.

## Phase 3, corpus assembly and reference verification

Normalize every record into `data/papers.csv`, the single source of truth. Controlled vocabularies
per column, one row per paper, and an `evidence_level` column recording how much of the paper you
actually read: `full-text`, `abstract`, or `metadata`. Schema in `references/methodology.md`.

Then verify, and treat this as non negotiable:

```bash
uv run scripts/verify_refs.py data/papers.csv --mailto you@example.com
```

Every DOI goes through Crossref, every arXiv id through the arXiv API. Failures are reported loudly
and the script exits nonzero until the corpus is clean. Fix or remove failures; never publish a
reference that did not resolve.

## Phase 4, acquisition

Retrieve open access PDFs, honor the paywall. Route priority, the `pdftotext` validation rule (a 200
response is not a PDF), and the `MANIFEST.md` format are in `references/verification.md`. Papers you
cannot retrieve go into the manifest with a DOI link and, when they carry evidence the report depends
on, a priority request list for interlibrary loan. Never attempt to bypass bot protection.

## Phase 5, analysis

Answer these from the corpus, with counts that trace to the CSV:

- **What are they solving for**, and what is the real world use case behind the benchmark.
- **What does the output look like**: shape, units, resolution, and who consumes it.
- **Where does the data come from**: sources, modalities, and how labels or ground truth were made.
- **What do the papers have in common**: taxonomy, chronology, and the shared assumptions.
- **Who did it best**, and **whether the comparison is even valid**. Different splits, different
  preprocessing and different test sets make most reported numbers non comparable. Say so.
- **What is the most common metric**, and what it hides. Prefer decision relevant metrics.
- **The most impactful papers**, and what each one actually proves.
- **The field's load bearing hypotheses**: the assumptions everyone builds on.

Metric inflation checklist in `references/verification.md`. Apply it before crowning a winner.

## Phase 6, hypotheses

Mine the future work sections of the highest impact papers together with the gaps your survey
verified. Distill into **3 to 5 numbered hypotheses**, each exactly: one sentence of claim, one
sentence of supporting evidence with citation, and one falsification criterion naming the experiment
that would kill it. Keep this tight; it is the most useful half page in the report.

## Phase 7, figures

4 to 6 figures, each answering one phase 5 question. Every count derives from `papers.csv` so prose
and plots cannot drift. Write `scripts/make_figures.py` using the style block and the rules in
`references/plotting.md`, then **look at every figure you generate** before accepting it.

## Phase 8, report

Fill `assets/template.tex` following the page budget in `references/report.md`, then:

```bash
uv run scripts/compile_report.py report.tex
```

The script finds whichever TeX engine exists and reports the page count. With no TeX toolchain it
exits cleanly and tells the user how to compile, and you deliver the `.tex` plus figures.

## Phase 9, verify before delivering

- Every number in the prose matches `papers.csv`. Recount rather than trust the draft.
- Negative claims are re checked, and worded as "no published work found in this scan", never as
  proof of absence.
- Every referenced figure file exists; the PDF compiles at roughly 5 pages.
- Every DOI in the bibliography appears in the verification output as resolved.
- State the corpus caveats plainly: how many records are abstract only, how many lack a DOI.
- **The corpus honors `data/scope.md`.** Spot check that papers fit the scope sentence and that
  nothing excluded slipped in. If the survey drifted, say so in the report and record the amendment
  in `scope.md` rather than quietly widening the boundary.

## Optional, a living survey

For a field that moves fast, propose a loop: re run the harvest on an interval, diff the corpus
against the previous run, and append a short changelog of new papers and shifted conclusions. See the
loops section in `references/methodology.md`.

## References

| File | Read it when |
|---|---|
| `references/methodology.md` | Setting up agents, writing prompts, defining the corpus schema, worked examples |
| `references/verification.md` | Verifying references, acquiring PDFs, judging whether a metric is trustworthy |
| `references/plotting.md` | Writing the figure script |
| `references/report.md` | Filling the LaTeX template and holding the page budget |
