# Docker Setup Guide

## Overview

This application has been fully containerized with Docker for easy deployment and development. The setup includes:

- **Development environment**: Docker Compose for easy local development
- **Production environment**: Optimized multi-stage Docker build
- **Environment variables**: All configuration externalized
- **Security**: Non-root user, minimal attack surface
- **Health checks**: Built-in monitoring

## Quick Start

### 1. Development with Docker Compose

```bash
# Copy environment template
cp env.example .env

# Edit .env file with your settings (optional)
nano .env

# Start the application
docker-compose up --build
```

### 2. Production Deployment

```bash
# Build production image
docker build -f Dockerfile.prod -t reactor-backend:prod .

# Run production container
docker run -d \
  --name reactor-backend \
  -p 8080:8080 \
  -e DEFAULT_ADMIN_PASSWORD=your_secure_password \
  -v $(pwd)/data:/app/data \
  reactor-backend:prod
```

## Docker Files Explained

### Dockerfile
- **Purpose**: Development and testing
- **Features**: 
  - Single-stage build
  - Includes development tools
  - Faster builds for development

### Dockerfile.prod
- **Purpose**: Production deployment
- **Features**:
  - Multi-stage build for smaller image
  - Only runtime dependencies
  - Security optimizations
  - Non-root user

### docker-compose.yml
- **Purpose**: Local development
- **Features**:
  - Environment variable support
  - Volume mounts for data persistence
  - Health checks
  - Easy service management

## Environment Variables

All configuration is externalized through environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `HOST` | `localhost` | Server host |
| `PORT` | `8080` | Server port |
| `DEBUG` | `true` | Debug mode |
| `RELOADER` | `true` | Auto-reload |
| `DB_PATH` | `users.db` | Database file path |
| `DEFAULT_ADMIN_USERNAME` | `admin` | Admin username |
| `DEFAULT_ADMIN_PASSWORD` | `admin123` | Admin password |
| `SESSION_EXPIRY_HOURS` | `24` | Session timeout |
| `TOKEN_LENGTH` | `32` | Token length |

## Security Features

### Container Security
- **Non-root user**: Application runs as `app` user
- **Minimal base image**: Python slim image
- **No unnecessary packages**: Only required dependencies
- **Read-only filesystem**: Where possible

### Application Security
- **Environment variables**: Secrets externalized
- **Token-based auth**: Secure session management
- **Password hashing**: SHA256 for passwords
- **Input validation**: Proper request validation

## Data Persistence

### Development
- Database file: `./data/users.db`
- Logs: `./logs/`

### Production
- Database file: `/app/data/users.db` (mounted volume)
- Logs: `/app/logs/` (mounted volume)

## Health Checks

The application includes built-in health checks:

```bash
# Check container health
docker ps

# View health check logs
docker inspect reactor-backend | grep Health -A 10
```

## Monitoring

### Container Metrics
```bash
# View container stats
docker stats reactor-backend

# View container logs
docker logs reactor-backend
```

### Application Health
```bash
# Health endpoint
curl http://localhost:8080/health
```

## Troubleshooting

### Common Issues

1. **Port already in use**
   ```bash
   # Change port in .env file
   PORT=8081
   ```

2. **Permission denied**
   ```bash
   # Fix volume permissions
   sudo chown -R $USER:$USER ./data ./logs
   ```

3. **Database not persisting**
   ```bash
   # Check volume mounts
   docker inspect reactor-backend | grep Mounts -A 20
   ```

### Debug Mode

Enable debug mode for detailed logs:

```bash
# In .env file
DEBUG=true
RELOADER=true
```

## Production Deployment

### Docker Swarm
```bash
# Deploy to swarm
docker stack deploy -c docker-compose.yml reactor-backend
```

### Kubernetes
```bash
# Apply Kubernetes manifests
kubectl apply -f k8s/
```

### Cloud Platforms
- **AWS ECS**: Use the production Dockerfile
- **Google Cloud Run**: Optimized for serverless
- **Azure Container Instances**: Simple deployment

## Best Practices

1. **Always use production Dockerfile** for production
2. **Set secure passwords** via environment variables
3. **Use secrets management** for sensitive data
4. **Monitor container health** regularly
5. **Backup database** regularly
6. **Update base images** periodically
7. **Scan for vulnerabilities** with tools like Trivy

## Performance Optimization

### Development
- Use Docker Compose for easy development
- Enable volume mounts for live code changes
- Use debug mode for detailed logging

### Production
- Use multi-stage builds for smaller images
- Disable debug mode
- Use proper resource limits
- Monitor performance metrics 