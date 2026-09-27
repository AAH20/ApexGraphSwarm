# MCP endpoint discovery

The Ecosystem workspace can discover tool declarations from a small set of server-configured MCP Streamable HTTP profiles. Discovery is read-only: the adapter negotiates a protocol version, sends `notifications/initialized`, and calls `tools/list` with bounded pagination. It never sends `tools/call`, resources, prompts, or arbitrary user-authored protocol messages.

## Configure a trusted profile

Set `MCP_SERVERS_JSON` in the Next.js server environment. The public `GET /api/ecosystem/mcp` response reports safe labels and readiness only; it does not reveal endpoint URLs or credential values. The protected `POST /api/ecosystem/mcp` accepts exactly `{ "serverId": "team-gateway" }` and uses the selected fixed profile.

```dotenv
MCP_SERVERS_JSON=[{"id":"team-gateway","label":"Team MCP Gateway","url":"https://mcp.example.net/mcp","tokenEnv":"MCP_SERVER_TEAM_GATEWAY_TOKEN"}]
MCP_SERVER_TEAM_GATEWAY_TOKEN=replace-with-a-server-side-secret
INTEGRATION_ACCESS_TOKEN=replace-with-a-separate-workspace-token
```

Profiles allow only `id`, `label`, `url`, and optional `tokenEnv`. IDs are lowercase slugs, at most eight profiles can be configured, and credentials must be referenced through environment variables named `MCP_SERVER_*_TOKEN`. Endpoint URLs are administrator-controlled, must use HTTPS (HTTP is accepted for loopback development), and cannot include URL credentials, query strings, or fragments. Redirects are rejected. Do not expose credentials through `NEXT_PUBLIC_*` variables. POST also uses the existing integration bearer-token and same-origin checks. Discovery does not make the configured MCP server's tool descriptions trustworthy; they are untrusted metadata and must be displayed as text.

## Protocol and limits

The client offers `2025-11-25` first and can negotiate the earlier stable versions `2025-06-18`, `2025-03-26`, and `2024-11-05`. It handles JSON and bounded Server-Sent Events replies. Stateful sessions carry `MCP-Session-Id`; protocol headers follow negotiation, cancellation is best-effort, and session deletion is attempted on completion. Stateless servers that omit a session are supported for this handshake.

The bounds are eight profiles, a 20-second primary discovery deadline plus up to one second for each best-effort cancellation/session-cleanup request, 1 MiB per server response, at most five `tools/list` pages, 100 returned tools, 2,048 characters per server-issued pagination cursor, and 32 KiB per tool input schema (with depth and node-count limits). A truncated result explicitly reports `pagination.truncated`. Malformed JSON-RPC, repeated cursors, invalid protocol versions, unsafe schemas, redirects, and oversized responses fail closed.

This implementation follows the stable session-based MCP lifecycle. It does not implement OAuth discovery, `stdio`, arbitrary custom headers, `tools/call`, server-side tool approval workflows, or the newer `2026-07-28` stateless lifecycle. OAuth credentials must be configured out of band as a server-side bearer token. MCP provides protocol compatibility, not tenant isolation; keep endpoint allowlists and secrets private and use trusted servers.

## References

- [MCP 2025-11-25 lifecycle](https://modelcontextprotocol.io/specification/2025-11-25/basic/lifecycle)
- [MCP 2025-11-25 transports](https://modelcontextprotocol.io/specification/2025-11-25/basic/transports)
- [MCP 2025-11-25 tools](https://modelcontextprotocol.io/specification/2025-11-25/server/tools)
- [MCP Registry documentation](https://registry.modelcontextprotocol.io/docs)
