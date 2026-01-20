# UniLink Architecture Documentation

## System Overview

UniLink is a real-time 1v1 video calling platform that connects university students randomly for meaningful conversations. The system consists of three main components:

```
┌─────────────────────────────────────────────────────────┐
│                     Browser Client                       │
│  ┌──────────────────────────────────────────────────────┐│
│  │  React Frontend (TypeScript + Tailwind)              ││
│  │  • Authentication (Register/Login/Verify)           ││
│  │  • Real-time Video Call Interface                    ││
│  │  • Text Chat Component                              ││
│  │  • Call History & User Management                   ││
│  └──────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────┘
              ↓ HTTP/HTTPS ↓ WebSocket WSS
┌─────────────────────────────────────────────────────────┐
│                  FastAPI Backend                         │
│  ┌──────────────────────────────────────────────────────┐│
│  │  REST API Routes                                     ││
│  │  • /auth/* - Authentication                         ││
│  │  • /users/* - User Management                       ││
│  │  • /calls/* - Call Management                       ││
│  └──────────────────────────────────────────────────────┘│
│  ┌──────────────────────────────────────────────────────┐│
│  │  WebSocket Server                                    ││
│  │  • Real-time Matching                               ││
│  │  • WebRTC Signaling                                 ││
│  │  • Chat Relay                                       ││
│  └──────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────┘
         ↓ TCP Connection ↓
┌─────────────────────────────────────────────────────────┐
│              PostgreSQL Database                         │
│  • User Accounts                                         │
│  • Call Records                                         │
│  • Block/Report Data                                    │
│  • Session Tokens                                       │
└─────────────────────────────────────────────────────────┘

        ↔ Direct P2P (WebRTC) ↔
        (No server bandwidth)
```

## Data Flow Architecture

### Registration & Email Verification

```
1. User submits registration form
   ├─ Email validation (must be @sample.kiit.ac.in)
   ├─ Username/email uniqueness check
   ├─ Password hashing (bcrypt)
   ├─ Database user creation
   ├─ Generate verification token (URL-safe)
   ├─ Send verification email with token
   └─ Return success to frontend

2. User clicks verification link
   ├─ Token validation (not expired, not used)
   ├─ Mark user as verified
   ├─ Mark token as used
   ├─ Generate JWT access token
   └─ Store token in localStorage
```

### Authentication Flow

```
1. Login Request
   ├─ Validate email format
   ├─ Fetch user from database
   ├─ Verify password (bcrypt)
   ├─ Check is_verified and is_active
   ├─ Create JWT token (sub: user_id, exp: +30 min)
   └─ Return token + user data

2. Subsequent Requests
   ├─ Extract token from Authorization header
   ├─ Decode JWT (verify signature & expiration)
   ├─ Fetch user from database
   └─ Proceed with authenticated endpoint
```

### Call Matching & WebRTC Signaling

```
1. User joins matching queue
   ├─ WebSocket connection established
   ├─ User added to waiting_users queue
   ├─ Try to find match
   │  ├─ Check user blocked status
   │  └─ Random selection from available users
   │
   ├─ If match found:
   │  ├─ Create Call record (status: ongoing)
   │  ├─ Send match_found to both users
   │  ├─ WebRTC offer/answer exchange starts
   │  └─ Start 15-minute timer
   │
   └─ If no match:
      ├─ Return queue_position
      └─ Wait for next match attempt
```

### WebRTC Connection

```
1. Peer A sends WebRTC Offer
   ├─ Create RTCPeerConnection with STUN/TURN
   ├─ Add local audio/video tracks
   ├─ Create SDP offer
   ├─ Set local description
   ├─ Send offer via WebSocket

2. Peer B receives offer
   ├─ Set remote description (offer)
   ├─ Create SDP answer
   ├─ Set local description (answer)
   ├─ Send answer via WebSocket
   └─ Start sending ICE candidates

3. Both peers exchange ICE candidates
   ├─ Each new candidate sent via WebSocket
   ├─ Add ICE candidate to remote peer
   └─ Continue until connection established

4. Audio/Video Stream
   ├─ Direct P2P connection (no server overhead)
   └─ Encrypted via DTLS/SRTP
```

## Database Schema

### Users Table
```
id (UUID) PRIMARY KEY
email (VARCHAR) UNIQUE
username (VARCHAR) UNIQUE
full_name (VARCHAR)
hashed_password (VARCHAR)
profile_picture (VARCHAR) nullable
bio (TEXT) nullable
is_verified (BOOLEAN)
is_active (BOOLEAN)
is_online (BOOLEAN)
role (ENUM: student, admin)
created_at (TIMESTAMP)
updated_at (TIMESTAMP)
```

