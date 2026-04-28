# 🎓 Campus 360 – This is a Production level AI Powered Role-Based System

## 🚀 Overview

Campus 360 is a full-stack Django-based web application with:

* Role-based authentication (Student / Teacher / Admin)
* Google OAuth login integration
* Admin approval system for teachers
* AI-powered assistant (via Hugging Face API)

---

## 🔐 Authentication Features

* Manual login & registration
* Google login (OAuth)
* Role selection after social login
* Teacher approval workflow
* Secure role-based dashboard access

---

## 🤖 AI Integration

* Connected to Hugging Face API
* Provides intelligent responses inside the system

---

## 🛠 Tech Stack

* Backend: Django
* Frontend: HTML, Bootstrap
* Auth: Django Allauth (Google OAuth)
* AI: Hugging Face API
* Deployment: Railway

---

## ⚙️ Setup Instructions

### 1. Clone repo

git clone https://github.com/YOUR_USERNAME/YOUR_REPO.git
cd YOUR_REPO

### 2. Create virtual environment

python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

### 3. Install dependencies

pip install -r requirements.txt

### 4. Setup environment variables

Create `.env` file:

SECRET_KEY=your_secret
DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost

GOOGLE_CLIENT_ID=your_id
GOOGLE_SECRET=your_secret

HUGGINGFACE_API_KEY=your_api_key

### 5. Run server

python manage.py migrate
python manage.py runserver

---

## 🌐 Deployment

This project is production-ready and deployable on Railway.

---

## 📌 Future Enhancements

* Email notifications for teacher approval
* Profile completion system
* Advanced AI features

---
