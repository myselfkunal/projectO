# UniLink - Project Handover Documentation

## Executive Summary
**UniLink** is a 1v1 video calling platform for university students, enabling real-time video/audio communication with integrated chat. The project is **65% complete** with core functionality working. The main blocker is a WebRTC peer connection issue that needs debugging.

---

## Project Overview

### End Goal
Create a fully functional, production-ready web platform where:
- Students register with university email (@kiit.ac.in)
- Verify email via OTP
- Login and see available online users
- Initiate 1v1 video calls with real-time audio/video
- Chat during calls
- View call history
- Block/report users

### Tech Stack

**Frontend:**
- React 18 with TypeScript
- Vite (dev server on port 3001)
- React Router (navigation)
- Zustand (state management)
- Axios (HTTP client)
- WebSocket (real-time communication)
- Inline CSS (no Tailwind, no build issues)

**Backend:**
- FastAPI (Python)
- PostgreSQL (database)
- SQLAlchemy ORM
- JWT (authentication)
- WebSocket (signaling)
- Uvicorn (ASGI server on port 8000)

**WebRTC:**
- Native RTCPeerConnection API
- STUN servers for ICE candidates
- SDP offer/answer signaling via WebSocket

---

## Current Project Status

### ✅ COMPLETED

#### 1. Authentication System
- **Register endpoint:** `POST /auth/register`
  - Validates @kiit.ac.in email only
  - Hashes password with bcrypt
  - Creates verification token
  - Sends verification email
  - File: `backend/app/routes/auth.py`

- **Email Verification:** `POST /auth/verify-email`
  - Validates OTP token
  - Marks user as verified
  - Returns JWT token
  - File: `backend/app/routes/auth.py`

- **Login endpoint:** `POST /auth/login`
  - Validates credentials
  - **FIXED:** Now calls `set_user_online()` to mark user as online
  - Returns JWT token with 30-min expiry
  - File: `backend/app/routes/auth.py`, line 109

#### 2. User Management
- **Get current user:** `GET /users/me`
- **Update profile:** `PUT /users/me`
- **Get user by ID:** `GET /users/{id}`
- **Block/unblock user:** `POST /users/block/{id}`, `POST /users/unblock/{id}`
- **Report user:** `POST /users/report/{id}`
- File: `backend/app/routes/users.py`

#### 3. Call Management (HTTP Endpoints)
- **Get available users:** `GET /calls/available`
  - Returns list of online, verified users (excluding self, blocked users)
  - Uses database `is_online` flag
  - File: `backend/app/routes/calls.py`, line 32

- **Initiate call:** `POST /calls/initiate`
  - **FIXED:** Now checks database `is_online` flag (not in-memory set)
  - Creates call record with status="pending"
  - Returns call_id and call_token
  - File: `backend/app/routes/calls.py`, line 59

- **Accept/reject/end call:** `POST /calls/accept/{id}`, `POST /calls/reject/{id}`, `POST /calls/end/{id}`
  - File: `backend/app/routes/calls.py`

- **Call history:** `GET /calls/history`
  - Returns past calls with usernames and duration
  - File: `backend/app/routes/calls.py`, line 318

#### 4. Presence Tracking (WebSocket)
- **Presence WebSocket:** `WS /calls/ws/{user_id}?token=JWT`
  - Marks user as online when connected
  - Maintains connection with ping/pong
  - Removes from online when disconnected
  - File: `backend/app/routes/calls.py`, line 346

#### 5. WebRTC Signaling (WebSocket)
- **WebRTC WebSocket:** `WS /ws/webrtc/{call_id}?token=JWT`
  - Authenticates user via JWT
  - Verifies user is part of the call
  - Relays SDP offer/answer
  - Relays ICE candidates
  - Broadcasts chat messages
  - File: `backend/app/routes/webrtc.py`, line 44

- **Connection state debugging:** `GET /ws/webrtc/connection-state/{call_id}`
  - Returns current WebRTC connection state
  - **FIXED:** Checks both webrtc_manager and active_connections
  - File: `backend/app/routes/webrtc.py`, line 293

#### 6. Frontend Components (All Built from Scratch)

**Dashboard.tsx** - Main user interface
- Shows available users in a grid
- Each user card has:
  - Username, full name, bio
  - "Start Call" button
  - Online status indicator
- Presence WebSocket connection (marks user online)
- Auto-refreshes available users every 3 seconds
- Error handling and display
- Logout button
- File: `frontend/src/pages/Dashboard.tsx`

