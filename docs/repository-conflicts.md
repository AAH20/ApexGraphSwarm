# Repository-grounded conflict planning

`apexgraphswarm.repository_conflicts` plans concurrent coding waves from Git
commits that already exist in a configured local repository. It is a read-only
planner: it does not check out a revision, fetch, move refs, run task code, merge
branches, apply patches, or contact a model/provider. The `repositoryConflicts`
lab action takes its repository path from server configuration; callers provide
only the base revision and task declarations.

## Input

Python callers use:

```python
from apexgraphswarm.repository_conflicts import plan_repository_conflicts

plan = plan_repository_conflicts(
    repo_path="/configured/server/repository",
    base_revision="main",
    tasks=[
        {"id": "api", "dependencies": [], "head_revision": "api-head",
         "reads": ["src/contracts.py"]},
        {"id": "tests", "dependencies": ["api"], "head_revision": "tests-head",
         "reads": ["src/contracts.py"]},
    ],
)
```

The JSON lab action is `repositoryConflicts`, with `baseRevision` and `tasks`;
each task has `id`, optional `dependencies`, `headRevision`, and optional
`reads`. The adapter maps `headRevision` to the Python `head_revision` field.
Unknown fields are rejected. Revisions are bounded Git revision tokens, not
arbitrary command arguments. Each resolved head must descend from the resolved
base commit. IDs are unique and dependencies must refer to tasks in the same
request.

Declared read paths must be canonical relative Git paths and must resolve to a
regular, non-symlink blob in the base tree. They are reported as
`declared_and_verified_at_base_not_runtime_trace`: the planner does not observe
what a task actually reads. Submodule paths are unsupported. Write paths come
from the committed base-to-head diff. Renames include both old and new paths;
copies conservatively include the source and destination. Deletes and file-type
changes remain represented with before/after object metadata.

## Result and stale checks

The result contains the resolved base commit/tree, each task's resolved commit
and tree, verified declared reads, derived write records, change digests,
conflicts, deterministic waves, and `inputDigest` / `planDigest`. Git object
identifiers are named `treeObjectId` and `blobObjectId`; `base.objectFormat`
states whether the repository uses SHA-1 or SHA-256 object IDs. The separate
`changeSha256`, `inputDigest`, and `planDigest` fields are SHA-256 hashes of
canonical JSON data.

For a previously returned plan, pass the same result to
`verify_repository_conflict_plan(repo_path, plan)`. It re-resolves the stored
revision tokens and recomputes the complete stable plan. A changed base/head
reference, changed source declaration, modified semantic result, or altered
stable metadata is reported as `stale`. The comparison excludes only volatile
`gitCallCount` and `gitElapsedSeconds`; a digest is a consistency check, not an
authentication signature.

## Planning and limits

Write/write, write/read, and read/write collisions serialize task pairs when
paths are equal or one path is an ancestor of the other (for example, `src`
and `src/file.py`). Existing dependency edges determine order when present;
otherwise the lexically earlier task ID is placed first. The resulting
dependency DAG is passed to the deterministic wave planner. This is conservative
file-path scheduling, not semantic merge analysis: disjoint paths can still
conflict through generated state, build tools, or undeclared reads.

The current hard bounds are 32 tasks, 32 dependencies per task, 64 declared
reads per task / 256 total, 2,000 changed paths per task / 20,000 total, 8 MiB
stdout and 64 KiB stderr per Git call, 256 Git subprocesses, 3 seconds per call,
and 12 seconds total. The implementation rejects unmerged index entries and
submodule changes. It disables system/global Git configuration, replace refs,
lazy fetching, fsmonitor, external diff/textconv, and hooks for its inspection
commands. All commands use argument arrays, bounded subprocess I/O/time, and
the local repository's already-available objects.

The working tree, index edits, and untracked files are ignored; only committed
trees are compared. This avoids treating local dirty state as task evidence, but
also means the operator must ensure the pinned commits represent the changes
they intend to review. The planner produces a reviewable schedule only. It does
not authorize or execute the schedule, prove runtime read sets, predict merge
success, or guarantee the tasks will still apply cleanly later. Re-run stale
verification before relying on a plan whose revision tokens may have moved.
