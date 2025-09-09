# Mail Service — Minimal

Small FastAPI service to send email via SMTP (defaults to Gmail SMTP). Minimal, drop-in, and ready for local testing.

---

## Files

* `main.py` — FastAPI app with `POST /send` to send email.
* `requirements.txt` — dependencies.

---

## Quick install & run

1. Create venv and install:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. Add env (example `.env`):

```
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=youraccount@gmail.com
SMTP_PASS=your_app_password_here
```

> Use a Google **App Password** if your account has 2FA. **Do not commit** `.env`.

3. Run:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Server is at `http://localhost:8000`.

---

## Endpoint

`POST /send` — accepts JSON:

```json
{
  "to": "recipient@example.com",
  "subject": "Hello",
  "body": "Text or HTML",
  "html": false,
  "from_name": "Optional",
  "from_email": "optional@sender.com",
  "attachments": [
    {
      "filename": "file.txt",
      "content_base64": "SGVsbG8=",
      "mime_type": "text/plain"
    }
  ]
}
```

Response: `200` on queued/send, error codes otherwise.

---

## Example curl

Plain text:

```bash
curl -X POST "http://localhost:8000/send" \
  -H "Content-Type: application/json" \
  -d '{
    "to": "friend@example.com",
    "subject": "Test",
    "body": "Hello from FastAPI",
    "html": false
  }'
```

---

## Notes

* Use App Passwords or OAuth2 for Gmail in production.
* Protect the endpoint (API key / auth) before exposing publicly.
* If frontend runs on a different origin, enable CORS in `main.py`.

---

If you want, I can also:

* add a 1-file `.env.example`, or
* add a tiny `dockerfile` for containerized testing.
