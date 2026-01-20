# UniLink - University 1v1 Video Calling Platform

## Project Overview

UniLink is a web-based platform that enables university students to connect with each other through 1v1 video calls with integrated text chat. It uses random matching to pair students in real-time.

### Features

- 🔐 University email authentication (sample.kiit.ac.in)
- 📹 High-quality 1v1 video and audio calls (WebRTC)
- 💬 Real-time text chat during calls
- 🎯 Random user matching with queue system
- 👥 User profiles and blocking system
- 📞 Call history tracking
- 🚫 Report inappropriate users
- ⏱️ 15-minute call limit (extensible)
- 🟢 Online/offline status indicator
- 🌐 Responsive web interface

## Tech Stack

### Backend
- **Framework:** FastAPI (Python)
- **Database:** PostgreSQL
- **Real-time:** WebSocket
- **Authentication:** JWT
- **Video:** WebRTC (STUN + TURN)

### Frontend
- **Framework:** React 18 + TypeScript
- **Styling:** Tailwind CSS
- **Build:** Vite
- **State:** Zustand
- **HTTP:** Axios

### Infrastructure
- **Containerization:** Docker & Docker Compose
- **Deployment:** AWS (EC2 + RDS)

## Project Structure

```
projectO/
├── backend/
│   ├── app/
│   │   ├── core/          # Configuration, database, security
│   │   ├── models/        # SQLAlchemy ORM models
│   │   ├── routes/        # API routes (auth, users, calls)
│   │   ├── schemas/       # Pydantic schemas
│   │   ├── utils/         # Business logic (email, matching, WebRTC)
│   │   └── main.py        # FastAPI app entry point
│   ├── requirements.txt
│   ├── .env.example
│   └── .dockerignore
│
├── frontend/
│   ├── src/
│   │   ├── components/    # React components
│   │   ├── pages/         # Page components
│   │   ├── hooks/         # Custom React hooks
│   │   ├── utils/         # Utility functions
│   │   ├── context/       # Zustand stores
│   │   ├── App.tsx
│   │   ├── main.tsx
│   │   └── index.css
│   ├── index.html
│   ├── package.json
│   ├── vite.config.ts
│   ├── tsconfig.json
│   └── .dockerignore
│
├── docker/
│   ├── Dockerfile.backend
│   ├── Dockerfile.frontend
│   └── docker-compose.yml
│
├── .env.example
└── README.md
```

## Installation & Setup

### Prerequisites

- Docker & Docker Compose
- Node.js 18+ (for local development)
- Python 3.11+ (for local backend development)
- PostgreSQL (or use Docker container)

### Option 1: Using Docker Compose (Recommended)

1. **Clone and Setup:**
   ```bash
   cd projectO
   cp .env.example .env
   cp backend/.env.example backend/.env
   ```

2. **Configure Environment:**
   - Edit `.env` and `backend/.env` with your settings
   - Update SMTP settings for email verification
   - Change SECRET_KEY to a strong random value

3. **Start Services:**
   ```bash
   cd docker
   docker-compose up -d
   ```

4. **Initialize Database:**
   ```bash
   docker-compose exec backend python -m alembic upgrade head
   ```

5. **Access the Application:**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

### Option 2: Local Development

#### Backend Setup:

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Setup environment
cp .env.example .env
# Edit .env with your settings

# Make sure PostgreSQL is running
# Create database: createdb unilink

# Run migrations
alembic upgrade head

# Start server
python -m uvicorn app.main:app --reload
```

#### Frontend Setup:

```bash
cd frontend

# Install dependencies
npm install

