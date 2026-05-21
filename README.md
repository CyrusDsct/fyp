# Fixopleth

Fixopleth is the current Streamlit version of my FYP prototype for reviewing
choropleth maps with AI assistance.

This handover version focuses on the Streamlit app code only.

## Current Progress

- The main Streamlit UI is implemented in `dashboard.py`.
- The app entrypoint is `streamlit_app.py`.
- Users can upload a choropleth map image in the left panel.
- Users can optionally upload CSV data for binning-related checks.
- Users can optionally provide target audience and map purpose context.
- Users enter their own OpenRouter API key in the control row beside the
  `Analyze` button.
- The OpenRouter key input is positioned on the left side of the `Analyze`
  button.
- The OpenRouter key is kept in the Streamlit session and is not stored in the
  repository.
- Analysis output is shown in the right panel.

The main UI change in this version is the OpenRouter key input position. The
key field was moved out of the top bar and placed directly to the left of the
`Analyze` button, so the user can enter the key immediately before starting
analysis.

## Main Files

- `streamlit_app.py` - Streamlit app entrypoint.
- `dashboard.py` - main Streamlit UI layout.
- `analysis_core.py` - in-memory OpenRouter analysis flow.
- `ui/components/styles.py` - Streamlit layout and styling.
- `ui/sections/` - individual Streamlit UI sections.
- `DATA_DICTIONARY.md` - expected JSON fields and scoring criteria.
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

Run the Streamlit app:

```powershell
streamlit run streamlit_app.py
```

Default local URL:

```text
http://localhost:8501
```

## Notes For Supervisor

This version is intended as a clean Streamlit handover point. The current focus
is:

- a single Streamlit interface for map upload and review,
- optional CSV and context inputs,
- user-provided OpenRouter key input beside the `Analyze` button,
- AI evaluation results displayed in the right panel.

Earlier backend files remain in the repository from development, but the current
Streamlit version runs through `streamlit_app.py` and uses the in-memory
analysis flow. Users provide their own OpenRouter key in the UI for each
analysis request.
