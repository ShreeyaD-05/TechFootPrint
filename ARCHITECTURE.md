# System Architecture

## Overview

The Developer Analytics Platform follows a microservice-inspired architecture with clear separation of concerns.

## Architecture Diagram

```
┌─────────────┐
│   Frontend  │ (React + TypeScript)
│   (Port 3000)│
└──────┬──────┘
       │
       │ HTTP/REST
       │
┌──────▼──────────────────────────────────────┐
│         API Gateway (FastAPI)               │
│              (Port 8000)                    │
└──────┬──────────────────────────────────────┘
       │
       ├─────────┬─────────┬─────────┬─────────┐
       │         │         │         │         │
   ┌───▼───┐ ┌──▼──┐  ┌───▼───┐ ┌───▼────┐ ┌──▼──┐
   │ Auth  │ │User │  │Connector│Analytics││Portfolio│
   │Service│ │Svc  │  │ Service │ Service ││Service│
   └───────┘ └─────┘  └────┬────┘ └────────┘ └─────┘
                           │
                    ┌──────▼──────┐
                    │  Connector  │
                    │  Registry   │
                    └──────┬──────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
   ┌────▼────┐      ┌──────▼──────┐   ┌──────▼──────┐
   │LeetCode │      │ Codeforces  │   │  CodeChef   │
   │Connector│      │  Connector  │   │  Connector  │
   └─────────┘      └─────────────┘   └─────────────┘

┌──────────────────────────────────────────────────┐
│           Background Workers (Celery)            │
│  - Platform Sync Workers                         │
│  - Analytics Calculation Workers                 │
│  - Scheduled Tasks (Celery Beat)                 │
└──────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────┐
│              Data Layer                          │
│  ┌──────────┐  ┌───────┐  ┌──────────┐         │
│  │PostgreSQL│  │ Redis │  │ RabbitMQ │         │
│  │(Primary) │  │(Cache)│  │  (Queue) │         │
│  └──────────┘  └───────┘  └──────────┘         │
└──────────────────────────────────────────────────┘
```

## Components

### 1. API Gateway
- Entry point for all client requests
- Routes requests to appropriate services
- Handles CORS and middleware
- Technology: FastAPI

### 2. Authentication Service
- JWT token generation and validation
- User registration and login
- Password hashing with bcrypt
- OAuth integration ready

### 3. User Service
- Profile management
- User preferences
- Portfolio configuration

### 4. Connector Service
- Platform integration framework
- Adapter pattern for unified data models
- Extensible connector registry
- Supported platforms:
  - LeetCode (GraphQL API)
  - Codeforces (REST API)
  - CodeChef (Scraping/API)
  - GitHub (REST API)

### 5. Analytics Service
- Problem statistics aggregation
- Streak calculation
- Topic distribution analysis
- Platform-wise breakdown
- Activity heatmap generation

### 6. Portfolio Service
- Public profile generation
- Portfolio data caching
- View tracking
- Shareable links

### 7. Background Workers
- Celery workers for async tasks
- Scheduled syncing (Celery Beat)
- Platform data fetching
- Analytics recalculation
- Notification dispatch

## Data Flow

### User Registration Flow
1. User submits registration form
2. Frontend sends POST to `/auth/register`
3. Auth service validates and creates user
4. Password hashed with bcrypt
5. User record stored in PostgreSQL
6. Success response returned

### Platform Connection Flow
1. User connects platform account
2. POST to `/platforms/connect`
3. Platform account record created
4. Background task queued for sync
5. Celery worker picks up task
6. Connector fetches data from platform
7. Data normalized and stored
8. Analytics recalculated
9. User notified of completion

### Analytics Calculation Flow
1. Triggered by sync completion or manual request
2. Aggregate problem stats from all platforms
3. Calculate difficulty distribution
4. Compute topic distribution
5. Calculate current and longest streaks
6. Store results in analytics table
7. Cache in Redis for fast retrieval

## Database Schema

### Core Tables
- `users` - User accounts
- `profiles` - User profiles and settings
- `platform_accounts` - Connected platform accounts
- `problem_stats` - Individual problem solutions
- `contest_stats` - Contest participation records
- `activity_logs` - User activity timeline
- `analytics` - Computed analytics data
- `portfolio_data` - Generated portfolio content

### Relationships
- User 1:1 Profile
- User 1:N PlatformAccounts
- PlatformAccount 1:N ProblemStats
- PlatformAccount 1:N ContestStats
- User 1:N ActivityLogs
- User 1:1 Analytics

## Scalability Considerations

### Horizontal Scaling
- Stateless API servers (scale with load balancer)
- Multiple Celery workers (scale based on queue depth)
- Read replicas for PostgreSQL
- Redis cluster for distributed caching

### Caching Strategy
- User analytics cached in Redis (TTL: 1 hour)
- Platform data cached after sync
- Portfolio pages cached (TTL: 24 hours)
- Cache invalidation on data updates

### Queue Management
- Separate queues for different task types
- Priority queue for user-initiated syncs
- Rate limiting for platform API calls
- Retry logic with exponential backoff

## Security

### Authentication
- JWT tokens with expiration
- Secure password hashing (bcrypt)
- OAuth 2.0 support
- Token refresh mechanism

### Data Protection
- Encrypted credentials storage
- SQL injection prevention (SQLAlchemy ORM)
- Input validation (Pydantic)
- CORS configuration
- Rate limiting

### API Security
- Authentication required for protected endpoints
- User-specific data isolation
- Public portfolio opt-in only
- Secure headers

## Monitoring & Observability

### Health Checks
- `/health` endpoint for service status
- Database connectivity check
- Redis connectivity check
- RabbitMQ connectivity check

### Logging
- Structured logging (JSON format)
- Request/response logging
- Error tracking
- Worker task logging

### Metrics
- API response times
- Task queue depth
- Sync success/failure rates
- Database query performance
- Cache hit rates

## Extensibility

### Adding New Connectors
1. Create new connector class extending `BaseConnector`
2. Implement required methods:
   - `authenticate()`
   - `fetch_profile()`
   - `fetch_problem_stats()`
   - `fetch_contest_stats()`
   - `fetch_activity()`
3. Register in `ConnectorRegistry`
4. Deploy and test

### Adding New Services
1. Create service directory under `backend/services/`
2. Implement service logic
3. Create API routes in `gateway/routes/`
4. Add to gateway router
5. Update documentation

## Technology Stack

### Backend
- FastAPI - Web framework
- SQLAlchemy - ORM
- Alembic - Database migrations
- Celery - Task queue
- Redis - Caching
- RabbitMQ - Message broker
- PostgreSQL - Primary database

### Frontend
- React 18 - UI framework
- TypeScript - Type safety
- Recharts - Data visualization
- Axios - HTTP client
- React Router - Navigation

### Infrastructure
- Docker - Containerization
- Docker Compose - Local development
- Kubernetes - Production orchestration
- Nginx - Reverse proxy (optional)
