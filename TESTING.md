# Testing Guide for UniLink

## Prerequisites
- PostgreSQL running on localhost:5432
- Backend running on http://localhost:8000
- Frontend running on http://localhost:3000

## Manual Testing Steps

### 1. Database Setup

```bash
# Create database (PostgreSQL)
createdb unilink

# Or connect to PostgreSQL and run:
CREATE DATABASE unilink;
```

### 2. Backend Testing

#### Start Backend
```bash
cd backend
source venv/bin/activate  # Windows: venv\Scripts\activate
python -m uvicorn app.main:app --reload
```

#### Test API Health
```bash
curl http://localhost:8000/health
# Expected: {"status": "healthy"}
```

#### Test Registration
```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user1@sample.kiit.ac.in",
    "username": "user1",
    "full_name": "User One",
    "password": "password123"
  }'
```

### 3. Frontend Testing

#### Start Frontend
```bash
cd frontend
npm run dev
```

#### Test Frontend Build
```bash
cd frontend
npm run build
# Check dist/ directory is created
```

### 4. WebSocket Testing

Use the WebSocket test tool or write a simple test:

```javascript
// Browser console
const token = localStorage.getItem('token');
const userId = 'user-id';
const ws = new WebSocket(`ws://localhost:8000/calls/ws/${userId}?token=${token}`);

ws.onopen = () => {
  console.log('Connected');
  ws.send(JSON.stringify({ type: 'join_queue' }));
};

ws.onmessage = (event) => {
  console.log('Message:', JSON.parse(event.data));
};
```

### 5. Docker Testing

#### Build Images
```bash
cd docker
docker build -f Dockerfile.backend -t unilink-backend ..
docker build -f Dockerfile.frontend -t unilink-frontend ..
```

#### Run with Docker Compose
```bash
cd docker
docker-compose up
```

#### Check Logs
```bash
docker-compose logs backend
docker-compose logs frontend
docker-compose logs postgres
```

#### Access Services
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- PostgreSQL: localhost:5432

### 6. Full Integration Test Flow

1. **Register User**
   - Go to http://localhost:3000/register
   - Enter email ending with @sample.kiit.ac.in
   - Complete registration

2. **Verify Email**
   - Check email for verification link
   - Or check backend logs for token
   - Visit /verify?token=XXXXX

3. **Login**
   - Go to http://localhost:3000/login
   - Login with registered credentials

4. **Start Call**
   - Click "Start a Call"
   - Should see "Finding a match..."

5. **Test Multiple Users**
   - Open another browser/tab and repeat steps 1-3
   - Both users should find each other

## Debugging

### Backend Logs
```bash
docker-compose logs -f backend
```

### Frontend Console
- Open Browser DevTools (F12)
- Check Console and Network tabs
- Look for WebSocket connections

### Database
```bash
psql unilink
\dt  # List tables
SELECT COUNT(*) FROM users;
```

### Common Issues

#### Database Connection Failed
- Check PostgreSQL is running
- Verify DATABASE_URL in .env
- Check firewall allows port 5432

#### WebSocket Connection Failed
- Check WebSocket URL in browser console
- Verify backend is running
- Check CORS settings

#### Email Not Sent
- Check SMTP credentials in .env
- Check backend logs for email errors
- For development, use mock email

#### Frontend Build Failed
- Delete node_modules and package-lock.json
- Run npm install again
- Check Node.js version (need 18+)

## Load Testing

Test with multiple concurrent connections:

```bash
# Using Apache Bench (if installed)
ab -n 100 -c 10 http://localhost:8000/health

# Using curl loop
for i in {1..10}; do
  curl http://localhost:8000/health &
done
```

## Performance Testing

Monitor resource usage:

```bash
# Docker container resources
docker stats unilink_backend
docker stats unilink_postgres

# System resources
top  # Linux/Mac
tasklist  # Windows
```

## API Documentation

- Interactive Docs: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Test Data

```sql
-- Insert test user
INSERT INTO users (id, email, username, full_name, hashed_password, is_verified, is_active)
VALUES (
  'test-user-1',
  'test1@sample.kiit.ac.in',
  'testuser1',
  'Test User',
  '$2b$12$...', -- bcrypt hashed password
  true,
  true
);
```

## Browser DevTools Tips

1. **Network Tab**
   - Monitor API calls
   - Check WebSocket connection
   - View request/response payloads

2. **Console Tab**
   - Check for JavaScript errors
   - Monitor WebSocket messages
   - Debug React components

3. **Storage Tab**
   - Check localStorage for token
   - Verify cookies

4. **Performance Tab**
   - Monitor page load times
   - Identify bottlenecks
