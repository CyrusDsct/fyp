import os


# Public deployment entrypoint.
#
# Keep the production UI identical to dashboard.py, but switch analysis to the
# in-memory OpenRouter path so Streamlit Cloud does not need Flask, MongoDB, a
# localhost backend, or an uploads directory.
os.environ["FIXOPLETH_ANALYSIS_MODE"] = "memory"

import dashboard  # noqa: E402,F401
