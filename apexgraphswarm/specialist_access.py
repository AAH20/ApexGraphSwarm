"""Opt-in, local specialist access contracts for reviewed execution snapshots.

These contracts are enforced only by ControlStore. They are not an external
IAM integration, an installed skill/tool attestation, or an execution sandbox.
"""
from __future__ import annotations

import hashlib
import json
import math
import re
import sqlite3
from typing import Any
from urllib.parse import urlsplit


class SpecialistContractError(ValueError):
    """A specialist contract, approval, or task binding is invalid."""


_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:@/-]{0,127}$")
_ACTION = re.compile(r"^[a-z][a-z0-9._:-]{0,63}$")
_SECRET = re.compile(r"(?:^|[_-])(api[_-]?key|access[_-]?token|password|secret|credential|authorization)(?:$|[_-])", re.I)
_DESIGN_FIELDS = {"schemaVersion", "id", "name", "agents", "teams", "nodes"}
_AGENT_FIELDS = {"id", "name", "role", "harnessId", "modelRef", "skills", "tools", "policy"}
_POLICY_FIELDS = {"provider", "subjectRef", "ownerRef", "tenantRef", "audience", "purpose", "actions", "resourceIds", "ttlSeconds", "maxDelegationDepth", "approvalQuorum"}
_TEAM_FIELDS = {"id", "name", "agentIds"}
_NODE_FIELDS = {"id", "label", "kind", "parentId", "teamIds", "externalRef"}
_SKILL_FIELDS = {"id", "sourceUrl", "revision", "sha256"}
_TOOL_FIELDS = {"serverId", "toolName", "gatewayId"}
_ASSIGNMENT_FIELDS = {"specialistId", "nodeId", "action", "audience", "purpose", "workerId", "principalId", "logicalAgentId", "modelId", "adapterId", "toolId", "resourceId", "mcpBinding", "expiresAt", "executionInput"}


def _canonical(value: Any, label: str, maximum: int) -> str:
    try:
        encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)
    except (TypeError, ValueError, RecursionError) as exc:
        raise SpecialistContractError(f"{label} must be bounded finite JSON data.") from exc
    if len(encoded.encode("utf-8")) > maximum:
        raise SpecialistContractError(f"{label} exceeds its size limit.")
    return encoded


def _digest(value: Any, label: str, maximum: int) -> str:
    return hashlib.sha256(_canonical(value, label, maximum).encode("utf-8")).hexdigest()


def _reject_secrets(value: Any) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if not isinstance(key, str) or key in {"__proto__", "constructor", "prototype"}:
                raise SpecialistContractError("Contract JSON contains an unsafe key.")
            if _SECRET.search(key) and not key.lower().endswith(("_ref", "-ref")):
                raise SpecialistContractError("Specialist contract data must not contain credential fields.")
            _reject_secrets(child)
    elif isinstance(value, list):
        for child in value:
            _reject_secrets(child)


def _record(value: Any, fields: set[str], label: str, required: set[str] | None = None) -> dict[str, Any]:
    required = fields if required is None else required
    if (not isinstance(value, dict) or any(not isinstance(key, str) for key in value)
            or set(value) - fields or required - set(value)):
        raise SpecialistContractError(f"{label} has missing or unsupported fields.")
    return value


def _identifier(value: Any, label: str) -> str:
    if not isinstance(value, str) or not _ID.fullmatch(value) or "://" in value or any(c in value for c in "?*[]"):
        raise SpecialistContractError(f"{label} must be a non-secret exact identifier.")
    return value


def _text(value: Any, label: str, max_length: int) -> str:
    if not isinstance(value, str) or len(value) > max_length or any(ord(char) < 32 or ord(char) == 127 for char in value):
        raise SpecialistContractError(f"{label} must be bounded text without control characters.")
    return value


def _json_hash(value: Any, label: str, max_bytes: int = 2 * 1024 * 1024) -> str:
    _reject_secrets(value)
    return _digest(value, label, max_bytes)