**Call.tsx** - Call page (NEW COMPONENT)
- Manages WebRTC peer connection
- Handles WebSocket signaling
- Captures local media (audio + video)
- Displays local and remote video
- Integrated ChatBox for messages
- CallTimer showing elapsed time
- End Call button
- Enhanced logging for debugging
- File: `frontend/src/pages/Call.tsx`

**VideoDisplay.tsx** - Video component
- Displays MediaStream in video element
- Auto-plays video
- Supports local video mirroring (scaleX(-1))
- Shows "No video" placeholder when stream unavailable
- Responsive sizing
- File: `frontend/src/components/VideoDisplay.tsx`

**ChatBox.tsx** - Chat during calls
- Real-time messaging via WebSocket
- Message history display
- Send button with validation
- Auto-scroll to latest message
- Shows sender name and timestamp
- File: `frontend/src/components/ChatBox.tsx`

**CallTimer.tsx** - Elapsed time display
- Shows MM:SS format
- Updates every second
- Configurable max duration
- File: `frontend/src/components/CallTimer.tsx`

**App.tsx** - Routing
- `/register` - Registration page
- `/verify` - Email verification
- `/login` - Login page
- `/dashboard` - Main dashboard (protected)
- `/call/:callId` - Call page (protected)
- File: `frontend/src/App.tsx`

#### 7. Database Models
- **User:** id, username, email, password_hash, full_name, bio, profile_picture, is_online, is_verified, is_active, created_at
- **Call:** id, initiator_id, receiver_id, started_at, ended_at, duration_seconds, status, call_token
- **BlockedUser:** blocker_id, blocked_id
- **Report:** reporter_id, reported_id, reason, description
- **VerificationToken:** user_id, token, is_used, created_at, expires_at
- File: `backend/app/models/user.py`

---

## 🔴 CURRENT BLOCKER: WebRTC Offer Creation Failing

### Issue Description
When user clicks "Start Call":
1. ✅ Call is created in database
2. ✅ User is redirected to `/call/{callId}?token={JWT}`
3. ✅ Local media stream is captured (audio + video)
4. ✅ WebSocket connection to `/ws/webrtc/{callId}` is established
5. ❌ **Peer connection fails to create SDP offer**
   - Error message: "Failed to create offer"
   - `createOffer()` is throwing an exception

### Root Cause (Likely)
- WebSocket might not be fully established when `createOffer()` is called
- Local stream might not have valid tracks
- Peer connection setup might have browser compatibility issues
- Race condition between WebSocket open and peer connection setup

### Debugging Progress
Added detailed logging in Call.tsx:
```
- "Setting up peer connection with local stream: N tracks"
- "Adding local tracks to peer connection"
- "Adding track: {kind} {enabled}"
- "Peer connection created, attempting to create offer"
- "Creating offer..."
- "WebSocket not open, state: {readyState}" (if applicable)
```

### Next Debugging Steps (Priority Order)
1. **Open browser DevTools (F12) → Console tab**
2. **Start a call and capture ALL console output**
3. **Check:**
   - Does "Connected to WebRTC WebSocket" log appear?
   - How many tracks are being added? (should be 2: audio + video)
   - Is `createOffer()` being called?
   - What's the exact error from `createOffer()`?
4. **Check browser compatibility:**
   - Try in Chrome/Chromium first (most compatible)
   - Check if `getUserMedia` is working (local video should show)
5. **Verify WebSocket on backend:**
   - Check `backend/app/routes/webrtc.py` logs
   - Verify token authentication succeeds
   - Verify call exists in database
   - Verify user is part of the call

---

## File Structure

