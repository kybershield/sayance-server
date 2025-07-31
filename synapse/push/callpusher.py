import json
import logging
import os
import uuid
from typing import Any, Dict, List, Optional, TYPE_CHECKING
import asyncio

if TYPE_CHECKING:
    from synapse.server import HomeServer

from aioapns import APNs, NotificationRequest, PushType
from firebase_admin import credentials, messaging, initialize_app
from firebase_admin.exceptions import FirebaseError

from synapse.events import EventBase
from synapse.push import Pusher, PusherConfig, PusherConfigException
from synapse.types import JsonDict

logger = logging.getLogger(__name__)

class CallPusher(Pusher):
    """Handles pushing VoIP notifications for calls using APN and FCM directly."""
    
    def __init__(self, hs: "HomeServer", pusher_config: PusherConfig):
        super().__init__(hs, pusher_config)
        
        self.app_display_name = pusher_config.app_display_name
        self.device_display_name = pusher_config.device_display_name
        self.data = pusher_config.data
        self._is_processing = False
        
        if self.data is None:
            raise PusherConfigException("'data' key can not be null for Call pusher")
            
        # Extract APN and FCM configuration from data
        self.apn_key_id = self.data.get("apn_key_id")
        self.apn_team_id = self.data.get("apn_team_id")
        self.apn_key_file = self.data.get("apn_key_file")
        self.fcm_credentials_file = self.data.get("fcm_credentials_file")
        self.fcm_project_id = self.data.get("fcm_project_id")
        self.notification_type = self.data.get("notification_type", "regular")
        self.apn_topic = 'com.kybershield.sayance'
        
        # Validate required configuration based on notification type
        if self.notification_type in ["voip_call", "regular"] and not all([self.apn_key_id, self.apn_team_id, self.apn_key_file]):
            logger.warning("APN configuration missing for Call pusher, VoIP calls may not work")
        if self.notification_type in ["fcm", "fcm_call"] and not all([self.fcm_credentials_file, self.fcm_project_id]):
            logger.warning("FCM configuration missing for Call pusher, Android notifications may not work")
            
        self.name = "%s/%s/%s" % (
            pusher_config.user_name,
            pusher_config.app_id,
            pusher_config.pushkey,
        )
        
        # Store APN configuration for async initialization (only if needed)
        self._apn_key_path = None
        if self.apn_key_file and self.notification_type in ["voip_call", "regular"]:
            self._apn_key_path = self._resolve_file_path(self.apn_key_file, [
                "/data/secrets",  # Docker mounted secrets directory
                "/data/config",    # Docker config directory
                os.getcwd(),       # Current working directory
                os.path.dirname(__file__),  # Synapse directory
            ])
            
            if self._apn_key_path and os.path.exists(self._apn_key_path):
                logger.info("Using APN key file: %s", self._apn_key_path)
            else:
                logger.warning(f"APN key file not found: {self.apn_key_file}")
        
        # Initialize APN client as None - will be initialized async
        self.apn_client = None
        
        # Store FCM configuration for async initialization (only if needed)
        self._fcm_credentials_path = None
        self.fcm_initialized = False
        if self.fcm_credentials_file and self.notification_type in ["fcm", "fcm_call"]:
            self._fcm_credentials_path = self._resolve_file_path(self.fcm_credentials_file, [
                "/data/secrets",  # Docker mounted secrets directory
                "/data/config",    # Docker config directory
                os.getcwd(),       # Current working directory
                os.path.dirname(__file__),  # Synapse directory
            ])
            
            if self._fcm_credentials_path and os.path.exists(self._fcm_credentials_path):
                logger.info("Using FCM credentials file: %s", self._fcm_credentials_path)
            else:
                logger.warning(f"FCM credentials file not found: {self.fcm_credentials_file}")
    
    async def _initialize_apn_client(self):
        """Initialize the APN client asynchronously."""
        if self.apn_client is not None or not self._apn_key_path:
            return
            
        try:
            # Read the key file from the mounted secrets directory
            with open(self._apn_key_path, 'r') as key_file:
                key = key_file.read()
            
            # Initialize APN client asynchronously
            self.apn_client = APNs(
                key=key,
                key_id=self.apn_key_id,
                team_id=self.apn_team_id,
                topic=f"{self.apn_topic}.voip", # Bundle ID for VoIP
                use_sandbox=False  # Use production APN
            )
            
            logger.info("APN client initialized successfully")
            
        except Exception as e:
            logger.error("Failed to initialize APN client: %s", e)
            raise PusherConfigException(f"APN client initialization failed: {e}")
    
    async def _initialize_fcm_client(self):
        """Initialize the FCM client asynchronously."""
        if self.fcm_initialized or not self._fcm_credentials_path:
            return
            
        try:
            # Read the FCM credentials file from the mounted secrets directory
            cred = credentials.Certificate(self._fcm_credentials_path)
            initialize_app(cred, {'projectId': self.fcm_project_id})
            self.fcm_initialized = True
            
            logger.info("FCM client initialized successfully")
            
        except Exception as e:
            logger.error("Failed to initialize FCM client: %s", e)
            raise PusherConfigException(f"FCM client initialization failed: {e}")
    
    def _resolve_file_path(self, filename: str, search_dirs: List[str]) -> Optional[str]:
        """Resolve a file path by searching in multiple directories."""
        # If it's already an absolute path and exists, use it
        if os.path.isabs(filename) and os.path.exists(filename):
            return filename
        
        # Search in the provided directories
        for search_dir in search_dirs:
            if not os.path.exists(search_dir):
                continue
                
            # Try the exact filename
            file_path = os.path.join(search_dir, filename)
            if os.path.exists(file_path):
                return file_path
            
            # Try just the basename (in case the path includes directories)
            basename = os.path.basename(filename)
            file_path = os.path.join(search_dir, basename)
            if os.path.exists(file_path):
                return file_path
        
        return None
    
    def on_started(self, have_notifs: bool) -> None:
        """Called when this pusher has been started."""
        if have_notifs:
            self._start_processing()
    
    def on_stop(self) -> None:
        """Called when this pusher is stopped."""
        self._is_processing = False
    
    def on_new_receipts(self) -> None:
        """Called when new read receipts are available."""
        # We don't need to do anything here as we handle badge counts
        # in the notification processing
        pass
    
    def _start_processing(self) -> None:
        """Start processing push notifications."""
        if self._is_processing:
            return
        self._is_processing = True
        self._process()
    
    async def _process(self) -> None:
        """Process notifications and send them via APN and FCM for calls."""
        try:
            # Initialize APN client if not already done
            await self._initialize_apn_client()
            
            # Get unprocessed push actions
            unprocessed = await self.store.get_unread_push_actions_for_user_in_range_for_http(
                self.user_id, self.last_stream_ordering, self.max_stream_ordering
            )
            
            for push_action in unprocessed:
                # Check if this is a call notification
                room_name = push_action.room_name or ""
                if "Call with " in room_name:
                    badge = await self.store.get_unread_push_actions_count_for_user(self.user_id)
                    
                    await self.send_notification(
                        badge=badge,
                        notification={
                            "body": push_action.body,
                            "sender": push_action.sender,
                            "type": push_action.event_type,
                        },
                        room_name=push_action.room_name,
                        room_id=push_action.room_id,
                        event_id=push_action.event_id,
                    )
                
                # Update last stream ordering
                self.last_stream_ordering = push_action.stream_ordering
                await self.store.update_pusher_last_stream_ordering_and_success(
                    self.app_id,
                    self.pushkey,
                    self.user_id,
                    self.last_stream_ordering,
                    self.clock.time_msec(),
                )
                
        except Exception as e:
            logger.exception("Error processing push notification: %s", e)
        finally:
            self._is_processing = False
    

    async def send_notification(
        self, 
        badge: int,
        notification: Dict[str, Any],
        room_name: Optional[str] = None,
        room_alias: Optional[str] = None,
        sender_display_name: Optional[str] = None,
        event_id: Optional[str] = None,
        room_id: Optional[str] = None,
    ) -> bool:
        """Sends push notifications based on the notification type."""
        
        logger.info("Sending %s notification to %s", self.notification_type, self.pushkey)
        
        success = False
        
        if self.notification_type == "voip_call":
            # VoIP call notification via APN for iOS
            success = await self._send_voip_apn_notification(
                badge, notification, room_name, sender_display_name, event_id, room_id
            )
        elif self.notification_type in ["fcm", "fcm_call"]:
            # FCM notification for Android
            success = await self._send_fcm_notification(
                badge, notification, room_name, sender_display_name, event_id, room_id
            )
        else:
            # Default to regular APN notification
            success = await self._send_regular_apn_notification(
                badge, notification, room_name, sender_display_name, event_id, room_id
            )
        
        return success
    
    async def _send_voip_apn_notification(
        self, badge: int, notification: Dict[str, Any], room_name: Optional[str],
        sender_display_name: Optional[str], event_id: Optional[str], room_id: Optional[str]
    ) -> bool:
        """Send VoIP notification via APN for iOS."""
        
        # Extract caller name from room name (e.g., "Call with John Doe" -> "John Doe")
        caller_name = room_name.replace("Call with ", "").strip() if room_name else sender_display_name or "Unknown"
        
        # Generate UUID for the call
        call_uuid = str(uuid.uuid4())
        
        # VoIP notification payload for iOS
        message = {
            "aps": {
                "alert": {
                    "title": "Incoming Call",
                    "body": f"{caller_name} is calling..."
                },
                "sound": "ringtone.caf",
                "badge": badge,
                "content-available": 1,
                "mutable-content": 1
            },
            "uuid": call_uuid,
            "callerName": caller_name,
            "handle": "",
            "callType": "voice",
            "roomId": room_id or ""
        }
        
        logger.debug("VoIP APN payload: %s", message)
        
        # Initialize APN client if needed
        if self.apn_client is None:
            await self._initialize_apn_client()
        
        if not self.apn_client:
            logger.error("APN client not available for VoIP notification")
            return False
        
        try:
            # Create notification request
            request = NotificationRequest(
                device_token=self.pushkey,
                message=message,
                notification_id=call_uuid,
                time_to_live=30,
                push_type=PushType.VOIP,
                priority=10,
                apns_topic=f"{self.apn_topic}.voip",
            )

            logger.info("Sending VoIP notification via APN to %s", self.pushkey)
            response = await self.apn_client.send_notification(request)
            
            if response.is_successful:
                logger.info("Successfully sent VoIP notification via APN to %s", self.pushkey)
                return True
            else:
                logger.error("Failed to send VoIP notification via APN: %s", response.description)
                return False
                
        except Exception as e:
            logger.error("Error sending VoIP notification via APN: %s", str(e))
            return False
    
    async def _send_fcm_notification(
        self, badge: int, notification: Dict[str, Any], room_name: Optional[str],
        sender_display_name: Optional[str], event_id: Optional[str], room_id: Optional[str]
    ) -> bool:
        """Send notification via FCM for Android."""
        
        # Initialize FCM client if needed
        if not self.fcm_initialized:
            await self._initialize_fcm_client()
        
        if not self.fcm_initialized:
            logger.error("FCM client not available for notification")
            return False
        
        try:
            is_call = self.notification_type == "fcm_call" or (room_name and "Call with " in room_name)
            
            if is_call:
                # Call notification for Android
                caller_name = room_name.replace("Call with ", "").strip() if room_name else sender_display_name or "Unknown"
                call_uuid = str(uuid.uuid4())
                
                fcm_message = messaging.Message(
                    notification=messaging.Notification(
                        title="Incoming Call",
                        body=f"{caller_name} is calling..."
                    ),
                    data={
                        "uuid": call_uuid,
                        "callerName": caller_name,
                        "handle": "",
                        "callType": "voice",
                        "roomId": room_id or "",
                        "type": "call"
                    },
                    android=messaging.AndroidConfig(
                        priority="high",
                        notification=messaging.AndroidNotification(
                            sound="ringtone",
                            priority="high",
                            channel_id="voip_calls"
                        )
                    ),
                    token=self.pushkey
                )
            else:
                # Regular notification for Android
                title = notification.get("title", "New message")
                body = notification.get("body", "You have a new message")
                
                fcm_message = messaging.Message(
                    notification=messaging.Notification(
                        title=title,
                        body=body
                    ),
                    data={
                        "event_id": event_id or "",
                        "room_id": room_id or "",
                        "sender": sender_display_name or "",
                        "type": "message"
                    },
                    android=messaging.AndroidConfig(
                        priority="high",
                        notification=messaging.AndroidNotification(
                            sound="default",
                            priority="high",
                            channel_id="messages"
                        )
                    ),
                    token=self.pushkey
                )
            
            response = messaging.send(fcm_message)
            logger.info("Successfully sent FCM notification: %s", response)
            return True
            
        except FirebaseError as e:
            logger.error("Firebase error sending notification: %s", str(e))
            return False
        except Exception as e:
            logger.error("Error sending FCM notification: %s", str(e))
            return False
    
    async def _send_regular_apn_notification(
        self, badge: int, notification: Dict[str, Any], room_name: Optional[str],
        sender_display_name: Optional[str], event_id: Optional[str], room_id: Optional[str]
    ) -> bool:
        """Send regular notification via APN for iOS."""
        
        # Initialize APN client if needed
        if self.apn_client is None:
            await self._initialize_apn_client()
        
        if not self.apn_client:
            logger.error("APN client not available for regular notification")
            return False
        
        try:
            title = notification.get("title", "New message")
            body = notification.get("body", "You have a new message")
            
            # Regular notification payload for iOS
            message = {
                "aps": {
                    "alert": {
                        "title": title,
                        "body": body
                    },
                    "sound": "default",
                    "badge": badge,
                    "content-available": 1
                },
                "event_id": event_id or "",
                "room_id": room_id or "",
                "sender": sender_display_name or "",
                "type": "message"
            }
            
            logger.debug("Regular APN payload: %s", message)
            
            # Create notification request
            request = NotificationRequest(
                device_token=self.pushkey,
                message=message,
                notification_id=str(uuid.uuid4()),
                time_to_live=3600,  # 1 hour for regular notifications
                push_type=PushType.ALERT,
                priority=10,
                apns_topic=self.apn_topic,
            )

            logger.info("Sending regular notification via APN to %s", self.pushkey)
            response = await self.apn_client.send_notification(request)
            
            if response.is_successful:
                logger.info("Successfully sent regular notification via APN to %s", self.pushkey)
                return True
            else:
                logger.error("Failed to send regular notification via APN: %s", response.description)
                return False
                
        except Exception as e:
            logger.error("Error sending regular notification via APN: %s", str(e))
            return False