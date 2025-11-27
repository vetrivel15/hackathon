# 🚀 Deployment Guide

## Production Build

### 1. Build Optimized Bundle
```bash
npm run build
```

Output:
```
dist/index.html                   0.46 kB │ gzip:   0.29 kB
dist/assets/index-Dhs_Qs8q.css   36.76 kB │ gzip:  10.53 kB
dist/assets/index-Cgp8dB9H.js   381.87 kB │ gzip: 115.60 kB
✓ built in 1.02s
```

### 2. Local Testing of Production Build
```bash
npm run preview
```
Opens production build at `http://localhost:4173`

## Deployment Options

### Option 1: Vercel (Recommended)
```bash
npm install -g vercel
vercel
```
- Automatic builds on git push
- No backend needed (static files only)
- Free tier available

### Option 2: GitHub Pages
```bash
# Update vite.config.js base
# base: '/repo-name/'

npm run build
# Push dist/ to gh-pages branch
```

### Option 3: Traditional Web Server (Nginx/Apache)

**Nginx Configuration:**
```nginx
server {
    listen 80;
    server_name your-robot-dashboard.com;

    root /var/www/humanoid-dashboard/dist;
    index index.html;

    # SPA routing
    location / {
        try_files $uri $uri/ /index.html;
    }

    # Cache busting for assets
    location ~* \.(js|css|png|jpg|jpeg|gif|svg|woff|woff2|ttf|eot)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

**Apache Configuration:**
```apache
<Directory /var/www/humanoid-dashboard/dist>
    <IfModule mod_rewrite.c>
        RewriteEngine On
        RewriteBase /
        RewriteRule ^index\.html$ - [L]
        RewriteCond %{REQUEST_FILENAME} !-f
        RewriteCond %{REQUEST_FILENAME} !-d
        RewriteRule . /index.html [L]
    </IfModule>
</Directory>
```

### Option 4: Docker

**Dockerfile:**
```dockerfile
FROM node:18-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

**Build and Run:**
```bash
docker build -t humanoid-dashboard .
docker run -p 80:80 humanoid-dashboard
```

## Environment Configuration

### Development
```javascript
// src/services/websocketService.js
const WS_URL = process.env.VITE_WS_URL || 'ws://localhost:8080';
```

### Production
Update `vite.config.js`:
```javascript
define: {
  'import.meta.env.VITE_WS_URL': JSON.stringify(
    process.env.VITE_WS_URL || 'wss://api.robot-system.com/ws'
  )
}
```

Create `.env.production`:
```
VITE_WS_URL=wss://your-robot-backend.com/ws
```

### Using Environment Variables
```bash
# Development
VITE_WS_URL=ws://localhost:8080 npm run dev

# Production build
VITE_WS_URL=wss://api.robot-system.com/ws npm run build
```

## SSL/TLS Configuration

### For Secure WebSocket (WSS)