def initialize_specialist_schema(db: sqlite3.Connection) -> None:
    db.executescript("""
        CREATE TABLE IF NOT EXISTS specialist_approver_allowlist (
            principal_id TEXT PRIMARY KEY,
            configured_at REAL NOT NULL
        );
        CREATE TABLE IF NOT EXISTS specialist_access_contracts (
            contract_id TEXT PRIMARY KEY,
            idempotency_key TEXT NOT NULL UNIQUE,
            request_digest TEXT NOT NULL DEFAULT '',
            contract_digest TEXT NOT NULL,
            status TEXT NOT NULL,
            contract_json TEXT NOT NULL,
            created_at REAL NOT NULL,
            activated_at REAL,
            revoked_at REAL
        );
        CREATE TABLE IF NOT EXISTS specialist_contract_approvals (
            contract_id TEXT NOT NULL REFERENCES specialist_access_contracts(contract_id) ON DELETE CASCADE,
            contract_digest TEXT NOT NULL,
            principal_id TEXT NOT NULL,
            worker_id TEXT NOT NULL,
            approved_at REAL NOT NULL,
            PRIMARY KEY(contract_id,principal_id)
        );
        CREATE INDEX IF NOT EXISTS specialist_contracts_status_expiry
            ON specialist_access_contracts(status,contract_id);
    """)
    columns = {row[1] for row in db.execute("PRAGMA table_info(specialist_access_contracts)")}
    if "request_digest" not in columns:
        db.execute("ALTER TABLE specialist_access_contracts ADD COLUMN request_digest TEXT NOT NULL DEFAULT ''")


def configure_approvers(db: sqlite3.Connection, principal_ids: Any, now: float) -> dict[str, Any]:
    if not isinstance(principal_ids, list) or not 1 <= len(principal_ids) <= 64:
        raise SpecialistContractError("principalIds must contain 1 to 64 exact approver principals.")
    principals = [_identifier(value, "approver principal") for value in principal_ids]
    if len(set(principals)) != len(principals):
        raise SpecialistContractError("Approver principals must be unique.")
    prior = {row[0] for row in db.execute("SELECT principal_id FROM specialist_approver_allowlist")}
    selected = set(principals)
    changed = prior != selected
    db.execute("DELETE FROM specialist_approver_allowlist")
    db.executemany("INSERT INTO specialist_approver_allowlist(principal_id,configured_at) VALUES(?,?)",
                   [(principal, now) for principal in sorted(principals)])
    if changed:
        removed = prior - selected
        if removed:
            db.executemany("DELETE FROM specialist_contract_approvals WHERE principal_id=?",
                           [(principal,) for principal in sorted(removed)])
        # A policy-admin change requires explicit reactivation of active
        # contracts, even if the currently recorded quorum still appears met.
        db.execute("UPDATE specialist_access_contracts SET status='pending_approval',activated_at=NULL "
                   "WHERE status='active'")
    return {"approverPrincipals": sorted(principals), "count": len(principals),
            "changed": changed, "activeContractsRequireReactivation": changed}


