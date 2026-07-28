# Non-Conformance Analysis of a Gen 3 Sensor Product

Analyzing where non-conformance (NC) cases concentrate for a field-deployed sensor product, to support the business case for a next-generation design.

## Interactive Viewer

GitHub renders the notebook with static plot images. For interactive Plotly
figures (hover, zoom, legend toggling), open it in nbviewer:

- [NC Data Analysis](https://nbviewer.org/github/stephengilbert1/nc-data-analysis/blob/main/notebooks/NC-data-analysis.ipynb)

## Background

When a deployed sensor fails to perform to specification it gets logged as a non-conformance. Each case records what went wrong, where it happened, and where it could be established, the root cause. On their own these are just support tickets. In aggregate they say something about where a product is weakest and what the next design should fix first.

This project takes the full set of NC cases for a Gen 3 sensor product and looks for structure. Which failure modes dominate. How much of the picture is actually understood versus recorded as undetermined. Whether the problems sit with the product or with particular sites. The output is a small set of charts intended for stakeholder review, feeding into the business case for the next-generation sensor.

## The finding

Unintended activation is the dominant failure mode. It accounts for roughly 70% of all NC cases. Of those, close to 38% have no determined root cause. That undetermined share is the single biggest gap in what is currently known about the product.

Leaking is the second theme. Around 73% of leaking cases trace back to one component, the rolling seal.

The cases are spread thin across the customer base. NC volume is broadly distributed across roughly 100 utility accounts rather than concentrated in a handful. That points to a product-level issue rather than a site- or customer-specific one.

## A note on the data

The analysis in this repository runs on synthetic data. The real NC records are confidential and excluded. The synthetic generator reproduces the real dataset's schema and the shape of its key distributions, so the notebook runs end to end and the charts render the same patterns, without exposing any real customer, product, or supplier information. Utility account names and transformer manufacturer names are fictional.

Because the underlying figures are synthetic, the exact percentages here demonstrate the analysis rather than report real-world quality metrics. The distributions were weighted to reproduce the same headline findings the real data produced.

## How it's put together

The notebook keeps only the narrative and the chart calls. The reusable logic lives in `src/`.

1. Ingest. The raw Salesforce CSV export is loaded and cleaned in `data_io.py`. This includes handling a cp1252/UTF-8 encoding artefact in the `Type` column that survives from the original export rather than silently dropping the affected rows.
2. Aggregate. `aggregate.py` builds the quarterly counts and the per-category breakdowns the charts run on. Quarter ordering is handled explicitly so the sort survives reformatting.
3. Chart. `plotting.py` holds the shared theme and helpers. The house style is applied through a copied Plotly template so charts stay independent of one another.
4. Export. Figures are written to `reports/figures/` via kaleido and committed as-run, so every chart renders directly on GitHub without executing the notebook.

## Visual style

The charts follow a consistent house style. Left-aligned titles, horizontal gridlines only, a warm grey and terracotta palette, and direct value labels on ranked and categorical bars in place of axis ticks. Accent colour is pinned to the category rather than to bar position, so the emphasised series stays the same colour across every chart it appears in.

## Known limitations

The large undetermined-root-cause share is a real limit on how far the conclusions can go. A failure mode that dominates the case count but is mostly unexplained tells you where to look, not what to fix.

NC data is reporting-driven. It reflects what gets logged, not necessarily all field behaviour, so absolute volumes should be read as a floor rather than a full picture.

And as above, the public figures are synthetic. They are faithful to the real distributions but should not be quoted as real-world reliability numbers.

## Structure

```
data/                        # excluded. real data confidential, synthetic data generated locally
notebooks/
  NC-data-analysis.ipynb
src/
  data_io.py                 # load and clean the raw export
  aggregate.py               # quarterly counts and category breakdowns
  plotting.py                # shared theme, ranked_bar, add_source helpers
scripts/
  generate_synthetic_data.py # builds a synthetic dataset against the real schema
outputs/
  figures/                   # exported chart PNGs, committed
requirements.txt
```

## Running it yourself

```bash
python -m venv .venv
.venv\Scripts\Activate.ps1      # Windows (PowerShell)
pip install -r requirements.txt
```

Generate the synthetic dataset, then run the notebook against it:

```bash
python scripts/generate_synthetic_data.py
```

Exporting charts to PNG needs a one-time kaleido setup:

```python
import kaleido
kaleido.get_chrome_sync()
```

## Tools

Python, pandas, Plotly Express and Graph Objects. Figures exported via kaleido. Full list in requirements.txt.
