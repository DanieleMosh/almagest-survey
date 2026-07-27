# Methodology

The full procedure behind SKILL.md: scoping by convergence, agent topology, prompt templates, the
corpus schema, a worked example, stopping rules, and the loop pattern for living surveys.

## Scoping by convergence

The depth of a survey is the single decision that most affects its usefulness, and users rarely state
it explicitly. "Survey battery research" could mean the electrochemistry of solid state interfaces or
the market landscape of pack manufacturing. Converge before harvesting.

### The ladder

Think of any topic as a ladder, and find the rung the user is standing on:

| Rung | Example | Corpus shape |
|---|---|---|
| Field | machine learning for Earth observation | hundreds of papers, only a map is possible |
| Sub field | soil property retrieval from hyperspectral data | 100 or more papers, survey by method family |
| Topic | soil organic carbon prediction from spaceborne hyperspectral | 40 to 60 papers, the sweet spot |
| Problem | domain shift between soil spectral libraries and satellite scenes | 15 to 30 papers, deep and specific |
| Technique | transfer learning for spectral calibration of EnMAP SOC models | under 15 papers, closer to a related work section |

Field level requests produce a map, not a survey: if the user genuinely wants one, say so and set
expectations, because no 5 page report can do a whole field justice at depth. Technique level requests
risk an empty corpus: check whether enough published work exists before committing, and offer the
rung above as a fallback.

The same ladder in a fast moving deep learning subfield, where the rungs are narrower and the
literature turns over in months rather than years:

| Rung | Example | Corpus shape |
|---|---|---|
| Field | interpretability of neural networks | hundreds of papers, only a map is possible |
| Sub field | mechanistic interpretability of transformers | 100 or more papers, survey by technique family |
| Topic | sparse autoencoders for feature disentanglement in LLMs | 40 to 60 papers, the sweet spot |
| Problem | feature absorption and dead latents in sparse autoencoder training | 15 to 30 papers, deep and specific |
| Technique | top k versus JumpReLU sparsity in SAE architectures | under 15 papers, closer to a related work section |

Two things this example teaches that the soil carbon one does not. First, in fields like this a large
share of the real literature sits on arXiv, on lab blogs, and in workshop tracks rather than in
indexed journals, so a DOI first corpus will silently miss the frontier: lean on the arXiv API, record
arXiv ids alongside DOIs, and say plainly in the report what fraction of the corpus is preprints that
have not been peer reviewed. Second, the vocabulary shifts fast, so confirm current terms during recon
rather than trusting the phrasing in the request.

### How to ask

Offer rungs as concrete named alternatives, never as abstract labels. This works:

> **How deep should this go?**
> - *Soil property retrieval from hyperspectral data, all properties* (broadest, roughly 100 papers,
>   organized by method family)
> - *Soil organic carbon specifically, lab through spaceborne* (recommended, roughly 50 papers)
> - *SOC from spaceborne sensors only: EnMAP, PRISMA, EMIT* (roughly 25 papers, deeper on each)
> - *Domain shift between spectral libraries and satellite scenes* (roughly 20 papers, one problem)

This does not work: "broad, medium, or narrow". The user cannot map those onto their own question, and
you learn nothing about vocabulary from the answer.

Each option should carry its rough corpus size, because that is what makes the tradeoff legible. Ask
about exclusions in the same round: users hold sharper opinions about what they do not want.

### Reading the answers

The user's wording is data. If they answer in the field's own vocabulary, they are an insider and you
can go a rung deeper than they said. If they answer in general terms, or pick the broadest option, they
are orienting, so stay at topic level and prioritize the taxonomy and the map over depth on any one
method. A custom answer that reframes the question means your ladder was wrong: rebuild it around
their framing and ask again.

### Worked scoping loop

Request: "survey the SOTA on soil organic carbon from hyperspectral".

*Round 1* offers the four rungs above plus an exclusions question. User picks SOC lab through
spaceborne, and excludes SOC flux modelling and non optical sensors. That fixes the rung but leaves
the method axis open.

