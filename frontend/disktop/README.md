# AURA Desktop Frontend

React and Vite frontend using JavaScript and Tailwind CSS.

## AURA desktop UI

The sidebar switches between separate Text Chat and Voice Assistant views. Text and voice conversations have stable browser-generated IDs, and conversation history remains stored in localStorage under `aura.conversations.v1`. The frontend sends messages and voice controls to the FastAPI backend; it does not call Groq directly.

Set `VITE_API_BASE_URL` in a local `.env` file if the API is not at `http://127.0.0.1:8000`. A template is provided in `.env.example`. Voice sessions use the backend machine's microphone and audio output.

## Start the application on Windows

Install the backend dependencies from the project root and configure `GROQ_API_KEY` in the project-root `.env` file (the template is `backend\.env.example`). For microphone support, also install `backend\requirements-voice.txt`; PyAudio may require Microsoft C++ Build Tools on Windows. Start the backend:

```powershell
cd "C:\LOCAL DISK D\IBM\AURA"
python -m pip install -r backend\requirements.txt
python -m uvicorn backend.main:app --reload
```

In a separate PowerShell window, start the frontend:

```sh
cd "C:\LOCAL DISK D\IBM\AURA\frontend\disktop"
npm install
npm run dev
```

Create a production frontend build from `frontend\disktop` with:

```sh
npm run build
```
