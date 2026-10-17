# BSO Catalyst — Campus Calendar

Mobile-first event calendar website (events, assignments, payments, recruitment) on a Flask + SQLite backend.
Flask serves both the API (`/api/...`) and the website (`frontend/`), so one command runs everything.

## Run

```bash
cd calendar_backend
pip install -r requirements.txt
python seed.py          # creates the admin account + sample data
python app.py           # http://localhost:5000
```

Open http://localhost:5000 (on your phone, use `http://<your-computer-ip>:5000` on the same Wi-Fi).

- **Admin login:** User ID `H1D026052`, password `admin123` (override with `ADMIN_PASSWORD=... python seed.py`).
- **Students:** use *Create account* on the login screen.
- Set `JWT_SECRET_KEY` in the environment for anything beyond local testing.

## What's in the site

| Tab | Who | What |
| --- | --- | --- |
| Calendar | everyone | Month grid with colored dots per type; tap a day to list its items |
| Tasks | everyone | Open and past items, filterable by type |
| Me | everyone | Your submissions with status, grades and feedback |
| Admin | admins | Create events, assignments, payments, recruitments |

Tap any item to see details, upload a file (PDF/PNG/JPG, max 2 MB) for assignments, payments and recruitments, or view a payment's budget sheet.

## Changes made to the backend

- Login now needs a password (`Password_Hash` on `User`); `POST /api/auth/register` creates student accounts. The old "auto-create any user" login is removed.
- `UserSchema` no longer exposes the password hash or device token.
- New admin routes: `POST /api/admin/events`, `POST /api/admin/recruitments`.
- Flask serves `frontend/`; added `requirements.txt` and `.gitignore`; `seed.py` is safe to re-run.
- The committed `calendar_tracking.db` and `__pycache__` files were removed from git — the old database has no password column, so run `python seed.py` to create a fresh one.
