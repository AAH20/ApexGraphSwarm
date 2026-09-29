# Video Script Outline: ApexGraphSwarm Solver Showcase

**Target length:** 10–12 minutes  
**Audience:** Technical practitioners who want to see the optimization kernels, scheduling experiments, and evaluation gates in action  
**Goal:** Demonstrate the four original optimization kernels, the Swarm Arena benchmark, the optimization lab experiments, and the evaluation/promotion pipeline — with real numbers and explicit boundaries.

---

## Scene 1 — What "Solver" Means Here (0:00–1:00)

**Visual:** A clean slide with the title "What 'Solver' Means in ApexGraphSwarm" and three bullet points: "Bounded exact search," "Greedy fallback," "Held-out evaluation." Cut to a shot of the `/optimization` route loading.

**Narration:**
> "ApexGraphSwarm doesn't claim to be a universal NP-hard solver. What it does is run bounded, reproducible optimization experiments against exact small-instance oracles and greedy fallbacks, with held-out evaluation gates that withhold promotion when costs are unknown. Let's see what that looks like in practice."

---

## Scene 2 — The Four Original Kernels (1:00–3:30)

**Visual:** Screen recording of the Ecosystem page (`/ecosystem`) and Architecture lab (`/ecosystem/research`). Show the kernel capability matrix. Then cut to a terminal running the optimization benchmark.

**Narration:**
> "Four original optimization kernels are pinned in the repository. Each has a distinct role."

**Kernel walkthrough:**

| Time | Kernel | Role | What to show |
|------|--------|------|--------------|
| 1:10 | `graph-rag-np-hard-kernel` | Bounded graph selection and GraphRAG optimization | Show the adapter config, the bounded snapshot input |
| 1:40 | `agentic-np-hard-kernel` | Agent/task optimization interfaces | Show the task DAG input, the assignment output |
| 2:10 | `mirofish-swarm-optimizer` | Swarm/simulation optimization | Show the simulation parameters, the objective value |
| 2:40 | `agentic-graph-swarm-kernel` | Combined graph/swarm solver | Show the combined input, the separate diagnostics |

**Narration (continued):**
> "The combined suite runs original implementations on a bounded snapshot and reports separate diagnostics and timings. Their objective values are not interchangeable benchmark scores. The source audit, capability matrix, and bottleneck analysis in the docs go deep on what each kernel can and cannot do. No universal NP-hard solver, optimality, or superiority claim follows from exposing these adapters."

---

## Scene 3 — Swarm Arena: The Five-Case Fixture (3:30–5:30)

**Visual:** Screen recording of `/arena`. Run the five-case deterministic optimization suite. Show the execution graph populating, the results table, the share link.

**Narration:**
> "The Swarm Arena is the most visible solver surface. It runs a versioned five-case synthetic optimization suite and produces a self-contained, unsigned evidence snapshot you can share or export.
>
> Let's run it. The fixture uses 300 logical agents, 600 tasks, and an active worker limit of 32. The observed peak is 32. Elapsed time on the recorded machine was about 6.3 seconds. Duplicate completions: zero. Provider calls: zero. API spend: zero dollars. Recovery checks — reopen, recovery completion, and stale-lease fencing — all recorded.
>
> Now, what does this measure? SQLite orchestration of harmless fixed tasks. It does not measure model intelligence, 300 simultaneous model calls, real infrastructure control, or superiority over another orchestration framework. Results depend on the machine and workload. Treat a shared link as unsigned evidence and rerun it before relying on it."

**On-screen text:** Key metrics overlay — 300 agents, 600 tasks, 32 workers, 6.3s, 0 duplicates, $0.

---

## Scene 4 — Optimization Lab: Experiments (5:30–8:00)

**Visual:** Screen recording of `/optimization`. Walk through each workstream: execution ledger, exact access grants, scheduling and delegation, evidence selection, coding swarm planning, evaluation and evolution, inference capacity.

**Narration:**
> "The optimization lab is where you design and run bounded experiments. Let's walk through the workstreams."

**Sub-scenes:**

