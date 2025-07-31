# VoIP Push Notifications Setup for Docker

This guide explains how to set up VoIP push notifications for calls using APN (Apple Push Notification service) and FCM (Firebase Cloud Messaging) in a Docker environment.

## Overview

The `CallPusher` handles VoIP push notifications for calls by:
1. Detecting when a room name contains "Call with "
2. Sending VoIP notifications via APN for iOS devices
3. Sending VoIP notifications via FCM for Android devices
4. Accessing secrets from the mounted `/data/secrets` directory in Docker

## Prerequisites

### For APN (iOS)
1. Apple Developer Account
2. APNs Authentication Key (`.p8` file)
3. Team ID from Apple Developer Account
4. Key ID from the APNs Authentication Key

### For FCM (Android)
1. Firebase Project
2. Firebase Admin SDK credentials JSON file
3. Firebase Project ID

## Docker Setup

### 1. Secrets Directory Structure

Your secrets should be organized as follows:

```
secrets/
├── AuthKey_5JMA4TNN47.p8    # APN authentication key
└── google-services.json      # Firebase credentials
```

### 2. Docker Compose Configuration

The Docker Compose file already mounts the secrets directory:

```yaml
version: '3'

services:
  synapse:
    build:
      context: ..
      dockerfile: docker/Dockerfile
    restart: always
    volumes:
      - synapse-data:/data
      - ../homeserver.yaml:/data/homeserver.yaml:ro
      - ../config:/data/config
      - ../config:/config
      - synapse-keys:/data/keys
      # Mount secrets directory - this is crucial!
      - ../secrets:/data/secrets:ro
    ports:
      - "8008:8008"
    environment:
      - SYNAPSE_CONFIG_PATH=/data/homeserver.yaml
    working_dir: /data
    entrypoint: /bin/sh
    command: -c "mkdir -p /data/keys && ln -sf /data/keys/sayance.signing.key /data/sayance.signing.key && python -m synapse.app.homeserver --config-path /data/homeserver.yaml"
```

### 3. File Path Resolution

The `CallPusher` now uses a robust file path resolution system that searches in this order:

1. `/data/secrets/` (Docker mounted secrets directory)
2. `/data/config/` (Docker config directory)
3. Current working directory
4. Synapse directory

## Configuration

### 1. APN Setup

