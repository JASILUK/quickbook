````markdown
# QuickBook

QuickBook is an event booking platform built with Django and Django REST Framework.

## Quick Setup

### Git Bash

Copy and paste the following commands:

```bash
git clone https://github.com/JASILUK/quickbook.git
cd quickbook

python -m venv .venv
source .venv/Scripts/activate

pip install -r requirements.txt

python manage.py migrate
python manage.py createsuperuser

python manage.py runserver
````

### PowerShell

If using PowerShell, use:

```powershell
git clone https://github.com/JASILUK/quickbook.git
cd quickbook

python -m venv .venv
.venv\Scripts\Activate.ps1

pip install -r requirements.txt

python manage.py migrate
python manage.py createsuperuser

python manage.py runserver
```

The project includes a development fallback `SECRET_KEY`, so an `.env` file is not required for basic local testing.

For custom local configuration:

```bash
cp .env.example .env
```

Then set:

```env
DJANGO_SECRET_KEY=your-secret-key
```

## Application

After starting the server:

**Application**

http://127.0.0.1:8000/

**Staff Dashboard**

http://127.0.0.1:8000/dashboard/

**Swagger / OpenAPI**

http://127.0.0.1:8000/api/docs/

## Features

* Customer registration and JWT authentication
* Event browsing, search and filtering
* Ticket booking and cancellation
* Seat availability validation
* Transaction-safe booking flow
* Booking history
* Binary referral network
* Referral tree, root and statistics
* Staff dashboard
* Customer management
* Vendor management
* Event management
* Booking management
* API pagination
* Swagger / OpenAPI documentation

## Main API Endpoints

### Authentication

```text
POST /api/auth/register/
POST /api/auth/login/
POST /api/auth/refresh/
POST /api/auth/logout/
GET  /api/auth/me/
```

### Events

```text
GET   /api/events/
POST  /api/events/
GET   /api/events/<id>/
PATCH /api/events/<id>/
```

### Bookings

```text
GET  /api/bookings/
POST /api/bookings/
GET  /api/bookings/<id>/
POST /api/bookings/<id>/cancel/
```

### Referrals

```text
GET /api/referrals/<user_id>/tree/
GET /api/referrals/<user_id>/root/
GET /api/referrals/<user_id>/stats/
```

### Dashboard

```text
GET /api/dashboard/
```

## Architecture

```text
HTTP Request
     ↓
View
     ↓
Serializer
     ↓
Service
     ↓
Repository
     ↓
Database
```

Business rules are handled in service classes, while reusable database queries are handled by repositories.

## Referral Placement

The referral system uses a binary tree.

When a customer registers using a referral code:

1. The referring customer becomes the sponsor.
2. The system searches for the next available position.
3. Placement uses breadth-first search.
4. LEFT is checked before RIGHT.
5. The customer is placed in the first available position.

The sponsor relationship and binary placement are stored separately.

## Booking

Bookings use transactional seat management to prevent invalid seat availability during concurrent booking requests.

The booking stores the ticket price at the time of booking as a price snapshot.

## Project Structure

```text
quickbook/
├── apps/
│   ├── accounts/
│   ├── bookings/
│   ├── events/
│   ├── referrals/
│   └── dashboard/
├── config/
├── templates/
├── manage.py
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

## Verification

Run:

```bash
python manage.py check
```

The staff dashboard is a custom Django dashboard and does not use Django Admin.

## Notes

* SQLite is used for the machine-test environment.
* `.env` is ignored by Git and must not be committed.
* `.env.example` contains configuration placeholders only.

````

One thing I'd do **before pushing this README**:

```bash
git add README.md .gitignore .env.example
git commit -m "docs: add project setup and documentation"
git push
````

Then the evaluator can open the repository and immediately see **Quick Setup → copy/paste → dashboard → Swagger → features**.
