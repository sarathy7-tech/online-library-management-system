# Online Library Management System

A Django-based library management system with role-based access (Admin / Librarian / Reader),
book circulation (borrow, return, renew, reserve), fines, email notifications, and staff reports.

## Tech stack

- **Backend:** Django 6.0
- **Database:** SQLite (default; easy to swap for MySQL later — see "Future improvements")
- **Frontend:** Django templates + Bootstrap 5.3.3 + Bootstrap Icons
- **Extras:** openpyxl (Excel reports), reportlab (PDF library cards), python-dotenv (config)

## 1. Setup

```bash
# 1. Create and activate a virtual environment
python -m venv venv
venv\Scripts\activate          # Windows
source venv/bin/activate       # macOS/Linux

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set up your local environment file
copy .env.example .env         # Windows
cp .env.example .env           # macOS/Linux
# Open .env and fill in a secret key (see the comment in the file for
# the one-line command that generates one). The other defaults are fine
# to start with.

# 4. Apply migrations (this also auto-creates the Admin/Librarian/Reader roles)
python manage.py migrate

# 5. Create your admin account
python manage.py createsuperuser

# 6. Run it
python manage.py runserver
```

Visit `http://127.0.0.1:8000/`. Log in with the superuser account you just created
to reach the staff dashboard, or register a new account to see the reader side.

### Optional: sample catalog data

If you want some books/authors/categories to browse right away instead of starting
from an empty catalog, ask for a fixture export, or add a few books from the
**Manage Books** screen once logged in as staff.

## 2. Project structure

```
library/          Project settings, root URLs
users/            Custom user model, roles, auth, dashboards, notifications, reports
books/            Book/Author/Category/Publisher catalog, reviews, digital resources
circulation/      Loans, reservations, fines, borrowing business logic (services.py)
templates/        All HTML templates
static/           CSS (style.css) and JS (main.js)
media/            Uploaded book covers and digital resources (created automatically)
```

`circulation/services.py` holds the actual borrowing/return/fine business rules
(borrowing limits, fine blocks, renewal limits) separately from the views — worth
reading if you want to see how the rules are enforced in one place.

## 3. What was fixed

These were real bugs/gaps found during review, not style nitpicks:

| Issue | Fix |
|---|---|
| Gmail address + app password hardcoded in `settings.py` | Moved to `.env` (gitignored). **Please regenerate that app password** at [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords) — treat the old one as compromised since it was sitting in plain text. |
| `SECRET_KEY` hardcoded | Moved to `.env`, with a dev-only fallback so the project still boots without one. |
| `ALLOWED_HOSTS = []` | Would reject every request the moment `DEBUG=False`. Now reads from `.env`, defaults to `localhost,127.0.0.1`. |
| `python manage.py createsuperuser` crashed | `CustomUser.role` is required but Django's built-in command never sets it. Added a custom user manager that auto-assigns the Admin role for superusers. |
| No way to seed Admin/Librarian/Reader roles | Previously had to be done by hand in `manage.py shell`. Now a migration (`users/migrations/0004_seed_roles.py`) creates them automatically. |
| `Loan.save()` could crash | Fallback due-date calculation used a field that isn't set yet at that point in the save. Fixed to use today's date directly. |
| Borrow / return / renew / reserve were plain `GET` links | Any link on any page could trigger these against a logged-in user (no CSRF protection on GET). Converted to POST forms with CSRF tokens. |
| `BookReview` and `DigitalResource` models existed but had no UI | Built out (see below) and registered in Django admin. |
| Empty `dashboard` app, a stray unused `users/settings.py`, dead code in a couple of views | Removed. |
| `requirements.txt` was UTF-16 and had ~60 unrelated packages from a general environment | Rewritten in UTF-8 with only what the project actually uses. |

## 4. What was added

- **Book reviews & ratings** — readers can rate/review any book; the average rating
  recalculates automatically. (`books/views.py`: `add_review`, `delete_review`)
- **Digital resource downloads** — the reader-facing piece was missing (staff could
  upload PDFs, but there was no way to actually open one). Now shown on the book
  detail page, with a download counter.
- **Reservation cancellation** — readers can back out of a pending reservation from
  the dashboard instead of it sitting there until it expires.
- **`expire_reservations` management command** — the `Reservation` model already had
  an `'Expired'` status that nothing ever set. This command (same pattern as the
  existing `send_due_reminders`) expires stale reservations and notifies the reader.
  Run it daily alongside `send_due_reminders` (cron, Windows Task Scheduler, etc.):
  ```bash
  python manage.py send_due_reminders
  python manage.py expire_reservations
  ```
- **PDF library card** — downloadable from the Profile page. Uses `reportlab`, which
  was already in `requirements.txt` but wasn't actually used anywhere yet.
- **Related books** ("More in [category]") on the book detail page.
- **A real homepage** — `home.html` existed but no view ever rendered it; visitors
  were always force-redirected to `/login/`. It's now a proper landing page shown
  to signed-out visitors.
- **Timezone set to `Asia/Kolkata`** — notification timestamps now show real local
  time instead of UTC.

## 5. Future improvements (didn't do these, but worth knowing about)

- **Templates don't use inheritance.** Every page is a full standalone HTML file
  (no `base.html`, no `{% extends %}`) — that's ~40 files each repeating the navbar,
  CDN links, etc. It all works fine as-is, but pulling the shared layout into one
  `base.html` and having pages `{% extends "base.html" %}` + `{% block content %}`
  would make future changes (like tweaking the navbar) a one-file edit instead of forty.
  This is genuinely a good exercise to do yourself once you're comfortable with how
  the current pages are structured.
- **`django-crispy-forms` and `django-filter`** are installed and configured but no
  template actually uses them yet — forms are styled manually. Worth wiring up if
  you want less repetitive form code.
- **MySQL** — `DATABASES` in `settings.py` is plain Django config, so switching from
  SQLite is mostly changing that one block once you have a MySQL server, `pip install
  mysqlclient`, and re-run migrations against it.
- **Payment gateway** — "Pay Fine" currently just marks a fine as paid; there's no
  real payment processing, which is fine for a college project but worth flagging.

## 6. Security checklist before deploying anywhere public

- [ ] Set a real `DJANGO_SECRET_KEY` in `.env` (don't use the fallback)
- [ ] Set `DJANGO_DEBUG=False`
- [ ] Set `DJANGO_ALLOWED_HOSTS` to your actual domain
- [ ] Rotate the Gmail app password mentioned above before switching `DJANGO_EMAIL_BACKEND` to SMTP
- [ ] Never commit `.env` or `db.sqlite3` (`.gitignore` already covers this)
