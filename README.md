# AURA

AURA is the starter backend for a future personal AI assistant. The backend
uses FastAPI and is designed to be shared by future Windows desktop and Android
mobile apps. AI, voice, database, and computer-control features are not
implemented yet.

## Setup on Windows

Open PowerShell and run these commands from the AURA project folder:

```powershell
cd "C:\LOCAL DISK D\IBM\AURA"
py -m venv .venv
.\.venv\Scripts\Activate.ps1
cd backend
python -m pip install -r requirements.txt
```

If PowerShell blocks virtual-environment activation, use
`Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` as appropriate for your
machine, or run the environment's Python directly at
`..\.venv\Scripts\python.exe`.

## Start the API

From the `backend` directory, with the virtual environment active:

```powershell
python -m uvicorn main:app --reload
```

The API runs at `http://127.0.0.1:8000`. Open
`http://127.0.0.1:8000/docs` for the interactive API documentation.

## Run the tests

In another PowerShell window, activate the virtual environment, return to the
project folder, and run:

```powershell
cd "C:\LOCAL DISK D\IBM\AURA"
.\.venv\Scripts\Activate.ps1
python -m pytest
```
# aura-ai-assistant
