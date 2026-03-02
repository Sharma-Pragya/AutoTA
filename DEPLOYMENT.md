# AutoTA Deployment Guide

This guide covers deploying AutoTA on a fresh server or machine.

## Prerequisites

- Python 3.10 or higher
- Node.js 18 or higher
- npm (comes with Node.js)
- SQLite3 (usually pre-installed on most systems)
- Git

## Fresh Installation Steps

### 1. Clone the Repository

```bash
git clone <repository-url>
cd AutoTA
```

### 2. Install Python Dependencies

```bash
# Create a virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install AutoTA package and dependencies
pip install -e .
```

This installs:
- FastAPI
- Uvicorn
- Pydantic
- All Phase 1 dependencies

### 3. Install Frontend Dependencies

```bash
cd frontend
npm install
cd ..
```

This installs:
- React 18
- Vite
- All frontend dependencies

**Note**: `node_modules/` is large (~120MB) and not committed to git. This step recreates it from `package.json`.

### 4. Create and Seed Database

The `data/` directory exists but the database file is not in git. Create it:

```bash
# Run Phase 2 migration (creates initial schema)
sqlite3 data/autota.db < migrations/001_initial_schema.sql

# Run Phase 2.1 migration (adds schema hardening)
sqlite3 data/autota.db < migrations/002_schema_hardening.sql

# Backfill variant pool from existing assignments
python -m migrations.backfill_variant_pool

# Seed database with test data
./seed.sh
```

After this, you'll have:
- Database file: `data/autota.db`
- 19 tables + 2 views
- 3 test students
- 1 assignment (Homework 5)
- 39 variants in the pool

### 5. Start the Application

```bash
# Option A: Start both backend and frontend together
./dev.sh

# Option B: Start separately (in different terminals)
./start-backend.sh  # Terminal 1 - Backend on :8000
./start-frontend.sh # Terminal 2 - Frontend on :5173
```

### 6. Access the Application

Open your browser:
- **Frontend**: http://localhost:5173/?sid=UID123456789
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

## Test Accounts

```
Student ID: UID123456789
Name: Pragya Sharma
Attempt: 2 of 3

Student ID: UID987654321
Name: Jane Bruin
Attempt: 1 of 3

Student ID: UID111222333
Name: Joe Bruin
Attempt: 1 of 3
```

## Production Deployment

### Environment Variables

Create a `.env` file (not in git):

```bash
# API Keys (if using Phase 1 LLM generation)
ANTHROPIC_API_KEY=your-key-here

# Database (optional, defaults to data/autota.db)
DATABASE_PATH=data/autota.db

# Server Config
BACKEND_PORT=8000
FRONTEND_PORT=5173
```

### Backend (Production)

```bash
# Install production ASGI server
pip install gunicorn

# Run with gunicorn
gunicorn autota.web.app:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000
```

### Frontend (Production)

```bash
cd frontend

# Build production bundle
npm run build

# Serve with a static server (e.g., nginx, or simple http server)
npx serve -s dist -l 5173
```

Or use nginx to serve the `frontend/dist/` directory.

### Nginx Configuration Example

```nginx
server {
    listen 80;
    server_name autota.example.com;

    # Frontend
    location / {
        root /path/to/AutoTA/frontend/dist;
        try_files $uri $uri/ /index.html;
    }

    # Backend API
    location /api {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## Directory Structure After Setup

```
AutoTA/
├── data/
│   ├── README.md
│   ├── .gitkeep
│   └── autota.db           # Created by migrations (NOT in git)
├── frontend/
│   ├── node_modules/       # Created by npm install (NOT in git)
│   ├── dist/               # Created by npm run build (NOT in git)
│   ├── src/                # ✓ In git
│   ├── package.json        # ✓ In git
│   └── ...
├── autota/
│   └── web/                # ✓ Backend code in git
├── migrations/             # ✓ SQL migrations in git
└── ...
```

## Troubleshooting

### Database Errors

```bash
# Check if database exists
ls -la data/autota.db

# If missing, run migrations (see step 4)
sqlite3 data/autota.db < migrations/001_initial_schema.sql
sqlite3 data/autota.db < migrations/002_schema_hardening.sql
```

### Frontend Build Issues

```bash
# Clear cache and reinstall
cd frontend
rm -rf node_modules package-lock.json
npm install
```

### Port Already in Use

```bash
# Kill process on port 8000
lsof -ti:8000 | xargs kill -9

# Kill process on port 5173
lsof -ti:5173 | xargs kill -9
```

### Migration Errors

If migrations fail:

```bash
# Check SQLite version (need 3.25+)
sqlite3 --version

# Reset database
rm data/autota.db
# Re-run migrations from step 4
```

## Updating the Application

```bash
# Pull latest code
git pull

# Update Python dependencies
pip install -e .

# Update frontend dependencies
cd frontend
npm install
cd ..

# Run any new migrations
# (Check migrations/ directory for new files)

# Restart servers
./dev.sh
```

## Backup and Restore

### Backup Database

```bash
# Copy database file
cp data/autota.db data/autota.db.backup

# Or export to SQL
sqlite3 data/autota.db .dump > backup.sql
```

### Restore Database

```bash
# From backup file
cp data/autota.db.backup data/autota.db

# From SQL export
sqlite3 data/autota.db < backup.sql
```

## Security Considerations

1. **Never commit `.env` files** - Contains API keys
2. **Never commit `data/autota.db`** - Contains student data
3. **Use HTTPS in production** - Protect student credentials
4. **Set up CORS properly** - Restrict allowed origins
5. **Use environment-specific configs** - Different settings for dev/prod

## Support

For issues or questions:
- Check `CHANGELOG.md` for known issues
- See `docs/phase2/` for detailed documentation
- Run tests: `pytest` (should show 79 passing)