| Time | Workstream | What to show | Narration |
|------|-----------|--------------|-----------|
| 5:40 | Execution ledger | Attempt identities, task/tool/resource attribution, settlement receipts | "The execution ledger shows stable attempt identities, task and tool attribution, settlement receipts, retry accounting, and unresolved liability. OpenRouter usage receipts are normalized; provider invoice reconciliation is separate." |
| 6:10 | Exact access grants | Principal/tool/resource matching, expiry, revocation, budget checks | "Access grants show principal/tool/resource matching, expiry, revocation, cumulative reserved and settled budget, and lease renewal checks. Enrolled worker credentials bind lease identity; there's no arbitrary harness sandboxing or multi-tenant identity service." |
| 6:40 | Scheduling and delegation | Dependency/model-capacity/budget/deadline constraints, bounded exact search | "Scheduling and delegation experiments run bounded exact search over dependency, model-capacity, budget, and deadline constraints. Supplied duration and cost estimates are inputs, not ground truth. Configured OpenRouter and vLLM reviews are the only model calls." |
| 7:10 | Evidence selection | Weighted coverage under token budgets, exact small-instance oracle, greedy fallback | "Evidence selection runs weighted coverage under token budgets, with an exact small-instance oracle and greedy fallback. Declared claims only — no answer-quality or complementary-evidence guarantee." |
| 7:30 | Evaluation and evolution | Versioned task splits, held-out gates, bounded greedy configuration search | "Evaluation and evolution use versioned task splits, training selection, held-out gates, and bounded local greedy configuration search against exact small-instance oracles. Synthetic coverage fixtures; unknown monetary costs withhold promotion; no generated code or deployment." |

---

## Scene 5 — Hierarchical Planning (8:00–9:30)

**Visual:** Screen recording of `/optimization?view=hierarchy`. Show the plan-only root/domain/cluster/worker hierarchy, field-weighted assignment evidence, IAM/PAM references, budget/deadline blockers.

**Narration:**
> "The hierarchical planning view lets you build a plan-only root/domain/cluster/worker hierarchy. It's a design tool, not a dispatch mechanism. You get field-weighted assignment evidence, explicit IAM/PAM references, and budget/deadline blockers. The synthetic local benchmark measures planner construction at 4, 32, 128, and 200 tasks. It does not run agents or establish scale capacity."

---

## Scene 6 — Algorithm Evolution & Sealed Fixtures (9:30–10:30)

**Visual:** Screen recording of the algorithm evolution experiment. Show the bounded synthetic candidates, the sealed fixtures, the independent evaluation path.

**Narration:**
> "The algorithm evolution experiment executes bounded synthetic candidates and preserves sealed fixtures for independent evaluation. This is the verification story: you can run the same fixture, get the same result, and check it against the sealed expectation. The recorded local fixture report includes source hashes, environment details, timings, and gate outcomes."

---

## Scene 7 — Close (10:30–11:30)

**Visual:** Return to the Swarm Arena results. Show the share link with the self-contained report, run checksum, source hashes, and measurement environment. Fade to a summary slide.

**Narration:**
> "Four kernels, a five-case arena, seven optimization workstreams, hierarchical planning, and sealed-fixture evolution. Every result is bounded, every claim is evidence-backed, and every boundary is explicit. That's the ApexGraphSwarm solver story — not a black box that claims to solve everything, but a glass box that shows you exactly what it did."

**On-screen text:** "Bounded · Reproducible · Evidence-backed"

---

## Production Notes

- **Real runs:** All screen recordings should be real runs, not mocked. The Swarm Arena and optimization lab produce real, reproducible results.
- **Numbers:** Use the actual recorded numbers from the checked-in benchmark artifacts. Do not round or approximate.
- **Pacing:** The kernel walkthrough (Scene 2) should be brisk — the audience can read the docs for depth. The Swarm Arena (Scene 3) should be the emotional peak — let the execution graph populate in real time.
- **Prerequisites:** Viewers should understand basic scheduling concepts (DAG, lease, fence). A brief glossary overlay is helpful.
