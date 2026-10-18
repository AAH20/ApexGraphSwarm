#!/usr/bin/env python3
"""Parse every Python file in the tree and report syntax errors.

Extracted from an inline `python -c "..."` in ci.yml for two reasons:

1. The embedded source carried the YAML block scalar's indentation into Python.
2. `Path.read_text()` with no `encoding=` uses the PLATFORM default, which is
   cp1252 on Windows -- so any file containing a non-ASCII byte (0x9d from a smart
   quote or an em dash) raised UnicodeDecodeError and failed the lint job on
   windows-latest only. Source files are UTF-8; say so explicitly.
"""
from __future__ import annotations

import ast
import pathlib
import sys

SKIP = (".integration-sources", "node_modules", ".venv")

errors: list[str] = []
for path in pathlib.Path(".").rglob("*.py"):
    if any(part in str(path) for part in SKIP):
        continue
    try:
        # encoding is explicit: the platform default is not UTF-8 on Windows.
        ast.parse(path.read_text(encoding="utf-8"))
    except (SyntaxError, UnicodeDecodeError) as exc:
        errors.append(f"{path}: {exc}")

if errors:
    for err in errors:
        print(f"FAIL {err}", file=sys.stderr)
    sys.exit(1)
print("AST parse check passed")
