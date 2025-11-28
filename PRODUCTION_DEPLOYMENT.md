# S4 Remote Robot Management System - Production Deployment Guide

## 🚀 Deployment Options

### Option 1: Local Development (Current Setup)

**Suitable for**: Testing, development, demonstrations

```bash
# Terminal 1 - Backend
cd backend
python app.py

# Terminal 2 - Frontend
cd frontEnd
npm run dev
```

**Access**: http://localhost:5173

---

### Option 2: Docker Containerization

**Suitable for**: Consistent deployment across environments

#### Create Dockerfile for Backend

```dockerfile
# backend/Dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .

ENV FLASK_ENV=production
ENV PORT=5001

EXPOSE 5001

CMD ["python", "app.py"]
```

#### Create Dockerfile for Frontend

```dockerfile
# frontEnd/Dockerfile
FROM node:16-alpine as build

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .
RUN npm run build

# Production stage
FROM node:16-alpine

WORKDIR /app

COPY package*.json ./
RUN npm install --only=production

COPY server.js .
COPY --from=build /app/dist ./dist

EXPOSE 5173

CMD ["npm", "start"]
```

#### Create docker-compose.yml

```yaml
# docker-compose.yml
version: '3.8'

services:
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    ports:
      - "5001:5001"
    environment:
      - FLASK_ENV=production
      - SECRET_KEY=${SECRET_KEY:-your-secure-key}
      - PORT=5001
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5001/api/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  frontend:
    build:
      context: ./frontEnd
      dockerfile: Dockerfile
    ports:
      - "80:5173"
    environment:
      - VITE_API_URL=http://localhost:5001
      - VITE_WS_URL=ws://localhost:5001/socket.io
    depends_on:
      - backend
    restart: unless-stopped

volumes:
  robot_data:
```

**Deploy with Docker:**

```bash
# Build and start containers
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

---

### Option 3: Cloud Deployment (AWS)

#### AWS EC2 Setup

```bash
# 1. Launch EC2 Instance (Ubuntu 20.04)
# Instance type: t3.medium (2 vCPU, 4GB RAM)
# Security Group: Allow 80, 443, 5001

# 2. SSH into instance
ssh -i your-key.pem ubuntu@your-instance-ip

# 3. Install dependencies
sudo apt update
sudo apt install -y python3.9 python3-pip nodejs npm git

# 4. Clone repository
git clone <your-repo-url>
cd hackathon

# 5. Install & run
cd backend
pip3 install -r requirements.txt
python3 app.py &

cd ../frontEnd
npm install
npm run build
npm start &
```

#### AWS Elastic Beanstalk Deployment

```bash
# Install EB CLI
pip install awsebcli

# Initialize EB application
eb init -p "Node.js 16 running on 64bit Amazon Linux 2" s4-robot-system

# Create environment
eb create s4-prod-env

# Deploy
git commit -m "Ready for deployment"
eb deploy

# View logs
eb logs
```

#### AWS RDS Database Setup (Optional)

```bash
# Create RDS PostgreSQL instance for production data storage
# Host: your-db-instance.xxxxx.us-east-1.rds.amazonaws.com
# Port: 5432
# Database: s4_robots
# Username: admin
# Password: (secure password)
```

---

### Option 4: Kubernetes Deployment

#### Create Kubernetes Manifests

```yaml
# k8s/backend-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: s4-backend
spec:
  replicas: 3
  selector:
    matchLabels:
      app: s4-backend
  template:
    metadata:
      labels:
        app: s4-backend
    spec:
      containers:
      - name: backend
        image: your-registry/s4-backend:latest
        ports:
        - containerPort: 5001
        env:
        - name: FLASK_ENV
          value: "production"
        - name: SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: s4-secrets
              key: secret-key
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /api/health
            port: 5001
          initialDelaySeconds: 30
          periodSeconds: 10
```

```yaml
# k8s/backend-service.yaml
apiVersion: v1
kind: Service
metadata:
  name: s4-backend-service
spec:
  selector:
    app: s4-backend
  ports:
  - protocol: TCP
    port: 5001
    targetPort: 5001
  type: LoadBalancer
