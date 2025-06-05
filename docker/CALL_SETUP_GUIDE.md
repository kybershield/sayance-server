# Sayance Call Infrastructure Setup Guide

This guide covers the Docker configuration for voice and video calling in the Sayance platform.

## 📋 Current Infrastructure

Your existing `docker-compose.sayance-full.yml` already includes all necessary services for calling:

### Core Services

1. **Synapse (Matrix Homeserver)**
   - Handles Matrix messaging and signaling
   - Supports MatrixRTC for group calls
   - Configured with proper federation

2. **LiveKit SFU Server**
   - WebRTC selective forwarding unit
   - Handles multi-participant video/audio routing
   - Configured for development with ports 7880-7882

3. **LiveKit JWT Auth Service**
   - Provides authentication tokens for LiveKit
   - Handles user authorization for calls
   - Configured with development keys

4. **Redis**
   - Backend storage for LiveKit
   - Handles session management

5. **Nginx**
   - Reverse proxy with SSL termination
   - Routes traffic to appropriate services
   - Configured for `sayance.localhost`

## ✅ Configuration Status

Your Docker setup is **already configured** for calling! No additional changes needed.

### Verified Configurations

- ✅ LiveKit server with UDP ports for WebRTC
- ✅ JWT authentication service
- ✅ Redis backend for LiveKit
- ✅ Nginx routing for call services
- ✅ SSL certificates for secure WebRTC
- ✅ Synapse with MatrixRTC support

### Service Endpoints

When running, the following endpoints are available:

- **Sayance Web**: `https://sayance.localhost`
- **Matrix Homeserver**: `https://sayance.localhost` (proxied)
- **LiveKit SFU**: `wss://rtc.sayance.localhost/livekit/sfu`
- **Auth Service**: Internal (port 6080)
- **Federation**: `https://sayance.localhost:8448`

## 🚀 Starting the Infrastructure

1. **Navigate to docker directory**:
   ```bash
   cd sayance-server/docker
   ```

2. **Start all services**:
   ```bash
   ./deploy-sayance.sh
   ```

3. **Verify services are running**:
   ```bash
   docker-compose -f docker-compose.sayance-full.yml ps
   ```

4. **Check service health**:
   ```bash
   # Check Synapse
   curl -k https://sayance.localhost/_matrix/client/versions
   
   # Check LiveKit (should return connection upgrade)
   curl -k https://rtc.sayance.localhost/livekit/sfu
   ```

## 🔧 Environment Variables

The following environment variables are configured for calling:

### LiveKit Configuration
```yaml
LIVEKIT_URL: wss://rtc.sayance.localhost/livekit/sfu
LIVEKIT_KEY: devkey
LIVEKIT_SECRET: secret
LIVEKIT_INSECURE_SKIP_VERIFY_TLS: YES_I_KNOW_WHAT_I_AM_DOING
```

### Auth Service Configuration
```yaml
LIVEKIT_JWT_PORT: 6080
```

## 🛠️ Troubleshooting

### Common Issues

1. **Calls not connecting**:
   ```bash
   # Check LiveKit logs
   docker-compose -f docker-compose.sayance-full.yml logs livekit
   
   # Check auth service logs
   docker-compose -f docker-compose.sayance-full.yml logs auth-service
   ```

2. **WebRTC connection failures**:
   - Verify UDP ports 50100-50200 are accessible
   - Check firewall settings
   - Ensure SSL certificates are valid

3. **Authentication errors**:
   - Verify JWT service is running
   - Check Synapse logs for MatrixRTC events
   - Ensure user has proper room permissions

### Log Commands

```bash
# View all service logs
docker-compose -f docker-compose.sayance-full.yml logs -f

# View specific service logs
docker-compose -f docker-compose.sayance-full.yml logs livekit
docker-compose -f docker-compose.sayance-full.yml logs auth-service
docker-compose -f docker-compose.sayance-full.yml logs synapse
```

### Port Configuration

The following ports are configured:

| Service | Ports | Purpose |
|---------|--------|---------|
| Nginx | 443, 8008, 8448 | HTTPS, HTTP, Federation |
| LiveKit | 7880-7882 | WebRTC signaling |
| LiveKit | 50100-50200/UDP | WebRTC media |
| Postgres | 5432 | Database (internal) |
| Redis | 6379 | Cache (internal) |

## 🔒 Security Considerations

### Development vs Production

**Current Setup (Development)**:
- Uses self-signed certificates
- Simplified authentication
- All services on single host

**For Production**:
- Use proper SSL certificates
- Implement proper security keys
- Separate services across hosts
- Enable firewalls and proper access controls

### SSL Certificates

The current setup uses self-signed certificates from `./element-call-backend/ssl/`. For production:

1. Replace with proper certificates
2. Update nginx configuration
3. Ensure certificate chain is complete

## 📊 Monitoring

### Health Checks

All services include health checks:

```bash
# Check service health
docker-compose -f docker-compose.sayance-full.yml ps

# Services should show "healthy" status
```

### Performance Monitoring

```bash
# Monitor resource usage
docker stats

# Check network connectivity
docker-compose -f docker-compose.sayance-full.yml exec livekit ping auth-service
```

## 🔄 Updates and Maintenance

### Updating Services

```bash
# Pull latest images
docker-compose -f docker-compose.sayance-full.yml pull

# Restart services
./deploy-sayance.sh
```

### Backup Important Data

```bash
# Backup Synapse data
docker run --rm -v sayance-docker_synapse-data:/data alpine tar czf /backup/synapse-data.tar.gz -C /data .

# Backup Postgres data
docker run --rm -v sayance-docker_postgres-data:/data alpine tar czf /backup/postgres-data.tar.gz -C /data .
```

## 📝 Configuration Files

### Key Configuration Files

- `docker-compose.sayance-full.yml` - Main service orchestration
- `element-call-backend/nginx.conf` - Reverse proxy configuration
- `element-call-backend/livekit.yaml` - LiveKit server configuration
- `element-call-backend/redis.conf` - Redis configuration

### Making Changes

1. Edit configuration files
2. Restart affected services:
   ```bash
   docker-compose -f docker-compose.sayance-full.yml restart <service-name>
   ```

## 🎯 Next Steps

Your Docker infrastructure is ready for calling! The next steps are:

1. **Test the web application** with call buttons
2. **Verify call functionality** between users
3. **Monitor logs** for any issues
4. **Optimize performance** based on usage patterns

## 📞 Testing Calls

1. **Start the infrastructure**: `./deploy-sayance.sh`
2. **Open browser**: Navigate to `https://sayance.localhost`
3. **Create/join room**: Use the web interface
4. **Test calls**: Use the call buttons in room headers
5. **Monitor logs**: Check for any errors in Docker logs

Your calling infrastructure is now ready to use! 