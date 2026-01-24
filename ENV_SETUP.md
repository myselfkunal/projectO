# Environment Configuration Guide

## Backend .env Configuration

Create `backend/.env` with the following:

### Database Configuration
```
DATABASE_URL=postgresql://unilink_user:unilink_password@localhost:5432/unilink
```

**For Local Development:**
```bash
# First, create PostgreSQL database and user:
psql -U postgres
CREATE USER unilink_user WITH PASSWORD 'unilink_password';
CREATE DATABASE unilink OWNER unilink_user;
ALTER ROLE unilink_user SET client_encoding TO 'utf8';
ALTER ROLE unilink_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE unilink_user SET default_transaction_deferrable TO on;
ALTER ROLE unilink_user SET default_transaction_read_only TO off;
GRANT ALL PRIVILEGES ON DATABASE unilink TO unilink_user;
```

### JWT Configuration
```
SECRET_KEY=your-super-secret-key-change-this-in-production-min-32-chars-12345
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

**Generate a secure SECRET_KEY:**
```python
import secrets
print(secrets.token_urlsafe(32))
```

### Email Configuration (SMTP)

**Gmail Example:**
```
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
EMAIL_FROM=your-email@gmail.com
```

**To get Gmail App Password:**
1. Enable 2-Factor Authentication
2. Go to https://myaccount.google.com/apppasswords
3. Create app password for Mail
4. Use the 16-character password

**Office 365 Example:**
```
SMTP_SERVER=smtp.office365.com
SMTP_PORT=587
SMTP_USER=your-email@youruniversity.edu
SMTP_PASSWORD=your-password
EMAIL_FROM=your-email@youruniversity.edu
```

### Application URLs
```
FRONTEND_URL=http://localhost:3000
BACKEND_URL=http://localhost:8000
```

**Production URLs:**
```
FRONTEND_URL=https://yourdomain.com
BACKEND_URL=https://api.yourdomain.com
```

## Production .env Templates

Use these templates when deploying:

- [backend/.env.production.example](backend/.env.production.example)
- [frontend/.env.production.example](frontend/.env.production.example)
- [docker/.env.example](docker/.env.example)

### Environment
```
ENVIRONMENT=development
```

**Options:**
- `development` - Debug mode enabled, auto-reload
- `production` - Debug mode disabled, optimized

## Frontend .env Configuration

Create `frontend/.env` with:

```
VITE_API_URL=http://localhost:8000
```

**Production:**
```
VITE_API_URL=https://api.yourdomain.com
```

## Docker Environment

When using `docker-compose`, create `docker/.env`:

```
# Database
POSTGRES_USER=unilink_user
POSTGRES_PASSWORD=unilink_password
POSTGRES_DB=unilink

# Backend
BACKEND_SECRET_KEY=your-super-secret-key-change-in-production
BACKEND_DATABASE_URL=postgresql://unilink_user:unilink_password@postgres:5432/unilink

