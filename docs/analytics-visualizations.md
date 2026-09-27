# Analytics visualization gallery

Open `/analytics`, load a snapshot or the labeled synthetic demo, then choose
**Visualizations**. The gallery is a native React/SVG implementation inspired by
familiar BI workflows; it does not embed Microsoft Power BI or execute AppSource
packages. Microsoft's [visualization overview](https://learn.microsoft.com/en-us/power-bi/visuals/power-bi-visualizations-overview)
provides the external reference taxonomy.

## Built-in views

- Bar and column charts, stacked variants, and 100% stacked variants.
- Pie, donut, treemap, cumulative waterfall and ranked-category funnel.
- Line, area, stacked area, and line/column combination.
- Gauge with an explicit target, KPI cards, table and tool/resource pivot matrix.
- Tool-to-resource decomposition and deterministic data narrative.

Statistics retains scatter plots, latency histograms and UTC activity heatmaps.
Predictions retains the forecast and heuristic interval visualization.

Group by tool, resource or UTC day; choose attempts, successful attempts or known
cost. Temporal charts use UTC days. Stacked and combination charts use attempt
counts, with successes versus other attempts clearly distinguished. The category
slicer filters labels; the display limit is explicit and no fabricated “Other”
category fills omitted values. Proportions describe the displayed selection,
with the query-matching total before the display limit shown separately. Mark
details report both denominators where relevant; percentages are rounded to one
decimal and include numerator and denominator. Use hover, keyboard focus, or
click/tap on a mark to inspect its reported values. Decomposition and matrix
details also include the snapshot source and generation time. The underlying
table labels percentages as shares of displayed rows. Selecting a mark or table
row highlights its reported values. Export SVG for vector graphics or JSON for
chart inputs and evidence.

The decomposition and matrix expose tool/resource marks with attempts,
successful and other outcomes, known-cost subtotals, unresolved-cost row counts,
and snapshot provenance in their details. The narrative distinguishes full
snapshot KPIs from the filtered, displayed selection. These marks are
descriptive aggregates, not causal explanations.

The matrix pivots selected tools against up to 20 resources. If more resources
match, the gallery reports how many columns were omitted and shows the visible
cell subtotal separately from the selected-tools total. Missing cells mean no
returned observations for that pair; they are not measured zero-cost records.
Cost values remain known-cost subtotals. When the report is partial or has
unresolved charges, details label that incompleteness instead of treating
unknown cost as zero or total spend.
Waterfall shows cumulative positive contributions, not inferred gains/losses.
Funnel is a category distribution, not a sequence of customer conversion stages.
Known-cost charts preserve warnings about unresolved costs and capped cohorts.

## Additional data or adapters required

- Ribbon: joint category-by-time history, unavailable from separate daily and
  cohort aggregates.
- Geographic maps: validated coordinates or region identifiers plus a map
  provider contract.
- Key influencers: row-level explanatory features, a target, fitted model and
  evaluation evidence. Correlation alone is not an explanation of causes.
- R/Python/custom visuals: a reviewed isolated execution or custom-visual adapter.

These options explain their requirements in the gallery. They do not generate
fabricated outputs or silently install dependencies.

## Shared relationship graph

**Relationships** uses the same `GraphCanvas` component as Graph Studio: Sigma
WebGL, Graphology and the bounded ForceAtlas2 worker, with SVG fallback when GPU
rendering is unavailable. Search, node filtering, neighborhood inspection,
keyboard-accessible node selection and fullscreen controls operate on analytics
aggregates. Tool/resource categories are rendering categories, not repository
symbols. Edges represent recorded tool-resource activity, not causal influence
or source-code dependencies. The inspector retains attempt and known-cost totals.