1. **Get APNs Authentication Key**:
   - Go to [Apple Developer Portal](https://developer.apple.com/account/)
   - Navigate to "Certificates, Identifiers & Profiles"
   - Go to "Keys" section
   - Create a new key with "Apple Push Notifications service (APNs)" enabled
   - Download the `.p8` file and note the Key ID

2. **Get Team ID**:
   - In the same Apple Developer Portal
   - Your Team ID is displayed in the top right corner

3. **Place APN Key in Docker**:
   ```bash
   # Copy your APN key to the secrets directory
   cp AuthKey_5JMA4TNN47.p8 secrets/
   ```

### 2. FCM Setup

1. **Create Firebase Project**:
   - Go to [Firebase Console](https://console.firebase.google.com/)
   - Create a new project or use existing one
   - Note the Project ID

2. **Generate Service Account Key**:
   - In Firebase Console, go to Project Settings
   - Go to "Service accounts" tab
   - Click "Generate new private key"
   - Download the JSON file

3. **Place FCM Credentials in Docker**:
   ```bash
   # Copy your Firebase credentials to the secrets directory
   cp google-services.json secrets/
   ```

### 3. Homeserver Configuration

Add the following to your `homeserver.yaml`:

```yaml
# VoIP Push Notification Configuration
voip_push:
  # APN Configuration (for iOS)
  apn:
    key_id: "5JMA4TNN47"  # Your actual Key ID
    team_id: "YOUR_TEAM_ID"  # Your actual Team ID
    key_file: "/data/secrets/AuthKey_5JMA4TNN47.p8"
    
  # FCM Configuration (for Android)
  fcm:
    credentials_file: "/data/secrets/google-services.json"
    project_id: "YOUR_FIREBASE_PROJECT_ID"  # Your actual Project ID
```

## Usage

### Creating a Call Pusher

When creating a pusher for calls via the API, use the `"call"` kind:

```python
pusher_config = PusherConfig(
    id=None,
    user_name="@user:example.com",
    profile_tag="",
    kind="call",  # Use "call" for VoIP notifications
    app_id="com.example.app",
    app_display_name="My App",
    device_display_name="iPhone",
    pushkey="device_token_here",
    ts=0,
    lang="en",
    data={
        "apn_key_id": "5JMA4TNN47",
        "apn_team_id": "YOUR_TEAM_ID", 
        "apn_key_file": "/data/secrets/AuthKey_5JMA4TNN47.p8",
        "fcm_credentials_file": "/data/secrets/google-services.json",
        "fcm_project_id": "YOUR_FIREBASE_PROJECT_ID",
    },
    device_id="device_id",
    enabled=True,
    last_stream_ordering=0,
    last_success=0,
    failing_since=None,
    access_token=None,
)
```

### Testing the Setup

1. **Run the test script**:
   ```bash
   # From inside the Docker container
   python scripts-dev/test_call_pusher_docker.py
   ```

2. **Check logs**:
   ```bash
   # View Synapse logs
   docker logs synapse-container-name
   ```

3. **Verify file access**:
   ```bash
   # Check if secrets are accessible
   docker exec synapse-container-name ls -la /data/secrets/
   ```

## Troubleshooting

### Common Issues

1. **File not found errors**:
   - Ensure secrets are in the correct location: `/data/secrets/`
   - Check file permissions (should be readable by the Synapse process)
   - Verify the Docker volume mount is working

2. **APN authentication failures**:
   - Verify the Key ID matches the filename
   - Ensure the Team ID is correct
   - Check that the `.p8` file is valid and not corrupted

3. **FCM authentication failures**:
   - Verify the Firebase Project ID is correct
   - Ensure the service account has the necessary permissions
   - Check that the JSON file is valid

### Debugging Steps

1. **Check file existence**:
   ```bash
   docker exec synapse-container-name ls -la /data/secrets/
   ```

2. **Test file readability**:
   ```bash
   docker exec synapse-container-name cat /data/secrets/AuthKey_5JMA4TNN47.p8
   ```

3. **Check Synapse logs**:
   ```bash
   docker logs synapse-container-name | grep -i "call\|apn\|fcm"
   ```

4. **Verify configuration**:
   ```bash
   docker exec synapse-container-name python -c "
   import os
   print('Secrets dir exists:', os.path.exists('/data/secrets'))
   print('APN key exists:', os.path.exists('/data/secrets/AuthKey_5JMA4TNN47.p8'))
   print('FCM creds exist:', os.path.exists('/data/secrets/google-services.json'))
   "
   ```

## Security Considerations

1. **File Permissions**: Ensure secret files have appropriate permissions (readable by Synapse, not world-readable)

2. **Docker Security**: The secrets volume is mounted as read-only (`:ro`) for security

3. **Network Security**: Ensure secure communication with APN and FCM servers

4. **Token Validation**: Validate device tokens before sending notifications

## Example Notification Payload

For calls, the notification includes:

```json
{
  "aps": {
    "alert": {
      "title": "Incoming call from John Doe",
      "body": "Tap to answer"
    },
    "badge": 1,
    "sound": "ringtone.caf",
    "content-available": 1,
    "mutable-content": 1
  },
  "event_id": "event_id",
  "room_id": "room_id", 
  "sender": "sender_user_id",
  "type": "voip_call",
  "caller_name": "John Doe"
}
```

## Next Steps

1. Configure your mobile app to register for push notifications
2. Set up the push gateway to handle call notifications
3. Test with real device tokens
4. Monitor logs for successful notifications 