def _validate_design(design: Any) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    _record(design, _DESIGN_FIELDS, "design")
    if design.get("schemaVersion") != 1 or type(design.get("schemaVersion")) is not int:
        raise SpecialistContractError("design.schemaVersion must be 1.")
    design_id = _identifier(design.get("id"), "design.id")
    _text(design.get("name"), "design.name", 128)
    agents, teams, nodes = design.get("agents"), design.get("teams"), design.get("nodes")
    if not isinstance(agents, list) or not 1 <= len(agents) <= 300:
        raise SpecialistContractError("design.agents must contain 1 to 300 specialists.")
    if not isinstance(teams, list) or len(teams) > 64 or not isinstance(nodes, list) or not 1 <= len(nodes) <= 300:
        raise SpecialistContractError("design teams or nodes exceed their supported bounds.")
    identifiers: set[str] = set()
    agent_by_id: dict[str, dict[str, Any]] = {}
    for agent in agents:
        _record(agent, _AGENT_FIELDS, "specialist")
        agent_id = _identifier(agent.get("id"), "specialist.id")
        if agent_id in identifiers:
            raise SpecialistContractError("Design identifiers must be globally unique.")
        identifiers.add(agent_id)
        for field in ("name", "role"):
            _text(agent.get(field), f"specialist.{field}", 256 if field == "role" else 128)
        _identifier(agent.get("harnessId"), "specialist.harnessId")
        _identifier(agent.get("modelRef"), "specialist.modelRef")
        policy = _record(agent.get("policy"), _POLICY_FIELDS, "specialist.policy")
        for field in ("subjectRef", "ownerRef", "tenantRef", "audience", "purpose"):
            _identifier(policy.get(field), f"policy.{field}")
        if (not isinstance(policy.get("provider"), str)
                or policy["provider"] not in {"agentiam-lab", "agent-jit-iam", "external"}):
            raise SpecialistContractError("specialist.policy.provider is unsupported.")
        actions, resources = policy.get("actions"), policy.get("resourceIds")
        if (not isinstance(actions, list) or len(actions) > 64
                or any(not isinstance(action, str) or not _ACTION.fullmatch(action) for action in actions)
                or len(set(actions)) != len(actions)):
            raise SpecialistContractError("specialist.policy.actions must be unique exact action identifiers.")
        if (not isinstance(resources, list) or len(resources) > 64
                or any(not isinstance(resource, str) or not _ID.fullmatch(resource) for resource in resources)
                or len(set(resources)) != len(resources)):
            raise SpecialistContractError("specialist.policy.resourceIds must be unique exact node identifiers.")
        for field, low, high in (("ttlSeconds", 1, 300), ("maxDelegationDepth", 0, 8), ("approvalQuorum", 0, 8)):
            value = policy.get(field)
            if type(value) is not int or not low <= value <= high:
                raise SpecialistContractError(f"specialist.policy.{field} is outside its supported range.")
        skills, tools = agent.get("skills"), agent.get("tools")
        if not isinstance(skills, list) or len(skills) > 32 or not isinstance(tools, list) or len(tools) > 32:
            raise SpecialistContractError("specialist skill or tool bindings exceed their supported bounds.")
        for skill in skills:
            _record(skill, _SKILL_FIELDS, "skill binding")
            _identifier(skill.get("id"), "skill.id")
            source_url = _text(skill.get("sourceUrl"), "skill.sourceUrl", 2048)
            try:
                parsed_url = urlsplit(source_url)
                if (parsed_url.scheme != "https" or not parsed_url.hostname
                        or parsed_url.username or parsed_url.password
                        or parsed_url.query or parsed_url.fragment):
                    raise ValueError("unsafe skill URL")
            except ValueError as exc:
                raise SpecialistContractError("skill.sourceUrl must be HTTPS without credentials, query, or fragment.") from exc
            _text(skill.get("revision"), "skill.revision", 256)
            if not isinstance(skill.get("sha256"), str) or not re.fullmatch(r"[a-f0-9]{64}", skill["sha256"]):
                raise SpecialistContractError("skill.sha256 must be a lowercase SHA-256 digest.")
        for tool in tools:
            _record(tool, _TOOL_FIELDS, "MCP tool binding")
            for field in _TOOL_FIELDS:
                _identifier(tool.get(field), f"MCP binding.{field}")
        skill_ids = [skill["id"] for skill in skills]
        tool_keys = [(tool["serverId"], tool["toolName"], tool["gatewayId"]) for tool in tools]
        if len(set(skill_ids)) != len(skill_ids) or len(set(tool_keys)) != len(tool_keys):
            raise SpecialistContractError("Specialist skill and MCP bindings must have unique identities.")
        agent_by_id[agent_id] = agent

    team_by_id: dict[str, dict[str, Any]] = {}
    for team in teams:
        _record(team, _TEAM_FIELDS, "team")
        team_id = _identifier(team.get("id"), "team.id")
        if team_id in identifiers:
            raise SpecialistContractError("Design identifiers must be globally unique.")
        identifiers.add(team_id)
        _text(team.get("name"), "team.name", 128)
        members = team.get("agentIds")
        if (not isinstance(members, list) or len(members) > 300
                or any(not isinstance(member, str) for member in members)
                or len(set(members)) != len(members)):
            raise SpecialistContractError("team.agentIds must be a unique list.")
        if any(member not in agent_by_id for member in members):
            raise SpecialistContractError("team references an unknown specialist.")
        team_by_id[team_id] = team

    node_by_id: dict[str, dict[str, Any]] = {}
    for node in nodes:
        _record(node, _NODE_FIELDS, "scope node")
        node_id = _identifier(node.get("id"), "node.id")
        if node_id in identifiers:
            raise SpecialistContractError("Design identifiers must be globally unique.")
        identifiers.add(node_id)
        _text(node.get("label"), "node.label", 128)
        if (not isinstance(node.get("kind"), str)
                or node["kind"] not in {"workspace", "repository", "module", "swarm", "datacenter", "rack", "fleet", "device", "iot-center"}):
            raise SpecialistContractError("scope node kind is unsupported.")
        parent = node.get("parentId")
        if parent is not None:
            _identifier(parent, "node.parentId")
        team_ids = node.get("teamIds")
        if (not isinstance(team_ids, list) or len(team_ids) > 64
                or any(not isinstance(team_id, str) for team_id in team_ids)
                or len(set(team_ids)) != len(team_ids)):
            raise SpecialistContractError("node.teamIds must be a unique list.")
        if any(team_id not in team_by_id for team_id in team_ids):
            raise SpecialistContractError("node references an unknown team.")
        _text(node.get("externalRef"), "node.externalRef", 2048)
        node_by_id[node_id] = node
    roots = [node for node in nodes if node["parentId"] is None]
    if len(roots) != 1 or roots[0]["kind"] != "workspace":
        raise SpecialistContractError("Design must have exactly one workspace root.")
    node_ids = set(node_by_id)
    if any(resource_id not in node_ids for agent in agents
           for resource_id in agent["policy"]["resourceIds"]):
        raise SpecialistContractError("Specialist policy references an unknown scope node.")
    for node in nodes:
        seen: set[str] = set()
        current = node
        while current["parentId"] is not None:
            if current["id"] in seen or current["parentId"] not in node_by_id:
                raise SpecialistContractError("Scope hierarchy is cyclic or disconnected.")
            seen.add(current["id"])
            current = node_by_id[current["parentId"]]
    return design, agent_by_id, team_by_id, node_by_id


