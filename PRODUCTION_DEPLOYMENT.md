# Production Deployment Guide

## Overview

This guide covers deploying UniLink to production with security, scalability, and reliability best practices.

## Phase 2 Improvements (Current)

### ✅ Completed

- **Rate Limiting**: 10 requests/minute on auth endpoints, 60/minute on general API
- **CORS Hardening**: Whitelist-based origin validation
- **Structured Logging**: Python logging module with detailed event tracking
- **Health Check**: `/health` endpoint with database connectivity verification
- **Database Indexes**: 8 performance indexes on frequently queried columns
- **Error Handling**: Middleware to catch and log unhandled exceptions
- **Frontend Error Boundary**: React error boundary with structured logging
- **Error Logging Utility**: Frontend error context tracking

---

## Deployment Architecture

### Recommended Setup

```
┌─────────────────────────────────────────────────────────────┐
│                    CloudFlare / CDN                         │
│              (SSL Termination + Caching)                    │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│                  Load Balancer (Nginx/HAProxy)              │
│                  (Port 443 → 80, Rate Limit)                │
└─────────────────────────────────────────────────────────────┘
         ↓                        ↓                    ↓
    ┌─────────┐            ┌─────────┐          ┌─────────┐
    │Backend-1│            │Backend-2│          │Backend-3│
    │:8000    │            │:8000    │          │:8000    │
    └─────────┘            └─────────┘          └─────────┘
         ↓                        ↓                    ↓
    ┌──────────────────────────────────────────────────────┐
    │   RDS PostgreSQL (Managed DB with Auto-backups)     │
    │   - Automated backups every 6 hours                 │
    │   - Multi-AZ failover                              │
    │   - Read replicas for scaling                       │
    └──────────────────────────────────────────────────────┘

    ┌──────────────────────────────────────────────────────┐
    │   Redis (Session Store + Cache)                      │
    │   - Connection pooling                              │
    │   - TTL-based expiration                            │
    └──────────────────────────────────────────────────────┘

    ┌──────────────────────────────────────────────────────┐
    │   Monitoring (Prometheus/Grafana + Sentry)           │
    │   - Real-time metrics                               │
    │   - Error tracking & alerting                       │
    └──────────────────────────────────────────────────────┘
```

---

## Environment Configuration

### Backend (.env)

```bash
# DATABASE
DATABASE_URL=postgresql://user:pass@db.example.com:5432/unilink
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=40

# JWT - GENERATE STRONG 32+ CHAR KEY
SECRET_KEY=your-super-secret-key-min-32-characters-generate-with-secrets.token_urlsafe(32)
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# EMAIL - Use AWS SES or SendGrid in production
SMTP_SERVER=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USER=apikey
SMTP_PASSWORD=SG.xxxxxxxxxxxx
EMAIL_FROM=noreply@unilink.app

# SERVER
BACKEND_URL=https://api.unilink.app
FRONTEND_URL=https://unilink.app
ENVIRONMENT=production

# SECURITY
ALLOWED_ORIGINS=["https://unilink.app", "https://www.unilink.app"]
RATE_LIMIT_AUTH=5
RATE_LIMIT_API=30

# MONITORING
SENTRY_DSN=https://xxxxx@sentry.io/project-id
LOG_LEVEL=INFO
```

### Docker Secrets (Use AWS Secrets Manager, HashiCorp Vault, or similar)

- Never commit .env files to git
- Use environment-specific configurations
- Rotate secrets regularly

---

## Deployment Steps

### 1. AWS ECS/EKS Deployment

#### Prerequisites
- AWS Account with EC2/ECS/RDS access
- Docker images pushed to ECR
- RDS PostgreSQL instance running
- Redis cluster running

#### Deploy Backend

```bash
# Build and push to ECR
docker tag docker-backend:latest 123456789.dkr.ecr.us-east-1.amazonaws.com/unilink:latest
docker push 123456789.dkr.ecr.us-east-1.amazonaws.com/unilink:latest

# Update ECS task definition with new image
# Deploy frontend to CloudFront + S3
aws s3 sync dist/ s3://unilink-frontend-prod/ --delete
aws cloudfront create-invalidation --distribution-id E1234 --paths "/*"
```

### 2. Database Migrations

```bash
# Connect to production DB
psql postgresql://user:pass@db.example.com:5432/unilink

# Apply migrations
alembic upgrade head

# Verify indexes created
SELECT * FROM pg_indexes WHERE tablename = 'users';
```

