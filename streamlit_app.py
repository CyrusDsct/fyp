"""Root Streamlit launcher for deployment platforms.

The application code lives in frontend/streamlit. Keeping this thin wrapper at
the repository root lets Streamlit Cloud and local users run the default
`streamlit run streamlit_app.py` command without duplicating app code.
"""

from __future__ import annotations

import runpy
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent
STREAMLIT_DIR = PROJECT_ROOT / "frontend" / "streamlit"
STREAMLIT_ENTRYPOINT = STREAMLIT_DIR / "streamlit_app.py"

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

if str(STREAMLIT_DIR) not in sys.path:
    sys.path.insert(0, str(STREAMLIT_DIR))

runpy.run_path(str(STREAMLIT_ENTRYPOINT), run_name="__main__")