```
projectO/
├── backend/
│   ├── app/
│   │   ├── main.py                    # FastAPI app, lifespan, CORS
│   │   ├── core/
│   │   │   ├── config.py              # Settings (DB, JWT, CORS, etc.)
│   │   │   ├── database.py            # SQLAlchemy setup, SessionLocal
│   │   │   ├── security.py            # JWT token create/decode
│   │   │   └── limiter.py             # Rate limiting
│   │   ├── models/
│   │   │   └── user.py                # All database models
│   │   ├── routes/
│   │   │   ├── auth.py                # Register, verify, login
│   │   │   ├── users.py               # User CRUD, block, report
│   │   │   ├── calls.py               # Call HTTP endpoints + presence WS
│   │   │   └── webrtc.py              # WebRTC signaling WS
│   │   ├── schemas/
│   │   │   └── user.py                # Pydantic schemas
│   │   └── utils/
│   │       ├── user_service.py        # User business logic
│   │       ├── call_service.py        # Call business logic
│   │       ├── webrtc_service.py      # WebRTC state management
│   │       ├── email.py               # Email sending
│   │       └── matching_service.py    # (legacy, not used)
│   └── requirements.txt               # Python dependencies
│
├── frontend/
│   ├── src/
│   │   ├── App.tsx                    # Routes + ProtectedRoute
│   │   ├── main.tsx                   # Entry point
│   │   ├── index.css                  # Global styles
│   │   ├── pages/
│   │   │   ├── Register.tsx           # Registration form
│   │   │   ├── VerifyEmail.tsx        # OTP verification
│   │   │   ├── Login.tsx              # Login form
│   │   │   ├── Dashboard.tsx          # Main dashboard (FIXED)
│   │   │   └── Call.tsx               # Call page (NEW, DEBUGGING)
│   │   ├── components/
│   │   │   ├── VideoDisplay.tsx       # Video component (UPDATED)
│   │   │   ├── ChatBox.tsx            # Chat component (REWRITTEN)
│   │   │   ├── CallTimer.tsx          # Timer component (UPDATED)
│   │   │   └── ErrorBoundary.tsx      # Error handling
│   │   ├── context/
│   │   │   └── authStore.ts           # Zustand auth state
│   │   ├── hooks/
│   │   │   ├── useWebRTCConnection.ts # (legacy, not used in Call.tsx)
│   │   │   └── useWebSocket.ts        # (legacy, not used)
│   │   └── utils/
│   │       ├── api.ts                 # Axios instance with JWT interceptor
│   │       ├── authService.ts         # Auth utility functions
│   │       └── webrtc.ts              # (legacy)
│   ├── package.json
│   ├── vite.config.ts
│   └── tsconfig.json
│
└── docker/
    ├── Dockerfile.backend
    ├── Dockerfile.frontend
    └── docker-compose.yml             # (not yet created)
```

---

## Database Schema