# Frontend
VITE_API_URL=http://localhost:8000
```

## Production Docker Compose (SSL + domain)

Use [docker/docker-compose.prod.yml](docker/docker-compose.prod.yml) with:

- [docker/.env.example](docker/.env.example)
- [docker/nginx-ssl.template.conf](docker/nginx-ssl.template.conf)

Steps:
1) Copy docker/.env.example to docker/.env and fill values
2) Build images: docker compose -f docker/docker-compose.yml build
3) Start prod stack: docker compose -f docker/docker-compose.prod.yml up -d
4) Issue certs (first time):
   certbot certonly --webroot -w docker/certbot/www -d yourdomain.com -d www.yourdomain.com

## AWS RDS Configuration

When deploying to AWS with RDS:

```
DATABASE_URL=postgresql://unilink_user:password@your-rds-instance.amazonaws.com:5432/unilink
```

**Steps:**
1. Create RDS PostgreSQL instance in AWS Console
2. Copy the endpoint
3. Create master user
4. Update DATABASE_URL
5. Ensure security group allows your app's IP

## Development vs Production Checklist

### Development
- [ ] DATABASE_URL points to local/dev database
- [ ] ENVIRONMENT=development
- [ ] SECRET_KEY is any string (doesn't need to be secure)
- [ ] Email can be mocked
- [ ] CORS allows localhost:3000

### Production
- [ ] DATABASE_URL points to production RDS/database
- [ ] ENVIRONMENT=production
- [ ] SECRET_KEY is cryptographically secure (32+ chars)
- [ ] SMTP credentials for real email provider
- [ ] FRONTEND_URL and BACKEND_URL use HTTPS
- [ ] CORS restricted to your domain
- [ ] Database backups enabled
- [ ] SSL certificates installed

## Secrets Management

### Using .env files (Development)
- Create `.env` with credentials
- Add `.env` to `.gitignore`
- Share `.env.example` with placeholders

### Using Environment Variables (Production)
```bash
# Linux/Mac
export DATABASE_URL="postgresql://..."
export SECRET_KEY="..."

# Windows PowerShell
$env:DATABASE_URL="postgresql://..."
$env:SECRET_KEY="..."
```

### Using Docker Secrets (Production)
Create `docker-secrets/` directory:
```
docker-secrets/
├── db_password
├── secret_key
└── smtp_password
```

Then in docker-compose:
```yaml
secrets:
  db_password:
    file: ./docker-secrets/db_password
```

## Testing Different Configurations

### Test with SQLite (no PostgreSQL needed)
For development testing only:

```
DATABASE_URL=sqlite:///./unilink.db
```

Modify `backend/app/core/database.py`:
```python
if "sqlite" in settings.DATABASE_URL:
    engine = create_engine(
        settings.DATABASE_URL,
        connect_args={"check_same_thread": False}
    )
```

### Mock Email (Development)
In `backend/app/utils/email.py`, add mock mode:
```python
if settings.ENVIRONMENT == "development":
    print(f"Mock email sent to {email}")
    print(f"Verification link: {verification_link}")
    return True
```

## Troubleshooting Configuration Issues

### "Invalid DATABASE_URL"
- Check syntax: `postgresql://user:password@host:port/dbname`
- Verify special characters are URL-encoded
- Ensure port number is correct

### "Email authentication failed"
- Verify SMTP credentials
- Check if SMTP_PORT is correct (usually 587 for TLS)
- Try sending test email manually

### "JWT token invalid"
- Ensure SECRET_KEY is consistent across all instances
- Check token hasn't expired (ACCESS_TOKEN_EXPIRE_MINUTES)

### "CORS origin not allowed"
- Add frontend URL to CORS middleware in `app/main.py`
- Ensure no typos in URL

## Quick Start Templates

### Minimal .env (Local Development)
```
DATABASE_URL=postgresql://user:password@localhost/unilink
SECRET_KEY=test-key
ENVIRONMENT=development
FRONTEND_URL=http://localhost:3000
BACKEND_URL=http://localhost:8000
```

### Production .env (AWS)
```
DATABASE_URL=postgresql://user:password@rds-instance.amazonaws.com/unilink
SECRET_KEY=<generate-secure-key>
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
SMTP_SERVER=smtp.office365.com
SMTP_PORT=587
SMTP_USER=admin@youruniversity.edu
SMTP_PASSWORD=<app-password>
EMAIL_FROM=admin@youruniversity.edu
FRONTEND_URL=https://yourdomain.com
BACKEND_URL=https://api.yourdomain.com
ENVIRONMENT=production
```

## Security Notes

1. **Never commit .env files to Git**
2. **Never share SECRET_KEY publicly**
3. **Rotate SECRET_KEY periodically in production**
4. **Use strong, randomly generated passwords**
5. **Enable HTTPS in production (not HTTP)**
6. **Use environment variables for sensitive data**
7. **Implement rate limiting on login endpoint**
8. **Enable database encryption at rest**