```

**Deploy to Kubernetes:**

```bash
# Create namespace
kubectl create namespace s4-system

# Create secrets
kubectl create secret generic s4-secrets \
  --from-literal=secret-key=your-secure-key \
  -n s4-system

# Deploy
kubectl apply -f k8s/ -n s4-system

# Check status
kubectl get pods -n s4-system
kubectl get services -n s4-system
```

---

## 🔒 Security Configuration

### 1. Environment Variables

Create `.env.production`:

```bash
# Security
SECRET_KEY=your-super-secure-random-key-here
FLASK_ENV=production
DEBUG=False

# API
API_PORT=5001
API_HOST=0.0.0.0

# WebSocket
WS_PING_TIMEOUT=60
WS_PING_INTERVAL=25

# CORS
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# Database (if using)
DATABASE_URL=postgresql://user:password@host:5432/s4_robots

# Logging
LOG_LEVEL=INFO
LOG_FILE=/var/log/s4/backend.log
```

### 2. HTTPS/TLS Configuration

**Using Nginx as reverse proxy:**

```nginx
# /etc/nginx/sites-available/s4-robot-system
upstream s4_backend {
    server localhost:5001;
}

server {
    listen 80;
    server_name yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # Frontend
    location / {
        root /var/www/s4-robot-system/dist;
        try_files $uri $uri/ /index.html;
    }

    # Backend API
    location /api/ {
        proxy_pass http://s4_backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # WebSocket
    location /socket.io/ {
        proxy_pass http://s4_backend/socket.io/;
        proxy_http_version 1.1;
        proxy_buffering off;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "Upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

**Enable SSL certificate:**

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Get certificate
sudo certbot certonly --nginx -d yourdomain.com

# Auto-renew
sudo systemctl enable certbot.timer
```

### 3. Authentication & Authorization

Add JWT authentication to backend:

```python
# In backend/app.py

from flask_jwt_extended import JWTManager, create_access_token, jwt_required

app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'change-this-key')
jwt = JWTManager(app)

@app.route('/api/auth/login', methods=['POST'])
def login():
    """Authenticate user and return JWT token"""
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    # Verify credentials (implement your auth logic)
    if verify_credentials(username, password):
        token = create_access_token(identity=username)
        return jsonify({'token': token})
    
    return jsonify({'error': 'Invalid credentials'}), 401

@app.route('/api/robot/state', methods=['GET'])
@jwt_required()
def api_robot_state():
    """Protected endpoint requiring JWT token"""
    return jsonify(get_robot_state())
```

### 4. Rate Limiting

```python
# Add rate limiting to backend

from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

@app.route('/api/robot/state', methods=['GET'])
@limiter.limit("10/minute")
def api_robot_state():
    return jsonify(get_robot_state())
```

---

## 📊 Monitoring & Logging

### 1. Application Logging

```python
# In backend/app.py

import logging
from logging.handlers import RotatingFileHandler

# Create logs directory
os.makedirs('logs', exist_ok=True)

# Setup logger
logger = logging.getLogger('s4-robot-system')
logger.setLevel(logging.INFO)

handler = RotatingFileHandler(
    'logs/app.log',
    maxBytes=10485760,  # 10MB
    backupCount=10
)

formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
handler.setFormatter(formatter)
logger.addHandler(handler)

# Log important events
logger.info('S4 Robot Management System started')
logger.info(f'Robot {current_robot_id} initialized')
```

### 2. System Monitoring with Prometheus

```yaml
# prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 's4-backend'
    static_configs:
      - targets: ['localhost:5001']
```

```python
# Add metrics to backend
from prometheus_client import Counter, Histogram, generate_latest

# Define metrics
control_commands = Counter('s4_control_commands_total', 'Total control commands')
telemetry_latency = Histogram('s4_telemetry_latency_seconds', 'Telemetry latency')
connected_clients = Counter('s4_connected_clients', 'Connected clients')

@app.route('/metrics')
def metrics():
    return generate_latest()
```

### 3. Error Tracking with Sentry

```python
# Add Sentry for error tracking
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration

sentry_sdk.init(
    dsn="https://your-sentry-dsn@sentry.io/project-id",
    integrations=[FlaskIntegration()],
    traces_sample_rate=1.0
)
```

---

## 🚨 Health Checks & Alerts

### 1. Health Check Endpoint

```python
@app.route('/api/health', methods=['GET'])
def health_check():
    """Comprehensive system health check"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'services': {
            'control': 'operational',
            'health': 'operational',
            'path_logging': 'operational',
            'ota_updates': 'operational',
            'events': 'operational'
        },
        'robot_online': current_robot_id in robot_fleet,
        'uptime_seconds': (datetime.now() - app_start_time).total_seconds(),
        'connected_clients': len(connected_clients)
    })
```

### 2. Alert Configuration

```bash
# AlertManager configuration for Prometheus

# /etc/alertmanager/config.yml
global:
  resolve_timeout: 5m

route:
  receiver: 'team-email'

receivers:
- name: 'team-email'
  email_configs:
  - to: 'ops-team@company.com'
    from: 'alerts@company.com'
    smarthost: 'smtp.gmail.com:587'
    auth_username: 'alerts@company.com'
    auth_password: 'password'
```

---

## 📈 Scaling Strategies

### Horizontal Scaling

```bash
# Run multiple backend instances with load balancer
# Start multiple workers
gunicorn -w 4 -b 0.0.0.0:5001 app:app

# With socketio worker class
gunicorn --worker-class eventlet -w 1 app:app
```

### Vertical Scaling

Increase resources:
- RAM: 4GB → 8GB → 16GB
- CPU: 2 cores → 4 cores → 8 cores
- Storage: 50GB → 200GB → 500GB

### Database Optimization

```sql
-- Create indexes for common queries
CREATE INDEX idx_robot_id ON telemetry(robot_id);
CREATE INDEX idx_timestamp ON telemetry(timestamp);
CREATE INDEX idx_event_level ON events(level);
```

---

## ✅ Pre-Deployment Checklist

- [ ] Change all default credentials
- [ ] Set secure SECRET_KEY
- [ ] Enable HTTPS/TLS
- [ ] Configure firewall rules
- [ ] Set up monitoring & alerting
- [ ] Configure backup & recovery
- [ ] Test failover procedures
- [ ] Load test the system
- [ ] Document runbooks
- [ ] Set up CI/CD pipeline
- [ ] Configure auto-scaling
- [ ] Enable rate limiting
- [ ] Set up authentication
- [ ] Configure logging
- [ ] Test all API endpoints
- [ ] Verify WebSocket connectivity
- [ ] Test path export functionality
- [ ] Verify OTA update flow
- [ ] Test emergency stop
- [ ] Document API for clients

---

## 🔄 CI/CD Pipeline

### GitHub Actions Example

```yaml
# .github/workflows/deploy.yml
name: Deploy S4 System

on:
  push:
    branches: [main, production]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run backend tests
        run: |
          cd backend
          pip install -r requirements.txt
          python -m pytest
      - name: Run frontend tests
        run: |
          cd frontEnd
          npm install
          npm run lint

  deploy:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/production'
    steps:
      - uses: actions/checkout@v2
      - name: Deploy to AWS
        env:
          AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
          AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
        run: |
          aws s3 sync frontEnd/dist s3://s4-prod-bucket
          # Add deployment commands
```

---

## 📞 Troubleshooting Deployments

### Backend Won't Start

```bash
# Check logs
tail -f logs/app.log

# Verify port availability
lsof -i :5001

# Check Python version
python --version

# Reinstall dependencies
pip install --upgrade -r requirements.txt
```

### WebSocket Connection Issues

```bash
# Check firewall
sudo ufw allow 5001/tcp

# Verify SocketIO is running
curl http://localhost:5001/socket.io/?EIO=4&transport=polling

# Check nginx config
sudo nginx -t
```

### High Memory Usage

```bash
# Monitor memory
watch -n 1 free -h

# Check process memory
ps aux | grep python

# Limit memory usage
ulimit -v 2097152  # 2GB limit
```

---

**For additional support or questions, refer to S4_SYSTEM_README.md**
