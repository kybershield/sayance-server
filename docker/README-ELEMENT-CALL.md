# Sayance with Element Call Integration

This document describes the deployment of Sayance with integrated Element Call support, providing secure voice and video calling functionality through Matrix.

## 🏗️ Architecture Overview

The deployment includes:

- **Sayance Web** - Custom Matrix client with integrated calling
- **Synapse** - Matrix homeserver with MatrixRTC support
- **LiveKit SFU** - Selective Forwarding Unit for media routing
- **LiveKit Auth Service** - JWT authentication for call access
- **Redis** - State management for LiveKit
- **PostgreSQL** - Database for Synapse
- **Nginx** - SSL termination and reverse proxy

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose
- 8GB+ RAM recommended
- Ports 443, 8008, 8448, 7880-7882, 50100-50200 available

### Deployment

1. **Clone and navigate to the project:**
   ```bash
   cd sayance-server/docker
   ```

2. **Run the deployment script:**
   ```bash
   chmod +x deploy-sayance.sh
   ./deploy-sayance.sh
   ```

3. **Add SSL certificate to browser:**
   - Import `element-call-backend/ssl/sayance-ca.crt` to your browser's trusted certificates
   - Chrome: Settings → Privacy and security → Manage certificates → Authorities → Import
   - Firefox: Settings → Privacy & Security → Certificates → View Certificates → Authorities → Import

4. **Access Sayance:**
   - Web App: https://app.sayance.localhost
   - Matrix Server: https://sayance.localhost

## 🌐 Service URLs

| Service | URL | Description |
|---------|-----|-------------|
| Sayance Web | https://app.sayance.localhost | Main application |
| Matrix Homeserver | https://sayance.localhost | Matrix server API |
| RTC Backend | https://rtc.sayance.localhost | LiveKit authentication |

## 📞 Using Voice/Video Calls

### Starting a Call

1. Navigate to Direct Messages
2. Hover over a conversation
3. Click the voice (👤) or video (▶️) call button
4. The call interface will open automatically

### Call Features

- **Audio/Video toggle** - Control your media during calls
- **Screen sharing** - Share your screen with participants
- **Participant management** - See who's in the call
- **Call quality adaptation** - Automatic quality adjustment

### Troubleshooting Calls

- **"No MatrixRTC backend configured"** - Check `.well-known/matrix/client` endpoint
- **"Failed to get call token"** - Verify LiveKit auth service is running
- **Audio/video not working** - Check browser permissions for camera/microphone

## 🔧 Configuration

### Environment Variables

The deployment uses these key configurations:

```yaml
# Synapse
SYNAPSE_CONFIG_PATH: /data/homeserver.yaml

# LiveKit Auth Service
LIVEKIT_URL: wss://rtc.sayance.localhost/livekit/sfu
LIVEKIT_KEY: devkey
LIVEKIT_SECRET: secret

# Sayance Web
VITE_DEFAULT_HOMESERVER_URL: https://sayance.localhost
VITE_ALLOW_REGISTRATION: true
```

### MatrixRTC Configuration

The homeserver exposes MatrixRTC configuration via `.well-known/matrix/client`:

```json
{
  "m.homeserver": {
    "base_url": "https://sayance.localhost"
  },
  "org.matrix.msc4143.rtc_foci": [{
    "type": "livekit",
    "livekit_service_url": "https://rtc.sayance.localhost/livekit/jwt"
  }]
}
```

### Synapse MSC Features

The following experimental features are enabled:

- **MSC3266** - Room summary API for federation
- **MSC4222** - Syncv2 state_after for room state tracking
- **MSC4140** - Delayed events for call signaling
- **MSC4143** - MatrixRTC support

## 🛠️ Management Commands

### View Service Status
```bash
docker-compose -f docker-compose.sayance-full.yml ps
```

### View Logs
```bash
# All services
docker-compose -f docker-compose.sayance-full.yml logs -f

# Specific service
docker-compose -f docker-compose.sayance-full.yml logs -f synapse
docker-compose -f docker-compose.sayance-full.yml logs -f livekit
```

### Restart Services
```bash
# All services
docker-compose -f docker-compose.sayance-full.yml restart

# Specific service
docker-compose -f docker-compose.sayance-full.yml restart synapse
```

### Stop Services
```bash
docker-compose -f docker-compose.sayance-full.yml down
```

### Reset Everything
```bash
docker-compose -f docker-compose.sayance-full.yml down -v
docker system prune -f
./deploy-sayance.sh
```

## 🔐 Security Considerations

### Development vs Production

This setup is designed for **local development**. For production:

1. **Replace self-signed certificates** with proper SSL certificates
2. **Change default secrets** in LiveKit configuration
3. **Configure proper firewall rules**
4. **Use external database** for better performance
5. **Enable proper monitoring** and logging
6. **Configure backup strategies**

### SSL Certificates

The deployment generates self-signed certificates for development:

- **CA Certificate**: `element-call-backend/ssl/sayance-ca.crt`
- **Server Certificate**: `element-call-backend/ssl/sayance.localhost.crt`
- **Private Key**: `element-call-backend/ssl/sayance.localhost.key`

### Network Security

- All services communicate over encrypted connections
- LiveKit uses secure WebSocket connections (WSS)
- Matrix federation uses TLS
- WebRTC media is encrypted end-to-end

## 🐛 Troubleshooting

### Common Issues

**Services won't start:**
```bash
# Check Docker resources
docker system df
docker system prune

# Check port conflicts
netstat -tulpn | grep -E ':(443|8008|8448|7880)'
```

**SSL certificate errors:**
```bash
# Regenerate certificates
cd element-call-backend
rm -rf ssl/
./setup-tls.sh
```

**Database connection issues:**
```bash
# Check PostgreSQL status
docker-compose -f docker-compose.sayance-full.yml exec postgres pg_isready
```

**LiveKit connection fails:**
```bash
# Check LiveKit logs
docker-compose -f docker-compose.sayance-full.yml logs livekit
docker-compose -f docker-compose.sayance-full.yml logs auth-service
```

### Performance Optimization

For better performance:

1. **Increase Docker resources** (CPU/Memory)
2. **Use SSD storage** for database volumes
3. **Configure Redis persistence** for call state
4. **Tune PostgreSQL** connection limits
5. **Monitor resource usage** with `docker stats`

## 📚 Additional Resources

- [Element Call Documentation](https://github.com/element-hq/element-call)
- [LiveKit Documentation](https://docs.livekit.io/)
- [Synapse Administration Guide](https://element-hq.github.io/synapse/latest/)
- [Matrix.org Developer Docs](https://matrix.org/docs/develop/)

## 🤝 Contributing

To contribute to the Sayance Element Call integration:

1. Fork the repository
2. Create a feature branch
3. Test your changes with the deployment
4. Submit a pull request

## 📄 License

This integration follows the same licensing as the individual components:
- Sayance: AGPL-3.0
- Element Call: AGPL-3.0
- Synapse: Apache License 2.0 