
# MO App Backend

A Django REST API for managing **Customers**, **Loans** and **Payments**, with:

- 🔑 API‑Key authentication (`djangorestframework‑api‑key`)  
- ⚖️ CRUD plus business rules for Customers, Loans and Payments  
- 🐍 Python 3.12, Django 4.2, PostgreSQL  
- 🐳 Optional Docker & Docker Compose  
- 🛠️ Admin UI via Grappelli & Honeypot  
- 📄 API docs via Swagger & ReDoc  

---

## 🚀 Features

1. **Customers**  
   - Create & retrieve customers (unique `external_id`, `status` ACTIVE/INACTIVE, `score` line‑of‑credit).  
   - Bulk import via plain‑text file or background Celery task.  
   - Balance endpoint: total debt vs. available credit.  

2. **Loans**  
   - Create & retrieve loans (unique `external_id`, `amount`, `outstanding`, `status` PENDING/ACTIVE/REJECTED/PAID).  
   - Business logic to enforce credit limit and status transitions (`activate`, `reject`).  

3. **Payments**  
   - Create & retrieve payments (unique `external_id`, `total_amount`, `status` COMPLETED/REJECTED).  
   - Automatic distribution across active loans, updating each loan’s `outstanding` and `status`.  

4. **Admin UI**  
   - **Grappelli**‑styled Django admin at `/grappelli/`  
   - **Honeypot** fake‑admin at `/admin/` to log unauthorized login attempts  

5. **API Documentation**  
   - **Swagger** UI at `/swagger/`  
   - **ReDoc** UI at `/redoc/`  

---

## 🏗️ Project Structure

```
mo/                   ← Django “project” package
├─ apps/
│  ├─ authentication  ← API‑Key mixin, JWT, permissions
│  ├─ common          ← shared BaseModel, utilities
│  ├─ customers       ← customer model, serializers, views, tasks
│  ├─ loans           ← loan model, serializers, views, status actions
│  └─ payments        ← payment model, serializers, views, distribution logic
├─ Dockerfile         ← multi‑stage build with Poetry
├─ docker-compose.yml ← services: web, postgres, (opt: redis, celery)
├─ pyproject.toml     ← Poetry config
└─ manage.py
```

---

## ⚙️ Configuration

1. Copy `env.example` → `.env` **alongside** your `settings.py` (e.g. in the same directory as `mo/mo/settings.py`).  
2. Fill in values:

   ```dotenv
   # SECURITY
   SECRET_KEY="your-secret-key"
   DEBUG=True
   ALLOWED_HOSTS="*"
   CSRF_TRUSTED_ORIGINS="http://localhost:8000"

   # DATABASE (Postgres)
   DATABASE_NAME="mo2"
   DATABASE_USER="postgres"
   DATABASE_PASSWD="admin1234"
   # Local: 
   DATABASE_HOST="localhost"
   # Docker (host machine):
   # DATABASE_HOST="host.docker.internal"
   DATABASE_PORT="5432"

   # CORS
   CORS_ALLOWED_ORIGINS="http://localhost:8000"
   CORS_ALLOW_CREDENTIALS=True

   # CELERY (if USE_CELERY=True)
   CELERY_BROKER_URL="redis://redis:6379"
   CELERY_RESULT_BACKEND="redis://redis:6379"
   USE_CELERY=False

   # AWS S3 (optional)
   AWS_ACCESS_KEY_ID=""
   AWS_SECRET_ACCESS_KEY=""
   AWS_STORAGE_BUCKET_NAME=""
   AWS_S3_REGION_NAME=""
   AWS_S3_SIGNATURE_VERSION=""
   AWS_S3_ADDRESSING_STYLE=""

   # API‑Key header
   API_KEY_CUSTOM_HEADER="HTTP_X_API_KEY"

   # Admin URLs
   ADMIN_URL="admin"
   ADMIN_HONEYPOT_URL="admin-honeypot"

   # JWT / AuthToken / OTP
   AUTH_JWT_BEHIND_BASIC=True
   TOKEN_EXPIRED_AFTER_SECONDS=900
   OTP_TOKEN_EXPIRATION_TIME=300
   ```

---

## 🛠️ Installation

1. **Clone**  
   ```bash
   git clone <your‑repo‑url> mo-app-backend
   cd mo-app-backend
   ```

2. **Prepare `.env`** (see above).

3. **Dependencies**  
   ```bash
   pip install poetry
   poetry install
   ```

4. **Database migrations**  
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

5. **Create Superuser**  
   ```bash
   python manage.py createsuperuser
   ```
   Follow prompts to set email & password.

6. **Create an API Key**  
   - **Via shell**:
     ```bash
     python manage.py shell
     >>> from rest_framework_api_key.models import APIKey
     >>> _, key = APIKey.objects.create_key(name="test-client")
     >>> print(key)
     ```
   - **Or via Django admin** at `/admin/rest_framework_api_key/apikey/` — click **Add**.

7. **Run locally**  
   ```bash
   python manage.py runserver
   ```

---

## 🐳 Docker & Docker Compose (optional)

```bash
docker compose build
docker compose up -d
```

- **web**: Django + Gunicorn on 0.0.0.0:8080  
- **postgres**: PostgreSQL  
- *(Redis & Celery only if `USE_CELERY=True`)*  

---

## 📑 API Documentation

- **Swagger UI** → `http://localhost:8000/swagger/`  
- **ReDoc UI**  → `http://localhost:8000/redoc/`  

---

## 🔒 Security

- **API‑Key** enforced on every view via `ApiKeyProtectedViewMixin`.  
- **Admin Honeypot** at `/admin/` to trap fake‑login attempts.  
- **Grappelli**‑styled admin at `/grappelli/`.  

---

## 🔍 Testing & Coverage

- **Run tests**  
  ```bash
  python manage.py test
  ```
- **Coverage**  
  ```bash
  coverage run manage.py test
  coverage report  # aim ≥ 91%
  ```

---

## 🖊️ Code Quality

- **Black** (formatter)  
  ```bash
  black .
  ```
- **Ruff** (linter)  
  ```bash
  ruff .
  ```
_Pre‑commit hooks run both on every commit._

---

## 🙌 Contributing

1. Fork this repo  
2. Create feature branch (`git checkout -b feat/…`)  
3. Commit & push (`git commit -am 'Add feature' && git push`)  
4. Open a Pull Request, ensure tests & linters pass  

---