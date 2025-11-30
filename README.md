# Minimalist Web App

## Prerequisites
- Docker & Docker Compose installed.
- Python 3.11+ (for local script execution if desired, though scripts run in docker too).

## Startup
1.  **Start Services**:
    ```bash
    docker compose up --build
    ```
    *Wait for `backend` and `frontend` to be ready.*

2.  **Access Application**:
    - Frontend: [http://localhost:5173](http://localhost:5173)
    - Backend API Docs: [http://localhost:8000/docs](http://localhost:8000/docs)

## User Management
Since public registration is disabled, you must create the first user via CLI.

**Password Requirements:**
- At least 8 characters
- At least one number
- At least one uppercase letter
- At least one lowercase letter

1.  **Create Admin User**:
    Open a new terminal and run:
    ```bash
    docker compose exec backend python scripts/manage_user.py admin@example.com Admin123 --admin
    ```
    **Default Admin Credentials:**
    - Email: `admin@example.com`
    - Password: `Admin123`
    
    *(Note: The `scripts` folder is mounted to `/app/scripts` in the container.)*

2.  **Create Regular (Non-Admin) User**:
    ```bash
    docker compose exec backend python scripts/manage_user.py user@example.com User123
    ```
    (Omit the `--admin` flag for regular users)

## Database Management

### Reset Database (Start from Scratch)
If you need to completely reset the database and start fresh:

1.  **Stop all services and remove volumes**:
    ```bash
    docker compose down -v
    ```
    This will:
    - Stop all running containers
    - Remove the `postgres_data` volume (⚠️ **all data will be lost**)
    - Remove the network

2.  **Start services again**:
    ```bash
    docker compose up --build
    ```

3.  **Recreate your admin user**:
    ```bash
    docker compose exec backend python scripts/manage_user.py admin@example.com Admin123 --admin
    ```

### Stop Services (Keep Data)
To stop services without losing data:
```bash
docker compose down
```

### View Logs
```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f backend
docker compose logs -f frontend
```

## SMTP Configuration (Password Reset)

To enable password reset functionality, configure SMTP settings in `.env`:

### Using Gmail
1. Enable 2-Factor Authentication on your Google account
2. Generate an App Password: https://myaccount.google.com/apppasswords
3. Update `.env`:
   ```env
   SMTP_HOST=smtp.gmail.com
   SMTP_PORT=587
   SMTP_USER=your-email@gmail.com
   SMTP_PASSWORD=your-16-char-app-password
   EMAILS_FROM_EMAIL=your-email@gmail.com
   ```

### Using Mailtrap (Testing)
1. Sign up at https://mailtrap.io (free tier available)
2. Get SMTP credentials from your inbox
3. Update `.env` with Mailtrap credentials

### Testing Password Reset
1. Go to http://localhost:5173/forgot-password
2. Enter your email address
3. Check your email for the reset link (or check logs if SMTP not configured)
4. Click the link or visit `/reset-password?token=<token>`

> **Note**: If SMTP is not configured, the reset token will be logged to `logs/backend.log` for testing.

## Database Access

PostgreSQL is exposed on port `5432` for development. Connect using:
```bash
psql -h localhost -p 5432 -U postgres -d app_db
# Password: postgres (from .env)
```

Or use GUI tools like pgAdmin, DBeaver, or TablePlus.

## Verification Steps

### 1. Automated Tests
Run the unit tests inside the backend container:
```bash
docker compose exec backend pytest
```
*Expected Output*: All tests passed (Logic & Auth).

### 2. Manual Verification (Frontend)
1.  Go to [http://localhost:5173](http://localhost:5173).
2.  Redirects to `/login`.
3.  Login with `admin@example.com` / `Admin123`.
4.  You should see the **Dashboard**.
5.  Enter `10` and `20` in the inputs.
6.  Click **Calculate**. Result `30` should appear.
7.  Check logs: `tail -f logs/backend.log`. You should see the request logged.

### 2. Access the Application
**Via Nginx (Port 80):**
```bash
open http://localhost
```

**Direct Access (Development):**
```bash
# Frontend
open http://localhost:5173

# Backend API docs
open http://localhost:8000/docs
```

### 3. Python Client Verification
Run the client script (requires `httpx` installed locally, or run in container):
```bash
# Locally
pip install httpx
python scripts/client.py
```
*Expected Output*: Login successful, Sum result: 30.

## API Usage with HTTPie

You can interact with the API using [HTTPie](https://httpie.io/).

### 1. Login & Get Token
```bash
http --session=./session.json POST http://localhost:8000/auth/jwt/login username=admin@example.com password=Admin123
```

### 2. Get User Profile
```bash
http --session=./session.json GET http://localhost:8000/users/me
```

### 3. Calculate Sum
```bash
http --session=./session.json POST http://localhost:8000/api/sum a:=10 b:=20
```

### 4. Register New User
```bash
http POST http://localhost:8000/auth/register email=newuser@example.com password=SecurePass123 is_active:=true is_superuser:=false is_verified:=false
```
