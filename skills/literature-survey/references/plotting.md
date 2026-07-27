# Plotting: Tufte for seaborn

Figures in the Tufte tradition: maximize the share of ink that carries data, erase everything else,
and let the caption state the finding. Write one `scripts/make_figures.py` per survey that reads
`data/papers.csv` and regenerates every figure; never hand edit an image.

## Principles, operationalized

- **Data ink.** Remove chart junk: no background shading, no heavy grids, no box around the plot.
  Despine top and right always; despine all four and use a light dotted y grid only when values must
  be read off.
- **Direct labels beat legends.** With few series, label the lines or bars directly and drop the
  legend box. Keep a legend only when direct labels would collide.
- **Small multiples beat overloading.** Two messages means two panels, never a dual axis.
- **Muted color, used sparingly.** One accent hue for the subject, gray for context. Colorblind safe
  pairs such as blue `#2a78d6` and orange `#eb6834`. Color encodes identity, never decoration.
- **Serif, small, quiet.** Modest font sizes, thin marks, generous whitespace.
- **The caption states the takeaway**, not the axes. "Only 3 of 52 papers validate forward" is a
  caption; "Papers by validation type" is a label.
- **Honesty defaults.** Bar baselines at zero. No truncated axes without a visible break and a note.
  Annotate corpus artifacts, for example a partial final year in a papers per year chart.

## Style block

Embed this at the top of the figure script (PEP 723 header for `uv run`):

```python
# /// script
# requires-python = ">=3.10"
# dependencies = ["seaborn", "matplotlib", "pandas"]
# ///
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

INK, MUTED, ACCENT, ACCENT2 = "#1a1a1a", "#8a8985", "#2a78d6", "#eb6834"

sns.set_theme(style="white", font="serif", rc={
    "figure.facecolor": "white", "axes.facecolor": "white",
    "font.size": 9, "axes.titlesize": 11, "axes.labelsize": 9,
    "text.color": INK, "axes.labelcolor": INK,
    "xtick.color": INK, "ytick.color": INK,
    "axes.edgecolor": MUTED, "axes.linewidth": 0.6,
    "xtick.major.width": 0.6, "ytick.major.width": 0.6,
    "xtick.major.size": 2.5, "ytick.major.size": 2.5,
})

def finish(ax, title=None):
    sns.despine(ax=ax)
    if title:
        ax.set_title(title, loc="left", fontweight="bold", pad=8)

def save(fig, path):
    fig.tight_layout()
    fig.savefig(path, dpi=200, bbox_inches="tight")
    plt.close(fig)
```

Usage pattern: build each figure from a fresh `pd.read_csv("data/papers.csv")` query, call
`finish(ax, ...)`, then `save(fig, "figures/NN_name.pdf")`. Save PDF (vector) for LaTeX inclusion;
save a PNG copy only if the user wants standalone images.

## The figure set

4 to 6 figures, each answering one analysis question. The usual suspects:

1. **Activity**: papers per year, method family, or venue. Horizontal bars, ordered, count labels at
   bar ends.
2. **Evolution**: method family by year, stacked bars in a single hue ramp, to show the field's
   trajectory.
3. **The comparison that is valid**: the decision relevant metric against its cost, as a scatter with
   direct labels, restricted to papers measuring it comparably; the caption states how many papers
   were excluded and why.
4. **Coverage or gap matrix**: taxonomy dimension against taxonomy dimension, counts in cells, so
   empty cells (the gaps) are visible.
5. Optionally: data provenance breakdown, or evaluation protocol share.

## Forbidden

Dual axes. Rainbow or unordered multi hue ramps for magnitude. 3D of any kind. Pie charts beyond a
two way share. Accuracy bar charts on imbalanced tasks. Legends restating a single series. Decorated
themes, gradients, shadows. Any figure whose numbers do not come from `papers.csv`.

## Final gate

Render, then look at every figure: label collisions, overflow, a colliding title, an unreadable
label, or a misleading baseline are defects even when the code ran clean. Fix and regenerate.
