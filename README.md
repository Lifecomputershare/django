# SmartHire Backend

SmartHire is a Django-based backend that powers an AI‑assisted hiring platform.  
It exposes a versioned REST API (`/api/v1/`) for:

- Authentication and user accounts
- Companies and multi‑tenant data isolation
- Subscription plans and company subscriptions
- Job postings and candidate applications
- AI match logging
- Payment endpoints (Stripe / Khalti stubs)

This document explains how to install, run, and use the backend as a developer or integrator.

---

## 1. Technology Stack

- Python 3.11+ (recommended)
- Django 6.x
- Django REST Framework
- MySQL (for the main database)

The current project layout:

- `SmartHire/` – main Django project (settings, URLs, common utilities)
- `api/` – core business APIs (companies, subscriptions, jobs, applications, AI, payments)
- `auth/` – authentication APIs (register, login, refresh, logout)

---

## 2. Project Structure

Key modules:

- `SmartHire/settings.py` – Django configuration, REST framework, JWT, throttling
- `SmartHire/urls.py` – root URL configuration and `/api/v1/` routing
- `SmartHire/exceptions.py` – global DRF exception handler
- `SmartHire/responses.py` – unified API response helpers
- `SmartHire/middleware.py` – request audit logging middleware
- `api/models.py` – core domain models:
  - `Company`
  - `SubscriptionPlan`
  - `CompanySubscription`
  - `UserProfile` (user roles and company mapping)
  - `Job`
  - `Application`
  - `AIMatchLog`
  - `UserAuditLog`
- `api/views.py` – business logic and REST endpoints
- `api/serializers.py` – DRF serializers for models
- `api/authentication.py` – custom JWT implementation
- `api/permissions.py` – role‑based permission classes
- `api/urls.py` – API routes for companies, jobs, applications, subscriptions, AI, payments
- `auth/views.py` – auth-related endpoints (register, login, refresh, logout)
- `auth/urls.py` – `/auth/` endpoint mapping

---

## 3. Setup and Installation

### 3.1. Prerequisites

- Python installed and available on the PATH
- MySQL server running locally (or accessible remotely)
- A MySQL database and user that Django can use  
  (default configuration in `SmartHire/settings.py` uses:
  `NAME=smartHire`, `USER=admin`, `PASSWORD=admin`, `HOST=localhost`, `PORT=3306`)

### 3.2. Virtual environment

From the project root (`c:\SmartHire AI` on Windows):

```bash
python -m venv .venv
.venv\Scripts\activate
```

### 3.3. Install dependencies

Install the required packages (adjust versions if needed):

```bash
pip install django djangorestframework mysqlclient
```

If you add more libraries (Celery, Stripe, etc.), remember to install them here as well.

### 3.4. Database migrations

Run migrations to create all tables:

```bash
.venv\Scripts\python.exe manage.py migrate
```

If you modify models later:

```bash
.venv\Scripts\python.exe manage.py makemigrations
.venv\Scripts\python.exe manage.py migrate
```

### 3.5. Environment variables

The project supports environment‑based configuration. The key variables:

- `DJANGO_ENV` – `"development"`, `"staging"`, or `"production"` (default: `"development"`)
- `DJANGO_SECRET_KEY` – secret key for signing; **must be set in production**
- `DJANGO_DEBUG` – `"True"` or `"False"`; automatically forced to `"False"` if `DJANGO_ENV=production`
- `DJANGO_ALLOWED_HOSTS` – space‑separated list of allowed hosts in non‑debug mode

Example (PowerShell):

```powershell
$env:DJANGO_ENV = "development"
$env:DJANGO_SECRET_KEY = "change-me-in-production"
$env:DJANGO_DEBUG = "True"
```

### 3.6. Running the development server

From the project root:

```bash
.venv\Scripts\python.exe manage.py runserver
```

By default, the server runs at:

- `http://127.0.0.1:8000/`

Base health endpoint:

- `GET /` → `{"message": "API is working"}` (from `SmartHire/views.py`)

---

## 4. Environment and Security Notes

- In **development**, hard‑coded defaults are used if environment variables are not provided.
- In **production**, always set:
  - A strong `DJANGO_SECRET_KEY`
  - Proper `DJANGO_ALLOWED_HOSTS`
  - `DJANGO_ENV=production` (this forces `DEBUG=False`)
- Database credentials are currently configured in `SmartHire/settings.py`.  
  For real deployments, move them to environment variables.

---

## 5. API Versioning and Base URLs

All main backend APIs are versioned under `/api/v1/`:

- Auth: `/api/v1/auth/...`
- Business APIs: `/api/v1/...`

