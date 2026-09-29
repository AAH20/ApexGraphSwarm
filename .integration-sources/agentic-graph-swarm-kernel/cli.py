#!/usr/bin/env python3
"""Root executable CLI entrypoint for Agentic Graph Swarm Kernel."""
import sys
from pathlib import Path

# Ensure root package is in sys.path
sys.path.insert(0, str(Path(__file__).parent))

from agentic_graph_swarm_kernel.cli import main

if __name__ == "__main__":
    main()