*Round 2* asks whether classical chemometrics (PLSR, Cubist) is in scope alongside deep learning, the
time window, and the emphasis. User keeps chemometrics as the baseline to beat, takes 2019 onward, and
asks for build oriented framing. The readiness test now passes, so stop.

*Written to `data/scope.md`:*

1. Sentence: methods predicting topsoil organic carbon content from hyperspectral reflectance, across
   lab, field, airborne and spaceborne acquisition, 2019 onward, including chemometric baselines.
2. Axes: sensor class, method family, evaluation protocol, metric.
3. Queries: "soil organic carbon hyperspectral", "soil spectroscopy deep learning", "EnMAP soil
   organic carbon", "spectral library transfer soil".
4. Out of scope: SOC flux and turnover modelling, radar and thermal sensors, non soil carbon pools.
5. In: an EnMAP SOC retrieval paper. Adjacent but out: a Sentinel 2 multispectral SOC paper, since it
   is not hyperspectral.

Point 5 is the test that catches a scope that only sounds precise. If you cannot name the adjacent
paper that is excluded, the boundary is not real yet.

## Agent topology

Three roles, strict boundaries:

| Role | Who | Owns | Never does |
|---|---|---|---|
| Coordinator | the main session | strand design, the merge, `papers.csv`, all final judgment | outsource the merge, or accept agent claims unchecked |
| Survey agents | 2 to 4 background agents | one strand each, structured records | write to the corpus, see each other's output |
| Overseer | 1 background agent, launched after the merge | auditing the merged corpus | write to the corpus directly |

Launch all survey agents in a single message so they run concurrently. Launch the overseer only
after the merge, and keep its prompt free of the harvest prompts so its audit is independent.

### Choosing strands

Split by the structure of the field, not by keyword. Good splits: sub problem (method families,
application areas), plus always one strand for **data, benchmarks, and infrastructure**, because no
method strand will cover provenance well. Two strands minimum, four maximum: beyond four the merge
cost exceeds the harvest gain.

### Survey agent prompt template

Fill the bracketed parts, keep the rest verbatim:

```
You are researching the state of the art in [STRAND] within [TOPIC], for a literature
survey by a senior researcher. Focus on [TIME WINDOW], weighted to the most recent 2 years.

Use the metadata APIs as your backbone: api.crossref.org, api.openalex.org,
api.semanticscholar.org, and the arXiv API. Web search is a bonus, not a dependency.

For EACH significant paper (target [N] papers), return a structured record:
- title, first author, year, venue, DOI (only if you actually resolved it)
- WHAT IT SOLVES FOR: the real task behind the benchmark, and who uses the output
- METHOD: family plus the specific architecture or algorithm
- INPUTS: data sources, modalities, named instruments or datasets
- OUTPUT: what the model emits, with shape, units, and resolution
- GROUND TRUTH: where labels came from, and how many
- METRIC and value, plus the evaluation protocol (split type, test set size)
- FUTURE WORK: what the authors themselves say should happen next, 1 or 2 sentences
- LIMITATIONS the authors admit

Hard rules: mark any field you could not confirm as [UNVERIFIED] rather than guessing.
Never fabricate a DOI. Distinguish clearly between what you verified by reading and what
you inferred. Report negative findings ("I found no work on X") explicitly, they are
valuable.
```

### Overseer prompt template

```
You are auditing a merged literature corpus on [TOPIC]. You have NOT seen how it was
collected. Independently:

1. Re resolve a random sample of [10 to 20] DOIs via api.crossref.org. Report any that
   fail or whose metadata (title, year) disagrees with the corpus record.
2. Attack every negative claim in the corpus summary ("no work exists on X") with fresh
   targeted queries. Report anything that contradicts them.
3. Sweep for internal contradictions: same paper recorded twice with different facts,
   metric values that disagree with the cited venue or year, implausible claims.
4. Answer: what is missing? Which sub field, venue, geography, or data modality does this
   corpus not cover at all?

Return findings as a correction list. Do not fix anything yourself.
```

Route every overseer finding through the coordinator: verify it, then correct the corpus or launch a
follow up mini strand. An overseer claim is itself unverified until you check it.

## Corpus schema

