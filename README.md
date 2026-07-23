# Developer Analytics Platform

A production-ready, scalable platform for aggregating coding statistics from multiple competitive programming platforms. Track your progress, showcase your skills, and maintain your developer portfolio all in one place.

## ✨ Features

- 🔗 **Multi-Platform Integration** - Connect LeetCode, Codeforces, CodeChef, HackerRank, GeeksforGeeks, GitHub, and more
- 📊 **Comprehensive Analytics** - Track problems solved, difficulty distribution, coding streaks
- 🎯 **Smart Sync** - Automatic background synchronization of your coding activity
- 📈 **Visual Insights** - Interactive charts and activity heatmaps
- 🌐 **Public Portfolio** - Shareable developer profile with all your achievements
- 🔐 **Secure Authentication** - JWT-based auth with OAuth support
- ⚡ **High Performance** - Redis caching and async task processing
- 🚀 **Production Ready** - Kubernetes-ready microservice architecture

## 🏗️ Architecture

### Tech Stack

- **Backend**: FastAPI (Python 3.11+)
- **Frontend**: React 18 + TypeScript
- **Database**: PostgreSQL 15
- **Cache**: Redis 7
- **Task Queue**: Celery + RabbitMQ
- **Containerization**: Docker + Docker Compose
- **Orchestration**: Kubernetes
- **Authentication**: JWT + OAuth 2.0

### Microservices

1. **API Gateway** - Request routing and middleware
2. **Auth Service** - User authentication and authorization
3. **User Service** - Profile and preferences management
4. **Connector Service** - Platform integration framework
5. **Analytics Service** - Statistics computation and aggregation
6. **Portfolio Service** - Public profile generation
7. **Background Workers** - Async data synchronization

## 🚀 Quick Start

### Prerequisites

- Docker Desktop (with 8GB+ RAM)
- Docker Compose
- Ports 3000, 8000, 5432, 6379, 5672 available

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd developer-analytics-platform

# Copy environment configuration
cp backend/.env.example backend/.env

# Start all services
docker-compose up -d

# Run database migrations
docker-compose exec backend alembic upgrade head
```

### Access the Application

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **RabbitMQ Management**: http://localhost:15672

### Using Make Commands

```bash
make up        # Start all services
make down      # Stop all services
make logs      # View logs
make migrate   # Run migrations
make clean     # Clean up everything
```

## 📖 Documentation

- **[Quick Start Guide](QUICKSTART.md)** - Get running in 5 minutes
- **[Architecture Overview](ARCHITECTURE.md)** - System design and components
- **[API Documentation](API_DOCUMENTATION.md)** - Complete API reference
- **[Deployment Guide](DEPLOYMENT.md)** - Production deployment instructions
- **[Project Structure](PROJECT_STRUCTURE.md)** - Codebase organization

## 🔌 Supported Platforms

### Currently Implemented
- ✅ **LeetCode** - GraphQL API integration
- ✅ **Codeforces** - REST API integration
- ✅ **GitHub** - REST API integration

### Easy to Add
The connector framework makes it simple to add new platforms:

```python
class NewPlatformConnector(BaseConnector):
    async def fetch_profile(self) -> ProfileData:
        # Implement platform-specific logic
        pass
    
    async def fetch_problem_stats(self) -> List[ProblemData]:
        # Fetch solved problems
        pass
```

Register and you're done!

## 📊 Features in Detail

### Analytics Dashboard
- Total problems solved across all platforms
- Difficulty distribution (Easy/Medium/Hard)
- Current and longest coding streaks
- Topic-wise problem breakdown
- Platform-wise statistics
- Activity heatmap (365 days)

### Public Portfolio
- Customizable developer profile
- Aggregated statistics from all platforms
- Social links (GitHub, LinkedIn, Website)
- Shareable public URL
- View tracking

### Background Sync
- Automatic daily synchronization
- Manual sync on-demand
- Retry logic with exponential backoff
- Rate limiting for API calls
- Real-time progress tracking

## 🏗️ Project Structure

```
developer-analytics-platform/
├── backend/                    # Backend services
│   ├── gateway/               # API Gateway (FastAPI)
│   ├── services/              # Business logic
│   │   ├── auth/             # Authentication
│   │   ├── connector/        # Platform integrations
│   │   └── analytics/        # Analytics engine
│   ├── shared/               # Common utilities
│   ├── workers/              # Celery workers
│   └── alembic/              # Database migrations
├── frontend/                  # React frontend
│   └── src/
│       ├── pages/            # Page components
│       ├── context/          # State management
│       └── App.tsx           # Main application
├── k8s/                      # Kubernetes manifests
├── docker-compose.yml        # Local development
└── docs/                     # Documentation
```

## 🔐 Security

- JWT token-based authentication
- Bcrypt password hashing
- SQL injection prevention (SQLAlchemy ORM)
- Input validation (Pydantic)
- CORS configuration
- Rate limiting
- Secure credential storage

## 📈 Scalability

### Horizontal Scaling
- Stateless API servers (scale with load balancer)
- Multiple Celery workers (scale based on queue depth)
- PostgreSQL read replicas
- Redis cluster for distributed caching

### Performance Optimization
- Redis caching (1-hour TTL for analytics)
- Database query optimization with indexes
- Async I/O for external API calls
- Connection pooling
- Background task processing

## 🧪 Testing

```bash
# Run backend tests
docker-compose exec backend pytest

# Run frontend tests
docker-compose exec frontend npm test

# Run integration tests
docker-compose exec backend pytest tests/integration/
```

## 🚢 Deployment

### Docker Compose (Development)
```bash
docker-compose up -d
```

### Kubernetes (Production)
```bash
# Create namespace
kubectl apply -f k8s/namespace.yaml

# Deploy services
kubectl apply -f k8s/

# Scale as needed
kubectl scale deployment backend --replicas=5 -n devanalytics
```

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed instructions.

## 🛠️ Development

### Backend Development
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn gateway.main:app --reload
```

### Frontend Development
```bash
cd frontend
npm install
npm start
```

### Adding a New Connector
1. Create `backend/services/connector/platform_name.py`
2. Extend `BaseConnector` class
3. Implement required methods
4. Register in `ConnectorRegistry`
5. Test and deploy

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📝 License

This project is licensed under the MIT License.

## 🙏 Acknowledgments

- FastAPI for the excellent web framework
- React team for the UI library
- Celery for distributed task processing
- All the competitive programming platforms for their APIs

## 📞 Support

- 📧 Email: support@devanalytics.com
- 💬 Discord: [Join our community]
- 🐛 Issues: [GitHub Issues]
- 📖 Docs: [Full Documentation]

---

Built with ❤️ for developers, by developers.
