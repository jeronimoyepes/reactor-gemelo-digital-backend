# Reactor Backend API

A simple Python API backend using Bottle framework with SQLite database and token-based authentication.

## Setup

### Option 1: Local Development

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Copy environment file:
```bash
cp env.example .env
```

3. Customize the `.env` file with your settings (optional)

4. Run the application:
```bash
python app.py
```

### Option 2: Docker Development

1. Copy environment file:
```bash
cp env.example .env
```

2. Customize the `.env` file with your settings (optional)

3. Build and run with Docker Compose:
```bash
docker-compose up --build
```

### Option 3: Docker Production

1. Build production image:
```bash
docker build -f Dockerfile.prod -t reactor-backend:prod .
```

2. Run production container:
```bash
docker run -d \
  --name reactor-backend \
  -p 8080:8080 \
  -e DEFAULT_ADMIN_PASSWORD=your_secure_password \
  -v $(pwd)/data:/app/data \
  reactor-backend:prod
```

The server will start on `http://localhost:8080` and automatically create the database with a default admin user.

## Environment Variables

Copy `env.example` to `.env` and customize the following variables:

### Database Configuration
- `DB_PATH`: Database file path (default: `users.db`)
- `DB_TYPE`: Database type (default: `sqlite`)

### Server Configuration
- `HOST`: Server host (default: `localhost` for local, `0.0.0.0` for Docker)
- `PORT`: Server port (default: `8080`)
- `DEBUG`: Enable debug mode (default: `true`)
- `RELOADER`: Enable auto-reload (default: `true`)

### Authentication Settings
- `DEFAULT_ADMIN_USERNAME`: Default admin username (default: `admin`)
- `DEFAULT_ADMIN_PASSWORD`: Default admin password (default: `admin123`)
- `SESSION_EXPIRY_HOURS`: Session expiration time in hours (default: `24`)

### Security Settings
- `TOKEN_LENGTH`: Length of session tokens (default: `32`)

## Default Credentials

- **Username**: `admin` (configurable via `DEFAULT_ADMIN_USERNAME`)
- **Password**: `admin123` (configurable via `DEFAULT_ADMIN_PASSWORD`)

## API Endpoints

### Authentication

#### POST /login
Login with username and password.

**Request Body:**
```json
{
    "username": "admin",
    "password": "admin123"
}
```

**Response:**
```json
{
    "token": "your_session_token",
    "expires_at": "2024-01-01T12:00:00",
    "message": "Login successful"
}
```

#### POST /logout
Logout and invalidate the current session token.

**Headers:**
```
Authorization: Bearer your_session_token
```

**Response:**
```json
{
    "message": "Logout successful"
}
```

### User Profile

#### GET /profile
Get the current user's profile information.

**Headers:**
```
Authorization: Bearer your_session_token
```

**Response:**
```json
{
    "username": "admin",
    "created_at": "2024-01-01T10:00:00"
}
```

### Health Check

#### GET /health
Check if the API is running.

**Response:**
```json
{
    "status": "ok",
    "message": "API is running"
}
```

## Database Schema

### Users Table
- `id`: Primary key
- `username`: Unique username
- `password_hash`: SHA256 hash of password
- `created_at`: User creation timestamp

### Sessions Table
- `id`: Primary key
- `user_id`: Foreign key to users table
- `token`: Unique session token
- `created_at`: Session creation timestamp
- `expires_at`: Session expiration timestamp

## Testing with curl

```bash
# Login
curl -X POST http://localhost:8080/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'

# Get profile (replace YOUR_TOKEN with the token from login response)
curl -X GET http://localhost:8080/profile \
  -H "Authorization: Bearer YOUR_TOKEN"

# Logout
curl -X POST http://localhost:8080/logout \
  -H "Authorization: Bearer YOUR_TOKEN"

# Health check
curl -X GET http://localhost:8080/health
``` 