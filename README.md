# Fixopleth

Fixopleth is the current Streamlit version of my FYP prototype for reviewing
choropleth maps with AI assistance.

This version focuses only on the Streamlit app. Browser extension work and
static page deployment are not part of the current handover scope.

## Current Progress

- The app UI is implemented in `dashboard.py`.
- The public Streamlit entrypoint is `streamlit_app.py`.
- Users upload a choropleth map image in the left panel.
- Users can optionally upload CSV data and provide context about the target
  audience and map purpose.
- Users enter their own OpenRouter API key beside the `Analyze` button.
- The OpenRouter key is kept in the Streamlit session and is not stored in the
  repository or `.env`.
- Analysis results are shown in the right panel as evaluation details.

The main recent UI change is the OpenRouter key input position. It has been
moved out of the top bar and placed beside the `Analyze` button, so the action
area contains both controls in one row.

## Main Files

- `streamlit_app.py` - public Streamlit Cloud entrypoint.
- `dashboard.py` - main Streamlit UI layout.
- `analysis_core.py` - in-memory OpenRouter analysis path used by Streamlit
  Cloud.
- `ui/components/styles.py` - Streamlit UI styling and layout CSS.
- `ui/sections/` - individual Streamlit UI sections.
- `DATA_DICTIONARY.md` - JSON fields and scoring criteria.
- `requirements.txt` - Python dependencies.

## Run Locally

Create and activate a virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install dependencies:

```powershell
pip install -r requirements.txt
```

Run the same Streamlit version used for public deployment:

```powershell
streamlit run streamlit_app.py
```

Default local URL:

```text
http://localhost:8501
```

## Streamlit Cloud Deployment

Current public app:

```text
https://fixopleth.streamlit.app/
```

Recommended Streamlit Cloud settings:

- Repository: `CyrusDsct/fyp`
- Branch: `main`
- Main file path: `streamlit_app.py`
- Python version: `3.12` recommended
- Secrets: none required for OpenRouter

Each user provides their own OpenRouter key in the app UI. The key is used only
for the current analysis request.

## Notes For Supervisor

This handover version is intentionally scoped to the Streamlit app. The browser
extension folder is not part of this current deliverable.

The app currently prioritizes:

- a single Streamlit interface for uploading a map,
- optional CSV/context inputs,
- user-provided OpenRouter key input,
- AI evaluation output in the right panel,
- deployability on Streamlit Community Cloud.

The Flask backend files remain in the repository from earlier development, but
the public Streamlit deployment uses `streamlit_app.py` and the in-memory
analysis path, so Flask and MongoDB are not required for the current public demo.
