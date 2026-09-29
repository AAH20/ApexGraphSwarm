# Video Script Outline: ApexGraphSwarm Architecture Deep Dive

**Target length:** 12–15 minutes  
**Audience:** Software architects, platform engineers, contributors who want to understand the system before extending it  
**Goal:** Explain the layered architecture — Python control plane, Next.js workspace, SQLite durability, integration adapters, and evaluation pipeline — with clear diagrams and code references.

---

## Scene 1 — The Big Picture (0:00–1:30)

**Visual:** Animated architecture diagram (Mermaid or hand-drawn SVG). Layers fade in from bottom to top: Repository → Analyzer → Snapshot → Studio → Designer → Adapters → Kernels/Services → Control Plane → Events → Evaluation.

**Narration:**
> "ApexGraphSwarm is built in layers, and each layer has a strict contract with the ones above and below it. At the bottom, a Python repository analyzer turns source code into an evidence-bearing graph snapshot. That snapshot feeds a Next.js Graph Studio, where you explore, design, and plan. Integration adapters bridge to external kernels and services. A durable SQLite control plane persists task DAGs, leases, events, and accounting. And an evaluation pipeline gates any promotion of routing or team changes. Let's go layer by layer."

**On-screen text:** Architecture diagram with labeled layers.

---

## Scene 2 — Layer 1: Repository Analyzer (1:30–3:30)

**Visual:** Code walkthrough. Show `apexgraphswarm/` package structure. Open the analyzer module. Show AST parsing for Python, lexical analysis for JS/TS, file inventory for Rust/Go/C++.

**Narration:**
> "The analyzer is pure Python 3.10+ standard library — no dependencies. For Python, it walks the AST to extract declarations, imports, and lexical calls. For JavaScript and TypeScript, it uses lexical hints — not compiler-complete semantic resolution. For Rust, Go, and C++, it produces a file inventory. Compiler-backed semantic modules are planned but not shipped.
>
> The output is a graph snapshot: nodes for modules, files, and symbols, edges for relationships, and evidence attached to every edge. The snapshot has hard bounds — 2,000 files, 10,000 symbols, 1 MB per source file by default. These are operating limits, not latency guarantees. The force-layout worker has a three-second computation budget. Narrow dense graphs and inspect truncation warnings."

**Key points to highlight:**
- Evidence types: `AST declaration`, `import`, `lexical call`, `unresolved`, `directory containment`
- Bounds: 1,800 visible nodes / 12,000 visible edges; imports up to 25,000 nodes / 100,000 edges / 15 MB
- No dynamic dispatch resolution for Python; no compiler-backed semantics for JS/TS

---

## Scene 3 — Layer 2: Graph Studio (3:30–5:30)

**Visual:** Screen recording of `/graph`. Show module/file/symbol view toggle, search, evidence filters, dependency neighborhoods, directed path tracing, force layout, fullscreen, SVG fallback.

**Narration:**
> "Graph Studio is the exploration surface. It's a Next.js app with a WebGL renderer for the node-link diagram, with an SVG overview and accessible node list as fallbacks when WebGL is unavailable.
>
> You can switch between module, file, and symbol views. Search by name or path. Filter by relationship type and evidence type. Zoom into a dependency neighborhood — all incoming and outgoing edges for a selected node. Trace directed paths through the graph. Toggle force layout for a physics-based arrangement, or grouped layout for a hierarchical view. And go fullscreen for presentations.
>
> Every edge carries its evidence. Click an edge and you'll see where it came from — which analyzer produced it, what kind of analysis, and what it doesn't prove. This is not a limitation; it's the design."

---

## Scene 4 — Layer 3: Specialist Designer & Scope Hierarchy (5:30–7:30)

**Visual:** Screen recording of `/teams`. Show the specialist editor, skill bindings, MCP tool bindings, scope hierarchy tree, authorization preview.

**Narration:**
> "The specialist designer is where you define who does what. Each specialist has a name, a precise responsibility, a model/provider reference, and a harness selection. Skills are pinned by library URL, revision, and SHA-256 hash — a recorded hash is not proof that content was fetched, verified, installed, or trusted. MCP tool bindings are exact: selecting a gateway does not grant all tools behind it.
>
> Specialists are organized into teams, and teams are assigned to scope nodes in the graph. The scope hierarchy is zoomable and searchable, with repository, module, swarm, data-center, rack, fleet, device, and IoT command-center nodes. Hierarchy membership does not imply inherited permissions — resource assignments are exact, without descendant inheritance.
>
> Authorization previews return one of three verdicts: `denied`, `approval-required`, or `eligible-for-review`. Execution remains disabled in every case. TTL intent is bounded to 1–300 seconds. Approver IDs are simulation inputs, not authenticated approvals. Administrative and physical actuation requests remain denied."

**Key points to highlight:**
- Up to 300 specialists, 64 teams, 300 scope nodes
- Up to 32 skill and 32 tool bindings per specialist
- Imports capped at 512 KiB
- Diagram renders a focused node and at most 40 direct children

