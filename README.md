fyp
===

Overview
--------
This project consists of:
1) A Flask backend (API server)
2) A Streamlit frontend (dashboard UI)

You must run the backend and the Streamlit dashboard in TWO separate terminals.

------------------------------------------------------------
Prerequisites
------------------------------------------------------------
- Python 3.10+ recommended
- pip (Python package manager)

------------------------------------------------------------
Project Setup 
------------------------------------------------------------

1) Get the project code
-----------------------
If you are cloning from GitHub:

    git clone <YOUR_REPO_URL>
    cd fyp

Make sure you are in the project root (you should see files like app.py, dashboard.py).

2) Create a virtual environment (recommended)
---------------------------------------------
A virtual environment keeps dependencies isolated and avoids conflicts.

Windows (PowerShell):

    python -m venv .venv
    .\.venv\Scripts\Activate.ps1

If activation is blocked, run this and try again:

    Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
    .\.venv\Scripts\Activate.ps1

macOS / Linux:

    python3 -m venv .venv
    source .venv/bin/activate

You should now see "(.venv)" in your terminal prompt.

To deactivate later:

    deactivate


3) Install dependencies
-----------------------
Option A (preferred): Install from requirements.txt

    pip install -r requirements.txt

Option B: Install manually (if requirements.txt does not exist)

    pip install flask pymongo streamlit requests python-dotenv


4) Create your local .env (DO NOT commit this file)
---------------------------------------------------
This project uses a local .env file for configuration.

4.1 Create .env from template

macOS / Linux:

    cp .env.example .env

Windows (PowerShell):

    Copy-Item .env.example .env

4.2 Edit .env and fill in values

Example .env:


Notes:
- OPENROUTER_API_KEY is sensitive. Keep it private. Do NOT push it to GitHub.
- MONGO_URI may contain credentials. Keep it private. Do NOT push it to GitHub.


5) IMPORTANT: Ensure .env is actually loaded
--------------------------------------------
Python does NOT automatically load .env by default.
This project expects python-dotenv to load it (load_dotenv()).

If you get missing-key errors even though .env is filled,
make sure the entry scripts call:

    from dotenv import load_dotenv
    load_dotenv()


------------------------------------------------------------
Running the project (Two terminals)
------------------------------------------------------------

Terminal 1: Start Flask backend
-------------------------------
From the project root:

    python app.py

Expected: backend runs on (default)
- http://127.0.0.1:5000

Keep this terminal running.


Terminal 2: Start Streamlit dashboard
------------------------------------
From the project root:

    streamlit run dashboard.py

Open the Streamlit UI in your browser:
- http://localhost:8501


------------------------------------------------------------
Troubleshooting
------------------------------------------------------------

1) Installation issues
- Ensure you activated the virtual environment
- Try upgrading pip:

    python -m pip install --upgrade pip


------------------------------------------------------------
What NOT to commit / push to GitHub
------------------------------------------------------------
Do NOT push:
- .env
- .venv/ or venv/
- __pycache__/ and *.pyc

You should use .gitignore to ignore these files.
Only push .env.example (template), not .env (real secrets).