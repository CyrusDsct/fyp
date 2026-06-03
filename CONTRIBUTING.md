# Contributing

Thank you for your interest in improving Fixopleth.

## Development Setup

Create and activate a virtual environment from the repository root:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install dependencies:

```powershell
pip install -r requirements.txt
```

Run the Streamlit app:

```powershell
streamlit run streamlit_app.py
```

## Project Structure

- `frontend/streamlit/` contains the Streamlit interface.
- `backend/` contains analysis services and the optional Flask API.
- `docs/specifications/` contains the prompt and structured output dictionary.
- `examples/` contains sample data and example generated reports.
- `tests/` contains lightweight checks for core helper behavior.

## Before Submitting Changes

Run:

```powershell
$files = Get-ChildItem backend,frontend\streamlit -Recurse -File -Filter *.py | Where-Object { $_.FullName -notmatch '__pycache__' } | ForEach-Object { $_.FullName }
python -m py_compile streamlit_app.py @files
python -m unittest discover tests
```

Do not commit API keys, `.env`, uploaded files, generated caches, or private datasets.
