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
- OpenRouter API key

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
OPENROUTER_API_KEY=...
```

The `.env` file is local only and should not be committed.

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