def _normalized_assignment(design: Any, assignment: Any, db: sqlite3.Connection,
                           now: float) -> tuple[dict[str, Any], dict[str, Any]]:
    _record(assignment, _ASSIGNMENT_FIELDS, "assignment")
    specialist_id = _identifier(assignment.get("specialistId"), "assignment.specialistId")
    node_id = _identifier(assignment.get("nodeId"), "assignment.nodeId")
    agent = design[1].get(specialist_id)
    node = design[3].get(node_id)
    if not agent or not node:
        raise SpecialistContractError("Specialist and scope node must exist in the reviewed design.")
    assigned = any(specialist_id in design[2][team_id]["agentIds"] for team_id in node["teamIds"])
    if not assigned:
        raise SpecialistContractError("Specialist must be assigned through a team to this exact scope node.")
    policy = agent["policy"]
    action = assignment.get("action")
    if action not in {"read", "plan"} or action not in policy["actions"]:
        raise SpecialistContractError("Only an exact allowlisted read or plan action can be contracted.")
    if node_id not in policy["resourceIds"]:
        raise SpecialistContractError("The exact node must appear in the specialist resource allowlist.")
    audience = _identifier(assignment.get("audience"), "assignment.audience")
    purpose = _identifier(assignment.get("purpose"), "assignment.purpose")
    if audience != policy["audience"] or purpose != policy["purpose"]:
        raise SpecialistContractError("Assignment audience and purpose must exactly match policy.")
    if policy["maxDelegationDepth"] != 0:
        raise SpecialistContractError("Specialist contracts currently support delegation depth 0 only.")
    worker_id = _identifier(assignment.get("workerId"), "assignment.workerId")
    principal_id = _identifier(assignment.get("principalId"), "assignment.principalId")
    if principal_id != policy["subjectRef"]:
        raise SpecialistContractError("Assignment principal must exactly match policy.subjectRef.")
    worker = db.execute("SELECT principal_id,expires_at,revoked_at FROM workers WHERE worker_id=?",
                        (worker_id,)).fetchone()
    if not worker or worker["revoked_at"] is not None or worker["expires_at"] <= now or worker["principal_id"] != principal_id:
        raise SpecialistContractError("Assignment requires an enrolled active worker bound to that principal.")
    logical_agent_id = _identifier(assignment.get("logicalAgentId"), "assignment.logicalAgentId")
    model_id = _identifier(assignment.get("modelId"), "assignment.modelId")
    adapter_id = _identifier(assignment.get("adapterId"), "assignment.adapterId")
    tool_id = _identifier(assignment.get("toolId"), "assignment.toolId")
    resource_id = _identifier(assignment.get("resourceId"), "assignment.resourceId")
    if (adapter_id not in {"openrouter", "vllm"} or model_id != agent["modelRef"]
            or adapter_id != agent["harnessId"]):
        raise SpecialistContractError("Model and adapter must exactly match the selected specialist bindings.")
    binding = _record(assignment.get("mcpBinding"), _TOOL_FIELDS, "assignment.mcpBinding")
    for field in _TOOL_FIELDS:
        _identifier(binding.get(field), f"assignment.mcpBinding.{field}")
    if binding not in agent["tools"]:
        raise SpecialistContractError("Selected MCP binding is not declared by the specialist.")
    if tool_id != f"integration:{adapter_id}:review":
        raise SpecialistContractError("Specialist contracts currently support only the exact adapter review tool.")
    expires_at = assignment.get("expiresAt")
    if type(expires_at) not in (int, float) or not math.isfinite(float(expires_at)):
        raise SpecialistContractError("assignment.expiresAt must be a finite Unix timestamp.")
    expires_at = float(expires_at)
    if expires_at <= now or expires_at > now + policy["ttlSeconds"] or expires_at > worker["expires_at"]:
        raise SpecialistContractError("Contract expiry must fit policy TTL and enrolled worker expiry.")
    execution_input = assignment.get("executionInput")
    _record(execution_input, {"goal", "graph", "parameters"}, "assignment.executionInput")
    if not isinstance(execution_input.get("goal"), str) or not execution_input["goal"].strip() or len(execution_input["goal"]) > 2000:
        raise SpecialistContractError("executionInput.goal must contain 1 to 2000 characters.")
    if not isinstance(execution_input.get("graph"), dict) or not isinstance(execution_input.get("parameters"), dict):
        raise SpecialistContractError("executionInput requires an exact graph object and parameters object.")
    input_hash = _json_hash(execution_input, "execution input", 1024 * 1024)
    normalized = {"designId": _identifier(design[0]["id"], "design.id"),
                  "specialistId": specialist_id, "nodeId": node_id,
                  "nodeExternalRef": node["externalRef"], "action": action,
                  "audience": audience, "purpose": purpose, "workerId": worker_id,
                  "principalId": principal_id, "logicalAgentId": logical_agent_id,
                  "modelId": model_id, "adapterId": adapter_id, "toolId": tool_id,
                  "resourceId": resource_id, "mcpBinding": binding,
                  "expiresAt": expires_at, "approvalQuorum": policy["approvalQuorum"],
                  "operation": "review", "executionInput": execution_input,
                  "reviewedDesign": design[0],
                  "executionInputSha256": input_hash}
    provenance = {"designSha256": _digest(design[0], "design", 512 * 1024),
                  "skillBindingsSha256": _digest(agent["skills"], "skill bindings", 128 * 1024),
                  "mcpBindingsSha256": _digest(agent["tools"], "MCP bindings", 128 * 1024),
                  "executionInputSha256": input_hash}
    return normalized, provenance


