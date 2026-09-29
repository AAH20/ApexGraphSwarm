# Video Script Outline: ApexGraphSwarm Product Demo

**Target length:** 8–10 minutes  
**Audience:** Engineering leaders, platform engineers, AI/ML practitioners evaluating agentic orchestration tools  
**Goal:** Show the full workspace in action — from repository import to evaluated swarm run — so viewers understand what ApexGraphSwarm does and what it deliberately does not do.

---

## Scene 1 — Cold Open (0:00–0:45)

**Visual:** Screen recording. Terminal window. A single command runs: `python3 -m apexgraphswarm graph /path/to/repo --output /tmp/graph.json`. Progress bar ticks. Cut to browser: Graph Studio loads a dense, colorful node-link diagram of a real repository.

**Narration:**
> "You've got a codebase you barely understand, a team of AI specialists you want to dispatch, and a budget you can't blow. ApexGraphSwarm is a local-first engineering workspace that turns your repository into an evidence-backed graph, lets you design specialist teams with explicit authority, and runs bounded, measurable swarm executions — all on your machine, all reproducible."

**On-screen text:** "Local-first · Evidence-backed · Bounded"

---

## Scene 2 — The Problem (0:45–1:30)

**Visual:** Split screen. Left: a tangled `node_modules` directory listing in a terminal. Right: a generic "AI agent" dashboard with a chat box and a single "Run" button. Red ✗ marks appear over claims like "300 agents," "production scale," "universal solver."

**Narration:**
> "Most agent orchestration tools are black boxes. You get a chat interface, a vague promise of 'agents working together,' and no way to verify what actually happened, what it cost, or whether the results are trustworthy. ApexGraphSwarm takes the opposite approach: every claim is evidence-backed, every execution is recorded, and every boundary is explicit."

---

## Scene 3 — Workspace Tour (1:30–3:30)

**Visual:** Screen recording of the web app at `http://127.0.0.1:3010`. Rapid cuts through each major route.

**Narration:**
> "The workspace has twelve linked views. Let's walk through the ones that matter."

**Sub-scenes:**

| Time | Route | What to show | Narration |
|------|-------|--------------|-----------|
| 1:35 | `/` Control room | Landing page, workspace cards | "The control room is your entry point — every workspace is one click away." |
| 1:50 | `/graph` Graph Studio | Force layout, node click → source panel, evidence filter toggles, dependency neighborhood | "Graph Studio is the heart. Import a repository, explore modules, files, and symbols. Click any node to see its source, incoming and outgoing relationships, and the evidence behind each edge. Filter by evidence type — declarations, imports, lexical calls — and trace directed paths through the codebase." |
| 2:20 | `/teams` Specialist teams | Create a specialist, bind skills, assign a scope node | "Design specialist teams with precise capabilities. Each specialist gets a name, a model reference, pinned skills with SHA-256 hashes, and exact MCP tool bindings. Assign them to a scope in the graph." |
| 2:45 | `/swarm` Swarm control | Run a fixture, watch the execution graph populate | "Swarm control runs deterministic task DAGs against a durable SQLite control plane. Watch claims, leases, completions, and recovery events stream in real time." |
| 3:05 | `/delegation` Delegation & cost | Edit cost assumptions, compare model candidates | "Compare model and harness candidates side by side. Edit token rates, fanout, success rate — the unit economics update live. Unknown costs stay unknown." |
| 3:20 | `/analytics` Analytics | Load synthetic demo, show cohort charts | "Analytics gives you six linked views over recorded events — cost trends, latency distributions, cohort economics, and guarded forecasts." |

---

## Scene 4 — The Killer Feature: Evidence & Boundaries (3:30–5:00)

**Visual:** Zoom into Graph Studio. Click a function node. The source panel shows the actual code. Toggle "evidence" — edges appear/disappear with labels like `AST declaration`, `lexical call`, `unresolved`. Cut to Swarm control: a run completes, and the execution graph shows attempt receipts with micro-USD accounting.

