# Tutorial 2: Graph Visualization with Graph Studio

## Overview

Graph Studio is the interactive heart of ApexGraphSwarm. It renders your repository as an explorable graph with multiple view modes, filtering, dependency tracing, and layout options. This tutorial covers every major feature.

## Accessing Graph Studio

Navigate to [http://127.0.0.1:3010/graph](http://127.0.0.1:3010/graph) or click **Graph Studio** in the navigation.

## View Modes

Graph Studio supports three granularity levels:

### Module View
Shows high-level modules and their relationships. Use this to understand the top-level architecture and identify major subsystems.

### File View
Shows individual files and their import/dependency relationships. Use this to trace how source files connect.

### Symbol View
Shows functions, classes, and other symbols within files. Use this for fine-grained analysis of call graphs and declaration hierarchies.

Switch between views using the view toggle in the toolbar.

## Search and Filter

### Name/Path Search
Type in the search box to find nodes by name or file path. The search is case-insensitive and matches substrings.

### Relationship Filters
Toggle relationship types on/off:
- **Imports** — module-level import statements
- **Calls** — lexical function/method calls
- **Declarations** — symbol definitions
- **Directory** — organizational containment

### Evidence Filters
Filter by evidence quality:
- **High confidence** — AST-backed Python declarations, verified imports
- **Medium confidence** — lexical hints for JS/TS
- **Low confidence** — directory containment, file inventory only

### Directory Filters
Narrow the graph to a specific directory subtree. This is useful for focusing on a single module or package.

## Dependency Inspection

Click any node to open the inspector panel:

- **Source location** — file path and line number
- **Summary** — AI-generated or extracted description
- **Incoming edges** — what depends on this node
- **Outgoing edges** — what this node depends on
- **Evidence** — the source text or AST node that established the relationship

## Directed Path Tracing

Use the path tool to find directed routes between two nodes:

1. Select a source node (right-click or use the path tool).
2. Select a target node.
3. The graph highlights the shortest directed path, if one exists.

This is invaluable for understanding impact chains — e.g., what happens if you change a particular function.

## Layout Options

### Grouped Layout
Nodes are clustered by directory or module. This reveals the organizational structure of the codebase.

### Force Layout
A physics-based simulation that pushes nodes apart and pulls connected nodes together. The force-layout worker has a **three-second computation budget**. Use this to discover natural clusters and isolated components.

### SVG Overview
A minimap-style overview of the entire graph. Navigate by clicking or dragging the viewport rectangle.

## Fullscreen Mode

Toggle fullscreen for an immersive exploration experience. The graph resizes to fill the screen, and all controls remain accessible.

## Accessible Node List

When WebGL is unavailable (or for accessibility), the accessible node list provides a text-based alternative. Every node is listed with its label, type, and relationships. Keyboard navigation is supported.

## Export and Neo4j

### Export Graph
Export the current graph view as JSON for sharing or archival.

### Neo4j Storage
Optional Neo4j integration provides explicit save/load through server configuration. It does not continuously synchronize the graph — you must explicitly save and load.

To enable Neo4j, configure the server-side connection settings. See `docs/neo4j-store-setup.cypher` for the schema setup.

## Performance Tips

- **Narrow dense graphs** before applying force layout — the 3-second budget may not converge on very dense graphs.
- **Inspect truncation warnings** — if the graph exceeds visible bounds, some nodes/edges may be omitted.
- **Use directory filters** to focus on relevant subgraphs.
- **Prefer grouped layout** for large graphs; force layout is best for smaller, focused subgraphs.

## Common Workflows

### Understanding a New Codebase
1. Start in **module view** with grouped layout.
2. Identify the major modules and their relationships.
3. Switch to **file view** and drill into interesting modules.
4. Use **symbol view** to understand key classes and functions.
5. Trace paths between components to understand data flow.

### Impact Analysis
1. Find the symbol you plan to change.
2. Use the inspector to see all incoming edges.
3. Use **path tracing** to find all downstream dependents.
4. Filter to high-confidence evidence to focus on real dependencies.

### Dependency Cleanup
1. Search for deprecated or unused modules.
2. Check incoming edges — if none exist, the module may be safe to remove.
3. Use **directory filters** to scope the analysis to a specific package.

## Next Steps

- [Tutorial 3: Solver Kernels](03-solver-kernels.md) — Run optimization experiments on your graph.
- [Tutorial 7: Performance Tuning](07-performance-tuning.md) — Benchmark and optimize graph operations.
