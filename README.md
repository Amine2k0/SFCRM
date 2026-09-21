# SFCRM — Support & Ticketing CRM

A role-based customer support CRM built with Django. Clients open support tickets,
agents are assigned to resolve them, and administrators track resolution metrics
from a dashboard.

[![Python](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/)
[![Django](https://img.shields.io/badge/django-5.2%20LTS-092E20.svg)](https://www.djangoproject.com/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

---

## Table of contents

- [Features](#features)
- [Tech stack](#tech-stack)
- [Screenshots](#screenshots)
- [Getting started](#getting-started)
- [Running with Docker](#running-with-docker)
- [Using MySQL or PostgreSQL](#using-mysql-or-postgresql)
- [Configuration reference](#configuration-reference)
- [Project structure](#project-structure)
- [Roles and permissions](#roles-and-permissions)
- [Running the tests](#running-the-tests)
- [Roadmap](#roadmap)
- [License](#license)

---

## Features

SFCRM models three kinds of users, each with a different view of the system.

**Clients**
- Self-service registration and login
- Open a support ticket with a subject line
- Track the status of their own tickets — and only their own

**Agents**
- See the queue of tickets assigned to them
- Update a ticket's status and subject
- Close or delete a resolved ticket
- Toggle their own availability, which controls whether new tickets route to them

**Administrators**
- Dashboard with live metrics: resolution rate, assigned volume, and a breakdown
  of tickets by status (Open / Pending / Solved / Closed)
- Full directory of registered agents and clients
- Unrestricted access to every ticket in the system
- Django admin for creating agents and managing records directly

## Tech stack

| Layer | Choice |
| --- | --- |
| Backend | Django 5.2 LTS (Python 3.11+) |
| Database | SQLite by default; MySQL and PostgreSQL supported |
| Frontend | Django templates, Bootstrap 5 (SCSS sources included) |
| Auth | Django auth with a custom `AbstractUser` model |
| Packaging | Docker + Docker Compose |

## Screenshots

<!--
Drop your screenshots into docs/screenshots/ and uncomment the lines below.
Suggested captures: the admin dashboard, the ticket list, and the new-ticket form.

| Dashboard | Ticket list |
| --- | --- |
| ![Dashboard](docs/screenshots/dashboard.png) | ![Tickets](docs/screenshots/tickets.png) |
-->

_Screenshots coming soon._

---

## Getting started

These steps take you from a fresh clone to a running server. They assume
**Python 3.11 or newer** and **git**. No database server is required — the
default configuration uses SQLite.

### 1. Clone the repository

```bash
git clone https://github.com/Amine2k0/SFCRM.git
cd SFCRM
```

### 2. Create and activate a virtual environment

```bash
python -m venv .venv
```

```bash
# Linux / macOS
source .venv/bin/activate

# Windows (PowerShell)
.venv\Scripts\Activate.ps1
```

### 3. Install the dependencies

```bash
pip install -r requirements.txt
```

### 4. Create your environment file

The project reads its configuration from a `.env` file that is never committed.
Copy the template:

```bash
cp .env.example .env
```

Then generate a secret key and paste it into `.env` as `DJANGO_SECRET_KEY`:

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

The defaults in `.env.example` are already set up for local development with
SQLite, so no other changes are needed to get started.

### 5. Apply the database migrations

```bash
python manage.py migrate
```

This creates `db.sqlite3` in the project root.

### 6. Create an administrator account

```bash
python manage.py createsuperuser
```

### 7. Run the development server

```bash
python manage.py runserver
```

Open **http://127.0.0.1:8000/login/** and sign in with the superuser you just
created. You will land on the admin dashboard.

### 8. Create an agent (optional but recommended)

Tickets are routed to available agents, so you need at least one before a client
can open a ticket. Visit **http://127.0.0.1:8000/admin/**, sign in with your
superuser, and add an entry under **CRM → Agents**. Make sure **Dispo**
(available) is checked and **Staff status** is enabled.

You can then register a client at **http://127.0.0.1:8000/register/** and open a
ticket from **http://127.0.0.1:8000/addticket/**.

---

## Running with Docker

If you prefer not to install Python locally, the whole stack runs in containers.

```bash
cp .env.example .env
docker compose up --build
```

The app is served at **http://localhost:8000/**. Migrations run automatically on
container start.

To create a superuser inside the running container:

```bash
docker compose exec web python manage.py createsuperuser
```

To stop and remove the containers:

```bash
docker compose down
```

---

## Using MySQL or PostgreSQL

SQLite is the default so that the project runs with zero setup. To point SFCRM at
a real database server, edit the database block in `.env`.

**MySQL** — also run `pip install mysqlclient`:

```dotenv
DB_ENGINE=django.db.backends.mysql
DB_NAME=sf_crm
DB_USER=sfcrm
DB_PASSWORD=your-password
DB_HOST=127.0.0.1
DB_PORT=3306
```

**PostgreSQL** — also run `pip install psycopg[binary]`:

```dotenv
DB_ENGINE=django.db.backends.postgresql
DB_NAME=sf_crm
DB_USER=sfcrm
DB_PASSWORD=your-password
DB_HOST=127.0.0.1
DB_PORT=5432
```

Create the database on the server first, then run `python manage.py migrate`
again to build the schema.

---

## Configuration reference

Every setting is read from the environment, with sensible development defaults.

| Variable | Default | Description |
| --- | --- | --- |
| `DJANGO_SECRET_KEY` | _(none)_ | Cryptographic signing key. **Required.** Generate a unique one per environment. |
| `DJANGO_DEBUG` | `False` | Set to `True` for local development only. Never enable in production. |
| `DJANGO_ALLOWED_HOSTS` | `localhost,127.0.0.1` | Comma-separated list of hostnames the app will serve. |
| `DB_ENGINE` | `django.db.backends.sqlite3` | Django database backend path. |
| `DB_NAME` | `db.sqlite3` | Database name, or file path when using SQLite. |
| `DB_USER` | _(empty)_ | Database user. Not used by SQLite. |
| `DB_PASSWORD` | _(empty)_ | Database password. Not used by SQLite. |
| `DB_HOST` | _(empty)_ | Database host. Not used by SQLite. |
| `DB_PORT` | _(empty)_ | Database port. Not used by SQLite. |

`.env` is listed in `.gitignore` and must never be committed.

---

## Project structure

```
SFCRM/
├── CRM/                     # The support ticketing app
│   ├── migrations/          # Database schema history
│   ├── static/              # CSS, SCSS, JS, images, fonts
│   ├── templates/           # Page templates (base, login, ticket, dashboard, ...)
│   ├── admin.py             # Django admin registrations
│   ├── forms.py             # Registration, login and ticket forms
│   ├── models.py            # CustomUser, Client, Agent, Ticket
│   ├── tests.py             # Test suite
│   ├── urls.py              # App routes
│   └── views.py             # Request handlers
├── SFCRM/                   # Project configuration
│   ├── settings.py          # Environment-driven settings
│   ├── urls.py              # Root URL configuration
│   ├── asgi.py
│   └── wsgi.py
├── .env.example             # Template for your local .env
├── Dockerfile
├── compose.yaml
├── manage.py
└── requirements.txt
```

### Routes

| Path | Name | Access |
| --- | --- | --- |
| `/` | `home` | Admin dashboard — superusers only |
| `/login/` | `login` | Public |
| `/register/` | `register` | Public — creates a Client |
| `/logout/` | `logout` | Authenticated |
| `/ticket/` | `ticket` | Authenticated — scoped to the user's role |
| `/addticket/` | `addticket` | Clients |
| `/editticket/<id>` | `editticket` | Agents and admins |
| `/deleteticket/<id>` | `deleteticket` | Agents and admins |
| `/user/` | `user` | Admin directory — superusers only |
| `/admin/` | — | Django admin — staff only |

---

## Roles and permissions

| Capability | Client | Agent | Admin |
| --- | :---: | :---: | :---: |
| Register an account | ✅ | — | — |
| Open a ticket | ✅ | — | — |
| View own tickets | ✅ | ✅ | ✅ |
| View all tickets | — | — | ✅ |
| Edit a ticket's status | — | ✅ | ✅ |
| Delete a ticket | — | ✅ | ✅ |
| View the metrics dashboard | — | — | ✅ |
| View the user directory | — | — | ✅ |

Agents are staff users, so they also have access to the Django admin.

---

## Running the tests

```bash
python manage.py test
```

---

## Roadmap

- [ ] Search, filtering and pagination on the ticket list
- [ ] Threaded comments between clients and agents on a ticket
- [ ] Least-loaded agent assignment instead of first-available
- [ ] Email notifications on ticket status changes
- [ ] REST API with Django REST Framework

---

## License

Released under the MIT License. See [LICENSE](LICENSE) for details.
