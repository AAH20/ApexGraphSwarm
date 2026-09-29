# Video Script Outline: ApexGraphSwarm Governance Walkthrough

**Target length:** 10–12 minutes  
**Audience:** Security engineers, compliance officers, platform operators who need to understand the identity, authorization, and audit model  
**Goal:** Walk through the specialist identity model, IAM/PAM intent, authorization previews, scope hierarchy, access ledger, and the explicit boundaries around what is simulation vs. what is enforcement.

---

## Scene 1 — Why Governance Matters Here (0:00–1:00)

**Visual:** A slide with the title "Governance in ApexGraphSwarm" and a subtitle: "Design-time intent, simulation-time preview, explicit boundaries." Cut to the `/teams` route.

**Narration:**
> "ApexGraphSwarm is a design and evaluation workspace, not a production authorization boundary. But governance is still central to the design. Every specialist carries explicit identity and authority intent. Every scope assignment is exact. Every authorization preview is bounded. And the access ledger records what was designed, what was previewed, and what was deliberately not enforced. Let's walk through the model."

---

## Scene 2 — Specialist Identity Model (1:00–3:00)

**Visual:** Screen recording of `/teams`. Create a specialist. Show the identity fields: name, model/provider reference, harness selection, accountable owner, tenant, audience, purpose.

**Narration:**
> "Every specialist has an identity model. At design time, you declare: a name, a precise responsibility, a model/provider reference, a harness selection, an accountable owner, a tenant, an audience, and a purpose. These are intent fields — they describe what the specialist should be allowed to do, not what it can actually do.
>
> The designer permits up to 300 specialists, 64 teams, and 300 scope nodes, with up to 32 skill and 32 tool bindings per specialist. Imports are capped at 512 KiB. The diagram renders a focused node and at most 40 direct children; the directory provides access to other nodes. These counts describe design capacity, not concurrently running agents."

**Key points to highlight:**
- Identity fields are design-time intent, not runtime enforcement
- Accountable owner is required
- Tenant and audience are explicit
- Purpose is a free-text field, but it's part of the export

---

## Scene 3 — IAM/PAM Intent (3:00–5:00)

**Visual:** Screen recording of the IAM/PAM section in the specialist editor. Show the fields: identity, actions, resources, TTL, delegation depth, approval quorum. Show the authorization preview panel.

**Narration:**
> "The IAM/PAM intent is where you declare authority. For each specialist, you specify: exact actions, exact resources, a TTL bounded to 1–300 seconds, a delegation depth, and an approval quorum. Resource assignments are exact — there's no descendant inheritance. If a specialist is assigned to a scope node, it does not automatically have access to all nodes beneath that scope.
>
> Authorization previews return one of three verdicts: `denied`, `approval-required`, or `eligible-for-review`. Execution remains disabled in every case. Approver IDs are simulation inputs, not authenticated approvals. Administrative and physical actuation requests remain denied.
>
> This is a design and preview surface. The two original identity projects — ai-agent-identity-authorization-security and agent-jit-iam — have pinned source assessments that inform the design, but neither has been installed as a production authorization boundary in this workspace."

**On-screen text:** Three verdicts: `denied` · `approval-required` · `eligible-for-review`

---

## Scene 4 — Scope Hierarchy & Team Assignment (5:00–6:30)

**Visual:** Screen recording of the scope hierarchy in `/teams`. Show the zoomable tree: repository → module → swarm → data-center → rack → fleet → device → IoT command-center. Assign a team to a scope node.

**Narration:**
> "The scope hierarchy is where you attach authority to the graph. The tree is zoomable and searchable, with node types for repository, module, swarm, data-center, rack, fleet, device, and IoT command-center. You select a Graph Studio node and choose 'Assign a specialist swarm.' Attach it beneath the intended scope, then explicitly assign teams.
>
> Hierarchy membership does not imply inherited permissions. If you assign a team to the `src/` module, it doesn't automatically get access to `src/auth/` or `src/db/`. Each assignment is exact. The scope examples you see in the demo are unsaved design demonstrations — they do not represent connected infrastructure, live IAM grants, or dispatched custom teams."

---

## Scene 5 — Access Ledger (6:30–8:30)

**Visual:** Screen recording of the access ledger in `/optimization`. Show principal/tool/resource matching, expiry, revocation, cumulative reserved/settled budget, lease renewal checks.

**Narration:**
> "The access ledger is the audit surface. It records principal/tool/resource matching, expiry, revocation, cumulative reserved and settled budget, and lease renewal checks. Enrolled worker credentials bind lease identity — there's no arbitrary harness sandboxing or multi-tenant identity service.
>
> The ledger is inspectable. You can see every grant, every expiry, every revocation, and every budget checkpoint. This is what you'd need to reconcile against a production IAM/PAM system. The ledger doesn't enforce anything — it records what was designed and what was previewed. Enforcement requires explicit adapters and a production authorization boundary."

**Key points to highlight:**
- Ledger records design and preview, not enforcement
- Expiry and revocation are explicit
- Budget checkpoints are cumulative
- No multi-tenant identity service

---

## Scene 6 — What's Simulation vs. What's Enforcement (8:30–10:00)

**Visual:** A clean two-column slide. Left: "Simulation (available now)" — design, preview, export, ledger. Right: "Enforcement (not connected)" — custom dispatch, live IAM/PAM, authenticated approvals, production boundary.

**Narration:**
> "This is the most important slide in this video. What's simulation: specialist design, scope assignment, authorization preview, design export, access ledger. What's not connected: custom team dispatch, live IAM/PAM enforcement, authenticated approvals, production authorization boundary.
>
> The designer permits you to declare intent and preview outcomes. It does not dispatch agents. It does not enforce access. It does not authenticate approvers. The authorization preview is a design tool, not a security control. If you need enforcement, you need to build or integrate a production authorization boundary — and the docs point to the two original identity projects as starting points."

---

## Scene 7 — Close (10:00–11:00)

**Visual:** Return to the `/teams` route. Show a completed specialist design with all identity fields filled in, a scope assignment, and an authorization preview. Fade to a summary slide.

**Narration:**
> "Governance in ApexGraphSwarm is explicit about what it is and what it isn't. It's a design and evaluation surface for identity, authority, and audit. It gives you the language to declare intent, the tools to preview outcomes, and the ledger to inspect what was designed. What it doesn't do is enforce — and it says so, loudly, in every preview and every export. That's not a limitation. That's the design."

**On-screen text:** "Design-time intent · Simulation-time preview · Explicit boundaries"

---

## Production Notes

- **Tone:** This video should feel precise and sober. No hype. The audience is security and compliance — they will punish overclaiming.
- **Real data:** Use the unsaved design demonstrations from the README. Do not imply they are connected to anything live.
- **On-screen text:** The three verdicts (`denied`, `approval-required`, `eligible-for-review`) should appear as overlays when the preview panel is shown.
- **Prerequisites:** Viewers should understand basic IAM concepts (principal, action, resource, TTL). A brief glossary overlay is helpful.