def create_contract(db: sqlite3.Connection, *, idempotency_key: str,
                    design_input: Any, assignment_input: Any, now: float) -> dict[str, Any]:
    key = _identifier(idempotency_key, "idempotencyKey")
    design_json = _canonical(design_input, "design", 512 * 1024)
    _reject_secrets(design_input)
    assignment_json = _canonical(assignment_input, "assignment", 2 * 1024 * 1024)
    _reject_secrets(assignment_input)
    request_digest = hashlib.sha256((design_json + "\n" + assignment_json).encode("utf-8")).hexdigest()
    prior = db.execute("SELECT * FROM specialist_access_contracts WHERE idempotency_key=?", (key,)).fetchone()
    if prior:
        if not prior["request_digest"] or prior["request_digest"] != request_digest:
            raise SpecialistContractError("Contract idempotency key was reused with different content.")
        return contract_status(db, prior["contract_id"], now=now)
    validated_design = _validate_design(design_input)
    assignment, provenance = _normalized_assignment(validated_design, assignment_input, db, now)
    contract = {**assignment, **provenance}
    digest = _digest(contract, "specialist contract", 1536 * 1024)
    contract_id = hashlib.sha256((key + ":" + digest).encode("utf-8")).hexdigest()
    # Persist the exact reviewed design and execution input with the contract;
    # approvals can inspect these immutable bytes before endorsing the digest.
    db.execute("INSERT INTO specialist_access_contracts(contract_id,idempotency_key,request_digest,contract_digest,status,contract_json,created_at) VALUES(?,?,?,?,?,?,?)",
               (contract_id, key, request_digest, digest, "pending_approval", _canonical(contract, "contract", 1536 * 1024), now))
    return contract_status(db, contract_id, now=now)


