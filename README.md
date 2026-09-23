  # 📚 Online Library Management System

A full-featured library management web application built with **Django**. It supports three
roles — **Admin**, **Librarian**, and **Reader** — and covers the whole lifecycle of running a
library online: cataloging books, borrowing/returning/renewing/reserving copies, fines,
digital downloads, reviews, notifications, and staff reports.

This README explains the project from the ground up: what it does, how it's built, how to run
it on your own machine, and how every major piece of the codebase fits together.

---

## Table of contents

1. [Features](#1-features)
2. [Tech stack](#2-tech-stack)
3. [Project structure](#3-project-structure)
4. [How the data model fits together](#4-how-the-data-model-fits-together)
5. [User roles & permissions](#5-user-roles--permissions)
6. [Getting started (step-by-step setup)](#6-getting-started-step-by-step-setup)
7. [Environment variables](#7-environment-variables)
8. [Everyday usage](#8-everyday-usage)
9. [Scheduled/management commands](#9-scheduledmanagement-commands)
10. [App-by-app tour of the code](#10-app-by-app-tour-of-the-code)
11. [Security notes before you deploy or publish this repo](#11-security-notes-before-you-deploy-or-publish-this-repo)
12. [Known limitations / roadmap](#12-known-limitations--roadmap)
13. [Troubleshooting](#13-troubleshooting)
14. [License](#14-license)

---

## 1. Features

**Catalog & discovery**
- Browse, search (including live/AJAX search), and filter books by title, author, category, or publisher
- Book detail pages with cover images, summaries, average rating, and related books ("More in this category")
- Multiple **physical copies** per book, each individually tracked (barcode + status: Available / Issued / Reserved / Lost / Damaged)
- **Digital resources** (PDFs/e-books) attached to a book, downloadable by members, with a download counter

**Circulation (borrowing workflow)**
- Borrow, return, and renew books (with renewal limits)
- Reserve a book that's currently unavailable, and cancel a reservation you no longer need
- Automatic due-date calculation and overdue detection
- Fines generated for late returns, with partial/full payment tracking

**Reviews & ratings**
- Readers can leave a star rating (1–5) and a comment on any book
- A book's average rating recalculates automatically as reviews come in

**Accounts & roles**
- Custom user model with three roles — Admin, Librarian, Reader — each with a different dashboard and permission set
- Registration, login/logout, and a full "forgot password" email flow
- Editable profile with borrowing limits, membership expiry, and total fines
- Downloadable **PDF library card** from the profile page

**Notifications**
- In-app notifications for due-soon books, overdue books, fine reminders, fulfilled reservations, and new arrivals
- Mark individual notifications (or all of them) as read

**Staff tools**
- Manage books, authors, categories, and publishers (full CRUD)
- Manage digital resources per book
- Reader management (create, view, edit, deactivate readers)
- Staff dashboard with library-wide stats
- **Excel report exports** (via openpyxl): most-borrowed books, fines, active readers
- Full audit log model for tracking who changed what

---

## 2. Tech stack

| Layer | Technology |
|---|---|
| Backend framework | **Django 6.0** |
| Database | **SQLite** (default, zero-config — see [§12](#12-known-limitations--roadmap) for swapping to MySQL) |
| Frontend | Django templates + **Bootstrap 5.3.3** + Bootstrap Icons |
| Config / secrets | **python-dotenv** (`.env` file, never committed) |
| Excel reports | **openpyxl** |
| PDF generation (library card) | **reportlab** |
| Image handling | **Pillow** |
| Forms/search (installed, ready to wire up) | django-crispy-forms, crispy-bootstrap5, django-filter |

---

## 3. Project structure

```
librarysystem/
├── manage.py                  # Django's command-line entry point
├── requirements.txt           # Python dependencies
├── .env.example                # Template for your local secrets file — copy this to .env
├── .gitignore
├── db.sqlite3                  # SQLite database (gitignored — created on first migrate)
│
├── library/                    # Project-level settings & root URL config
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py / asgi.py
│
├── users/                      # Custom user model, auth, roles, dashboards, notifications, reports
│   ├── models.py                # CustomUser, Role, Notification, AuditLog
│   ├── views.py                 # login/register/dashboards/profile/reports/notifications
│   ├── forms.py
│   ├── urls.py
│   ├── admin.py
│   └── migrations/
│
├── books/                      # Book catalog: books, authors, categories, publishers, reviews, digital resources
│   ├── models.py                # Book, Author, Publisher, Category, BookCopy, DigitalResource, BookReview
│   ├── views.py
│   ├── urls.py
│   ├── templatetags/book_extras.py
│   └── migrations/
│
├── circulation/                # Borrowing/returning/reserving/fines — the business logic layer
│   ├── models.py                # Loan, Reservation, Fine
│   ├── services.py              # Core rules: borrowing limits, fine blocks, renewal limits
│   ├── views.py
│   ├── urls.py
│   ├── management/commands/     # expire_reservations.py (+ send_due_reminders)
│   └── migrations/
│
├── templates/                  # All HTML templates, grouped by app
│   ├── users/
│   ├── books/
│   └── circulation/
│
├── static/                     # CSS and JS shipped with the app
│   └── css/style.css
│
└── media/                      # Uploaded book covers & digital resources (created automatically, gitignored)
```

> 💡 **Where the "brains" of the app live:** `circulation/services.py` is worth reading first —
> it holds the actual borrowing/return/fine rules (borrowing limits, fine blocks, renewal
> limits) in one place, separate from the views that call it.

---

## 4. How the data model fits together

```
Role ──< CustomUser ──< Loan >── BookCopy >── Book >── Author
                    │                              │
                    ├──< Reservation >── Book       ├── Publisher
                    ├──< Fine                       ├── Category
                    ├──< Notification                └──< DigitalResource
                    ├──< BookReview >── Book
                    └──< AuditLog
```

- **A `Book`** is the catalog entry (title, author, category, summary, cover image, etc.).
- **A `BookCopy`** is one physical copy of a `Book`, identified by a barcode, with its own
  status (`Available`, `Issued`, `Reserved`, `Lost`, `Damaged`). This is what actually gets
  borrowed — a popular title can have several copies in circulation at once.
- **A `Loan`** links a `CustomUser` to the specific `BookCopy` they borrowed, with loan date,
  due date, return date, status, and any fine amount.
- **A `Reservation`** links a `CustomUser` to a `Book` (not a specific copy) they want to
  borrow once one becomes available.
- **A `Fine`** is generated against a `Loan` when a book comes back late, and tracks how much
  has been paid.
- **A `DigitalResource`** is an uploaded file (PDF/e-book) attached to a `Book`, with an
  access level (`Public`/`Member`) and a download counter.
- **A `BookReview`** ties one rating+comment per `(Book, CustomUser)` pair — a reader can only
  review a given book once.
- **`Role`** is a simple lookup table (`Admin` / `Librarian` / `Reader`) that `CustomUser`
  points to via a foreign key, seeded automatically by a migration.

---

## 5. User roles & permissions

| Capability | Reader | Librarian | Admin |
|---|:---:|:---:|:---:|
| Browse/search catalog, borrow/return/renew/reserve | ✅ | ✅ | ✅ |
| Write reviews, download digital resources, download library card | ✅ | ✅ | ✅ |
| Manage books/authors/categories/publishers | ❌ | ✅ | ✅ |
| Upload/manage digital resources | ❌ | ✅ | ✅ |
| View staff dashboard & reports (Excel exports) | ❌ | ✅ | ✅ |
| Manage readers (create/edit/deactivate) | ❌ | ✅ | ✅ |
| Django admin site access | ❌ | Depends on `is_staff` | ✅ |

The role is stored on `CustomUser.role` (a foreign key to `Role`), and view-level checks
(`is_admin()`, `is_librarian()`, `is_reader()` helper methods on the model) gate access to
staff-only pages.

---

## 6. Getting started (step-by-step setup)

### Prerequisites
- **Python 3.11+** installed ([python.org](https://www.python.org/downloads/))
- `pip` (comes with Python)
- Git (only needed if you're cloning from GitHub)

### Step 1 — Get the code
```bash
git clone https://github.com/sarathy7-tech/online-library-management-system.git
cd online-library-management-system
```
*(If you downloaded this as a zip instead, just extract it and `cd` into the `librarysystem` folder.)*

### Step 2 — Create and activate a virtual environment
A virtual environment keeps this project's Python packages separate from everything else on
your machine.

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```
You'll know it worked when you see `(venv)` at the start of your terminal prompt.

### Step 3 — Install dependencies
```bash
pip install -r requirements.txt
```

### Step 4 — Set up your local environment file
The app reads its secret configuration from a `.env` file, which is **not** committed to git.

```bash
# Windows
copy .env.example .env

# macOS / Linux
cp .env.example .env
```

Now open `.env` and fill it in — see [§7 Environment variables](#7-environment-variables) for
what each value means and how to generate a secret key.

### Step 5 — Apply database migrations
```bash
python manage.py migrate
```
This creates `db.sqlite3` and also auto-creates the `Admin` / `Librarian` / `Reader` roles via
a data migration — you don't need to create them by hand.

### Step 6 — Create your admin (superuser) account
```bash
python manage.py createsuperuser
```
Follow the prompts (username, email, password). This account is automatically given the
**Admin** role.

### Step 7 — Run the development server
```bash
python manage.py runserver
```

### Step 8 — Open the app
Visit **http://127.0.0.1:8000/** in your browser.
- Log in with the superuser account to land on the **staff dashboard**.
- Or click **Register** to create a normal **Reader** account and browse the site as a member.
- Visit **http://127.0.0.1:8000/admin/** for the built-in Django admin panel.

---

## 7. Environment variables

All configuration lives in `.env` (copied from `.env.example` in Step 4 above). None of these
values should ever be hardcoded into `settings.py` or committed to git.

| Variable | What it's for | Example / how to get it |
|---|---|---|
| `DJANGO_SECRET_KEY` | Cryptographic key Django uses for sessions, password resets, CSRF, etc. | Generate one with:<br>`python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"` |
| `DJANGO_DEBUG` | `True` for local development (shows detailed error pages). **Must be `False`** in any real deployment. | `True` |
| `DJANGO_ALLOWED_HOSTS` | Comma-separated list of domains/IPs allowed to serve the app | `localhost,127.0.0.1` (add your real domain when deploying) |
| `DJANGO_EMAIL_BACKEND` | Where notification/password-reset emails go | `django.core.mail.backends.console.EmailBackend` (prints to terminal — safe default) or `django.core.mail.backends.smtp.EmailBackend` (actually sends email) |
| `EMAIL_HOST_USER` | The sending email address (only used with the SMTP backend) | your own address |
| `EMAIL_HOST_PASSWORD` | An **app password** for that email account — never your real account password | For Gmail: generate one at [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords) |
| `DEFAULT_FROM_EMAIL` | "From" address shown on outgoing emails | usually same as `EMAIL_HOST_USER` |

By default the email backend is the **console backend**, so you don't need real email
credentials at all to run and demo the project — notification emails simply print to your
terminal.

---

## 8. Everyday usage

**As a Reader**
1. Register an account or log in.
2. Browse/search the catalog from the home page.
3. Open a book to see details, its average rating, reviews, and any digital resources.
4. Click **Borrow** on an available copy, or **Reserve** if all copies are checked out.
5. Manage your active loans, renewals, and returns from **My Books**.
6. Check **Fines** for anything owed, and pay from there.
7. Leave a review/rating on books you've read.
8. Download your **library card** as a PDF from your profile.

**As a Librarian/Admin**
1. Log in — you'll land on the **staff dashboard** with library-wide stats.
2. Use **Manage Books / Authors / Categories / Publishers** to maintain the catalog.
3. Upload **digital resources** (e-books/PDFs) to any book.
4. Use **Readers** to view, create, or edit reader accounts.
5. Use **Reports** to export Excel sheets: most-borrowed books, fines, and active readers.
6. (Admin only) Use `/admin/` for full database-level access, including the audit log.

---

## 9. Scheduled/management commands

Two commands should be run **daily** (via cron, Windows Task Scheduler, or a hosting
provider's scheduled-jobs feature) to keep the system's automated notifications and
reservation expiry working:

```bash
python manage.py send_due_reminders     # notifies readers about books due soon / overdue
python manage.py expire_reservations    # expires stale reservations and notifies the reader
```

---

## 10. App-by-app tour of the code

### `library/` — project configuration
- `settings.py` — all Django settings, loaded with sensible env-var-driven defaults (see §7)
- `urls.py` — top-level routing: `/admin/`, and includes each app's `urls.py`

### `users/` — accounts, roles, dashboards, notifications, reports
- `models.py` — `CustomUser` (extends Django's `AbstractUser`), `Role`, `Notification`, `AuditLog`
- `views.py` — registration, login/logout, password reset, both role-specific dashboards,
  profile editing, PDF library card generation, notification endpoints, and the three Excel
  report exports
- `forms.py` — registration and profile forms

### `books/` — the catalog
- `models.py` — `Book`, `Author`, `Publisher`, `Category`, `BookCopy`, `DigitalResource`, `BookReview`
- `views.py` — catalog browsing/search, live AJAX search, full CRUD for books/authors/
  categories/publishers, digital resource upload/download, and review add/delete
- `templatetags/book_extras.py` — custom template filters used in the catalog templates

### `circulation/` — the borrowing workflow
- `models.py` — `Loan`, `Reservation`, `Fine`
- `services.py` — **the actual business rules**: how borrowing limits, renewal limits, and
  fine blocks are enforced. Read this file first if you want to understand *why* a borrow or
  renewal request succeeds or fails.
- `views.py` — thin views that call into `services.py`
- `management/commands/expire_reservations.py` — the daily reservation-expiry job (see §9)

### `templates/` and `static/`
- Templates are grouped by app (`templates/users/`, `templates/books/`, `templates/circulation/`)
- Each page is currently a self-contained HTML file (see [§12](#12-known-limitations--roadmap)
  for a note on template inheritance)
- `static/css/style.css` holds the site's custom styling on top of Bootstrap

---

## 11. Security notes before you deploy or publish this repo

This section applies whether you're pushing to GitHub or deploying somewhere real.

**Before pushing to GitHub:**
- ✅ `.gitignore` already excludes `.env`, `db.sqlite3`, and `media/` — double check none of
  these show up in `git status` before your first commit.
- ✅ Only `.env.example` (with placeholder values) should ever be committed — never the real `.env`.
- ✅ If a real secret key, password, or personal email/API key was ever committed to git
  history (even once, even if later removed), treat it as compromised: rotate it, and consider
  scrubbing git history (e.g. with `git filter-repo` or BFG Repo-Cleaner) before making the
  repo public.

**Before deploying anywhere public:**
- [ ] Set a real, freshly-generated `DJANGO_SECRET_KEY` in `.env`
- [ ] Set `DJANGO_DEBUG=False`
- [ ] Set `DJANGO_ALLOWED_HOSTS` to your actual domain(s)
- [ ] Switch to a real database (SQLite is fine for development/small use, but doesn't handle
  concurrent writes well in production — see §12)
- [ ] Use HTTPS and set Django's security middleware settings (`SECURE_SSL_REDIRECT`,
  `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE`, etc.)
- [ ] If enabling real email, use an **app password**, never your main account password, and
  rotate it periodically

---

## 12. Known limitations / roadmap

These are conscious trade-offs or things intentionally left for later — worth knowing about if
you plan to keep developing this project:

- **No template inheritance.** Every page is a full standalone HTML file rather than extending
  a shared `base.html`. It works fine as-is, but pulling the shared layout (navbar, CDN links,
  etc.) into one `base.html` with `{% extends %}` / `{% block %}` would make site-wide changes
  a one-file edit instead of forty. A good next exercise once you're comfortable with the
  current structure.
- **`django-crispy-forms` and `django-filter`** are installed and configured but not yet wired
  into any template — forms are currently styled by hand. Worth adopting if you want less
  repetitive form markup.
- **SQLite only.** Fine for development and small deployments, but doesn't handle concurrent
  writes well at scale. Switching to MySQL/PostgreSQL is mostly a matter of updating the
  `DATABASES` block in `settings.py`, installing the relevant driver
  (`mysqlclient` or `psycopg2`), and re-running migrations against the new database.
- **No real payment processing.** "Pay Fine" currently just marks a fine as paid — there's no
  integration with an actual payment gateway.

---

## 13. Troubleshooting

| Problem | Likely fix |
|---|---|
| `ModuleNotFoundError` when running `manage.py` | Make sure your virtual environment is activated and `pip install -r requirements.txt` completed without errors. |
| `createsuperuser` fails or crashes | Make sure you've run `python manage.py migrate` first — the custom role-seeding migration must run before a superuser can be created. |
| Emails don't seem to send | By default the console backend just prints emails to your terminal — check there first. Only switches to real SMTP once you set `DJANGO_EMAIL_BACKEND` to the SMTP backend and fill in real email credentials. |
| Static files / styling look broken | Confirm `DEBUG=True` while running locally with `runserver` — static file serving works differently once `DEBUG=False`. |
| "Disallowed Host" error | Add the host/domain you're accessing the site from to `DJANGO_ALLOWED_HOSTS` in `.env`. |

---

## 14. License

This project is licensed under the [MIT License](LICENSE).

You are free to use, copy, modify, and distribute this project in accordance with the terms of the MIT License.


## 👨‍💻 Author

**Sarathy K**
GitHub: [@sarathy7-tech](https://github.com/sarathy7-tech)

---
