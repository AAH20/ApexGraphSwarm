# ADR-029: MCP discovery with bounded handshake subset

- Status: Accepted
- Date: 2026-09-27
- Deciders: ApexGraphSwarm maintainers

## Context

The system must support MCP (Model Context Protocol) discovery for tool integration. However, MCP is a broad protocol with multiple transports, protocol revisions, gateways, and authentication modes. The system must be explicit about what it supports and what it does not.

## Decision

**MCP discovery supports the documented handshake/HTTP subset with bounded responses.** Key characteristics:

- **Supported subset**: The documented handshake/HTTP subset and configured server profiles.
- **Bounded responses**: Discovery responses are capped in size.
- **Explicit compatibility limits**: "It is not universal support for every MCP transport, protocol revision, gateway, or authentication mode."
- **Configured server profiles**: Only pre-configured MCP servers are discovered.
- **No automatic installation**: Skills and tools are not automatically installed or executed.

**Explicit non-goals:**
- Not universal MCP support
- Not every transport or protocol revision
- Not every gateway or authentication mode
- No automatic installation of skills or tools

## Alternatives considered

1. **Full MCP support**: Would require implementing all transports, protocol revisions, and authentication modes — a massive undertaking.
2. **No MCP support**: Would simplify the system but would prevent tool integration.
3. **Automatic discovery of any MCP server**: Would be convenient but would be unsafe and unbounded.

## Consequences

- **Positive**: Bounded discovery; explicit compatibility limits; no unsafe auto-discovery.
- **Negative**: Limited to supported subset; not universal; requires configured server profiles.
- **Critical statement**: "It is not universal support for every MCP transport, protocol revision, gateway, or authentication mode."

## Related

- ADR-006 (bounded execution model)
- ADR-012 (explicit adapter pattern)
- ADR-023 (local harness runner)
