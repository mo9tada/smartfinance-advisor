# 🚀 Smart Finance Advisor - Getting Started

This guide covers everything you need to run the newly updated platform with **Authentication** and **Admin Management**.

## 📋 System Requirements
- **Python 3.10+** (Backend)
- **Node.js 18+** & **npm** (Frontend)
- **PostgreSQL** (Database)

---

## 🛠️ One-Time Setup

### 1. Database Configuration
Ensure your PostgreSQL database `trading_pipeline` is running. 
The system now uses a dedicated `auth` schema. If you haven't run the migration yet, use the `move_to_auth_schema.sql` found in the backend folder.

### 2. Backend Dependencies
In a terminal, navigate to the project root and run:
```powershell
pip install flask-jwt-extended flask-bcrypt flask-mail python-dotenv psycopg2-binary
```

### 3. SMTP Mail Configuration (.env)
Create a `.env` file at the project root and set:

```env
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your_email@gmail.com
MAIL_PASSWORD=your_app_password
MAIL_DEFAULT_SENDER=your_email@gmail.com
```

Without these values, account approval and forgot-password emails cannot be delivered.

### 4. Frontend Dependencies
Navigate to the `frontend` folder and run:
```powershell
npm install
```

---

## 🏃 How to Run the Application

You must have **two terminals** running at the same time:

### Terminal 1: Backend (Flask API)
```powershell
cd v4/backend
python start_api.py
```
*API will be available at: http://localhost:5000*

### Terminal 2: Frontend (Angular Dashboard)
```powershell
cd v4/frontend
npm start
```
*Dashboard will open at: http://localhost:4200*

---

## 🔑 Your Credentials

### Administrator Account
Use this to access the dashboard and approve new users:
- **Matricule**: `SFA-0001`
- **Password**: the value of `SEED_ADMIN_PASSWORD`, or the random password printed by `seed_admin.py`

### New User Registration Flow
1.  Navigate to `http://localhost:4200/register`.
2.  Fill in the details for a new user and click **Request Account**.
3.  Log out and log back in as the **Administrator** (`SFA-0001`).
4.  Go to **Administration > Pending Requests** in the sidebar.
5.  **Approve** the new user.
6.  The user can now log in with their generated Matricule.

---

## 📊 Technical Summary of Changes
- **New Auth Schema**: Users moved to a secure `auth` schema in PostgreSQL for better data isolation.
- **Standalone Login**: The login flow is now isolated from the dashboard (no sidebar/navbar until login).
- **Security**: JWT-based authentication with Bcrypt password hashing.
- **Admin Dashboard**: Real-time management of user approvals and account settings.
- **Dynamic UI**: Layout adapts to the user's role and displays profile initials/name in the topbar.
