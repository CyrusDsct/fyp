# Fixopleth

Fixopleth is a map auditing tool for reviewing choropleth maps with AI-assisted extraction, validation, and feedback. The current application lets users upload a map image, optionally add CSV data and map context, and receive structured feedback about map quality, binning, labeling, color use, and missing information.

## Repository Layout

```text
backend/
  app.py                  Optional Flask API for file upload and persisted analysis.
  analysis_core.py        OpenRouter analysis flow used by Streamlit Cloud.
  backend_client.py       Client used by the Streamlit UI when calling the Flask API.
  analysis_helper.py      Shared analysis helpers.

frontend/streamlit/
  streamlit_app.py        Streamlit application entrypoint.
  dashboard.py            Main Streamlit layout and interaction flow.
  ui/                     Streamlit components and page sections.
  utils/                  Frontend data and JSON helpers.
  binning/                Binning algorithms and similarity calculations used by the UI.

docs/specifications/
  DATA_DICTIONARY.md      Expected analysis fields and scoring criteria.
  prompt.txt              Main model prompt used by the Python analysis flow.

examples/
  data/                   Sample CSV datasets.
  reports/                Example generated binning reports.

tests/
  test_analysis_core.py   Smoke and unit checks for core analysis helpers.

.github/workflows/
  ci.yml                  Basic Python compile and test workflow.

requirements.txt          Python dependencies.
.python-version           Python runtime version hint.
.env.example              Environment variable template.
.streamlit/config.toml    Streamlit deployment and theme configuration.
streamlit_app.py          Root launcher for Streamlit deployment platforms.
CONTRIBUTING.md           Contribution and local development guide.
```

## Run The Streamlit App

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

The default local URL is:

```text
http://localhost:8501
```

Users provide their own OpenRouter API key in the Streamlit interface. The key is kept in Streamlit session state and is not stored in the repository.

## Optional Flask Backend

The Streamlit Cloud path uses the in-memory analysis flow in `backend/analysis_core.py`, so it does not require Flask, MongoDB, or local uploads.

The legacy Flask API remains available for local or server-backed workflows:

```powershell
python backend\app.py
```

The Flask backend requires a configured `.env` file based on `.env.example`, including `MONGO_URI`. Uploaded files are written under `uploads/`, which is ignored by git.

## Security And Privacy

Fixopleth does not store the OpenRouter API key in the repository. In the Streamlit app, users enter their own key in the interface and the key is kept in session state for the current analysis flow.

Uploaded maps and optional CSV data are sent to OpenRouter for model analysis. Users should avoid uploading confidential or sensitive data unless they have reviewed the relevant data handling policies.

See `SECURITY.md` and `PRIVACY.md` for more details.

## License

The software is available under the MIT License. See `LICENSE` for details.

## Contact

If you have any questions, feel free to open an issue or contact the Fixopleth maintainers.

## Development Checks

Run the lightweight checks before opening a pull request:

```powershell
$files = Get-ChildItem backend,frontend\streamlit -Recurse -File -Filter *.py | Where-Object { $_.FullName -notmatch '__pycache__' } | ForEach-Object { $_.FullName }
python -m py_compile streamlit_app.py @files
python -m unittest discover tests
```

## Roadmap

- Add user testing tasks and issue templates.
- Improve corrected previews for detected map issues.
- Support additional map types beyond choropleth maps.
- Add dataset validation for uploaded CSV files.
- Strengthen computer vision and OCR extraction.
- Explore browser extension support as a later-stage feature with compact panel layouts and automated map-region capture.
- Review sample datasets and generated reports for redistribution rights before packaging formal releases.
