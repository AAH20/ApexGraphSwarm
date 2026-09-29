export type OrchestrationEvidence = {
  id: string;
  name: string;
  layer: string;
  role: string;
  strengths: string[];
  limits: string[];
  retrievalFit: string;
  benchmark: {status: string; description: string; source: string};
  sources: string[];
  adoption: string;
  asOf: '2026-09-27';
};

/**
 * Constant orchestrationEvidence.
 *
 *
 * @example
 * ```typescript
 * import { orchestrationEvidence } from './module';
 * ```
 */
export const orchestrationEvidence: readonly OrchestrationEvidence[] = Object.freeze([
  {
    id: 'langchain-stack',
    name: 'LangChain · LangGraph · Deep Agents',
    layer: 'Agent framework, execution runtime, and harness',
    role: 'LangChain supplies model/tool/agent building blocks; LangGraph is the low-level stateful graph runtime; Deep Agents is a higher-level harness with planning, filesystem context, subagents, skills, and approval patterns.',
    strengths: [
      'Composable deterministic and model-driven graph steps with checkpoint persistence, interrupts, streaming, and cross-thread stores.',
      'Deep Agents supports context isolation, synchronous and asynchronous delegation, tool/MCP integration, pluggable filesystem backends, and human steering.',
      'Retrieval building blocks can be composed into fixed two-step RAG or agentic retrieval workflows.',
    ],
    limits: [
      'These are distinct layers, not one ready-made fleet scheduler; production behavior depends on the chosen checkpointer/store, server, adapters, tools, and sandbox.',
      'In-memory checkpointers do not survive process restarts; checkpoints can grow and need retention. Checkpoint replay means external side effects need application-level idempotency.',
      'More model calls and context can raise latency and cost; the official pattern comparison is illustrative call/token arithmetic, not a measured speed or quality benchmark.',
    ],
    retrievalFit: 'Strong composition fit: document loaders, splitters, embedding models, vector stores, retrievers, and RAG patterns are modular. Retrieval data, authorization, freshness, and evaluation remain application responsibilities.',
    benchmark: {
      status: 'Reproducible upstream evaluation artifacts; no controlled cross-framework result established here',
      description: 'Deep Agents publishes model-backed trajectory evaluations and a Harbor/Terminal-Bench runner with task verification and JSON/LangSmith reporting. These are reproducible evaluation routes, but results depend on the pinned model, prompt, tools, tasks, and sandbox; they do not isolate LangGraph runtime throughput. The LangChain multi-agent page also contains publisher-authored example call/token counts, which are methodology illustrations rather than measurements.',
      source: 'https://github.com/langchain-ai/deepagents/tree/main/libs/evals',
    },
    sources: [
      'https://docs.langchain.com/oss/python/langgraph/overview',
      'https://docs.langchain.com/oss/python/langgraph/persistence',
      'https://docs.langchain.com/oss/python/langchain/multi-agent',
      'https://docs.langchain.com/oss/python/deepagents/overview',
      'https://docs.langchain.com/oss/python/deepagents/async-subagents',
      'https://docs.langchain.com/oss/python/deepagents/retrieval',
      'https://github.com/langchain-ai/deepagents/blob/main/libs/evals/CONTRIBUTING.md',
    ],
    adoption: 'Use LangGraph when Apex needs an explicitly programmed, resumable agent workflow; use Deep Agents when the agent harness needs delegated research/coding and filesystem context. Keep Apex as the transactional run ledger, budget reservation, and tenant boundary, and pin persistent stores and sandboxes explicitly.',
    asOf: '2026-09-27',
  },
  {
    id: 'crewai',
    name: 'CrewAI',
    layer: 'Agent framework and workflow runtime',
    role: 'Crews coordinate role/task agents with sequential or hierarchical processes; Flows add event-driven state transitions, branching, and the ability to invoke Crews for open-ended subtasks.',
    strengths: [
      'Role/task abstractions support sequential and hierarchical execution with manager-agent configuration, callbacks, and request-per-minute controls.',
      'Flows document resumable state persistence with a default SQLite backend, including resume and fork-from-state operations.',
      'Knowledge and memory APIs connect source documents, ChromaDB or Qdrant, embeddings, and semantic/recency/importance recall.',
    ],
    limits: [
      'A Crew’s manager or hierarchical process is an agent coordination pattern, not a cluster scheduler or a proof of optimal multi-agent reasoning.',
      'Flow-state persistence is not itself an externally enforced provider budget ledger, global concurrency policy, or guarantee of exactly-once external side effects.',
      'Memory, embedding, vector-store, model, tool, and deployment choices must be configured and separately costed; default memory can invoke models and embeddings.',
    ],
    retrievalFit: 'High framework-level fit: first-party Knowledge sources and a provider-neutral RAG client expose ChromaDB and Qdrant; unified memory supports semantic, recency, and importance-based recall. Apex repository-graph evidence still needs an explicit ingestion adapter and provenance policy.',
    benchmark: {
      status: 'Third-party benchmark report surfaced in upstream repository; not independently reproduced or suitable for orchestration ranking',
      description: 'A Bench’d contributor reported a CrewAI Memory run on LongMemEval v1.0 with 500 questions in an issue on the official repository. The linked result page was not independently retrievable during this review, and the post does not supply enough model/version/judge configuration here for a comparable score claim. No controlled CrewAI-versus-LangGraph orchestration benchmark was established.',
      source: 'https://github.com/crewAIInc/crewAI/issues/5800',
    },
    sources: [
      'https://docs.crewai.com/en/concepts/crews',
      'https://docs.crewai.com/en/concepts/flows',
      'https://docs.crewai.com/en/concepts/knowledge',
      'https://docs.crewai.com/en/concepts/memory',
      'https://github.com/crewAIInc/crewAI/issues/5800',
    ],
    adoption: 'Try CrewAI behind the existing fixed adapter when the team already has Crew/Flow definitions or wants its Knowledge API. Keep process admission, cross-run budgets, identity, and terminal-result reconciliation in Apex; test resume and retry behavior against real external side effects before production.',
    asOf: '2026-09-27',
  },
  {
    id: 'paperclip',
    name: 'Paperclip',
    layer: 'Business-oriented agent control plane',
    role: 'Runs an organization/task control plane: org charts and goals, issue assignment, heartbeat scheduling, adapter dispatch, budgets, approvals, workspaces, and audit trails. Agent reasoning/execution happens through external adapters.',
    strengths: [
      'The documented model separates the control plane from execution adapters and supports multiple agent runtimes.',
      'Task checkout is described as atomic and single-assignee; agent/company budgets, usage reports, approvals, and activity auditing provide governance around work.',
      'Workspaces, task documents, MCP/plugin extension points, schedules, and recovery visibility fit ongoing software/business operations.',
    ],
    limits: [
      'A manager/CEO agent that decomposes company goals is not a general swarm-search engine, capability optimizer, or mechanism for proving a group’s answer is better.',
      'Reported usage and cost events depend on adapters/heartbeats reporting provider, model, token, and cost data; budget reporting should be reconciled with provider invoices.',
      'The product control plane does not replace adapter-specific sandboxing or execution lifecycle. Dedicated knowledge retrieval is described as plugin territory in the implementation spec rather than a built-in core vector RAG service.',
    ],
    retrievalFit: 'Primarily operational context through goals, issue ancestry, comments, and work artifacts; connect an external knowledge/retrieval service through an adapter or plugin. Do not treat the organization hierarchy as a retrieval index.',
    benchmark: {
      status: 'No comparable published capacity result located; upstream Terminal-Bench loop is explicitly a non-comparable smoke workflow',
      description: 'The canonical repository includes a bounded Terminal-Bench operating skill that explicitly says its smoke/diagnosis/fix runs are non-comparable and not ranking submissions. Public performance issues are operator incident reports, not controlled capacity benchmarks: one issue documents an 11-agent, 4-vCPU deployment report against version 2026.525.0 and a heartbeat query bottleneck. Treat it as a bottleneck lead tied to that environment/version, not a general throughput claim or current-head defect.',
      source: 'https://github.com/paperclipai/paperclip/blob/master/.agents/skills/terminal-bench-loop/SKILL.md',
    },
    sources: [
      'https://github.com/paperclipai/paperclip',
      'https://github.com/paperclipai/paperclip/blob/master/docs/start/core-concepts.md',
      'https://github.com/paperclipai/paperclip/blob/master/docs/guides/board-operator/costs-and-budgets.md',
      'https://github.com/paperclipai/paperclip/blob/master/doc/SPEC.md',
      'https://github.com/paperclipai/paperclip/blob/master/.agents/skills/terminal-bench-loop/SKILL.md',
      'https://github.com/paperclipai/paperclip/issues/6947',
    ],
    adoption: 'Evaluate Paperclip as an external operator/control plane when organizational delegation, approvals, recurring heartbeats, and adapter governance are primary. Keep Apex’s transactional ledger or define a tested ownership boundary before running both schedulers; make one system authoritative for claims, cancellation, and cost settlement.',
    asOf: '2026-09-27',
  },
  {
    id: 'microsoft-agent-framework',
    name: 'Microsoft Agent Framework',
    layer: 'Agent framework and typed workflow runtime',
    role: 'Unifies agent abstractions with graph/dataflow workflow orchestration. Built-in patterns include sequential, concurrent, handoff, group chat, and Magentic manager coordination; it is a runtime for application workflows rather than an organization/task control plane.',
    strengths: [
      'Typed workflow edges, concurrent execution, streaming, human request/response gates, and optional checkpoints that can be restored into a rebuilt workflow.',
      'Provider-facing agent abstraction, middleware, tools, agent skills, RAG integrations, and self-hosted or managed hosting options.',
      'Migration guides provide explicit paths from both AutoGen and Semantic Kernel; the framework is a distinct successor/migration target, not evidence that those separate projects were one product.',
    ],
    limits: [
      'Checkpointing is opt-in and checkpoint storage must be supplied; rehydration requires the same workflow topology and executor identities. Durable persistence does not guarantee exactly-once external side effects.',
      'Session history can be local or service-managed; custom history providers are needed for database/Redis/blob persistence, and provider support for deletion differs.',
      'The framework supplies orchestration primitives, not a universal cross-agent job ledger, tenant boundary, or measured global concurrency/budget service.',
    ],
    retrievalFit: 'Good integration surface: documented RAG capability and provider packages, plus custom context/history providers. Apex graph retrieval still needs a scoped connector, evidence IDs, and independent freshness/access-control rules.',
    benchmark: {
      status: 'Not established for cross-framework orchestration performance',
      description: 'Official docs describe workflow patterns and checkpoint features but do not establish a controlled multi-framework throughput, quality, or cost comparison. Microsoft migration guides describe API changes and migration paths, not a benchmark.',
      source: 'https://learn.microsoft.com/en-us/agent-framework/workflows/orchestrations/',
    },
    sources: [
      'https://github.com/microsoft/agent-framework',
      'https://learn.microsoft.com/en-us/agent-framework/workflows/orchestrations/',
      'https://learn.microsoft.com/en-us/agent-framework/workflows/checkpoints',
      'https://learn.microsoft.com/en-us/agent-framework/agents/conversations/storage',
      'https://learn.microsoft.com/en-us/agent-framework/migration-guide/from-autogen/',
      'https://learn.microsoft.com/en-us/agent-framework/migration-guide/from-semantic-kernel/',
    ],
    adoption: 'Evaluate when typed workflows, concurrency, and a Microsoft provider/hosting path fit the deployment. Migrate AutoGen or Semantic Kernel components incrementally using their separate guides; keep Apex authoritative for durable admissions, tenant isolation, unknown-spend reconciliation, and cross-framework run records.',
    asOf: '2026-09-27',
  },
  {
    id: 'google-adk',
    name: 'Google Agent Development Kit (ADK)',
    layer: 'Cross-language agent framework and graph workflow runtime',
    role: 'ADK 2.0 combines model/tool agents, deterministic graph-based workflow nodes, prebuilt sequential/parallel/loop patterns, dynamic workflows, managed agents, and deployment/evaluation tooling across several language SDKs.',
    strengths: [
      'Graph workflows combine code, tools, and LLM agents with explicit routes and typed handoff data; human input and run resume/cancel surfaces are documented.',
      'Session and long-term MemoryService abstractions separate conversation state from searchable cross-session knowledge; choices include in-memory and managed/persistent services.',
      'The official evaluation path covers response criteria and tool-trajectory criteria, and ADK exposes model/provider integrations including local-serving options.',
    ],
    limits: [
      'In-memory session and memory services lose state on restart; durable operation depends on selecting and operating a persistent backend or managed service.',
      'ADK graph/workflow execution is not by itself a cross-tenant admission queue or provider-cost ledger. Deployment concurrency, quotas, and usage reconciliation remain infrastructure/application concerns.',
      'Evaluation tooling enables repeatable tests but does not publish a comparable, controlled ADK-versus-peer benchmark in the reviewed sources; live-model outcomes depend on model, tools, prompts, datasets, and judge criteria.',
    ],
    retrievalFit: 'Strong first-party memory and RAG fit: MemoryService supports ingestion/search, and the Python docs distinguish in-memory, Vertex AI Memory Bank, and Vertex AI RAG Memory. For Apex, repository evidence still needs stable node citations, snapshot identity, and permission-aware retrieval.',
    benchmark: {
      status: 'Reproducible evaluation tooling documented; comparative benchmark not established',
      description: 'ADK documents eval datasets, response/tool-trajectory criteria, and evaluation CLI workflows. Those are repeatable evaluation mechanisms, not an independently reproduced cross-framework performance result. Google Agents CLI examples and product capacity language are not treated as measured throughput evidence.',
      source: 'https://adk.dev/evaluate/',
    },
    sources: [
      'https://adk.dev/',
      'https://adk.dev/graphs/',
      'https://adk.dev/sessions/',
      'https://adk.dev/sessions/memory/',
      'https://adk.dev/evaluate/',
      'https://adk.dev/evaluate/criteria/',
      'https://adk.dev/agents/managed-agents/',
    ],
    adoption: 'Evaluate for explicitly routed graph workflows, multi-language support, Google Cloud deployment, or first-party MemoryService. Pin the ADK version and chosen persistence/runtime services; retain Apex as the ledger for admissions, tenancy, shared budgets, and durable cross-adapter accounting.',
    asOf: '2026-09-27',
  },
  {
    id: 'google-ax',
    name: 'Google Agent Executor (AX)',
    layer: 'Distributed task and sandbox executor',
    role: 'Declaratively provisions tasks, workspaces, and models over Agent Substrate; it is a lower-level executor/runtime, distinct from agent frameworks and business control planes.',
    strengths: [
      'Provides cluster-oriented task/workspace/model resources and task lifecycle operations, including readiness observation and suspend/resume patterns.',
      'Workspace manifests can declare MCP and skill-registry setup; model credentials are referenced as deployment secrets.',
      'Separating execution placement from Apex’s run ledger gives a plausible integration boundary if the result and cancellation contracts are completed.',
    ],
    limits: [
      'The reviewed public API is declarative gRPC/resource lifecycle rather than a one-shot JSON execute-and-return-result API.',
      'The runner contract does not make child command exit status a terminal task success signal; a result callback/artifact channel is still needed.',
      'The reviewed open-source release has no public reproducible 150,000-live-agent benchmark. Do not confuse registered agents, provisioned tasks, suspended tasks, active workers, and simultaneous model calls.',
    ],
    retrievalFit: 'Workspace MCP/skill setup can expose tools and registries, but AX does not automatically ingest Apex graph snapshots, supply vector retrieval semantics, or enforce Apex evidence permissions.',
    benchmark: {
      status: 'Not established; existing assessment found no reproducible public concurrency benchmark for the reviewed open-source release',
      description: 'The local AX assessment checks public repo/release/API contracts and separates Google architecture/product statements from capacity measurements. No cluster run or model-backed benchmark was performed for this comparison.',
      source: 'https://github.com/google/ax/tree/e70162a34037c221fe6fadefd98308c05a4ad8f3',
    },
    sources: [
      '../docs/google-ax-assessment.md',
      'https://github.com/google/ax',
      'https://github.com/google/ax/blob/main/pkg/apis/v1alpha1/ax.proto',
      'https://agentexecutor.io/',
    ],
    adoption: 'Keep AX as an optional externally operated executor below the Apex control plane. Before integration, require a pinned AX/Substrate version, private/authenticated API, idempotent task provisioning, bounded result callback, explicit cancellation semantics, and reconciled token/resource usage.',
    asOf: '2026-09-27',
  },
]);
