"""Make the project root importable so `pytest` can find pawpal_system.

Without this, `pytest` puts the tests/ directory on sys.path instead of the
repository root, and `import pawpal_system` fails. `python -m pytest` does the
right thing anyway; this file makes plain `pytest` work too.
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