### Calls Table
```
id (UUID) PRIMARY KEY
initiator_id (UUID) FOREIGN KEY → users.id
receiver_id (UUID) FOREIGN KEY → users.id
started_at (TIMESTAMP)
ended_at (TIMESTAMP) nullable
duration_seconds (INTEGER)
status (VARCHAR): ongoing | completed | missed
call_token (VARCHAR) UNIQUE
```

### BlockedUsers Table
```
id (UUID) PRIMARY KEY
blocker_id (UUID) FOREIGN KEY → users.id
blocked_id (UUID) FOREIGN KEY → users.id
created_at (TIMESTAMP)
```

### Reports Table
```
id (UUID) PRIMARY KEY
reporter_id (UUID) FOREIGN KEY → users.id
reported_id (UUID) FOREIGN KEY → users.id
reason (VARCHAR)
description (TEXT) nullable
is_resolved (BOOLEAN)
created_at (TIMESTAMP)
```

### VerificationTokens Table
```
id (UUID) PRIMARY KEY
user_id (UUID) FOREIGN KEY → users.id
token (VARCHAR) UNIQUE
is_used (BOOLEAN)
created_at (TIMESTAMP)
expires_at (TIMESTAMP) [+24 hours]
```

## Backend Architecture

### Directory Structure
```
backend/
├── app/
│   ├── core/
│   │   ├── config.py          # Settings from environment
│   │   ├── database.py        # SQLAlchemy setup
│   │   ├── security.py        # JWT + password hashing
│   │   └── __init__.py
│   │
│   ├── models/
│   │   ├── user.py            # SQLAlchemy ORM models
│   │   └── __init__.py
│   │
│   ├── schemas/
│   │   ├── user.py            # Pydantic validation schemas
│   │   └── __init__.py
│   │
│   ├── routes/
│   │   ├── auth.py            # /auth/* endpoints
│   │   ├── users.py           # /users/* endpoints
│   │   ├── calls.py           # /calls/* endpoints
│   │   └── __init__.py
│   │
│   ├── utils/
│   │   ├── email.py           # Email verification
│   │   ├── user_service.py    # User business logic
│   │   ├── matching_service.py # Queue + matching
│   │   └── __init__.py
│   │
│   └── main.py               # FastAPI app + lifespan
│
├── migrations/               # Alembic migrations
├── requirements.txt
└── .env.example
```

### API Endpoints

#### Authentication
```
POST /auth/register
├─ Body: {email, username, full_name, password}
├─ Response: {id, email, username, full_name, is_verified, ...}
└─ Action: Create user, send verification email

POST /auth/verify-email
├─ Body: {token, password}
├─ Response: {access_token, token_type, user}
└─ Action: Mark user verified, generate JWT

POST /auth/login
├─ Body: {email, password}
├─ Response: {access_token, token_type, user}
└─ Action: Authenticate user, generate JWT
```

#### Users
```
GET /users/me
├─ Auth: Required
└─ Response: Current user profile

PUT /users/me
├─ Auth: Required
├─ Body: {full_name, bio, profile_picture}
└─ Response: Updated user profile

GET /users/{user_id}
├─ Auth: Required
└─ Response: User profile (if not blocked)

POST /users/block/{user_id}
├─ Auth: Required
└─ Action: Block user from matching/viewing

POST /users/unblock/{user_id}
├─ Auth: Required
└─ Action: Unblock user

POST /users/report/{user_id}
├─ Auth: Required
├─ Body: {reason, description}
└─ Action: Report user for inappropriate behavior
```

#### Calls
```
WS /calls/ws/{user_id}
├─ Query: token (JWT)
├─ Protocol: WebSocket
└─ Messages:
   ├─ join_queue
   ├─ leave_queue
   ├─ webrtc_offer
   ├─ webrtc_answer
   ├─ webrtc_ice
   ├─ chat_message
   └─ end_call

GET /calls/history
├─ Auth: Required
├─ Query: limit (default: 20)
└─ Response: List of past calls
```

## Frontend Architecture

### Component Hierarchy
```
App
├── Routes
│   ├── Register
│   ├── VerifyEmail
│   ├── Login
│   └── Dashboard
│       ├── Menu (start call button)
│       ├── Queue (waiting indicator)
│       └── InCall
│           ├── VideoDisplay (remote)
│           ├── VideoDisplay (local)
│           ├── ChatBox
│           └── CallTimer
│
└── Providers
    └── AuthStore (Zustand)
```

### State Management

#### AuthStore (Zustand)
```typescript
{
  user: User | null
  token: string | null
  isAuthenticated: boolean
  setUser(user)
  setToken(token)
  logout()
}
```

