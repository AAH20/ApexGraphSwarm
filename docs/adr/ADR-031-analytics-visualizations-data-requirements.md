# ADR-031: Analytics visualizations with explicit data requirements

- Status: Accepted
- Date: 2026-09-27
- Deciders: ApexGraphSwarm maintainers

## Context

The system must provide a rich BI-style visualization gallery for analytics. However, some visualizations require data or adapters that may not be available. The system must be explicit about these requirements rather than showing misleading empty charts.

## Decision

**The visualization gallery includes explicit data requirements and adapter dependencies.** Key characteristics:

- **21 layouts × 21 styles**: The gallery covers pie/donut, bar/column variants, area/line/combo, treemap, waterfall, funnel, gauge, KPI, table, matrix, and hierarchical views.
- **Explicit missing data**: "Geographic, ribbon and model-driven visuals explain missing data/adapter requirements."
- **Accessible values**: Aggregate evidence export and revenue/overhead scenarios preserve explicit assumptions.
- **Shared renderer**: Tool/resource relationships use Graph Studio's shared WebGL renderer with fullscreen, force/grouped layouts, and SVG fallback.

## Alternatives considered

1. **Show empty charts**: Would be simpler but would be misleading.
2. **Hide unavailable visualizations**: Would be cleaner but would prevent users from understanding what data is needed.
3. **Mock data for all visualizations**: Would be more visually appealing but would be misleading.

## Consequences

- **Positive**: Clear data requirements; no misleading charts; accessible alternatives; explicit assumptions.
- **Negative**: Some visualizations are unavailable without specific data; users must understand data requirements.
- **Critical statement**: "Geographic, ribbon and model-driven visuals explain missing data/adapter requirements."

## Related

- ADR-004 (Next.js web frontend)
- ADR-015 (read-only analytics)
- ADR-022 (inference telemetry read-only)
