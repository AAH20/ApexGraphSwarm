"""Pytest configuration for ApexGraphSwarm test suite.

Handles integration source path setup and graceful skipping of tests
that require external kernel sources not present in the repository.
"""

import os
import sys

# Add integration sources to path for kernel tests
_integration_sources = os.path.join(os.path.dirname(__file__), '..', '.integration-sources')
if os.path.isdir(_integration_sources):
    for item in os.listdir(_integration_sources):
        full_path = os.path.join(_integration_sources, item)
        if os.path.isdir(full_path) and full_path not in sys.path:
            sys.path.insert(0, full_path)

# Add project root to path for apexgraphswarm package
_project_root = os.path.join(os.path.dirname(__file__), '..')
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)