---

## Scene 5 — Layer 4: SQLite Control Plane (7:30–10:00)

**Visual:** Code walkthrough of `apexgraphswarm.control.ControlStore`. Show the schema, the state machine, the lease mechanism, the event log, the accounting. Diagram the task DAG lifecycle.

**Narration:**
> "The control plane is the durability layer. `ControlStore` uses SQLite transactions to persist task DAGs, dependency-ready claims, lease tokens, fenced completion, ordered events, recovery state, and integer micro-USD accounting.
>
> Admission is strict. It rejects invalid or cyclic plans, unknown agents, unknown reservation costs, and budget overcommitment. Ambiguous external completion or spend requires reconciliation instead of automatic replay. Budget overruns are recorded and block further claims — accounting cannot reverse a charge already made by a provider.
>
> The store supports up to 300 logical agents by default, independently of its database-wide active lease cap. The default active cap is four. Swarm control runs deterministic fixtures; the existing framework-job registry has a separate lifecycle and is not made durable by this database.
>
> The state machine is simple: a task goes from `pending` to `claimed` (with a lease), to `completed` (fenced), or to `failed` (with a retry class). Recovery events are recorded — reopen, recovery completion, and stale-lease fencing. Every event is ordered and inspectable."

**Key points to highlight:**
- SQLite transactions, not a distributed queue
- Lease tokens with fencing
- Integer micro-USD accounting
- Recovery: reopen, recovery completion, stale-lease fencing
- 300 logical agents, 4 active leases (default)

---

## Scene 6 — Layer 5: Integration Adapters (10:00–12:00)

**Visual:** Diagram of adapter layer. Show the four original optimization kernels, the configured HTTP/service adapters (Cognee, MiroFish, LangGraph, CrewAI, Hermes), the optional local harness profiles (OpenManus, Understand Anything), and the MCP discovery surface.

**Narration:**
> "Adapters are explicit and bounded. The four original optimization kernels — graph-rag-np-hard-kernel, agentic-np-hard-kernel, mirofish-swarm-optimizer, and agentic-graph-swarm-kernel — run original implementations on a bounded snapshot and report separate diagnostics and timings. Their objective values are not interchangeable benchmark scores. No universal NP-hard solver, optimality, or superiority claim follows from exposing these adapters.
>
> Configured HTTP adapters for Cognee, MiroFish, LangGraph, CrewAI, and Hermes require their documented service configuration. A successful submission can still require a later status check. Optional local harness profiles for OpenManus and Understand Anything depend on separately installed applications and reviewed profiles. The local harness runner accepts allowlisted profile identifiers and bounded goals — commands, workspaces, and authentication modes are fixed server-side. It uses a loopback bearer-protected interface, a two-process cap, a 40-second limit, and bounded output. It is not an OS security sandbox.
>
> MCP discovery supports the documented handshake/HTTP subset and configured server profiles, with bounded responses and explicit compatibility limits. It is not universal support for every MCP transport, protocol revision, gateway, or authentication mode."

---

## Scene 7 — Layer 6: Evaluation & Promotion Pipeline (12:00–14:00)

**Visual:** Screen recording of `/evaluations` and `/optimization`. Show held-out gates, versioned task splits, training selection, bounded greedy configuration search.

**Narration:**
> "The evaluation pipeline is what keeps the system honest. Evaluation plans distinguish task quality, latency, throughput, cost, recovery, and constraints. Configuration evolution should pass held-out quality and budget/latency gates before promotion.
>
> The algorithm evolution experiment executes bounded synthetic candidates and preserves sealed fixtures for independent evaluation. The evaluation lab shows measured local scheduler results and lets you design held-out evaluations and evolution gates. Unknown monetary costs withhold promotion. No generated code, no deployment.
>
> Published third-party reports, documented features, proposed tests, and locally measured results have different evidence levels. The system never conflates them."

---

## Scene 8 — Close (14:00–15:00)

**Visual:** Return to the full architecture diagram. Each layer is labeled with its key contract. Fade to a summary slide.

**Narration:**
> "Six layers, each with a strict contract. The analyzer produces evidence-backed snapshots. The studio makes them explorable. The designer makes them actionable. The control plane makes them durable. The adapters make them connected. The evaluation pipeline makes them trustworthy. That's ApexGraphSwarm — not a black box, but a glass box."

**On-screen text:** "Local-first · Evidence-backed · Bounded"

---

## Production Notes

- **Diagrams:** Use the Mermaid diagram from the README as the base. Animate layer-by-layer reveals.
- **Code walkthroughs:** Use a dark theme (e.g., Monokai) with syntax highlighting. Zoom to 140% for readability.
- **Pacing:** This is a technical audience. Don't rush the control plane layer — it's the most important. The adapter layer can move faster.
- **Prerequisites:** Viewers should have read the README or watched the product demo first.