Configured in [SmartHire/urls.py](file:///c:/SmartHire%20AI/SmartHire/urls.py):

- `path("api/v1/auth/", include("auth.urls"))`
- `path("api/v1/", include("api.urls"))`

---

## 6. Authentication & Authorization

### 6.1. JWT tokens

The backend uses stateless JWT authentication:

- Custom implementation in `api/authentication.py`
- Algorithm: HS256
- Tokens:
  - Access token: ~15 minutes
  - Refresh token: 7 days
  - Claims: `user_id`, `type` (`"access"` or `"refresh"`), `iat`, `exp`

Include tokens in requests using:

```http
Authorization: Bearer <access_token>
```

### 6.2. User roles

User roles are stored in `UserProfile.role`:

- `admin`
- `recruiter`
- `candidate`

The `UserProfile` model is linked one‑to‑one with Django’s `User` model.

### 6.3. Permission enforcement

Role‑based permissions are in `api/permissions.py`, for example:

- `IsAdmin`
- `IsRecruiter`
- `IsCandidate`
- `IsAdminOrRecruiter`

These are used in viewsets to control access:

- Companies and jobs: only admins and recruiters can manage them.
- Applications:
  - Admin: all applications
  - Recruiter: applications for jobs in their company
  - Candidate: their own applications only

---

## 7. Standard API Response Format

All APIs return a unified JSON structure:

```json
{
  "success": true,
  "data": { ... },
  "error": null,
  "message": "optional"
}
```

On errors:

```json
{
  "success": false,
  "data": null,
  "error": {
    "detail": "Error message or field errors"
  }
}
```

This is implemented via:

- `SmartHire/exceptions.py` – global DRF exception handler
- `SmartHire/responses.py` – `api_success` and `api_error` helpers

---

## 8. Auth APIs (Accounts)

Base path: `/api/v1/auth/`

All responses follow the standard format and include JWT tokens where relevant.

### 8.1. Register

- **Endpoint**: `POST /api/v1/auth/register`
- **Purpose**: Create a new user and associated profile, optionally linked to a company.

**Request body:**

```json
{
  "email": "user@example.com",
  "password": "StrongPassword123",
  "role": "admin | recruiter | candidate",
  "company_id": 1
}
```

`company_id` is optional; if provided, must match an existing `Company.id`.

**Response (201):**

```json
{
  "success": true,
  "data": {
    "access": "<access_token>",
    "refresh": "<refresh_token>",
    "user": {
      "id": 1,
      "email": "user@example.com",
      "role": "recruiter",
      "company_id": 1
    }
  },
  "error": null
}
```

### 8.2. Login

- **Endpoint**: `POST /api/v1/auth/login`
- **Purpose**: Authenticate a user and return tokens.

**Request body:**

```json
{
  "email": "user@example.com",
  "password": "StrongPassword123"
}
```

**Response (200):** same shape as register.

### 8.3. Refresh token

- **Endpoint**: `POST /api/v1/auth/refresh`
- **Purpose**: Exchange a refresh token for a new access token (and a new refresh token).

**Request body:**

```json
{
  "refresh": "<refresh_token>"
}
```

### 8.4. Logout

- **Endpoint**: `POST /api/v1/auth/logout`
- **Auth**: Requires valid access token.
- **Purpose**: Client‑side logout (tokens become invalid only by expiry).

---

## 9. Companies & Multi‑Tenancy

Base path: `/api/v1/companies/`

Viewset: `CompanyViewSet` in `api/views.py`.

- **Permissions**:
  - Admin: full access to all companies.
  - Recruiter: only their own company.
  - Candidate: no access.
- **Auto‑assignment**:
  - When a recruiter creates their first company, they are automatically linked to it.

### 9.1. List companies

- `GET /api/v1/companies/`

Returns companies visible to the current user (see permissions above).

### 9.2. Create company

- `POST /api/v1/companies/`

**Body example:**

```json
{
  "name": "SmartHire Inc",
  "industry": "HR Tech",
  "website": "https://smarthire.example",
  "description": "AI powered hiring"
}
```

On success, recruiters are auto‑linked to the new company if they weren’t linked before.

### 9.3. Retrieve / update / delete

- `GET /api/v1/companies/{id}/`
- `PUT /api/v1/companies/{id}/`
- `DELETE /api/v1/companies/{id}/`

Access is restricted according to role and company relationship.

---

## 10. Subscription & Plan Management

### 10.1. Subscription plans (public)

- **Endpoint**: `GET /api/v1/subscriptions/plans/`
- **Permissions**: Public (`AllowAny`)

Lists all available subscription plans:

- `name`
- `price`
- `job_limit`
- `ai_match_limit`
- `duration_days`

### 10.2. Company subscription (current)

- **Endpoint**: `GET /api/v1/subscriptions/company`
- **Permissions**: Authenticated
- **Logic**:
  - Uses `request.user.profile.company`.
  - Returns the latest active `CompanySubscription` for that company.

### 10.3. Subscribe company to plan

- **Endpoint**: `POST /api/v1/subscriptions/subscribe`
- **Permissions**: Authenticated, user must be linked to a company.

**Request body:**

```json
{
  "plan_id": 1
}
```

**Behavior:**

- Validates `plan_id`.
- Uses plan’s `duration_days` to compute `start_date` and `end_date`.
- Creates a `CompanySubscription` with `payment_status="pending"` (payment logic can be added later).

---

## 11. Job Management

Base path: `/api/v1/jobs/`

Viewset: `JobViewSet` in `api/views.py`.

**Permissions:**

- Admin: full CRUD on all jobs.
- Recruiter: CRUD on jobs belonging to their company.
- Candidate: read‑only, only jobs with `is_active=True`.

### 11.1. List jobs

- `GET /api/v1/jobs/`

Result is filtered depending on role (see above).

### 11.2. Create job

- `POST /api/v1/jobs/` (admin or recruiter)

**Body example:**

```json
{
  "title": "Senior Backend Engineer",
  "description": "Build and scale our APIs",
  "salary_min": 60000,
  "salary_max": 90000,
  "location": "Remote",
  "job_type": "full_time",
  "is_active": true
}
```

When a recruiter is linked to a company, the job will automatically be created for that company.

---

## 12. Applications & Candidates

Base path: `/api/v1/applications/`

Viewset: `ApplicationViewSet` in `api/views.py`.

**Permissions and visibility:**

- Admin: all applications.
- Recruiter: applications for all jobs in their company.
- Candidate: only their own applications.

### 12.1. Submit an application

- `POST /api/v1/applications/`
- Requires `Authorization: Bearer <access_token>` as a candidate.
- `applicant` is automatically set to `request.user`.

The application contains:

- `job` (job ID)
- `resume_file` (uploaded file)
- `match_score` (optional, for AI results)
- `status` (workflow: pending, reviewed, rejected, hired)

### 12.2. Manage applications

- `GET /api/v1/applications/`
- `GET /api/v1/applications/{id}/`
- `PUT /api/v1/applications/{id}/`
- `DELETE /api/v1/applications/{id}/`

Recruiters can update statuses and add notes via additional fields you may introduce later.

---

## 13. AI Matching and Logs

### 13.1. AI match log model

`AIMatchLog` stores:

- `application` – FK to `Application`
- `similarity_score` – numeric match score
- `keywords_matched` – JSON list of important keywords
- `processed_at` – timestamp

### 13.2. AI match endpoint

- **Endpoint**: `GET /api/v1/ai/match/{id}/`
- **Permissions**: Authenticated
- **Behavior**:
  - `{id}` is an `Application.id`.
  - Returns the application and the latest `AIMatchLog` for it.

You can plug in your own AI matching pipeline that:

- Parses resumes
- Computes TF‑IDF and cosine similarity
- Stores results in `AIMatchLog` and `Application.match_score`

---

## 14. Payment Endpoints (Stripe & Khalti)

Base paths:

- `POST /api/v1/payments/stripe`
- `POST /api/v1/payments/khalti`

Currently implemented as stubs in `api/views.py`:

- Require authentication.
- Return a simple success response.

Integration steps (future work):

- Stripe:
  - Create payment intents
  - Handle checkout sessions
  - Verify webhooks and activate subscriptions
- Khalti:
  - Initiate payment
  - Verify tokens and signatures
  - Persist payment status and activate subscriptions

---

## 15. Rate Limiting & Security

### 15.1. Throttling

Configured in `REST_FRAMEWORK`:

- Anonymous users: `100/hour`
- Authenticated users: `1000/hour`

Helps protect from abuse and brute‑force attacks.

### 15.2. Audit logging

`UserAuditMiddleware` writes entries to `UserAuditLog`:

- `user` (if authenticated)
- `method`
- `path`
- `status_code`
- `ip_address`
- `created_at`

Useful for:

- Monitoring sensitive operations
- Debugging requests
- Auditing security events

---

## 16. Extending the System

This backend is designed to be extended with:

- Email verification and password reset flows
- Soft delete for entities
- Background workers (Celery) for:
  - Resume parsing
  - AI matching
  - Subscription expiry and notifications
- Full payment processing (Stripe/Khalti) and webhooks
- Notification system (emails, etc.)
- Admin‑only analytics and configuration APIs

When adding new endpoints:

1. Create or extend models in `api/models.py`.
2. Add serializers in `api/serializers.py`.
3. Implement views in `api/views.py` (use `api_success` / `api_error`).
4. Register URLs in `api/urls.py`.
5. Apply role permissions using the helpers from `api/permissions.py`.

---

## 17. Health Checks and Diagnostics

Useful commands:

- Basic system check:

  ```bash
  .venv\Scripts\python.exe manage.py check
  ```

- Run migrations:

  ```bash
  .venv\Scripts\python.exe manage.py migrate
  ```

- Run tests (once you add them):

  ```bash
  .venv\Scripts\python.exe manage.py test
  ```

---

## 18. Summary

The SmartHire backend provides:

- A secure, JWT‑based authentication system
- Role‑based access control and tenant‑aware data isolation
- Core APIs for companies, subscriptions, jobs, and applications
- AI logging hooks and payment endpoint stubs
- Environment‑aware configuration and audit logging

You can use this README as a guide to:

- Set up your local environment
- Integrate frontend or external services
- Extend the system with AI, payments, notifications, and admin features.