def _active_approval_count(db: sqlite3.Connection, contract_row: sqlite3.Row,
                           contract: dict[str, Any], now: float) -> int:
    rows = db.execute("SELECT a.principal_id,a.worker_id,w.principal_id AS current_principal,w.expires_at,w.revoked_at "
                      "FROM specialist_contract_approvals a "
                      "JOIN specialist_approver_allowlist l ON l.principal_id=a.principal_id "
                      "JOIN workers w ON w.worker_id=a.worker_id "
                      "WHERE a.contract_id=? AND a.contract_digest=? ORDER BY a.principal_id",
                      (contract_row["contract_id"], contract_row["contract_digest"])).fetchall()
    approvers = {row["principal_id"] for row in rows
                 if row["current_principal"] == row["principal_id"]
                 and row["expires_at"] > now and row["revoked_at"] is None
                 and row["principal_id"] != contract["principalId"]}
    return len(approvers)


def approval_is_satisfied(db: sqlite3.Connection, contract_row: sqlite3.Row,
                          contract: dict[str, Any], now: float) -> bool:
    return _active_approval_count(db, contract_row, contract, now) >= contract["approvalQuorum"]


def _check_target_worker(db: sqlite3.Connection, contract: dict[str, Any], now: float) -> None:
    worker = db.execute("SELECT principal_id,expires_at,revoked_at FROM workers WHERE worker_id=?",
                        (contract["workerId"],)).fetchone()
    if (not worker or worker["principal_id"] != contract["principalId"]
            or worker["revoked_at"] is not None or worker["expires_at"] <= now):
        raise SpecialistContractError("Contract worker identity is revoked, expired, or no longer bound to its principal.")


def approve_contract(db: sqlite3.Connection, *, contract_id: str, worker_id: str,
                     credential: str | None, now: float) -> dict[str, Any]:
    contract_id = _identifier(contract_id, "contractId")
    worker_id = _identifier(worker_id, "workerId")
    contract_row = db.execute("SELECT * FROM specialist_access_contracts WHERE contract_id=?",
                              (contract_id,)).fetchone()
    if not contract_row:
        raise SpecialistContractError("Specialist contract was not found.")
    contract = json.loads(contract_row["contract_json"])
    if contract_row["status"] != "pending_approval" or contract["expiresAt"] <= now:
        raise SpecialistContractError("Only an unexpired pending contract can be approved.")
    from .identity import WorkerIdentityError, verify_credential
    try:
        worker = verify_credential(db, worker_id=worker_id, credential=credential, now=now)
    except WorkerIdentityError as exc:
        raise SpecialistContractError("Approver worker authentication failed.") from exc
    principal = worker["principal_id"]
    if principal == contract["principalId"]:
        raise SpecialistContractError("The target specialist principal cannot approve its own contract.")
    if not db.execute("SELECT 1 FROM specialist_approver_allowlist WHERE principal_id=?", (principal,)).fetchone():
        raise SpecialistContractError("Approver principal is not on the administrator allowlist.")
    db.execute("INSERT OR IGNORE INTO specialist_contract_approvals(contract_id,contract_digest,principal_id,worker_id,approved_at) VALUES(?,?,?,?,?)",
               (contract_id, contract_row["contract_digest"], principal, worker_id, now))
    return contract_status(db, contract_id, now=now)