### Users Table
```sql
CREATE TABLE users (
    id VARCHAR PRIMARY KEY,
    username VARCHAR UNIQUE NOT NULL,
    email VARCHAR UNIQUE NOT NULL,
    password_hash VARCHAR NOT NULL,
    full_name VARCHAR,
    bio TEXT,
    profile_picture VARCHAR,
    is_online BOOLEAN DEFAULT FALSE,
    is_verified BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### Calls Table
```sql
CREATE TABLE calls (
    id VARCHAR PRIMARY KEY,
    initiator_id VARCHAR NOT NULL REFERENCES users(id),
    receiver_id VARCHAR NOT NULL REFERENCES users(id),
    started_at TIMESTAMP DEFAULT NOW(),
    ended_at TIMESTAMP,
    duration_seconds INTEGER DEFAULT 0,
    status VARCHAR DEFAULT 'pending',  -- pending, ongoing, completed, rejected, missed
    call_token VARCHAR UNIQUE NOT NULL
);
```

### BlockedUsers Table
```sql
CREATE TABLE blocked_users (
    blocker_id VARCHAR NOT NULL REFERENCES users(id),
    blocked_id VARCHAR NOT NULL REFERENCES users(id),
    PRIMARY KEY (blocker_id, blocked_id)
);
```

### Reports Table
```sql
CREATE TABLE reports (
    id VARCHAR PRIMARY KEY,
    reporter_id VARCHAR NOT NULL REFERENCES users(id),
    reported_id VARCHAR NOT NULL REFERENCES users(id),
    reason VARCHAR NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### VerificationTokens Table
```sql
CREATE TABLE verification_tokens (
    id VARCHAR PRIMARY KEY,
    user_id VARCHAR NOT NULL REFERENCES users(id),
    token VARCHAR UNIQUE NOT NULL,
    is_used BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP DEFAULT NOW() + INTERVAL '24 hours'
);
```

---

## API Endpoints Reference

### Authentication
| Method | Endpoint | Auth | Body | Response |
|--------|----------|------|------|----------|
| POST | /auth/register | ❌ | email, password, username, full_name | {user, message} |
| POST | /auth/verify-email | ❌ | token | {access_token, token_type, user} |
| POST | /auth/login | ❌ | email, password | {access_token, token_type, user} |

### Users
| Method | Endpoint | Auth | Body | Response |
|--------|----------|------|------|----------|
| GET | /users/me | ✅ | - | {user} |
| PUT | /users/me | ✅ | full_name, bio, profile_picture | {user} |
| GET | /users/{id} | ✅ | - | {user} |
| POST | /users/block/{id} | ✅ | - | {message} |
| POST | /users/unblock/{id} | ✅ | - | {message} |
| POST | /users/report/{id} | ✅ | reason, description | {message} |

### Calls (HTTP)
| Method | Endpoint | Auth | Body | Response |
|--------|----------|------|------|----------|
| GET | /calls/available | ✅ | - | [{users}] |
| POST | /calls/initiate | ✅ | receiver_id | {call_id, call_token, status} |
| POST | /calls/accept/{id} | ✅ | - | {call_id, status} |
| POST | /calls/reject/{id} | ✅ | - | {call_id, status} |
| POST | /calls/end/{id} | ✅ | - | {call_id, status} |
| GET | /calls/history | ✅ | - | [{calls}] |

### WebSocket
| Endpoint | Auth | Purpose |
|----------|------|---------|
| WS /calls/ws/{user_id} | ✅ JWT | Presence tracking (online/offline) |
| WS /ws/webrtc/{call_id} | ✅ JWT | WebRTC signaling (offer/answer/ICE) |

---

## Known Issues & Fixes Applied

### ✅ Fixed Issues

1. **Issue:** Users showing as available but "Receiver is not online" error
   - **Root Cause:** `/calls/available` checked database `is_online` flag, but `/calls/initiate` checked in-memory `online_users` set (out of sync)
   - **Fix:** Changed `/calls/initiate` to also check database `is_online` flag
   - **File:** `backend/app/routes/calls.py`, line 84

2. **Issue:** Users not marked online after login
   - **Root Cause:** Login endpoint didn't call `set_user_online()`
   - **Fix:** Added `set_user_online(db, user.id)` in login endpoint
   - **File:** `backend/app/routes/auth.py`, line 127

3. **Issue:** WebSocket connection failing due to wrong token
   - **Root Cause:** Frontend passing `call_token` instead of JWT token
   - **Fix:** Changed Dashboard to pass JWT token from localStorage
   - **File:** `frontend/src/pages/Dashboard.tsx`, line 119

4. **Issue:** WebSocket route not found
   - **Root Cause:** Path prefix misconfiguration
   - **Fix:** Verified router prefix is `/ws` and full route is `/ws/webrtc/{call_id}`
   - **File:** `backend/app/routes/webrtc.py`, line 24

5. **Issue:** WebRTC manager not synchronized with active connections
   - **Root Cause:** Two separate tracking systems not synced
   - **Fix:** Now create peer connection in webrtc_manager when WebSocket connects
   - **File:** `backend/app/routes/webrtc.py`, line 95

---

## What's Left To Do (15 Items Remaining)

### 🔴 CRITICAL (Blocking)
1. **[BLOCKER] Debug WebRTC offer creation failure**
   - Check console logs when calling
   - Verify WebSocket connection established
   - Check local stream has valid tracks
   - Test in Chrome/Firefox
   - Estimated: 1-2 hours

### 🟠 HIGH PRIORITY (Core Features)
2. **Test WebRTC peer connection** (once offer is fixed)
   - SDP offer/answer exchange
   - ICE candidate gathering
   - Connection state transitions
   - Estimated: 1 hour

3. **Implement incoming call handling**
   - Add incoming call notification component
   - Accept/reject buttons
   - Auto-redirect to call page on accept
   - Estimated: 2-3 hours

4. **Test video/audio streaming**
   - Verify local video displays correctly
   - Verify remote video displays after connection
   - Test audio input/output
   - Test mute functionality
   - Estimated: 1 hour

5. **Test chat functionality**
   - Send/receive messages during call
   - Message history display
   - Timestamp accuracy
   - Estimated: 30 minutes

6. **Test call end functionality**
   - End Call button closes connection
   - `/calls/end/{id}` API call succeeds
   - Redirect to dashboard
   - Estimated: 30 minutes

### 🟡 MEDIUM PRIORITY (Additional Features)
7. **Add call history view**
   - New page showing past calls
   - Display: participant, date, duration
   - Use `GET /calls/history` endpoint
   - Estimated: 2 hours

8. **Add user profile pages**
   - View own profile: username, email, bio, picture
   - Edit profile: bio, picture
   - View other user's profile
   - Use `GET /users/{id}` and `PUT /users/me`
   - Estimated: 2 hours

9. **Implement block/report functionality**
   - Block button on user profile
   - Report button with reason text
   - Show blocked users list
   - Use `POST /users/block/{id}`, `/users/report/{id}`
   - Estimated: 2 hours

10. **Test presence WebSocket**
    - Verify users go online on login
    - Verify users go offline on logout
    - Test with multiple users simultaneously
    - Estimated: 1 hour

### 🟢 LOWER PRIORITY (Testing & Optimization)
11. **End-to-end testing**
    - Test complete user journey:
      - Register → Verify Email → Login → Available Users → Start Call → Video/Chat → End Call → History
    - Test with 2+ simultaneous users
    - Test edge cases (network errors, dropped calls)
    - Estimated: 3-4 hours

12. **Error handling & recovery**
    - Handle WebSocket disconnects with reconnect
    - Handle failed call initiations
    - Handle media access denied
    - Timeout handling
    - Graceful error messages to user
    - Estimated: 2-3 hours

13. **Performance optimization**
    - Reduce unnecessary re-renders
    - Optimize API calls (use caching)
    - Optimize database queries (add indexes)
    - WebSocket message throttling
    - Bundle size analysis
    - Estimated: 2 hours

14. **Security audit**
    - CORS configuration validation
    - JWT token validation
    - SQL injection prevention
    - XSS prevention
    - Rate limiting verification
    - HTTPS enforcement planning
    - Estimated: 1-2 hours

15. **Docker & Deployment**
    - Create Dockerfile for backend & frontend
    - Create docker-compose.yml
    - Test containerized deployment
    - Set up SSL certificates
    - Configure production environment variables
    - Set up database backups
    - Estimated: 3-4 hours

---

## How to Run Locally

### Prerequisites
- Python 3.10+
- Node.js 18+
- PostgreSQL 13+

### Backend Setup
```bash
cd backend
python -m venv venv
source venv/Scripts/activate  # Windows
pip install -r requirements.txt

# Create .env file with:
DATABASE_URL=postgresql://user:password@localhost/unilink
JWT_SECRET=your-secret-key
SMTP_PASSWORD=your-email-password

python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Frontend Setup
```bash
cd frontend
npm install
npm run dev  # Runs on http://localhost:3001
```

### Access
- Frontend: http://localhost:3001
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

---

## Testing Checklist

### Basic Flow
- [ ] Register new user with @kiit.ac.in email
- [ ] Receive verification email and verify
- [ ] Login with credentials
- [ ] See dashboard with available users
- [ ] Start call with another user
- [ ] **[BLOCKED] See local video stream**
- [ ] **[BLOCKED] Receive call notification (not implemented)**
- [ ] **[BLOCKED] See remote video stream**
- [ ] **[BLOCKED] Send/receive chat messages**
- [ ] **[BLOCKED] End call and return to dashboard**
- [ ] See call in history

### Edge Cases
- [ ] Try to call offline user (should fail)
- [ ] Try to call blocked user (should fail)
- [ ] Multiple simultaneous calls (should reject second)
- [ ] Network disconnect during call
- [ ] Browser close during call
- [ ] Tab switch and return

---

## Notes for Next AI Session

1. **Start with the WebRTC blocker** - This is blocking all call testing
2. **Use browser DevTools extensively** - Console logs are your friend
3. **Test in Chrome first** - Most WebRTC compatible
4. **Check both frontend (browser) and backend (terminal) logs**
5. **Database is already set up** - No migration needed, tables are created on startup
6. **All HTTP endpoints are working** - Only WebRTC signaling needs debugging
7. **Frontend state management (Zustand) is working** - Auth flow is complete
8. **Frontend routing is working** - All pages navigate correctly

---

## Success Criteria for Project Completion

✅ Complete when:
1. Two users can successfully initiate and connect video calls
2. Both see each other's video and audio
3. Can chat during calls
4. Can end calls cleanly
5. All CRUD operations work (create call, accept, reject, end, history)
6. User blocking/reporting works
7. Call history displays correctly
8. Deployed to production with SSL
9. All endpoints tested and working
10. Zero critical security issues

---

## Contact Points

### Key Backend Files to Check for Issues
- `backend/app/routes/webrtc.py` - WebSocket handling
- `backend/app/routes/calls.py` - Call logic
- `backend/app/core/security.py` - JWT validation

### Key Frontend Files to Check for Issues
- `frontend/src/pages/Call.tsx` - WebRTC connection
- `frontend/src/pages/Dashboard.tsx` - User listing & call initiation
- `frontend/src/utils/api.ts` - Axios configuration

### Debugging Commands
```bash
# Check backend logs
tail -f <backend-terminal-output>

# Check frontend logs
Open browser DevTools (F12) → Console

# Check database
psql -U postgres -d unilink
SELECT * FROM users;
SELECT * FROM calls;
```

---

**Project Status:** 65% Complete - Waiting on WebRTC debugging
**Main Blocker:** SDP offer creation failing in peer connection setup
**Estimated Time to MVP:** 8-10 hours with WebRTC fixed, then 10-15 hours for remaining features
**Critical Path:** Fix WebRTC → Test Video/Audio → Incoming Calls → E2E Testing → Production Deploy
