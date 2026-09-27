"""Dependency-free repository graph command."""
import argparse
import json
from pathlib import Path
from .repository_graph import build_repository_graph


def main():
    parser = argparse.ArgumentParser(prog="apexgraphswarm")
    parser.add_argument("command", choices=["graph"])
    parser.add_argument("repository", nargs="?", default=".")
    parser.add_argument("--output")
    args = parser.parse_args()
    graph = build_repository_graph(args.repository)
    graph["name"] = Path(args.repository).resolve().name
    rendered = json.dumps(graph, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        Path(args.output).write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")


if __name__ == "__main__":
    main()