# Start dev server
npm run dev
```

## API Endpoints

### Authentication
- `POST /auth/register` - Register new user
- `POST /auth/verify-email` - Verify email with token
- `POST /auth/login` - Login user

### Users
- `GET /users/me` - Get current user profile
- `PUT /users/me` - Update user profile
- `GET /users/{user_id}` - Get user profile
- `POST /users/block/{user_id}` - Block user
- `POST /users/unblock/{user_id}` - Unblock user
- `POST /users/report/{user_id}` - Report user

### Calls (WebSocket)
- `WS /calls/ws/{user_id}` - WebSocket connection for calling
- `GET /calls/history` - Get call history

## WebSocket Message Types

### Client -> Server
- `join_queue` - Join matchmaking queue
- `leave_queue` - Leave matchmaking queue
- `webrtc_offer` - Send WebRTC offer
- `webrtc_answer` - Send WebRTC answer
- `webrtc_ice` - Send ICE candidate
- `chat_message` - Send chat message
- `end_call` - End current call

### Server -> Client
- `queue_joined` - Successfully joined queue
- `queue_left` - Left queue
- `match_found` - Match found, call initiated
- `webrtc_offer` - Receive WebRTC offer
- `webrtc_answer` - Receive WebRTC answer
- `webrtc_ice` - Receive ICE candidate
- `chat_message` - Receive chat message
- `call_ended` - Call ended by other user

## Database Schema

### Tables
- `users` - User accounts
- `calls` - Call records
- `blocked_users` - Blocked user relationships
- `reports` - User reports
- `verification_tokens` - Email verification tokens

## Deployment to AWS

### Prerequisites
- AWS Account with EC2 & RDS access
- Domain name (optional)

### Steps

1. **Create EC2 Instance:**
   - Launch Ubuntu 22.04 instance (t3.medium or larger)
   - Security groups: Allow SSH (22), HTTP (80), HTTPS (443)
   - Download key pair

2. **Setup EC2:**
   ```bash
   ssh -i your-key.pem ubuntu@your-instance-ip
   
   # Install Docker
   sudo apt-get update
   sudo apt-get install -y docker.io docker-compose nginx
   sudo usermod -aG docker $USER
   
   # Clone project
   git clone your-repo projectO
   cd projectO
   cp .env.example .env
   # Edit .env with production values
   ```

3. **Setup RDS PostgreSQL:**
   - Create RDS instance in AWS Console
   - Update DATABASE_URL in .env

4. **Deploy with Docker:**
   ```bash
   cd docker
   docker-compose -f docker-compose.yml up -d
   ```

5. **Setup SSL with Let's Encrypt:**
   ```bash
   sudo apt-get install -y certbot python3-certbot-nginx
   sudo certbot certonly --standalone -d your-domain.com
   ```

## Testing

### Backend Tests
```bash
cd backend
pytest
```

### Frontend Tests
```bash
cd frontend
npm test
```

## Troubleshooting

### Database Connection Issues
- Check PostgreSQL is running: `docker-compose logs postgres`
- Verify DATABASE_URL in .env
- Ensure database exists: `createdb unilink`

### WebRTC Connection Issues
- Check if STUN/TURN servers are accessible
- Verify firewall allows WebRTC ports (typically 49152-65535)
- Check browser console for errors

### Email Verification Not Working
- Verify SMTP credentials in .env
- Check email spam folder
- For Gmail, enable "Less secure app access"

### Cors Issues
- Verify FRONTEND_URL in backend .env
- Check CORS middleware in app/main.py

## Performance Optimization

- Use CDN for static assets
- Implement database indexing on frequently queried fields
- Cache user profiles with Redis
- Use connection pooling for database
- Implement rate limiting for API endpoints

## Security Considerations

- Change SECRET_KEY in production
- Use HTTPS/SSL in production
- Implement rate limiting
- Validate all user inputs
- Use environment variables for sensitive data
- Regularly update dependencies
- Enable CORS only for your domain
- Implement CSRF protection if needed

## Future Enhancements

- [ ] Payment integration for premium features
- [ ] Group video calls (3+ users)
- [ ] Screen sharing
- [ ] Call recording
- [ ] Video filters and effects
- [ ] Interests/course-based matching
- [ ] Mobile app (React Native)
- [ ] Call queue notifications
- [ ] User ratings and reviews
- [ ] Analytics dashboard

## Contributing

1. Create a feature branch
2. Make your changes
3. Test thoroughly
4. Submit a pull request

## Support

For issues and questions, open an GitHub issue or contact the development team.

## License

This project is licensed under the MIT License.

---

**Last Updated:** January 19, 2026
**Version:** 1.0.0
