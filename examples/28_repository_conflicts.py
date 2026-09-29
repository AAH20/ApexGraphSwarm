"""Example 28: Repository conflict planning.

Plan read-only conflict analysis for committed task heads
against a common base revision.
"""
from apexgraphswarm.repository_conflicts import plan_repository_conflicts

# Plan conflicts for multiple task heads
result = plan_repository_conflicts(
    ".",  # repository path
    "HEAD~5",  # base revision
    [
        {
            "id": "task-1",
            "headRevision": "abc123...",
            "dependencies": [],
            "reads": ["src/auth.py", "src/models.py"],
        },
        {
            "id": "task-2",
            "headRevision": "def456...",
            "dependencies": ["task-1"],
            "reads": ["src/api.py"],
        },
    ],
)

print(f"Version: {result['version']}")
print(f"Tasks: {len(result['tasks'])}")
print(f"Conflicts: {len(result.get('conflicts', []))}")
print(f"Warnings: {result.get('warnings', [])}")

for task in result["tasks"]:
    print(f"\n  Task: {task['id']}")
    print(f"    Head: {task['headRevision'][:12]}...")
    print(f"    Dependencies: {task.get('dependencies', [])}")
    print(f"    Reads: {task.get('reads', [])}")