1. **Get SSL Certificate** (Let's Encrypt)
```bash
sudo certbot certonly --standalone -d your-robot-dashboard.com
```

2. **Update Nginx**
```nginx
server {
    listen 443 ssl http2;
    server_name your-robot-dashboard.com;

    ssl_certificate /etc/letsencrypt/live/your-robot-dashboard.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-robot-dashboard.com/privkey.pem;

    # ... rest of config
}
```

3. **Update Frontend URL**
```javascript
const WS_URL = 'wss://your-robot-dashboard.com/ws';
```

## Performance Optimization

### 1. Enable GZIP Compression
**Nginx:**
```nginx
gzip on;
gzip_types text/plain text/css application/json application/javascript;
gzip_min_length 1000;
```

### 2. Add Cache Headers
Already configured in Nginx/Apache examples above

### 3. CDN Integration (Cloudflare)
- Free tier includes:
  - DDoS protection
  - Global CDN
  - SSL/TLS
  - Caching

## Monitoring & Logging

### Browser Performance
```javascript
// Add to Dashboard.jsx
useEffect(() => {
  const observer = new PerformanceObserver((list) => {
    for (const entry of list.getEntries()) {
      console.log(`${entry.name}: ${entry.duration}ms`);
    }
  });
  observer.observe({ entryTypes: ['measure', 'navigation'] });
}, []);
```

### Server-Side Logging
Implement logging on your robot backend WebSocket server:
```javascript
// server.js
const fs = require('fs');
const logger = (msg) => {
  fs.appendFileSync('robot-dashboard.log', 
    `[${new Date().toISOString()}] ${msg}\n`);
};
```

### Error Tracking (Optional)
Add Sentry integration:
```bash
npm install @sentry/react
```

```javascript
// src/main.jsx
import * as Sentry from "@sentry/react";

Sentry.init({
  dsn: "your-sentry-dsn",
  environment: "production"
});
```

## Scaling Considerations

### Single Backend Server
```
Client (Dashboard) → WebSocket → Single Robot Backend
```

### Multiple Robots
```
Client Dashboard
  ├→ Robot-1 Backend (ws://robot1.local:8080)
  ├→ Robot-2 Backend (ws://robot2.local:8080)
  └→ Robot-N Backend (ws://robotN.local:8080)
```

**Implementation:**
```javascript
// src/services/websocketService.js
constructor(robotId = 'default', url = null) {
  this.robotId = robotId;
  this.url = url || `ws://robot-${robotId}.local:8080`;
}

// Usage in Dashboard
const robot1WS = new WebSocketService('robot-1', 'ws://robot1.local:8080');
const robot2WS = new WebSocketService('robot-2', 'ws://robot2.local:8080');
```

### Load Balancer (for many concurrent connections)
```
Clients → Nginx Load Balancer → Robot Backend Cluster
         (port 80/443)
```

## Backup & Recovery

### Backup Logs
```bash
# Daily backup
0 2 * * * tar -czf /backup/logs-$(date +\%Y\%m\%d).tar.gz /var/log/robot-dashboard/
```

### Configuration Backup
```bash
# Version control for configs
git add vite.config.js .env.production nginx.conf
git commit -m "Production configuration"
```

## Troubleshooting Production Issues

### WebSocket Won't Connect
1. Check firewall rules for port 8080/443
2. Verify DNS resolution: `nslookup your-robot-backend.com`
3. Test WebSocket: `wscat -c wss://your-robot-backend.com/ws`
4. Check CORS headers if applicable

### High CPU Usage
1. Reduce update frequency in mock server (increase interval from 150ms)
2. Enable browser devtools to check for memory leaks
3. Monitor with: `htop` or `docker stats`

### Network Issues
1. Add connection retry logging
2. Implement exponential backoff (ready in websocketService.js)
3. Add network status monitoring

## Post-Deployment Checklist

- [ ] Build passes without errors
- [ ] Production build is minified and optimized
- [ ] SSL/TLS certificate is valid
- [ ] WebSocket URL points to correct backend
- [ ] CORS headers configured (if needed)
- [ ] Cache headers set correctly
- [ ] Logging is enabled
- [ ] Error tracking is configured
- [ ] Monitoring dashboards set up
- [ ] Backup strategy documented
- [ ] Team trained on dashboard
- [ ] User documentation updated

## Rollback Plan

If issues occur in production:

```bash
# Keep previous build as backup
cp -r dist dist-backup-$(date +%Y%m%d-%H%M%S)

# Revert to previous version
git revert HEAD
npm run build

# Re-deploy
# ... (copy dist/ to server)
```

## Support & Documentation

1. **User Guide**: `/docs/USER_GUIDE.md`
2. **API Reference**: WebSocket protocol in `README.md`
3. **Troubleshooting**: `README.md` Troubleshooting section
4. **Technical Docs**: This file

---

For questions or issues with deployment, refer to:
- Vite Documentation: https://vitejs.dev/guide/
- React Documentation: https://react.dev/
- Leaflet Documentation: https://leafletjs.com/