### 3. Health Check

```bash
# Verify all services are healthy
curl https://api.unilink.app/health

# Expected response:
{
  "status": "healthy",
  "database": "connected",
  "version": "1.2.0"
}
```

---

## Security Checklist

- [ ] **HTTPS/TLS**: All traffic encrypted (Let's Encrypt certificates)
- [ ] **JWT Secret**: Use cryptographically strong key (32+ characters)
- [ ] **Rate Limiting**: Active on all public endpoints
- [ ] **CORS**: Whitelist only known domains
- [ ] **SQL Injection**: All queries parameterized (SQLAlchemy handles this)
- [ ] **XSS Protection**: React auto-escapes HTML
- [ ] **CSRF**: Token validation for state-changing requests
- [ ] **DDoS Protection**: CloudFlare or AWS Shield
- [ ] **API Keys**: Rotate every 90 days
- [ ] **Secrets Management**: Use vault (not committed to git)
- [ ] **Logging**: Centralized logging (ELK Stack or CloudWatch)
- [ ] **Monitoring**: Real-time alerts for errors > threshold

---

## Monitoring & Alerting

### Key Metrics to Monitor

1. **Backend**
   - Request latency (p50, p95, p99)
   - Error rate (4xx, 5xx)
   - Database connection pool usage
   - WebSocket connection count
   - Auth endpoint rate limit hits

2. **Database**
   - Query execution time
   - Connection pool saturation
   - Disk usage
   - Replication lag

3. **Frontend**
   - Page load time
   - Error rate (JS exceptions)
   - WebSocket reconnect frequency
   - WebRTC connection failures

### Alerting Rules

```yaml
# Example Prometheus alerts

groups:
  - name: unilink_alerts
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.05
        for: 5m
        annotations:
          summary: "High error rate detected"

      - alert: HighDatabaseLatency
        expr: histogram_quantile(0.95, rate(db_query_duration_seconds_bucket[5m])) > 1
        for: 5m

      - alert: LowDiskSpace
        expr: node_filesystem_avail_bytes{mountpoint="/"} < 1073741824  # 1GB
        for: 1m
```

---

## Scaling Strategy

### Horizontal Scaling (Multiple Backends)

1. **Load Balancing**: Nginx/HAProxy distributes traffic
2. **Session Storage**: Move from memory to Redis
3. **Database**: Use read replicas for read-heavy queries
4. **WebSocket**: Use Redis pub/sub for cross-server message relay

### Vertical Scaling (Single Backend)

1. **CPU**: Increase container limits
2. **Memory**: Add caching layer (Redis)
3. **Connections**: Increase PostgreSQL pool size

---

## Maintenance & Backups

### Database Backups

```bash
# Daily automated backups (AWS RDS)
# Manual backup before major deployments
pg_dump postgresql://user:pass@db.example.com/unilink > unilink_$(date +%Y%m%d).sql
```

### Log Retention

- Errors: 30 days
- Info/Debug: 7 days
- Audit logs: 1 year

### Dependency Updates

- Security patches: Apply within 24 hours
- Minor updates: Monthly
- Major updates: Quarterly with staging tests

---

## Disaster Recovery

### RTO (Recovery Time Objective): 1 hour
### RPO (Recovery Point Objective): 15 minutes

1. **Backup Strategy**
   - Automated daily RDS snapshots
   - Weekly full database backups to S3
   - Point-in-time recovery enabled

2. **Failover Procedure**
   - Switch traffic to standby region (via Route53)
   - Restore from latest backup
   - Verify data integrity

3. **Communication Plan**
   - Incident: Notify on #status-page
   - Update: Post to twitter/slack every 15 min
   - Resolution: Full postmortem within 48 hours

---

## Next Steps (Phase 3)

- [ ] Automated testing (E2E with Playwright)
- [ ] Load testing (Apache JMeter / k6)
- [ ] Security audit & penetration testing
- [ ] GDPR/Privacy compliance review
- [ ] Mobile app support (iOS/Android)
- [ ] Call recording & transcription
- [ ] Analytics dashboard
- [ ] Admin panel for moderation

---

## Support & Incident Response

**On-Call Rotation**: Engineering team rotating weekly
**PagerDuty Integration**: Automatic escalation after 15 min
**Status Page**: https://status.unilink.app

Contact: ops@unilink.app
