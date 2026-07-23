# Deployment Guide

## Local Development

### Prerequisites
- Docker & Docker Compose
- Python 3.11+
- Node.js 18+

### Setup

1. Clone the repository
2. Copy environment file:
```bash
cp backend/.env.example backend/.env
```

3. Start services:
```bash
docker-compose up -d
```

4. Run migrations:
```bash
docker-compose exec backend alembic upgrade head
```

5. Access the application:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- RabbitMQ Management: http://localhost:15672

## Kubernetes Deployment

### Prerequisites
- Kubernetes cluster (1.24+)
- kubectl configured
- Docker registry access

### Build Images

```bash
# Backend
docker build -t your-registry/devanalytics-backend:latest ./backend
docker push your-registry/devanalytics-backend:latest

# Frontend
docker build -t your-registry/devanalytics-frontend:latest ./frontend
docker push your-registry/devanalytics-frontend:latest
```

### Create Secrets

```bash
kubectl create secret generic db-secret \
  --from-literal=password=your-db-password \
  -n devanalytics

kubectl create secret generic app-secret \
  --from-literal=jwt-secret=your-jwt-secret \
  -n devanalytics
```

### Deploy

```bash
# Create namespace
kubectl apply -f k8s/namespace.yaml

# Deploy infrastructure
kubectl apply -f k8s/postgres.yaml
kubectl apply -f k8s/redis.yaml

# Deploy application
kubectl apply -f k8s/backend.yaml
kubectl apply -f k8s/frontend.yaml
kubectl apply -f k8s/celery-worker.yaml
```

### Run Migrations

```bash
kubectl exec -it deployment/backend -n devanalytics -- alembic upgrade head
```

### Verify Deployment

```bash
kubectl get pods -n devanalytics
kubectl get services -n devanalytics
```

## Scaling

### Horizontal Scaling

```bash
# Scale backend
kubectl scale deployment backend --replicas=5 -n devanalytics

# Scale workers
kubectl scale deployment celery-worker --replicas=4 -n devanalytics
```

### Auto-scaling

```bash
kubectl autoscale deployment backend \
  --cpu-percent=70 \
  --min=3 \
  --max=10 \
  -n devanalytics
```

## Monitoring

### Health Checks

- Backend: http://backend:8000/health
- Check pod status: `kubectl get pods -n devanalytics`

### Logs

```bash
# Backend logs
kubectl logs -f deployment/backend -n devanalytics

# Worker logs
kubectl logs -f deployment/celery-worker -n devanalytics
```

## Backup

### Database Backup

```bash
kubectl exec -it deployment/postgres -n devanalytics -- \
  pg_dump -U devuser devanalytics > backup.sql
```

### Restore

```bash
kubectl exec -i deployment/postgres -n devanalytics -- \
  psql -U devuser devanalytics < backup.sql
```
