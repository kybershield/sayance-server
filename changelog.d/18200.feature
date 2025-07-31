Add support for VoIP push notifications for calls using APN and FCM directly.

A new `CallPusher` has been added that handles VoIP push notifications for calls by:
- Detecting when a room name contains "Call with "
- Sending VoIP notifications via APN for iOS devices
- Sending VoIP notifications via FCM for Android devices
- Using ringtone sounds and call-specific notification formats

The push gateway automatically detects call notifications and uses the appropriate pusher type.
Users need to configure APN and FCM credentials as documented in `docs/voip_push_notifications.md`. 