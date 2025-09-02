# User Service Microservice

A comprehensive user management microservice built with FastAPI, JWT authentication, and PostgreSQL. This service provides complete user account management, authentication, profile management, and session handling.

## Features

### 🔐 Authentication & Security
- **JWT-based authentication** with access and refresh tokens
- **Password hashing** using bcrypt
- **Session management** with device tracking
- **Password reset** functionality
- **Email verification** system
- **Token revocation** and cleanup

### 👤 User Management
- **User registration** with validation
- **Profile management** (basic and extended profiles)
- **User preferences** for job matching
- **Account status** management (active/inactive, verified/unverified)
- **Premium subscription** management

### 🛡️ Security Features
- **Input validation** with Pydantic schemas
- **Password strength** requirements
- **Rate limiting** (configurable)
- **CORS** protection
- **Session tracking** and management
- **Token expiration** and cleanup

### 📊 Monitoring & Health
- **Health check** endpoints
- **Database connection** monitoring
- **Service metrics** collection
- **Comprehensive logging**
- **Error handling** and reporting

## Architecture

```
user-service/
├── app/
│   ├── models/
│   │   ├── user_models.py      # Database models
│   │   └── schemas.py          # Pydantic schemas
│   ├── routers/
│   │   ├── auth_routes.py      # Authentication endpoints
│   │   └── user_routes.py      # User management endpoints
│   ├── services/
│   │   └── user_service.py     # Business logic
│   ├── utils/
│   │   └── auth.py            # JWT and auth utilities
│   └── database.py            # Database configuration
├── main.py                    # FastAPI application
├── requirements.txt           # Dependencies
├── env.example               # Environment configuration
└── README.md                 # This file
```

## Database Schema

### Core Tables
- **users** - Main user accounts
- **user_profiles** - Extended profile information
- **user_preferences** - Job matching preferences
- **user_sessions** - Active user sessions
- **refresh_tokens** - JWT refresh tokens
- **password_resets** - Password reset tokens
- **email_verifications** - Email verification tokens

## API Endpoints

### Authentication (`/api/v1/auth`)
- `POST /register` - User registration
- `POST /login` - User login
- `POST /refresh` - Refresh access token
- `POST /logout` - Logout user
- `POST /logout-all` - Logout from all devices
- `POST /password-reset-request` - Request password reset
- `POST /password-reset-confirm` - Confirm password reset
- `POST /verify-email-request` - Request email verification
- `POST /verify-email` - Verify email with token
- `GET /me` - Get current user info
- `POST /change-password` - Change password
- `GET /sessions` - Get user sessions
- `DELETE /sessions/{session_id}` - Revoke session

### User Management (`/api/v1/users`)
- `GET /me` - Get current user profile
- `PUT /me` - Update current user profile
- `GET /me/profile` - Get extended profile
- `PUT /me/profile` - Update extended profile
- `GET /me/preferences` - Get user preferences
- `PUT /me/preferences` - Update user preferences
- `GET /me/stats` - Get user statistics
- `DELETE /me` - Delete account
- `POST /me/upgrade` - Upgrade to premium
- `POST /me/downgrade` - Downgrade to basic
- `GET /search` - Search users (premium)
- `GET /{user_id}` - Get user by ID (premium)
- `GET /{user_id}/profile` - Get user profile (premium)
- `GET /{user_id}/preferences` - Get user preferences (premium)

### System Endpoints
- `GET /` - Service information
- `GET /health` - Health check
- `GET /metrics` - Service metrics
- `GET /db/status` - Database status

## Installation & Setup

### Prerequisites
- Python 3.8+
- PostgreSQL 12+
- pip

### 1. Clone and Setup
```bash
# Navigate to user-service directory
cd user-service

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Database Setup
```bash
# Create PostgreSQL database
createdb user_service_db

# Set up environment variables
cp env.example .env
# Edit .env with your database credentials
```

### 3. Environment Configuration
Edit `.env` file with your configuration:
```env
# Database
DATABASE_URL=postgresql://username:password@localhost:5432/user_service_db

# JWT Secret (generate a secure key)
JWT_SECRET_KEY=your-super-secret-jwt-key

# Other settings...
```

### 4. Run the Service
```bash
# Development mode
python main.py

# Or with uvicorn directly
uvicorn main:app --host 0.0.0.0 --port 8001 --reload
```

## Usage Examples

### User Registration
```bash
curl -X POST "http://localhost:8001/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "username": "testuser",
    "full_name": "Test User",
    "password": "SecurePass123",
    "confirm_password": "SecurePass123"
  }'
```

### User Login
```bash
curl -X POST "http://localhost:8001/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecurePass123"
  }'
```

### Update Profile
```bash
curl -X PUT "http://localhost:8001/api/v1/users/me" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "full_name": "Updated Name",
    "current_title": "Software Engineer",
    "location": "San Francisco, CA"
  }'
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | - |
| `JWT_SECRET_KEY` | Secret key for JWT tokens | - |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Access token expiration | 30 |
| `REFRESH_TOKEN_EXPIRE_DAYS` | Refresh token expiration | 7 |
| `ALLOWED_ORIGINS` | CORS allowed origins | * |
| `DB_POOL_SIZE` | Database connection pool size | 10 |
| `DB_MAX_OVERFLOW` | Database pool max overflow | 20 |

### Security Settings

- **Password Requirements**: Minimum 8 characters, uppercase, lowercase, digits
- **JWT Token Expiration**: 30 minutes (access), 7 days (refresh)
- **Session Management**: Automatic cleanup of expired tokens
- **Rate Limiting**: Configurable per endpoint

## Development

### Running Tests
```bash
# Install test dependencies
pip install pytest pytest-asyncio pytest-cov

# Run tests
pytest

# Run with coverage
pytest --cov=app
```

### Database Migrations
```bash
# Install Alembic
pip install alembic

# Initialize migrations
alembic init alembic

# Create migration
alembic revision --autogenerate -m "Initial migration"

# Apply migrations
alembic upgrade head
```

### Code Quality
```bash
# Install development tools
pip install black flake8 mypy

# Format code
black app/

# Lint code
flake8 app/

# Type checking
mypy app/
```

## Deployment

### Docker Deployment
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8001

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
```

### Production Considerations
- Use environment-specific configurations
- Set up proper logging and monitoring
- Configure database connection pooling
- Implement rate limiting
- Set up SSL/TLS certificates
- Use secure JWT secrets
- Configure backup strategies

## API Documentation

Once the service is running, you can access:
- **Swagger UI**: http://localhost:8001/docs
- **ReDoc**: http://localhost:8001/redoc
- **Health Check**: http://localhost:8001/health
- **Metrics**: http://localhost:8001/metrics

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Run the test suite
6. Submit a pull request

## License

This project is licensed under the MIT License.

## Support

For support and questions:
- Create an issue in the repository
- Check the API documentation
- Review the logs for debugging information

