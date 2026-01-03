# How to run the project locally

Follow these steps in separate terminals.

1) Start the backend (Terminal 1)

```powershell
cd "d:\Study\HerbalLife\nutrition-lead-system\backend"
py -3 -m uvicorn main:app --reload
```

2) Start the frontend (Terminal 2)

```powershell
cd "d:\Study\HerbalLife\nutrition-lead-system\frontend"
py -3 -m http.server 5500
```

3) Open the site in your browser

http://localhost:5500


Notes
- The backend reads env vars from `.env` at the repo root. To use Google Sheets and Telegram features, set `GOOGLE_SHEET_ID`, `GOOGLE_SERVICE_ACCOUNT_FILE`, `TELEGRAM_BOT_TOKEN`, and `TELEGRAM_CHAT_ID` in `.env`, and place the service account JSON at the path referenced by `GOOGLE_SERVICE_ACCOUNT_FILE`.
- If `py` is unavailable, replace `py -3` with `python`.
- You can also use VS Code Live Server (open `frontend/index.html`) or `npx serve -l 5500` as alternatives.
