# Fixopleth

Fixopleth is a small web application for reviewing choropleth maps. It has a
Flask backend for file upload and AI analysis, and a Streamlit dashboard for the
user interface.

The current JSON fields and scoring criteria are documented in
`DATA_DICTIONARY.md`.

## Requirements

- Python 3.10 or newer
- pip
- MongoDB connection string
- User-provided OpenRouter API key

## Setup

Create and activate a virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, run this once in the same terminal:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

Install the dependencies:

```powershell
pip install -r requirements.txt
```

Create a local `.env` file from the example:

```powershell
Copy-Item .env.example .env
```

Then fill in the required values:

```text
MONGO_URI=...
```

The `.env` file is local only and should not be committed.
OpenRouter keys are entered by users in the dashboard and are not stored in
`.env`.

For public/demo use, keep the privacy defaults disabled:

```text
STORE_ANALYSIS_RESULTS=false
ENABLE_UPLOAD_LISTING=false
ENABLE_UPLOAD_SERVING=false
ENABLE_UPLOAD_DELETE=false
KEEP_UPLOADS_AFTER_ANALYSIS=false
UPLOAD_RETENTION_SECONDS=3600
```

## Running

Run the backend and dashboard in two separate terminals.

Backend:

```powershell
python app.py
```

Default backend URL:

```text
http://127.0.0.1:5000
```

Dashboard:

```powershell
streamlit run dashboard.py
```

Default dashboard URL:

```text
http://localhost:8501
```

## Notes

- Keep `.env`, `.venv/`, `__pycache__/`, and `*.pyc` out of Git.
- If environment variables are not being read, check that the entry scripts call
  `load_dotenv()`.
- The backend must stay running while the Streamlit dashboard calls the analysis
  API.
- The dashboard requires each user to enter their own OpenRouter key before
  analysis starts.
- Uploaded maps use private random filenames. Upload listing and direct upload
  serving are disabled unless explicitly enabled for local debugging. Uploaded
  map files are deleted after each analysis by default, and abandoned uploads
  are pruned by the retention setting.

## Public Deployment

For a real public URL, deploy `streamlit_app.py` on Streamlit Community Cloud
from this GitHub repository.

Recommended Community Cloud settings:

- Repository: this repo
- Branch: `main`
- Main file path: `streamlit_app.py`
- Python version: 3.12 or newer
- Secrets: none required for OpenRouter

The public Streamlit app does not use Flask, MongoDB, or the `uploads/` folder.
Uploaded maps and CSV files are handled in Streamlit session memory only. Each
user enters their own OpenRouter key, and the key is used only for the current
analysis request.

GitHub Pages is not enough for this app because it hosts static HTML/CSS/JS,
not Python server code.
