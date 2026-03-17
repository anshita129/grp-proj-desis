# GRP DESIS - Stock Market Learning Platform

This repository contains the source code for a comprehensive Stock Market Learning and Trading Simulation Platform. It features a Django backend providing a RESTful API and a React (Vite) frontend with a modern UI.

## Project Structure

- `backend/`: Django project providing REST APIs, authentication, and database models.
- `frontend/`: React application built with Vite and TailwindCSS v4.

---

## 🚀 Running the Backend (Django)

The backend is built with Django and Django REST Framework. It uses SQLite for local development.

### Prerequisites
- Python 3.8+ 

### 1. Setup Virtual Environment
Navigate to the backend directory and create a virtual environment:
```bash
cd backend
python3 -m venv venv
```

### 2. Activate the Virtual Environment
- **Mac/Linux:**
  ```bash
  source venv/bin/activate
  ```
- **Windows:**
  ```bash
  venv\Scripts\activate
  ```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```
*(If `requirements.txt` is missing, you can install the core packages manually: `pip install django djangorestframework django-cors-headers python-dotenv psycopg2-binary`)*

### 4. Setup Database & Migrations
Ensure you have a `.env` file in the `backend/` directory with `DB_ENGINE=django.db.backends.sqlite3` for local development. Then run:
```bash
python manage.py makemigrations
python manage.py migrate
```

### 5. Create a Superuser (For Admin Access)
You need an admin account to access the Django admin panel and manage content:
```bash
python manage.py createsuperuser
```
*(Follow the prompts to enter a username, email, and password).*

### 6. Run the Development Server
```bash
python manage.py runserver
```
The backend API and Admin Panel will now be running at [http://localhost:8000](http://localhost:8000).
- Admin Panel: [http://localhost:8000/admin/](http://localhost:8000/admin/)

### 7. Seed Initial Data (Optional)
To populate the Learning Module with modules, lessons, quizzes, and badges:
```bash
python manage.py seed_learning
```

---

## 🚀 Running the Frontend (React + Vite)

The frontend is a single-page application (SPA) built with React, Vite, React Router DOM, and TailwindCSS v4. It is configured to proxy API requests to the Django backend.

### Prerequisites
- Node.js (v18+)
- npm

### 1. Install Dependencies
Open a **new terminal window/tab**, navigate to the frontend directory, and install the Node packages:
```bash
cd frontend
npm install
```

### 2. Run the Development Server
Start the Vite development server:
```bash
npm run dev
```
The frontend application will now be running at [http://localhost:5173](http://localhost:5173).

---

## 🔑 Logging In (Important for API Access)

Because the API uses Session Authentication, you must log in to establish a session cookie before using the application features.

1. Ensure **both** the backend (`localhost:8000`) and the frontend (`localhost:5173`) are running.
2. Go to **[http://localhost:5173/admin](http://localhost:5173/admin)** in your browser *(Notice this is on the frontend's port 5173 — the frontend is proxying it to Django)*.
3. Log in with the **Superuser credentials** you created earlier.
4. After logging in, navigate to **[http://localhost:5173/learning](http://localhost:5173/learning)** to view the Learning Modules!

### Why login via port 5173?
The Vite server proxies `/api` and `/admin` to Django. By logging in through `localhost:5173/admin`, the session cookie is assigned to the `localhost:5173` origin, allowing the React API calls to authenticate successfully.

---

## ✉️ Password Reset OTP Email (SMTP)

By default, the backend prints outgoing emails to the terminal because `EMAIL_BACKEND` defaults to Django's console email backend. To send the password reset OTP to a real inbox, configure SMTP in `backend/.env` (or your environment):

```env
# Turn on real email sending (either set EMAIL_BACKEND or set EMAIL_HOST)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend

EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=true
EMAIL_HOST_USER=your_email@gmail.com
EMAIL_HOST_PASSWORD=your_app_password

DEFAULT_FROM_EMAIL="GRP DESIS <your_email@gmail.com>"
```

Then restart the Django server.
