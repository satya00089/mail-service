"""Simple FastAPI app to send emails via Gmail SMTP with optional attachments."""

from typing import List, Optional
from email.message import EmailMessage
import os
import base64
import logging

import smtplib

from fastapi import FastAPI, BackgroundTasks, HTTPException
from pydantic import BaseModel, EmailStr

app = FastAPI()
log = logging.getLogger("uvicorn.error")

# ----- Config from env (safe: do NOT commit creds) -----
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER")  # e.g. youraccount@gmail.com
SMTP_PASS = os.getenv(
    "SMTP_PASS"
)  # App password (recommended) or OAuth2 token if implemented


# ----- request schemas -----
class Attachment(BaseModel):
    """Attachment with base64-encoded content."""

    filename: str
    content_base64: str  # base64-encoded bytes
    mime_type: Optional[str] = "application/octet-stream"


class EmailPayload(BaseModel):
    """Email payload."""

    to: EmailStr
    subject: str
    body: str
    html: Optional[bool] = False
    from_name: Optional[str] = None  # optional display name
    from_email: Optional[EmailStr] = None  # overrides SMTP_USER if provided
    attachments: Optional[List[Attachment]] = None


# ----- sync send function (run in background) -----
def _send_email(payload: EmailPayload) -> None:
    """Send email via SMTP."""
    if not SMTP_USER or not SMTP_PASS:
        raise RuntimeError(
            "SMTP credentials not provided (SMTP_USER / SMTP_PASS required)."
        )

    msg = EmailMessage()
    sender_email = payload.from_email or SMTP_USER
    if payload.from_name:
        from_header = f"{payload.from_name} <{sender_email}>"
    else:
        from_header = sender_email

    msg["From"] = from_header
    msg["To"] = payload.to
    msg["Subject"] = payload.subject

    if payload.html:
        # add html alternative
        msg.add_alternative(payload.body, subtype="html")
    else:
        msg.set_content(payload.body)

    # attachments (base64)
    if payload.attachments:
        for att in payload.attachments:
            try:
                data = base64.b64decode(att.content_base64)
            except Exception as e:
                log.exception("Bad base64 for attachment %s", att.filename)
                raise Exception("Bad base64 for attachment %s", att.filename) from e

            maintype, _, subtype = (
                att.mime_type or "application/octet-stream"
            ).partition("/")
            # EmailMessage.attach will guess maintype/subtype if bytes are supplied with maintype/subtype explicitly:
            msg.add_attachment(
                data,
                maintype=maintype or "application",
                subtype=subtype or "octet-stream",
                filename=att.filename,
            )

    # connect and send
    with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=30) as smtp:
        smtp.ehlo()
        smtp.starttls()
        smtp.ehlo()
        smtp.login(SMTP_USER, SMTP_PASS)
        smtp.send_message(msg)
        smtp.quit()


# ----- endpoint -----
@app.post("/send")
async def send_email(payload: EmailPayload, background_tasks: BackgroundTasks):
    """
    Queue an email to be sent via Gmail SMTP.
    Use an app password for SMTP_USER if using a Google account with 2FA.
    """
    try:
        # validation of payload happens via pydantic
        background_tasks.add_task(_send_email, payload)
        return {"status": "queued", "to": payload.to, "subject": payload.subject}
    except Exception as e:
        # keep error messages concise
        log.exception("Failed to queue/send email")
        raise HTTPException(status_code=500, detail=str(e)) from e