def activate_contract(db: sqlite3.Connection, contract_id: str, now: float) -> dict[str, Any]:
    contract_id = _identifier(contract_id, "contractId")
    row = db.execute("SELECT * FROM specialist_access_contracts WHERE contract_id=?", (contract_id,)).fetchone()
    if not row:
        raise SpecialistContractError("Specialist contract was not found.")
    contract = json.loads(row["contract_json"])
    _check_target_worker(db, contract, now)
    if row["status"] == "active":
        if contract["expiresAt"] > now and approval_is_satisfied(db, row, contract, now):
            return contract_status(db, contract_id, now=now)
        raise SpecialistContractError("Active contract approval quorum is no longer valid.")
    if row["status"] != "pending_approval" or contract["expiresAt"] <= now:
        raise SpecialistContractError("Only an unexpired pending contract can be activated.")
    if not approval_is_satisfied(db, row, contract, now):
        raise SpecialistContractError("Authenticated current approver quorum has not been met.")
    db.execute("UPDATE specialist_access_contracts SET status='active',activated_at=? WHERE contract_id=?",
               (now, contract_id))
    return contract_status(db, contract_id, now=now)


def revoke_contract(db: sqlite3.Connection, contract_id: str, now: float) -> bool:
    contract_id = _identifier(contract_id, "contractId")
    row = db.execute("UPDATE specialist_access_contracts SET status='revoked',revoked_at=? "
                     "WHERE contract_id=? AND status!='revoked'", (now, contract_id))
    return row.rowcount == 1


def contract_status(db: sqlite3.Connection, contract_id: str, *, now: float | None = None) -> dict[str, Any]:
    row = db.execute("SELECT * FROM specialist_access_contracts WHERE contract_id=?", (contract_id,)).fetchone()
    if not row:
        raise SpecialistContractError("Specialist contract was not found.")
    contract = json.loads(row["contract_json"])
    approvals = db.execute("SELECT principal_id,worker_id,approved_at FROM specialist_contract_approvals "
                           "WHERE contract_id=? AND contract_digest=? ORDER BY approved_at,principal_id",
                           (contract_id, row["contract_digest"])).fetchall()
    valid_count = _active_approval_count(db, row, contract, now) if now is not None else None
    return {"contract": {"contractId": row["contract_id"], "status": row["status"],
                          **contract, "createdAt": row["created_at"],
                          "activatedAt": row["activated_at"], "revokedAt": row["revoked_at"],
                          "expired": now is not None and contract["expiresAt"] <= now,
                          "contractDigest": row["contract_digest"]},
            "approvals": [{"principalId": item["principal_id"], "workerId": item["worker_id"],
                           "approvedAt": item["approved_at"]} for item in approvals],
            "recordedApprovalCount": len(approvals), "validApprovalCount": valid_count,
            "approvalQuorum": contract["approvalQuorum"],
            "quorumSatisfied": valid_count is not None and valid_count >= contract["approvalQuorum"]}


def contract_binding(contract_id: str, contract: dict[str, Any]) -> dict[str, Any]:
    return {"contractId": contract_id, "designId": contract["designId"],
            "specialistId": contract["specialistId"], "nodeId": contract["nodeId"],
            "action": contract["action"], "audience": contract["audience"],
            "purpose": contract["purpose"], "modelId": contract["modelId"],
            "adapterId": contract["adapterId"], "toolId": contract["toolId"],
            "resourceId": contract["resourceId"],
            "designSha256": contract["designSha256"],
            "skillBindingsSha256": contract["skillBindingsSha256"],
            "mcpBindingsSha256": contract["mcpBindingsSha256"],
            "executionInputSha256": contract["executionInputSha256"]}