One row per paper in `data/papers.csv`. Every figure and every count in the report derives from this
file. Recommended columns, adapt vocabularies to the field during phase 1:

| Column | Content |
|---|---|
| `key` | citation slug, for example `smith2025socmapping` |
| `title`, `first_author`, `year`, `venue`, `doi`, `arxiv_id` | identity; `doi` verified before publication |
| `task` | controlled vocabulary, what the paper predicts or produces |
| `method_family` | controlled vocabulary: for example `classical-ML`, `CNN`, `transformer`, `foundation-SSL`, `physics-based` |
| `method_detail` | free text |
| `inputs` | pipe separated modalities and named instruments or datasets |
| `output_type` | controlled vocabulary, with units and resolution in `output_detail` |
| `ground_truth` | label source and count |
| `metric_name`, `metric_value` | headline number as reported |
| `eval_protocol` | split type: random, spatial or temporal block, cross site, forward validation |
| `evidence_level` | `full-text`, `abstract`, or `metadata`: how much you actually read |
| `peer_reviewed` | true or false: false for records that exist only as preprints. Separate axis from `evidence_level` |
| `notes` | free text, including `[UNVERIFIED]` flags |

Two principles. **Blank, not inferred**: a cell the paper does not state stays empty. **Counts trace
to the CSV**: if the report says "14 of 52 papers use spatial cross validation", that number is a
query on this file, not a recollection.

## Worked example: soil organic carbon prediction from hyperspectral imagery

A remote sensing topic, shown end to end at sketch level.

**Scope.** Topic: estimating topsoil organic carbon (SOC) from hyperspectral data, lab, field,
airborne, and spaceborne. Out of scope: SOC flux modeling, non optical sensors. Window: 2019 to
present, weighted to the last 2 years.

**Recon.** Seed via OpenAlex: reviews of soil spectroscopy plus a recent EnMAP or PRISMA SOC paper.
Taxonomy dimensions fixed early: sensor class (lab spectrometer, field, airborne such as AVIRIS or
HySpex, spaceborne such as EnMAP, PRISMA, EMIT), method family (PLSR, Cubist or random forest, 1D
CNN, transformer, spectral foundation model), evaluation protocol (random CV, spatial CV, cross site
transfer), and the metric trio common in this field: R2, RMSE in g per kg, and RPIQ.

**Strands.** (1) Spaceborne and airborne hyperspectral SOC mapping. (2) Chemometrics and deep
learning on soil spectral libraries, LUCAS, ICRAF, OSSL. (3) Data and infrastructure: spectral
libraries, their sizes and licenses, benchmark protocols, sensor status.

**What the records surface.** What they solve for: SOC stock baselines for carbon markets and soil
health policy, not laboratory curiosity. Output shape: SOC maps in g per kg at 30 m for spaceborne
work, point predictions for library work. Ground truth: LUCAS topsoil points and national soil
surveys. The validity question phase 5 must ask: random CV on a spectral library inflates skill
versus spatial CV on a mapped region, and cross site transfer numbers are far lower than within site
ones, so a single "best R2" claim is close to meaningless without the protocol column.

**Hypothesis sketch, the phase 6 shape.** "Spectral foundation models pretrained on large soil
libraries transfer to spaceborne SOC mapping with less than half the calibration data of PLSR:
supported by early library scale results `[cite]`; falsified if a matched calibration budget
comparison on EnMAP scenes shows no significant RMSE gain."

## Stopping rule

Stop harvesting when a strand's marginal query returns mostly papers you already hold, duplicates
across strands exceed roughly a third of new returns, or the corpus target is met with every
taxonomy cell either populated or confirmed empty. Confirmed empty cells are findings, record them.

## Loops: the living survey

For fast moving fields, offer the user a recurring re run. Each iteration: re harvest with the same
strand prompts, diff new `papers.csv` against the previous run by DOI, verify only the new rows,
regenerate figures, and append a dated changelog section to the report listing new papers and any
conclusion that moved. Schedule with the host's loop or scheduling facility when available; otherwise
leave a `SURVEY_STATE.md` noting the last run date and the diff command, so any future session can
resume.
