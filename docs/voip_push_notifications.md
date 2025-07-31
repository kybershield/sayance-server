# VoIP Push Notifications Setup

This document explains how to set up VoIP push notifications for calls using APN (Apple Push Notification service) and FCM (Firebase Cloud Messaging).

## Overview

The `CallPusher` handles VoIP push notifications for calls by:
1. Detecting when a room name contains "Call with "
2. Sending VoIP notifications via APN for iOS devices
3. Sending VoIP notifications via FCM for Android devices

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

3. **Configure APN settings**:
   ```yaml
   # In your homeserver.yaml or pusher configuration
   apn_key_id: "YOUR_KEY_ID"
   apn_team_id: "YOUR_TEAM_ID"
   apn_key_file: "/path/to/APNsAuthKey_KEYID.p8"
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

3. **Configure FCM settings**:
   ```yaml
   # In your homeserver.yaml or pusher configuration
   fcm_credentials_file: "/path/to/firebase-credentials.json"
   fcm_project_id: "YOUR_FIREBASE_PROJECT_ID"
   ```

## Usage

### Creating a Call Pusher

When creating a pusher for calls, use the `"call"` kind and include the required configuration:

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
        "apn_key_id": "YOUR_APN_KEY_ID",
        "apn_team_id": "YOUR_APN_TEAM_ID", 
        "apn_key_file": "/path/to/APNsAuthKey_KEYID.p8",
        "fcm_credentials_file": "/path/to/firebase-credentials.json",
        "fcm_project_id": "YOUR_FCM_PROJECT_ID",
    },
    device_id="device_id",
    enabled=True,
    last_stream_ordering=0,
    last_success=0,
    failing_since=None,
    access_token=None,
)
```

### Push Gateway Integration

The push gateway automatically detects call notifications by checking if the room name contains "Call with ". For call notifications, it will:

1. Use the `CallPusher` instead of `ExpoPusher`
2. Send VoIP-specific notifications with ringtone sounds
3. Include call-specific metadata in the notification payload

### Notification Format

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

## Security Considerations

1. **APN Key Security**: Store the `.p8` file securely and restrict access
2. **FCM Credentials**: Keep the Firebase service account JSON file secure
3. **Network Security**: Ensure secure communication with APN and FCM servers
4. **Token Validation**: Validate device tokens before sending notifications

## Troubleshooting

### Common Issues

1. **APN Authentication Failed**:
   - Verify the Key ID and Team ID are correct
   - Ensure the `.p8` file path is accessible
   - Check that the key has APNs enabled

2. **FCM Authentication Failed**:
   - Verify the Firebase project ID
   - Ensure the credentials JSON file is valid
   - Check that the service account has proper permissions

3. **Notifications Not Received**:
   - Verify device tokens are valid
   - Check network connectivity to APN/FCM
   - Ensure app has proper push notification permissions

### Logs

The `CallPusher` logs detailed information about:
- APN client initialization
- FCM client initialization  
- Notification sending attempts
- Success/failure responses
- Error details

Check the Synapse logs for troubleshooting information.

## Dependencies

The following Python packages are required:
- `apns2 >= 0.7.0` - For APN notifications
- `firebase-admin >= 6.0.0` - For FCM notifications

These are automatically installed when using the `call` pusher type. 