def bind_plan(db: sqlite3.Connection, *, contract_id: str, plan: Any,
              task_id: str, now: float) -> dict[str, Any]:
    row = db.execute("SELECT * FROM specialist_access_contracts WHERE contract_id=?", (contract_id,)).fetchone()
    if not row:
        raise SpecialistContractError("Specialist contract was not found.")
    contract = json.loads(row["contract_json"])
    if (row["status"] != "active" or contract["expiresAt"] <= now
            or not approval_is_satisfied(db, row, contract, now)):
        raise SpecialistContractError("Only an active, unexpired, currently approved contract can bind a plan.")
    _check_target_worker(db, contract, now)
    _canonical(plan, "plan", 2 * 1024 * 1024)
    if not isinstance(plan, dict) or set(plan) != {"version", "agents", "tasks"} or plan.get("version") != 1:
        raise SpecialistContractError("Plan must have the standard version 1 control shape.")
    task_id = _identifier(task_id, "taskId")
    matches = [task for task in plan["tasks"] if isinstance(task, dict) and task.get("id") == task_id]
    if len(matches) != 1:
        raise SpecialistContractError("taskId must identify exactly one plan task.")
    task = matches[0]
    payload = task.get("payload")
    if not isinstance(payload, dict):
        raise SpecialistContractError("Selected task payload must be an object.")
    _assert_task_binding(contract_id, contract, task.get("agentId"), task.get("tool"),
                         task.get("resource"), payload, task.get("specialistContractId"))
    if task.get("specialistContractId") not in (None, contract_id):
        raise SpecialistContractError("Selected task is already bound to another specialist contract.")
    bound = json.loads(_canonical(plan, "plan", 2 * 1024 * 1024))
    target = next(item for item in bound["tasks"] if item["id"] == task_id)
    target["specialistContractId"] = contract_id
    target["payload"]["specialistAccess"] = contract_binding(contract_id, contract)
    return {"plan": bound, "contractId": contract_id, "taskId": task_id,
            "executionInputSha256": contract["executionInputSha256"],
            "planBindingPerformed": True}


def _assert_task_binding(contract_id: str, contract: dict[str, Any], agent_id: Any,
                         tool_id: Any, resource_id: Any, payload: Any,
                         attached_contract_id: Any) -> None:
    if attached_contract_id not in (None, contract_id):
        raise SpecialistContractError("Task is already bound to another specialist contract.")
    if (agent_id != contract["logicalAgentId"] or tool_id != contract["toolId"]
            or resource_id != contract["resourceId"] or not isinstance(payload, dict)):
        raise SpecialistContractError("Task agent, tool, or resource does not match the specialist contract.")
    if tool_id != f"integration:{contract['adapterId']}:review" or payload.get("operation") != "review":
        raise SpecialistContractError("Specialist contracts are restricted to the exact review operation.")
    if payload.get("modelId") != contract["modelId"] or payload.get("adapterId") != contract["adapterId"]:
        raise SpecialistContractError("Task model or adapter does not match the specialist contract.")
    execution = payload.get("execution")
    if (not isinstance(execution, dict) or type(execution.get("version")) is not int
            or execution.get("version") != 1 or execution.get("operation") != "review"
            or execution.get("integrationId") != contract["adapterId"]):
        raise SpecialistContractError("Task execution must use version 1 and the exact review operation/adapter.")
    if (not isinstance(execution.get("input"), dict)
            or _json_hash(execution["input"], "task execution input") != contract["executionInputSha256"]):
        raise SpecialistContractError("Task execution input does not match the reviewed specialist snapshot.")
    binding = payload.get("specialistAccess")
    if binding is not None and binding != contract_binding(contract_id, contract):
        raise SpecialistContractError("Task specialistAccess provenance does not match the contract.")


def validate_task_contract(db: sqlite3.Connection, *, contract_id: str,
                           agent_id: str, tool_id: str | None,
                           resource_id: str | None, payload: dict[str, Any],
                           now: float, require_active: bool = True) -> tuple[sqlite3.Row, dict[str, Any]]:
    row = db.execute("SELECT * FROM specialist_access_contracts WHERE contract_id=?", (contract_id,)).fetchone()
    if not row:
        raise SpecialistContractError("Specialist contract was not found.")
    contract = json.loads(row["contract_json"])
    _check_target_worker(db, contract, now)
    if require_active and row["status"] != "active":
        raise SpecialistContractError("Specialist contract is not active.")
    if contract["expiresAt"] <= now:
        raise SpecialistContractError("Specialist contract has expired.")
    if require_active and not approval_is_satisfied(db, row, contract, now):
        raise SpecialistContractError("Specialist contract approval quorum is no longer valid.")
    _assert_task_binding(contract_id, contract, agent_id, tool_id, resource_id,
                         payload, contract_id)
    if payload.get("specialistAccess") != contract_binding(contract_id, contract):
        raise SpecialistContractError("Task must carry the contract's exact specialistAccess binding.")
    return row, contract
