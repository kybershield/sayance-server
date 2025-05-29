# Element Call Setup for Sayance Homeserver

This guide will help you set up voice and video calling functionality for your Sayance homeserver using Element Call with LiveKit backend.

## Prerequisites

1. **Domain Configuration**: You need the following subdomains configured:
   - `matrix.sayance.io` - Your Matrix homeserver
   - `matrixrtc.sayance.io` - Your Element Call backend
   - `sayance.io` - Your main domain for well-known files

2. **Port Forwarding**: Ensure the following ports are open in your firewall/router:
   - `7881/tcp` - LiveKit signaling
   - `50100-50200/udp` - LiveKit media ports

3. **Reverse Proxy**: You'll need a reverse proxy (Nginx, Apache, Traefik, etc.) configured for SSL termination and routing.

## Setup Steps

### 1. Start the Services

Start your existing Synapse and PostgreSQL services:
```bash
cd /Users/victorwhyte/dev/orgs/kybershield/sayance/sayance-server/docker
docker-compose -f docker-compose.local.yml up -d
```

Start the Element Call services:
```bash
docker-compose -f docker-compose.element-call.yml up -d
```

### 2. Configure Reverse Proxy

#### For Nginx:
Add this to your Nginx configuration:

```nginx
# Matrix homeserver
server {
    listen 443 ssl http2;
    server_name matrix.sayance.io;

    # SSL configuration here...

    location / {
        proxy_pass http://localhost:8008;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

# Element Call backend
server {
    listen 443 ssl http2;
    server_name matrixrtc.sayance.io;

    # SSL configuration here...

    location ^~ /livekit/jwt/ {
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # JWT Service running at port 8070
        proxy_pass http://localhost:8070/;
    }

    location ^~ /livekit/sfu/ {
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        proxy_send_timeout 120;
        proxy_read_timeout 120;
        proxy_buffering off;

        proxy_set_header Accept-Encoding gzip;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";

        # LiveKit SFU websocket connection running at port 7880
        proxy_pass http://localhost:7880/;
    }

    # Default route to JWT service
    location / {
        proxy_pass http://localhost:8070;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

#### For Apache:
Add this to your Apache VirtualHost configuration:

```apache
# Matrix homeserver
<VirtualHost *:443>
    ServerName matrix.sayance.io
    
    # SSL configuration here...
    
    ProxyPreserveHost On
    ProxyPass / http://localhost:8008/
    ProxyPassReverse / http://localhost:8008/
</VirtualHost>

# Element Call backend
<VirtualHost *:443>
    ServerName matrixrtc.sayance.io
    
    # SSL configuration here...
    
    ProxyPreserveHost On
    
    # JWT Service
    ProxyPass /livekit/jwt/ http://localhost:8070/
    ProxyPassReverse /livekit/jwt/ http://localhost:8070/
    
    # LiveKit SFU
    ProxyPass /livekit/sfu/ ws://localhost:7880/
    ProxyPassReverse /livekit/sfu/ ws://localhost:7880/
    
    # Default to JWT service
    ProxyPass / http://localhost:8070/
    ProxyPassReverse / http://localhost:8070/
</VirtualHost>
```

### 3. Configure Well-Known File

Copy the well-known file to your web server's document root:

```bash
# For Nginx/Apache (adjust path as needed)
sudo mkdir -p /var/www/html/.well-known/matrix/
sudo cp well-known-matrix-client.json /var/www/html/.well-known/matrix/client
```

Ensure your web server serves this file with the correct headers:

#### For Nginx:
```nginx
server {
    listen 443 ssl http2;
    server_name sayance.io;

    # SSL configuration here...

    location /.well-known/matrix/client {
        add_header Access-Control-Allow-Origin *;
        add_header Content-Type application/json;
        try_files $uri =404;
    }
}
```

#### For Apache:
```apache
<Location "/.well-known/matrix/client">
    Header set Access-Control-Allow-Origin "*"
    Header set Content-Type "application/json"
</Location>
```

### 4. Test the Setup

1. **Check services are running**:
   ```bash
   docker ps | grep sayance
   ```

2. **Test well-known file**:
   ```bash
   curl -s https://sayance.io/.well-known/matrix/client | jq
   ```

3. **Test Matrix homeserver**:
   ```bash
   curl -s https://matrix.sayance.io/_matrix/client/versions
   ```

4. **Test Element Call backend**:
   ```bash
   curl -s https://matrixrtc.sayance.io/livekit/jwt/health
   ```

### 5. Test Video Calls

1. Open a Matrix client (Element, ElementX, etc.)
2. Log in to your Sayance homeserver
3. Start a voice or video call in a room or direct message
4. The call should now use your self-hosted Element Call backend

## Troubleshooting

### Check Logs
```bash
# Synapse logs
docker logs sayance-synapse-1

# Element Call JWT service logs
docker logs sayance-element-call-jwt

# LiveKit logs
docker logs sayance-element-call-livekit
```

### Common Issues

1. **Calls don't connect**: Check firewall/port forwarding for UDP ports 50100-50200
2. **Authentication errors**: Verify LIVEKIT_SECRET matches in both services
3. **Well-known file not accessible**: Check CORS headers and MIME type
4. **SSL certificate issues**: Ensure valid certificates for all subdomains

## Security Notes

1. **Change the default secrets**: Update `LIVEKIT_SECRET` in both docker-compose files
2. **Limit access**: The `LIVEKIT_LOCAL_HOMESERVERS` setting restricts call creation to your homeserver
3. **Firewall**: Only open necessary ports (7881/tcp and 50100-50200/udp)
4. **SSL**: Use valid SSL certificates for all endpoints

## Customization

You can customize the LiveKit configuration in `element-call-config.yaml`:
- Adjust participant limits
- Modify audio/video quality settings
- Configure recording options
- Set up webhooks for call events 