### Custom Hooks

#### useWebSocket
- Manages WebSocket connection
- Auto-reconnect on disconnect
- Sends/receives JSON messages
- Callback for message handling

#### useWebRTC (implicit in WebRTCManager)
- Creates RTCPeerConnection
- Manages local/remote streams
- ICE candidate handling
- Cleanup on disconnect

## Real-time Communication Flow

### Connection Sequence
```
1. Frontend: Connect WebSocket
   └─→ Backend: Accept connection, verify token
   
2. Frontend: send {type: 'join_queue'}
   └─→ Backend: Add user to queue, find match
   
3. Backend: send {type: 'match_found', matched_user, call_id}
   ←─ Frontend: Initialize WebRTC peer connection
   
4. Frontend: send {type: 'webrtc_offer'}
   ←─→ Backend: Relay to peer B
   
5. Frontend B: send {type: 'webrtc_answer'}
   ←─→ Backend: Relay to peer A
   
6. Both: Exchange ICE candidates
   ←─→ Backend: Relay candidates
   
7. Direct P2P: Audio/Video Stream (no server)
   └─→ Both: Monitor connection quality

8. Frontend: send {type: 'end_call'}
   └─→ Backend: Close connection, record call
```

## Security Layers

### 1. Authentication Layer
- Email domain validation (@sample.kiit.ac.in)
- Password hashing (bcrypt)
- JWT token validation
- Token expiration (30 minutes)

### 2. Authorization Layer
- JWT sub claim verification
- User active status check
- Email verification requirement
- Block/report status checking

### 3. Data Validation
- Pydantic schema validation
- Email format validation
- Input sanitization

### 4. WebRTC Encryption
- DTLS-SRTP for media encryption
- Peer-to-peer (no eavesdropping)

### 5. CORS Protection
- Restrict to known frontend origins
- Prevent cross-origin attacks

## Scalability Considerations

### Current Architecture (Single Server)
- **Users:** ~100-200 concurrent
- **Database:** PostgreSQL single instance
- **Backend:** Single FastAPI process
- **Frontend:** Static files (CDN optional)

### Future Scaling (Multi-Server)
```
Load Balancer (AWS ELB)
    ├── Backend Server 1
    ├── Backend Server 2
    └── Backend Server N
           ↓
   Shared PostgreSQL (RDS)
```

### Scaling Challenges
1. **WebSocket State:** Share session state (Redis)
2. **Matching Queue:** Use distributed queue (RabbitMQ)
3. **Database:** Add read replicas, connection pooling
4. **Media:** Use media servers (Janus/Kurento) for large scale

## Deployment Architecture

### Docker Composition
```
Docker Host
├── Postgres Container
├── Backend Container
│   └── FastAPI + Uvicorn (4 workers)
└── Frontend Container
    └── Nginx (serve static + proxy API)
```

### AWS Deployment
```
Internet → CloudFront (CDN) → S3 (Frontend)
                             → API Gateway → ALB → EC2 (Backend)
                                              → RDS PostgreSQL

With:
- SSL/TLS termination at CloudFront
- Auto-scaling group for EC2
- Multi-AZ RDS for HA
- CloudWatch for monitoring
```

## Error Handling

### Backend Errors
- 400: Bad Request (validation error)
- 401: Unauthorized (missing/invalid token)
- 403: Forbidden (blocked user, not verified)
- 404: Not Found (user/call doesn't exist)
- 409: Conflict (duplicate email/username)
- 500: Server Error (unexpected error)

### Frontend Error Handling
- Display user-friendly error messages
- Log errors for debugging
- Retry logic for transient failures
- Fallback UI for connection loss

## Monitoring & Logging

### Key Metrics
- Active users
- Calls per minute
- Call success rate
- Average call duration
- API response times
- Database connection pool
- WebSocket connection count

### Logging Points
- User authentication events
- Call start/end
- Match success/failure
- Error events
- WebSocket connect/disconnect

## Performance Optimization

1. **Database Indexing:** Fast lookups on email, username
2. **Connection Pooling:** Reuse DB connections
3. **Caching:** Cache user profiles (short TTL)
4. **Static Files:** Serve via CDN
5. **Compression:** Gzip responses
6. **WebRTC Optimization:** Use media constraints, adaptive bitrate

## Future Features

1. **Group Calls:** 3+ users
2. **Screen Sharing:** Desktop/application sharing
3. **Recording:** Call recordings for users
4. **Filters:** Audio/video filters and effects
5. **Interests:** Match based on courses/interests
6. **Mobile:** React Native app
7. **Notifications:** Real-time call notifications
8. **Analytics:** Dashboard for university admins
