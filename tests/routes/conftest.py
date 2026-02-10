"""Pytest configuration for Jira plugin route tests.

TestClient-based tests — no server process needed.
"""

import sys
from pathlib import Path

# Add tests directory to path for helpers import
sys.path.insert(0, str(Path(__file__).parent))
