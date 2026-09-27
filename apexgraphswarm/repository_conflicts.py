"""Repository-grounded, read-only conflict planning for committed task heads.

The planner resolves immutable Git commits and compares their trees to one
common base. It never changes refs, checks out files, invokes a provider, runs
hooks, or applies/merges a task. Declared reads are verified against the base
tree but are not runtime read traces.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import selectors
import subprocess
import time
from typing import Any, Mapping, Sequence

from .optimization import CodeTask, OptimizationInputError, plan_waves

VERSION = 1
MAX_TASKS = 32
MAX_DEPENDENCIES_PER_TASK = 32
MAX_READS_PER_TASK = 64
MAX_TOTAL_READS = 256
MAX_CHANGES_PER_TASK = 2_000
MAX_TOTAL_CHANGES = 20_000
MAX_STDOUT_BYTES = 8 * 1024 * 1024
MAX_STDERR_BYTES = 64 * 1024
MAX_GIT_CALLS = 256
MAX_TOTAL_SECONDS = 12
MAX_CALL_SECONDS = 3.0
MAX_REVISION_CHARS = 256
MAX_PATH_CHARS = 4_096
MAX_TASK_ID_CHARS = 128
TASK_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_./:@-]{0,127}$")
HEX_SHA_RE = re.compile(r"^(?:[0-9a-f]{40}|[0-9a-f]{64})$")
ZERO_SHA_RE = re.compile(r"^0+$")


class RepositoryConflictError(ValueError):
    """Invalid request, ungrounded Git input, or a reached safety bound."""


@dataclass
class _GitSession:
    repo: Path
    started: float = field(default_factory=time.monotonic)
    calls: int = 0
    last_return_code: int = 0

    @property
    def deadline(self) -> float:
        return self.started + MAX_TOTAL_SECONDS

    def run(self, *args: str, stdout_limit: int = MAX_STDOUT_BYTES,
            allowed_return_codes: tuple[int, ...] = (0,)) -> bytes:
        self.calls += 1
        if self.calls > MAX_GIT_CALLS:
            raise RepositoryConflictError("Git subprocess-count limit exceeded.")
        remaining = self.deadline - time.monotonic()
        if remaining <= 0:
            raise RepositoryConflictError("Total Git analysis time limit exceeded.")
        timeout = min(MAX_CALL_SECONDS, remaining)
        call_deadline = time.monotonic() + timeout
        environment = _git_environment()
        safe_prefix = ["git", "-c", "core.fsmonitor=false", "-c", f"core.hooksPath={os.devnull}",
                       "-c", "diff.external=", "-c", f"core.attributesFile={os.devnull}"]
        try:
            process = subprocess.Popen(
                [*safe_prefix, *args], cwd=str(self.repo), stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False,
                env=environment, close_fds=True,
            )
        except (OSError, ValueError):
            raise RepositoryConflictError("Unable to start bounded Git inspection.") from None
        assert process.stdout is not None and process.stderr is not None
        stdout_fd = process.stdout.fileno()
        selector = selectors.DefaultSelector()
        buffers: dict[int, bytearray] = {process.stdout.fileno(): bytearray(),
                                         process.stderr.fileno(): bytearray()}
        limits = {process.stdout.fileno(): stdout_limit,
                  process.stderr.fileno(): MAX_STDERR_BYTES}
        try:
            os.set_blocking(process.stdout.fileno(), False)
            os.set_blocking(process.stderr.fileno(), False)
            selector.register(process.stdout, selectors.EVENT_READ)
            selector.register(process.stderr, selectors.EVENT_READ)
            while selector.get_map():
                remaining = min(call_deadline - time.monotonic(), self.deadline - time.monotonic())
                if remaining <= 0:
                    process.kill()
                    process.wait()
                    raise RepositoryConflictError("Git command exceeded its time limit.")
                for key, _ in selector.select(min(0.1, remaining)):
                    stream = key.fileobj
                    fd = stream.fileno()
                    try:
                        chunk = os.read(fd, 65_536)
                    except BlockingIOError:
                        continue
                    if not chunk:
                        selector.unregister(stream)
                        continue
                    buffers[fd].extend(chunk)
                    if len(buffers[fd]) > limits[fd]:
                        process.kill()
                        process.wait()
                        label = "stdout" if fd == process.stdout.fileno() else "stderr"
                        raise RepositoryConflictError(f"Git {label} byte limit exceeded.")
            return_code = process.wait(timeout=max(0.01, min(remaining, self.deadline-time.monotonic())))
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()
            raise RepositoryConflictError("Git command exceeded its time limit.") from None
        finally:
            selector.close()
            process.stdout.close()
            process.stderr.close()
        self.last_return_code = return_code
        if return_code not in allowed_return_codes:
            raise RepositoryConflictError(f"Git inspection failed (exit status {return_code}).")
        return bytes(buffers[stdout_fd])


def plan_repository_conflicts(repo_path: str | os.PathLike[str], base_revision: str,
                              tasks: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """Plan safe concurrent waves from committed Git diffs and declared reads.

    `tasks` entries are strict objects with `id`, `dependencies`,
    `head_revision`, and `reads`. Writes are derived from `base_revision` to
    each pinned task head. All refs are resolved before diffing, and every head
    must descend from the common base.
    """
    normalized_base, normalized_tasks = _validate_request(base_revision, tasks)
    try:
        repo = Path(repo_path).expanduser().resolve(strict=True)
    except (OSError, RuntimeError, TypeError):
        raise RepositoryConflictError("Repository path must identify an existing directory.") from None
    if not repo.is_dir():
        raise RepositoryConflictError("Repository path must identify a directory.")
    session = _GitSession(repo)
    try:
        root = session.run("rev-parse", "--show-toplevel").rstrip(b"\n").decode("utf-8", errors="strict")
    except UnicodeDecodeError:
        raise RepositoryConflictError("Repository root path is not valid UTF-8.") from None
    session.repo = Path(root).resolve(strict=True)
    unmerged = session.run("ls-files", "--unmerged", "-z", stdout_limit=MAX_STDERR_BYTES)
    if unmerged:
        raise RepositoryConflictError("Unmerged index entries are unsupported; committed trees remain unchanged.")
    base_sha = _resolve_commit(session, normalized_base)
    base_tree = _resolve_tree(session, base_sha)
    resolved_heads: dict[str, tuple[str, str]] = {}
    for task in normalized_tasks:
        head_sha = _resolve_commit(session, task["head_revision"])
        session.run("merge-base", "--is-ancestor", base_sha, head_sha,
                    allowed_return_codes=(0, 1))
        ancestor = session.last_return_code
        if ancestor != 0:
            if ancestor == 1:
                raise RepositoryConflictError(f"Task {task['id']!r} head is not descended from the common base.")
            raise RepositoryConflictError("Unable to verify base ancestry for a task head.")
        resolved_heads[task["id"]] = (head_sha, _resolve_tree(session, head_sha))

    declared_read_paths = sorted({path for task in normalized_tasks for path in task["reads"]})
    if len(declared_read_paths) > MAX_TOTAL_READS:
        raise RepositoryConflictError(f"Declared reads exceed the {MAX_TOTAL_READS}-path total bound.")
    read_records = _read_base_paths(session, base_sha, declared_read_paths)
    reads_by_task: dict[str, list[dict[str, Any]]] = {}
    for task in normalized_tasks:
        reads_by_task[task["id"]] = [dict(read_records[path]) for path in task["reads"]]

    task_results: list[dict[str, Any]] = []
    writes_by_task: dict[str, tuple[str, ...]] = {}
    total_changes = 0
    for task in normalized_tasks:
        head_sha, head_tree = resolved_heads[task["id"]]
        statuses = _diff_name_status(session, base_sha, head_sha)
        raw = _diff_raw(session, base_sha, head_sha)
        entries = _reconcile_diffs(statuses, raw)
        if len(entries) > MAX_CHANGES_PER_TASK:
            raise RepositoryConflictError(f"Task {task['id']!r} exceeds the {MAX_CHANGES_PER_TASK}-change limit.")
        total_changes += len(entries)
        if total_changes > MAX_TOTAL_CHANGES:
            raise RepositoryConflictError(f"Total changes exceed the {MAX_TOTAL_CHANGES}-change bound.")
        writes = [record for entry in entries for record in entry["writes"]]
        task_writes = tuple(sorted({record["path"] for record in writes}))
        writes_by_task[task["id"]] = task_writes
        change_digest = _digest(entries)
        task_results.append({
            "id": task["id"], "dependencies": list(task["dependencies"]),
            "headRevision": task["head_revision"], "resolvedCommit": head_sha,
            "treeObjectId": head_tree,
            "declaredReads": reads_by_task[task["id"]],
            "readEvidence": "declared_and_verified_at_base_not_runtime_trace",
            "writes": writes, "changeRecords": entries,
            "changeSha256": change_digest,
        })

    conflicts = _find_conflicts(normalized_tasks, writes_by_task)
    effective_tasks = _serialize_conflicts(normalized_tasks, conflicts)
    try:
        waves = plan_waves(effective_tasks)
    except OptimizationInputError as exc:
        raise RepositoryConflictError(f"Invalid dependency or conflict wave plan: {exc}") from exc
    source = {"baseRevision": normalized_base,
              "tasks": [{"id": task["id"], "dependencies": list(task["dependencies"]),
                         "headRevision": task["head_revision"], "reads": list(task["reads"])}
                        for task in normalized_tasks]}
    body = {
        "version": VERSION, "source": source,
        "base": {"requestedRevision": normalized_base, "resolvedCommit": base_sha,
                 "treeObjectId": base_tree,
                 "objectFormat": "sha256" if len(base_sha) == 64 else "sha1"},
        "tasks": task_results,
        "conflicts": conflicts,
        "waves": [list(wave) for wave in waves.waves],
        "algorithm": "committed-diff-with-prefix-aware-dependency-frontiers",
        "limits": [
            f"at most {MAX_TASKS} tasks, {MAX_TOTAL_READS} declared reads, and {MAX_TOTAL_CHANGES} total change records",
            "writes are committed base-to-head paths; rename and copy include both endpoints conservatively",
            "file conflicts include exact and ancestor/descendant path overlap; unordered pairs are serialized by task ID",
            "declared reads are checked against the base tree but are not measured runtime read traces",
            "working-tree and untracked changes are ignored; only resolved committed trees are analyzed",
            "plans do not checkout, reset, fetch, execute hooks/commands, merge, or apply task changes",
        ],
        "metadata": {"readOnly": True, "changesApplied": False,
                     "workingTreeIgnored": True, "unmergedIndexRejected": True,
                     "gitCallCount": session.calls,
                     "gitElapsedSeconds": time.monotonic() - session.started,
                     "stdoutLimitBytesPerCall": MAX_STDOUT_BYTES,
                     "stderrLimitBytesPerCall": MAX_STDERR_BYTES,
                     "totalTimeLimitSeconds": MAX_TOTAL_SECONDS},
    }
    body["inputDigest"] = _digest({"source": source, "resolvedBase": body["base"],
                                   "resolvedTasks": task_results})
    body["planDigest"] = _stable_plan_digest(body)
    return body


def verify_repository_conflict_plan(repo_path: str | os.PathLike[str],
                                   supplied_plan: Mapping[str, Any]) -> dict[str, Any]:
    """Re-resolve the supplied refs and report whether a grounded plan is stale."""
    if not isinstance(supplied_plan, Mapping) or supplied_plan.get("version") != VERSION:
        raise RepositoryConflictError("supplied plan has an unsupported version or shape.")
    source = supplied_plan.get("source")
    if not isinstance(source, dict) or set(source) != {"baseRevision", "tasks"}:
        raise RepositoryConflictError("supplied plan has no strict source revision record.")
    if not isinstance(source["tasks"], list):
        raise RepositoryConflictError("supplied plan source tasks must be a list.")
    source_tasks = []
    for index, task in enumerate(source["tasks"]):
        if not isinstance(task, dict) or set(task) != {"id", "dependencies", "headRevision", "reads"}:
            raise RepositoryConflictError(f"supplied plan source task {index} has an invalid shape.")
        source_tasks.append({"id": task["id"], "dependencies": task["dependencies"],
                             "head_revision": task["headRevision"], "reads": task["reads"]})
    stored_input_digest = supplied_plan.get("inputDigest")
    stored_plan_digest = supplied_plan.get("planDigest")
    if not _valid_digest(stored_input_digest) or not _valid_digest(stored_plan_digest):
        raise RepositoryConflictError("supplied plan digests are invalid.")
    stored_plan_valid = _stable_plan_digest(supplied_plan) == stored_plan_digest
    fresh = plan_repository_conflicts(repo_path, source["baseRevision"], source_tasks)
    semantic_match = _stable_plan_digest(supplied_plan) == fresh["planDigest"]
    stale = (not stored_plan_valid or stored_input_digest != fresh["inputDigest"]
             or not semantic_match)
    return {
        "status": "stale" if stale else "current",
        "stale": stale,
        "storedPlanDigestValid": stored_plan_valid,
        "semanticPlanMatchesCurrent": semantic_match,
        "storedInputDigest": stored_input_digest,
        "currentInputDigest": fresh["inputDigest"],
        "storedPlanDigest": stored_plan_digest,
        "currentPlanDigest": fresh["planDigest"],
        "currentBaseCommit": fresh["base"]["resolvedCommit"],
        "currentHeadCommits": {task["id"]: task["resolvedCommit"] for task in fresh["tasks"]},
    }


def _validate_request(base_revision: Any,
                      tasks: Any) -> tuple[str, list[dict[str, Any]]]:
    base = _revision(base_revision, "base_revision")
    if not isinstance(tasks, (list, tuple)) or not 1 <= len(tasks) <= MAX_TASKS:
        raise RepositoryConflictError(f"tasks must be a list of 1 to {MAX_TASKS} task objects.")
    normalized: list[dict[str, Any]] = []
    seen: set[str] = set()
    total_reads = 0
    for index, raw in enumerate(tasks):
        if not isinstance(raw, Mapping) or set(raw) - {"id", "dependencies", "head_revision", "reads"}:
            raise RepositoryConflictError(f"tasks[{index}] has unsupported fields or is not an object.")
        if not {"id", "head_revision"} <= set(raw):
            raise RepositoryConflictError(f"tasks[{index}] requires id and head_revision.")
        task_id = raw["id"]
        if not isinstance(task_id, str) or not TASK_ID_RE.fullmatch(task_id):
            raise RepositoryConflictError(f"tasks[{index}].id must be a stable identifier.")
        if task_id in seen:
            raise RepositoryConflictError("task IDs must be unique.")
        seen.add(task_id)
        head = _revision(raw["head_revision"], f"tasks[{index}].head_revision")
        dependencies = _string_list(raw.get("dependencies", []), f"tasks[{index}].dependencies",
                                    MAX_DEPENDENCIES_PER_TASK)
        if task_id in dependencies or len(set(dependencies)) != len(dependencies):
            raise RepositoryConflictError(f"Task {task_id!r} has duplicate or self dependencies.")
        reads = _string_list(raw.get("reads", []), f"tasks[{index}].reads", MAX_READS_PER_TASK)
        normalized_reads = [_canonical_path(path, f"tasks[{index}].reads") for path in reads]
        if len(set(normalized_reads)) != len(normalized_reads):
            raise RepositoryConflictError(f"Task {task_id!r} reads contain duplicate or aliased paths.")
        total_reads += len(normalized_reads)
        normalized.append({"id": task_id, "dependencies": dependencies,
                           "head_revision": head, "reads": normalized_reads})
    for task in normalized:
        missing = set(task["dependencies"]) - seen
        if missing:
            raise RepositoryConflictError(f"Task {task['id']!r} has missing dependencies.")
    if total_reads > MAX_TOTAL_READS:
        raise RepositoryConflictError(f"Declared reads exceed the {MAX_TOTAL_READS}-path total bound.")
    return base, normalized


def _revision(value: Any, label: str) -> str:
    if (not isinstance(value, str) or not value or len(value) > MAX_REVISION_CHARS
            or value.startswith("-") or any(ord(char) < 33 or ord(char) == 127 for char in value)
            or "\x00" in value):
        raise RepositoryConflictError(f"{label} must be a bounded, non-option Git revision token.")
    return value


def _string_list(value: Any, label: str, maximum: int) -> list[str]:
    if not isinstance(value, (list, tuple)) or len(value) > maximum:
        raise RepositoryConflictError(f"{label} must be a list of at most {maximum} strings.")
    if any(not isinstance(item, str) for item in value):
        raise RepositoryConflictError(f"{label} must contain only strings.")
    return list(value)


def _canonical_path(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value or len(value) > MAX_PATH_CHARS:
        raise RepositoryConflictError(f"{label} paths must be non-empty relative Git paths.")
    if value.startswith("/") or "\\" in value or "\x00" in value:
        raise RepositoryConflictError(f"{label} contains an absolute or platform-ambiguous path.")
    parts = value.split("/")
    if any(part in {"", ".", ".."} for part in parts):
        raise RepositoryConflictError(f"{label} contains a non-canonical or traversing path.")
    normalized = PurePosixPath(value).as_posix()
    if normalized != value:
        raise RepositoryConflictError(f"{label} path is not canonical.")
    return normalized


def _decode_git_path(raw: bytes) -> str:
    try:
        path = raw.decode("utf-8", errors="strict")
    except UnicodeDecodeError:
        raise RepositoryConflictError("Git path is not valid UTF-8; refusing ambiguous path identity.") from None
    return _canonical_path(path, "Git")


def _resolve_commit(session: _GitSession, revision: str) -> str:
    raw = session.run("rev-parse", "--verify", "--end-of-options", f"{revision}^{{commit}}")
    sha = raw.decode("ascii", errors="strict").strip()
    if not HEX_SHA_RE.fullmatch(sha):
        raise RepositoryConflictError("Git returned an unsupported commit object ID.")
    return sha


def _resolve_tree(session: _GitSession, commit_sha: str) -> str:
    raw = session.run("rev-parse", "--verify", f"{commit_sha}^{{tree}}")
    sha = raw.decode("ascii", errors="strict").strip()
    if not HEX_SHA_RE.fullmatch(sha):
        raise RepositoryConflictError("Git returned an unsupported tree object ID.")
    return sha


def _git_environment() -> dict[str, str]:
    environment = {key: value for key, value in os.environ.items()
                   if not key.startswith("GIT_")}
    environment.update({"GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": os.devnull,
                        "GIT_OPTIONAL_LOCKS": "0", "GIT_TERMINAL_PROMPT": "0",
                        "GIT_NO_LAZY_FETCH": "1", "GIT_NO_REPLACE_OBJECTS": "1",
                        "GIT_ATTR_NOSYSTEM": "1", "LC_ALL": "C"})
    return environment


def _semantic_plan_projection(plan: Mapping[str, Any]) -> dict[str, Any]:
    """Fields grounded in Git or deterministic planning, excluding timings."""
    keys = ("version", "source", "base", "tasks", "conflicts", "waves",
            "algorithm", "limits", "inputDigest")
    return {key: plan.get(key) for key in keys}


def _stable_plan_digest(plan: Mapping[str, Any]) -> str:
    """Hash stable semantics only; subprocess counts/timing are observations."""
    stable = dict(_semantic_plan_projection(plan))
    metadata = plan.get("metadata")
    if isinstance(metadata, Mapping):
        stable["metadata"] = {key: metadata.get(key) for key in
                               ("readOnly", "changesApplied", "workingTreeIgnored", "unmergedIndexRejected",
                                "stdoutLimitBytesPerCall", "stderrLimitBytesPerCall", "totalTimeLimitSeconds")}
    else:
        stable["metadata"] = None
    return _digest(stable)


def _diff_name_status(session: _GitSession, base: str, head: str) -> list[dict[str, Any]]:
    raw = session.run("diff", "--name-status", "-z", "--no-ext-diff", "--no-textconv",
                      "--find-renames", "--find-copies", "--find-copies-harder",
                      base, head, "--")
    tokens = raw.split(b"\x00")
    if tokens and tokens[-1] == b"":
        tokens.pop()
    rows = []
    index = 0
    while index < len(tokens):
        status = tokens[index].decode("ascii", errors="strict")
        index += 1
        if not status or status[0] not in {"A", "C", "D", "M", "R", "T"}:
            raise RepositoryConflictError("Git diff returned an unsupported change status.")
        endpoint_count = 2 if status[0] in {"R", "C"} else 1
        if index + endpoint_count > len(tokens):
            raise RepositoryConflictError("Git name-status output is truncated.")
        paths = [_decode_git_path(tokens[index + offset]) for offset in range(endpoint_count)]
        index += endpoint_count
        rows.append({"status": status, "paths": paths})
        if len(rows) > MAX_CHANGES_PER_TASK:
            raise RepositoryConflictError("Git change-record limit exceeded.")
    return rows


def _diff_raw(session: _GitSession, base: str, head: str) -> list[dict[str, Any]]:
    raw = session.run("diff", "--raw", "--no-abbrev", "-z", "--no-ext-diff", "--no-textconv",
                      "--find-renames", "--find-copies", "--find-copies-harder",
                      base, head, "--")
    tokens = raw.split(b"\x00")
    if tokens and tokens[-1] == b"":
        tokens.pop()
    rows = []
    index = 0
    while index < len(tokens):
        header = tokens[index].decode("ascii", errors="strict")
        index += 1
        parts = header.split()
        if len(parts) != 5 or not parts[0].startswith(":"):
            raise RepositoryConflictError("Git raw diff output is malformed.")
        old_mode, new_mode, old_sha, new_sha, status = parts[0][1:], parts[1], parts[2], parts[3], parts[4]
        endpoint_count = 2 if status[0] in {"R", "C"} else 1
        if index + endpoint_count > len(tokens):
            raise RepositoryConflictError("Git raw diff output is truncated.")
        paths = [_decode_git_path(tokens[index + offset]) for offset in range(endpoint_count)]
        index += endpoint_count
        if not all(re.fullmatch(r"[0-7]{6}", mode) for mode in (old_mode, new_mode)):
            raise RepositoryConflictError("Git returned an unsupported file mode.")
        if old_mode == "160000" or new_mode == "160000":
            raise RepositoryConflictError("Git submodule paths are unsupported for repository conflict planning.")
        if (not ZERO_SHA_RE.fullmatch(old_sha) and not HEX_SHA_RE.fullmatch(old_sha)) or (
                not ZERO_SHA_RE.fullmatch(new_sha) and not HEX_SHA_RE.fullmatch(new_sha)):
            raise RepositoryConflictError("Git returned an unsupported blob object ID.")
        rows.append({"status": status, "paths": paths,
                     "oldMode": None if old_mode == "000000" else old_mode,
                     "newMode": None if new_mode == "000000" else new_mode,
                     "oldSha": None if ZERO_SHA_RE.fullmatch(old_sha) else old_sha,
                     "newSha": None if ZERO_SHA_RE.fullmatch(new_sha) else new_sha})
        if len(rows) > MAX_CHANGES_PER_TASK:
            raise RepositoryConflictError("Git raw change-record limit exceeded.")
    return rows


def _reconcile_diffs(statuses: list[dict[str, Any]], raw_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if [(row["status"], row["paths"]) for row in statuses] != [
            (row["status"], row["paths"]) for row in raw_rows]:
        raise RepositoryConflictError("Git name-status and raw diff paths did not reconcile.")
    entries = []
    for row in raw_rows:
        status = row["status"]
        paths = row["paths"]
        if status[0] == "R":
            writes = [
                _write_record(paths[0], status, "rename_from", row["oldMode"], None, row["oldSha"], None),
                _write_record(paths[1], status, "rename_to", None, row["newMode"], None, row["newSha"]),
            ]
        elif status[0] == "C":
            writes = [
                _write_record(paths[0], status, "copy_source_conservative", row["oldMode"], row["oldMode"], row["oldSha"], row["oldSha"]),
                _write_record(paths[1], status, "copy_to", None, row["newMode"], None, row["newSha"]),
            ]
        else:
            writes = [_write_record(paths[0], status, "changed_path", row["oldMode"], row["newMode"],
                                    row["oldSha"], row["newSha"])]
        entries.append({"status": status, "paths": paths, "writes": writes})
    return entries


def _write_record(path: str, status: str, endpoint: str,
                  before_mode: str | None, after_mode: str | None,
                  before_sha: str | None, after_sha: str | None) -> dict[str, Any]:
    return {"path": path, "status": status, "endpoint": endpoint,
            "beforeMode": before_mode, "afterMode": after_mode,
            "beforeBlobObjectId": before_sha, "afterBlobObjectId": after_sha}


def _read_base_paths(session: _GitSession, base_sha: str,
                     paths: Sequence[str]) -> dict[str, dict[str, Any]]:
    if not paths:
        return {}
    pathspecs = [f":(literal){path}" for path in paths]
    raw = session.run("ls-tree", "-r", "-z", "--full-tree", base_sha, "--", *pathspecs)
    records: dict[str, dict[str, Any]] = {}
    tokens = raw.split(b"\x00")
    if tokens and tokens[-1] == b"":
        tokens.pop()
    for token in tokens:
        try:
            header, path_bytes = token.split(b"\t", 1)
            mode_bytes, object_type_bytes, object_sha_bytes = header.split(b" ", 2)
            mode, object_type, object_sha = (mode_bytes.decode("ascii"), object_type_bytes.decode("ascii"),
                                             object_sha_bytes.decode("ascii"))
        except (ValueError, UnicodeDecodeError):
            raise RepositoryConflictError("Git base-tree read metadata is malformed.") from None
        path = _decode_git_path(path_bytes)
        if mode == "160000" or object_type == "commit":
            raise RepositoryConflictError("Declared reads through a submodule are unsupported.")
        if object_type != "blob" or mode == "120000":
            raise RepositoryConflictError("Declared reads must resolve to regular Git blobs; symlinks are unsupported.")
        if not HEX_SHA_RE.fullmatch(object_sha):
            raise RepositoryConflictError("Git returned an unsupported read blob object ID.")
        records[path] = {"path": path, "mode": mode, "blobObjectId": object_sha}
    missing = set(paths) - records.keys()
    if missing:
        raise RepositoryConflictError(f"Declared reads are missing from the base tree: {sorted(missing)!r}.")
    return records


def _path_overlap(left: str, right: str) -> bool:
    return left == right or left.startswith(right + "/") or right.startswith(left + "/")


def _find_conflicts(tasks: Sequence[Mapping[str, Any]],
                    writes_by_task: Mapping[str, Sequence[str]]) -> list[dict[str, Any]]:
    by_id = {task["id"]: task for task in tasks}
    edges = {task["id"]: set(task["dependencies"]) for task in tasks}

    def ancestors(task_id: str) -> set[str]:
        seen: set[str] = set()
        stack = list(edges[task_id])
        while stack:
            current = stack.pop()
            if current not in seen:
                seen.add(current)
                stack.extend(edges[current])
        return seen

    result = []
    ids = sorted(by_id)
    for index, first_id in enumerate(ids):
        first = by_id[first_id]
        first_writes = tuple(writes_by_task[first_id])
        first_reads = tuple(first["reads"])
        for second_id in ids[index + 1:]:
            second = by_id[second_id]
            second_writes = tuple(writes_by_task[second_id])
            second_reads = tuple(second["reads"])
            overlaps = []
            for a in first_writes:
                for b in (*second_writes, *second_reads):
                    if _path_overlap(a, b):
                        overlaps.append({"firstPath": a, "secondPath": b,
                                         "reason": "write_write" if b in second_writes else "write_read"})
            for a in first_reads:
                for b in second_writes:
                    if _path_overlap(a, b):
                        overlaps.append({"firstPath": a, "secondPath": b, "reason": "read_write"})
            if not overlaps:
                continue
            before: str | None = None
            after: str | None = None
            if first_id in ancestors(second_id):
                before, after = first_id, second_id
            elif second_id in ancestors(first_id):
                before, after = second_id, first_id
            else:
                before, after = first_id, second_id
                edges[after].add(before)
            result.append({"firstTask": first_id, "secondTask": second_id,
                           "overlaps": sorted(overlaps, key=lambda row: (
                               row["firstPath"], row["secondPath"], row["reason"])),
                           "serializedBefore": before, "serializedAfter": after})
    return result


def _serialize_conflicts(tasks: Sequence[Mapping[str, Any]],
                         conflicts: Sequence[Mapping[str, Any]]) -> tuple[CodeTask, ...]:
    dependencies = {task["id"]: set(task["dependencies"]) for task in tasks}
    for conflict in conflicts:
        dependencies[conflict["serializedAfter"]].add(conflict["serializedBefore"])
    return tuple(CodeTask(task["id"], tuple(sorted(dependencies[task["id"]])),
                          tuple(task["reads"]), tuple()) for task in tasks)


def _digest(value: Any) -> str:
    try:
        body = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
                          allow_nan=False).encode("utf-8")
    except (TypeError, ValueError, RecursionError):
        raise RepositoryConflictError("Plan data must be finite bounded JSON.") from None
    return hashlib.sha256(body).hexdigest()


def _valid_digest(value: Any) -> bool:
    return isinstance(value, str) and len(value) == 64 and all(char in "0123456789abcdef" for char in value)
