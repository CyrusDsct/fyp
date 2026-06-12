import os
import sys
from pathlib import Path


# Public deployment entrypoint.
#
# Keep the production UI identical to dashboard.py, but switch analysis to the
# in-memory OpenRouter path so Streamlit Cloud does not need Flask, MongoDB, a
# localhost backend, or an uploads directory.
os.environ["FIXOPLETH_ANALYSIS_MODE"] = "memory"

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import front.dashboard as dashboard  # noqa: E402,F401
