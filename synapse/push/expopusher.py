import json
import logging
from typing import Any, Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from synapse.server import HomeServer

from exponent_server_sdk import (
    DeviceNotRegisteredError,
    PushClient,
    PushMessage,
    PushServerError,
)

from synapse.events import EventBase
from synapse.push import Pusher, PusherConfig, PusherConfigException
from synapse.types import JsonDict

logger = logging.getLogger(__name__)

class ExpoPusher(Pusher):
    """Handles pushing notifications to Expo Push Notification Service."""
    
    def __init__(self, hs: "HomeServer", pusher_config: PusherConfig):
        super().__init__(hs, pusher_config)
        
        self.app_display_name = pusher_config.app_display_name
        self.device_display_name = pusher_config.device_display_name
        self.data = pusher_config.data
        self._is_processing = False
        
        if self.data is None:
            raise PusherConfigException("'data' key can not be null for Expo pusher")
            
        self.name = "%s/%s/%s" % (
            pusher_config.user_name,
            pusher_config.app_id,
            pusher_config.pushkey,
        )
    
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
        """Process notifications and send them via Expo push service."""
        try:
            # Get unprocessed push actions
            unprocessed = await self.store.get_unread_push_actions_for_user_in_range_for_http(
                self.user_id, self.last_stream_ordering, self.max_stream_ordering
            )
            
            for push_action in unprocessed:
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
        """Sends a push notification to the Expo Push Notification Service."""
        
        event_type = notification.get("type", "")  
        membership = notification.get("membership")
        sender = sender_display_name or notification.get("sender", "")
        room_display = room_name or room_alias or "a room"

        if event_type == "m.room.member" and membership == "invite":
            body = f"{sender} invited you to join {room_display}"
        elif event_type == "m.room.encrypted":
            body = f"New message from {sender}"
        else:
            body = "New activity"

        try:
            message = {
                "to": self.pushkey,
                "title": room_name or room_alias or "New message",
                "body": body,
                "data": {
                    "event_id": event_id,
                    "room_id": room_id,
                    "sender": notification.get("sender", ""),
                    "type": notification.get("type", ""),
                },
                "badge": badge,
                "sound": "default",
            }
            
            # Send the notification using Expo's SDK
            push_message = PushMessage(**message)
            response = PushClient().publish(push_message)
            
            # Check for errors
            if hasattr(response, 'status') and response.status == "error":
                logger.error("Failed to send push notification: %s", getattr(response, 'message', 'Unknown error'))
                return False
                
            logger.info("Successfully sent push notification to %s", self.pushkey)
            return True

            
        except DeviceNotRegisteredError:
            logger.warning(
                "Device not registered for user %s with pushkey %s",
                self.user_id,
                self.pushkey,
            )
            return False
        except PushServerError as e:
            logger.error("Failed to send push notification: %s", str(e))
            return False
        except Exception as e:
            logger.error("Unexpected error sending push notification: %s", str(e))
            return False 