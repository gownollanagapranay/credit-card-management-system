# Credit Card Payment Processing System

A financial microservices project built with Django, FastAPI, and MySQL. It runs locally on Windows without Docker.

## Features

- Module 1 (Auth): User Registration and Login with JWT authentication (Django).
- Module 2 (Card Management): Add, view, and delete cards. Raw card numbers and CVVs are never saved; only masked numbers and hashes are stored (Django).
- Module 3 (Payment Gateway): Real-time payment processing with status transitions (PENDING -> SUCCESS or FAILED) (FastAPI).
- Module 4 (Transactions): View audit history and transaction logs per user (Django).
- Frontend: Lightweight dashboard (HTML/CSS/JS) to test all modules.

## Tech Stack

- Database: MySQL Server 8.4 & MySQL Workbench
- Backend 1: Django 5.x, Django REST Framework, PyMySQL
- Backend 2: FastAPI, Uvicorn, SQLAlchemy
- Frontend: HTML5, CSS3, JavaScript

## Project Structure

```text
credit-card-payment-system/
│
├── backend/
│   ├── django_service/     # Auth, Card Management, Transactions (Port 8000)
│   └── fastapi_service/    # Payment Processing Gateway (Port 8001)
├── frontend/               # Web UI (Port 5173)
├── .env.example
├── .gitignore
└── README.md
```

## Setup & Installation

### 1. Database Setup

Open MySQL Workbench and run:

```sql
CREATE DATABASE credit_card_payment_db1;
```

### 2. Environment Variables

Create a .env file in the root directory:

```dotenv
MYSQL_DATABASE=credit_card_payment_db1
MYSQL_USER=root
MYSQL_PASSWORD=YOUR_MYSQL_PASSWORD
MYSQL_HOST=127.0.0.1
MYSQL_PORT=3306

DJANGO_SECRET_KEY=your-django-secret-key
DJANGO_DEBUG=True

JWT_SECRET_KEY=super-secure-shared-jwt-secret-key-for-django-and-fastapi-32bytes
JWT_ALGORITHM=HS256
```

### 3. Install Dependencies

Open Command Prompt / PowerShell in the project root:

```powershell
python -m venv venv
venv\Scripts\activate

pip install -r backend/django_service/requirements.txt
pip install -r backend/fastapi_service/requirements.txt
```

### 4. Database Migrations

```powershell
cd backend\django_service
python manage.py makemigrations core
python manage.py migrate
python manage.py createsuperuser
```

## Running the Project

Open 3 separate terminals (activate venv\Scripts\activate in each):

### Terminal 1: Django (Port 8000)

```powershell
cd backend\django_service
python manage.py runserver 127.0.0.1:8000
```



### Terminal 2: FastAPI (Port 8001)

```powershell
cd backend\fastapi_service
uvicorn app.main:app --reload --host 127.0.0.1 --port 8001
```

### Terminal 3: Frontend (Port 5173)

```powershell
cd frontend
python -m http.server 5173
```


### Terminal 1: Django Admin page

-> python manage.py createsuperuser # to access admin pannel

-> You will be prompted to enter:
Username: (e.g., admin)
Email address: (e.g., admin@example.com or press Enter to skip)
Password: (type a secure password; the characters will not show while typing)
Password (again): (re-enter the password)

-> re-start the server: python manage.py runserver 127.0.0.1:8000


## Key URLs

- Frontend Dashboard: [http://127.0.0.1:5173](http://127.0.0.1:5173)
- FastAPI Swagger Docs: [http://127.0.0.1:8001/docs](http://127.0.0.1:8001/docs)
- Django Admin Panel: [http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/)