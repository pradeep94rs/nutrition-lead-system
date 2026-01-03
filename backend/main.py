from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import requests, re, os, uuid, json
from datetime import datetime, timedelta
import pytz
import gspread
from google.oauth2.service_account import Credentials

# --------------------------------------------------
# Environment
# --------------------------------------------------
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
GOOGLE_SHEET_ID = os.getenv("GOOGLE_SHEET_ID")
GOOGLE_SERVICE_ACCOUNT_JSON = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")

# --------------------------------------------------
# Validate required env vars
# --------------------------------------------------
if not GOOGLE_SHEET_ID:
    raise RuntimeError("Missing GOOGLE_SHEET_ID")

if not GOOGLE_SERVICE_ACCOUNT_JSON:
    raise RuntimeError("Missing GOOGLE_SERVICE_ACCOUNT_JSON")

# --------------------------------------------------
# Google Sheet (ENV-based auth)
# --------------------------------------------------
creds_dict = json.loads(GOOGLE_SERVICE_ACCOUNT_JSON)

creds = Credentials.from_service_account_info(
    creds_dict,
    scopes=["https://www.googleapis.com/auth/spreadsheets"]
)

gc = gspread.authorize(creds)
sheet = gc.open_by_key(GOOGLE_SHEET_ID).sheet1

# --------------------------------------------------
# App
# --------------------------------------------------
app = FastAPI(title="Health Clarity API")

# TEMP: allow all (lock to Netlify domain after deploy)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://poetic-smakager-e36275.netlify.app"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --------------------------------------------------
# Models
# --------------------------------------------------
class Lead(BaseModel):
    name: str
    contact: str
    city_state: str
    dob: str
    age: int
    gender: str

    primary_goals: List[str]
    issue_duration: str
    lifestyle_discipline: str
    biggest_challenges: List[str]

    health_importance_score: int
    past_attempts: str
    time_comfort: str

    preferred_languages: List[str]
    additional_notes: Optional[str] = ""
    consent: bool


class Referral(BaseModel):
    source: str

# --------------------------------------------------
# Helpers
# --------------------------------------------------
def ist_now():
    return datetime.now(pytz.timezone("Asia/Kolkata"))


def get_recent(contact):
    rows = sheet.get_all_records()
    recent = []
    for r in reversed(rows):
        if str(r.get("contact")) == str(contact):
            t = datetime.fromisoformat(r["submitted_at"])
            if ist_now() - t <= timedelta(hours=24):
                recent.append(r)
    return recent


def wait_time(first_time):
    reset = first_time + timedelta(hours=24)
    diff = reset - ist_now()
    h = diff.seconds // 3600
    m = (diff.seconds % 3600) // 60
    return f"{h} hours {m} minutes"


def send_telegram(msg):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return
    requests.post(
        f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
        json={"chat_id": TELEGRAM_CHAT_ID, "text": msg}
    )

# --------------------------------------------------
# APIs
# --------------------------------------------------
@app.post("/submit-lead")
def submit_lead(lead: Lead):

    if not lead.consent:
        raise HTTPException(400, "Consent required")

    if not re.fullmatch(r"\d{10}", lead.contact):
        raise HTTPException(400, "Invalid WhatsApp number")

    recent = get_recent(lead.contact)

    if len(recent) >= 3:
        first = datetime.fromisoformat(recent[-1]["submitted_at"])
        raise HTTPException(
            429,
            f"Submission limit reached. Please try again after {wait_time(first)}."
        )

    status = "NEW" if len(recent) == 0 else "DUPLICATE"
    lead_id = uuid.uuid4().hex[:8].upper()
    now = ist_now().isoformat()

    sheet.append_row([
        lead_id,
        now,
        lead.name,
        lead.contact,
        lead.city_state,
        lead.dob,
        lead.age,
        lead.gender,
        ", ".join(lead.primary_goals),
        lead.issue_duration,
        lead.lifestyle_discipline,
        ", ".join(lead.biggest_challenges),
        lead.health_importance_score,
        lead.past_attempts,
        lead.time_comfort,
        ", ".join(lead.preferred_languages),
        lead.additional_notes,
        status
    ])

    telegram_msg = f"""
🟢 {status} | Health Clarity Form

👤 {lead.name} ({lead.age}, {lead.gender})
📞 {lead.contact}
📍 {lead.city_state}

🎯 Goals: {", ".join(lead.primary_goals)}
🔥 Importance: {lead.health_importance_score}/10
🧠 Challenges: {", ".join(lead.biggest_challenges)}
🕓 4–5 PM Comfort: {lead.time_comfort}
🗣 Languages: {", ".join(lead.preferred_languages)}
""".strip()

    send_telegram(telegram_msg)

    return {"status": status, "lead_id": lead_id}


@app.post("/track-referral")
def track_referral(ref: Referral):
    sheet.append_row([
        "REFERRAL",
        ist_now().isoformat(),
        "", "", "", "", "", "",
        "", "", "", "",
        "", "", "",
        ref.source,
        "",
        "REFERRAL"
    ])
    return {"status": "ok"}

# --------------------------------------------------
# Local run (ignored on Railway)
# --------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 8000)),
    )
