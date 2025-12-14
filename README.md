# 🏠 HomeStock

**Modern Home Inventory Management System**

HomeStock is a full-stack web application designed to help you track and manage your home inventory with ease. Keep tabs on food items, household supplies, and equipment with a clean, intuitive interface.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/)
[![React 19](https://img.shields.io/badge/react-19-blue.svg)](https://reactjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-green.svg)](https://fastapi.tiangolo.com/)
[![PostgreSQL 17](https://img.shields.io/badge/postgresql-17-blue.svg)](https://www.postgresql.org/)

---

## ✨ Features

- 📦 **Inventory Management** - Track food, household items, and supplies
- 🔍 **Smart Search** - Quickly find items with fuzzy search
- 📊 **Categories & Units** - Organize items with custom categories and units
- 👥 **User Management** - Secure multi-user support with JWT authentication
- 📱 **Responsive Design** - Works seamlessly on desktop, tablet, and mobile
- 🔒 **Security First** - Argon2id password hashing, JWT tokens, rate limiting
- 🐳 **Docker Ready** - One-command deployment with Docker Compose
- 📈 **Real-time Updates** - Optimistic UI updates for instant feedback

---

## 🛠️ Tech Stack

### Backend
- **[FastAPI](https://fastapi.tiangolo.com/)** - High-performance Python web framework
- **[PostgreSQL 17](https://www.postgresql.org/)** - Robust relational database
- **[SQLAlchemy 2.0](https://www.sqlalchemy.org/)** - SQL toolkit and ORM
- **[Pydantic](https://pydantic.dev/)** - Data validation with Python type hints
- **[Passlib](https://passlib.readthedocs.io/)** - Argon2id password hashing
- **[PyJWT](https://pyjwt.readthedocs.io/)** - JWT authentication with Ed25519

### Frontend
- **[React 19](https://react.dev/)** - Modern UI library
- **[TypeScript](https://www.typescriptlang.org/)** - Type-safe JavaScript
- **[Vite](https://vitejs.dev/)** - Lightning-fast build tool
- **[Tailwind CSS v4](https://tailwindcss.com/)** - Utility-first CSS framework

### Infrastructure
- **[Docker](https://www.docker.com/)** - Containerization
- **[Docker Compose](https://docs.docker.com/compose/)** - Multi-container orchestration

---

## 🚀 Quick Start

### Prerequisites
- Linux server (Debian/Ubuntu recommended)
- Docker and Docker Compose
- 4GB RAM minimum
- 20GB disk space

### Automated Installation (Recommended)

The easiest way to deploy HomeStock is using our interactive deployment script:

```bash
# Clone the repository
git clone https://github.com/yourusername/HomeStock.git
cd HomeStock

# Make the deployment script executable
chmod +x deploy.sh

# Run the deployment script
./deploy.sh
```

The script will:
- ✅ Install Docker and Docker Compose (if needed)
- ✅ Guide you through configuration with interactive prompts
- ✅ Generate secure random passwords
- ✅ Create and configure your `.env` file
- ✅ Start all services with Docker Compose
- ✅ Display your admin credentials

**Important:** Save the displayed credentials immediately - they won't be shown again!

---

## 📋 Manual Installation

If you prefer manual setup or need more control:

### 1. Install Docker

```bash
# Update package list
sudo apt update

# Install Docker and Docker Compose
sudo apt install -y docker.io docker-compose

# Start Docker service
sudo systemctl start docker
sudo systemctl enable docker

# Add your user to docker group
sudo usermod -aG docker $USER
# Log out and back in for this to take effect
```

### 2. Configure Environment

```bash
# Copy the example environment file
cp .env.example .env

# Edit the .env file with your settings
nano .env
```

**Critical `.env` settings:**
```bash
# Production environment
ENVIRONMENT=production

# Database credentials (change these!)
POSTGRES_USER=homestock_app
POSTGRES_PASSWORD=<your-secure-password>
POSTGRES_DB=homestock

# CORS origins (use your actual domain/IP)
CORS_ORIGINS=http://your-domain.com

# JWT expiry (minutes)
JWT_EXPIRY_MINUTES=30

# Cookie security
COOKIE_SECURE=true  # Set to true if using HTTPS
COOKIE_SAMESITE=strict

# Rate limiting
RATELIMIT_ENABLED=true
```

### 3. Start Services

```bash
# Start all services in detached mode
docker-compose up -d

# View logs
docker-compose logs -f

# Check service status
docker-compose ps
```

### 4. Get Admin Credentials

On first startup, a default admin user is created with a randomly generated password:

```bash
# View the generated password in logs
docker-compose logs backend | grep "Default Password"
```

**Save these credentials immediately!**

---

## 🔧 Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `ENVIRONMENT` | `development` | Deployment environment (`development` or `production`) |
| `POSTGRES_USER` | `homestock_app` | Database username |
| `POSTGRES_PASSWORD` | - | Database password (**required**) |
| `POSTGRES_DB` | `homestock` | Database name |
| `CORS_ORIGINS` | `http://localhost:5173` | Comma-separated allowed origins |
| `JWT_EXPIRY_MINUTES` | `30` | JWT token expiration time |
| `COOKIE_SECURE` | `false` | Enable secure cookies (requires HTTPS) |
| `COOKIE_SAMESITE` | `lax` | Cookie SameSite attribute (`strict`, `lax`, or `none`) |
| `RATELIMIT_ENABLED` | `true` | Enable API rate limiting |

### Ports

- **8000** - Backend API
- **5173** - Frontend application
- **5432** - PostgreSQL (container only, not exposed to host)

---

## 📱 Usage

### Accessing the Application

After deployment, access HomeStock at:

- **Frontend:** `http://your-server:5173`
- **API:** `http://your-server:8000`
- **API Docs:** `http://your-server:8000/docs` (development mode only)

### First Login

1. Navigate to `http://your-server:5173`
2. Log in with the admin credentials from deployment logs
3. **Change your password immediately** via the settings page

### Managing Inventory

1. **Add Items** - Click the "+" button to add new inventory items
2. **Edit Items** - Click the edit button on any item to modify details
3. **Adjust Quantity** - Use +/- buttons or enter quantity directly
4. **Search** - Use the search bar to quickly find items
5. **Filter** - Switch between Food and Household inventory types

### User Management

Admins can manage users via the API:

- **Create User:** `POST /api/auth/register`
- **List Users:** `GET /api/auth/users`
- **Delete User:** `DELETE /api/auth/users/{user_id}`

See API documentation at `/docs` for detailed endpoint information.

---

## 🛡️ Security Features

HomeStock implements industry-standard security practices:

- **🔐 Argon2id Password Hashing** - 64MB memory, 3 iterations, 4 threads
- **🔑 Ed25519 JWT Signing** - Modern elliptic curve cryptography
- **🍪 HttpOnly Cookies** - XSS attack prevention
- **⏱️ Constant-Time Authentication** - Prevents username enumeration via timing attacks
- **🚦 Rate Limiting** - Prevents brute force and DoS attacks
- **🔒 JWT Blacklist** - Secure logout and session revocation
- **✅ Input Validation** - Pydantic schemas validate all user input
- **🛡️ SQL Injection Prevention** - Parameterized queries throughout
- **📜 CORS Configuration** - Explicit origin whitelist

---

## 🧑‍💻 Development

### Local Development Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/HomeStock.git
cd HomeStock

# Start services
docker-compose up

# Backend will be available at http://localhost:8000
# Frontend will be available at http://localhost:5173
```

### Running Tests

```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test
```

### Database Access

```bash
# Access PostgreSQL shell
docker exec -it homestock-db psql -U homestock-app -d homestock

# Set search path
SET search_path = homestock;

# Query items
SELECT * FROM items;
```

### Hot Reload

Both frontend and backend support hot reload during development:
- **Backend:** Volume-mounted source code with `uvicorn --reload`
- **Frontend:** Vite HMR (Hot Module Replacement)

---

## 📚 API Documentation

When running in development mode, interactive API documentation is available:

- **Swagger UI:** `http://localhost:8000/docs`
- **ReDoc:** `http://localhost:8000/redoc`

### Key Endpoints

#### Authentication
- `POST /api/auth/token` - Login and receive JWT token
- `POST /api/auth/register` - Register new user (requires auth)
- `POST /api/auth/logout` - Logout and revoke token
- `GET /api/auth/me` - Get current user info

#### Items
- `GET /api/items` - List items (paginated)
- `POST /api/items` - Create new item
- `GET /api/items/{id}` - Get item details
- `PATCH /api/items/{id}` - Update item
- `PATCH /api/items/{id}/stock` - Adjust quantity
- `DELETE /api/items/{id}` - Delete item

#### Metadata
- `GET /api/healthz` - Health check endpoint
- `GET /api/categories` - List categories
- `GET /api/units` - List units

---

## 🔄 Common Operations

### Update Application

```bash
# Pull latest changes
git pull

# Rebuild and restart containers
docker-compose up -d --build
```

### Backup Database

```bash
# Export database to SQL file
docker-compose exec db pg_dump -U homestock_app homestock > backup.sql

# Restore from backup
cat backup.sql | docker exec -i homestock_db psql -U homestock_app homestock
```

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f db
```

### Stop Services

```bash
# Stop containers (data persists)
docker-compose stop

# Stop and remove containers (data persists in volumes)
docker-compose down

# Stop and remove everything including volumes (⚠️ deletes data!)
docker-compose down -v
```

---

## 🐛 Troubleshooting

### "Cannot connect to database"

**Solution:** Check if PostgreSQL container is running
```bash
docker-compose ps
docker-compose logs db
```

### "Authentication failed"

**Solution:** Check credentials in logs and verify .env configuration
```bash
docker-compose logs backend | grep "Default Password"
```

### "Port already in use"

**Solution:** Stop conflicting services or change ports in `docker-compose.yml`
```bash
# Check what's using port 8000
sudo lsof -i :8000

# Or change the port in docker-compose.yml
```

### "Frontend can't reach backend"

**Solution:** Verify CORS_ORIGINS in `.env` matches your frontend URL
```bash
# Example for localhost
CORS_ORIGINS=http://localhost:5173

# Example for production
CORS_ORIGINS=https://homestock.example.com
```

---

## 📊 Project Structure

```
HomeStock/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── routers/          # API endpoints
│   │   │   ├── services/         # Business logic
│   │   │   └── schemas.py        # Pydantic models
│   │   ├── dependencies/         # Dependency injection
│   │   ├── init/                 # Initialization scripts
│   │   ├── config.py             # Configuration management
│   │   └── main.py               # FastAPI app
│   └── requirements.txt          # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── components/           # React components
│   │   ├── services/             # API client services
│   │   ├── types/                # TypeScript types
│   │   └── App.tsx               # Root component
│   └── package.json              # Node dependencies
├── db/
│   └── init.sql                  # Database schema
├── docker-compose.yml            # Service orchestration
├── deploy.sh                     # Automated deployment script
├── .env.example                  # Environment template
└── README.md                     # This file
```

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🗺️ Roadmap

Future features under consideration:

- [ ] Barcode scanning for quick item entry
- [ ] Expiration date tracking and alerts
- [ ] Shopping list generation
- [ ] Recipe management integration
- [ ] Statistics and usage analytics

---

**Version:** 1.0.0 | **Status:** Production Ready ✅