**Narration:**
> "Here's what makes ApexGraphSwarm different. Every relationship in the graph carries evidence — where it came from, what kind of analysis produced it, and what it doesn't prove. Python gets AST-level declarations and imports. JavaScript and TypeScript get lexical hints, not compiler-complete resolution. Rust, Go, and C++ get file inventory. These aren't limitations to hide — they're boundaries to design around.
>
> And when a swarm run completes, you don't get a chat log. You get an execution graph: every task, every attempt, every lease, every receipt, every micro-USD accounted. Recovery events are recorded. Duplicate completions are zero. This is what verifiable orchestration looks like."

---

## Scene 5 — What It's Not (5:00–6:00)

**Visual:** A clean slide with three columns: "Available now," "Planned," "Not claimed." Icons and short labels.

**Narration:**
> "ApexGraphSwarm is honest about its boundaries. Specialist team designs don't yet dispatch custom teams. Data-center, Physical AI, and IoT nodes are planning scopes, not connected infrastructure controllers. There's no universal NP-hard solver, no 150,000-agent production claim, no cross-framework performance victory. What you get is a durable local foundation — SQLite-backed scheduling, explicit integration contracts, reproducible benchmarks, and a workspace where you can design, evaluate, and evolve agentic systems with your eyes open."

---

## Scene 6 — Live Run: Zero to Evaluated (6:00–8:30)

**Visual:** Full screen recording, real-time. The presenter starts from a fresh workspace.

**Narration:**
> "Let's run the whole workflow. I'll import a repository, design a two-specialist team, attach a scope, run a bounded swarm fixture, and check the evaluation gates."

**Steps:**

1. **Import** (6:10): `python3 -m apexgraphswarm graph . --output /tmp/demo-graph.json` → Import graph in Studio.
2. **Design** (6:30): Create "Code Analyst" specialist (model: Claude Code, skills: code-review, graph-analysis) and "Test Engineer" specialist (model: Codex, skills: test-generation). Assign both to the `src/` scope node.
3. **Preview authority** (7:00): Show authorization preview — `eligible-for-review` for read-only actions, `approval-required` for write actions. Export the design JSON.
4. **Run fixture** (7:20): Swarm control → run the 5-case synthetic optimization suite. Watch the execution graph populate. Point out: 300 logical agents, 32 active workers, 0 duplicate completions, $0 API spend.
5. **Evaluate** (8:00): Open Evaluation lab. Show held-out promotion gates. Point out: "Unknown costs withhold promotion." Show the checked-in benchmark artifact with source hashes and environment details.

---

## Scene 7 — Close (8:30–9:30)

**Visual:** Return to the control room. The workspace cards are now populated with the demo data. Fade to a text overlay with the repo URL and quick-start commands.

**Narration:**
> "ApexGraphSwarm is a local-first engineering workspace for repository intelligence, specialist teams, bounded swarm orchestration, evaluation, and cost-aware delegation. It's open source, Apache 2.0, and the quick start is two commands. The graph is local. The control plane is local. The evidence is local. The only thing you need to bring is your repository — and your judgment."

**On-screen text:**
```
npm --prefix apps/web ci
npm --prefix apps/web run dev
# → http://127.0.0.1:3010
```

**End card:** Repo link, docs link, "Star if it's useful."

---

## Production Notes

- **Screen recording:** Use QuickTime or OBS at 1080p. Record the terminal and browser in separate passes if possible for cleaner cuts.
- **Font:** Monospace for code/terminal, system sans-serif for UI.
- **Music:** Low, neutral background track. No vocals.
- **Captions:** Burn in or provide SRT. Technical terms (DAG, lease, micro-USD, IAM/PAM) should be spelled out on first use.
- **Pacing:** The workspace tour (Scene 3) should feel fast — 15–20 seconds per route. The live run (Scene 6) should feel deliberate — let the execution graph breathe.
