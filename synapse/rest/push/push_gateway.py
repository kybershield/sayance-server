import logging
from http import HTTPStatus
from typing import Tuple, TYPE_CHECKING
import re
import json

if TYPE_CHECKING:
    from synapse.server import HomeServer

from synapse.http.server import HttpServer
from synapse.http.servlet import RestServlet, parse_json_object_from_request
from synapse.http.site import SynapseRequest
from synapse.push import PusherConfig
from synapse.push.expopusher import ExpoPusher
from synapse.types import JsonDict
from synapse.rest.client._base import client_patterns

logger = logging.getLogger(__name__)

class PushGatewayServlet(RestServlet):
    """Handles push gateway requests for Expo push notifications."""

    PATTERNS = [re.compile("^/_matrix/push/v1/notify$")]
    
    def __init__(self, hs: "HomeServer"):
        super().__init__()
        self.hs = hs
        # self.auth = hs.get_auth()
        self.store = hs.get_datastores().main
        
    async def on_POST(self, request: SynapseRequest) -> Tuple[int, JsonDict]:
        """Handle POST requests to the push gateway.
        
        Args:
            request: The HTTP request.
            
        Returns:
            A tuple of (response code, response object).
        """
        # requester = await self.auth.get_user_by_req(request)
        body = parse_json_object_from_request(request)

        # Log the complete request body
        logger.info("Full push notification request body: %s", json.dumps(body, indent=2))
        
        required_fields = ["notification"]
        missing_fields = [field for field in required_fields if field not in body]
        if missing_fields:
            return HTTPStatus.BAD_REQUEST, {
                "error": f"Missing required fields: {', '.join(missing_fields)}"
            }
            
        try:
            notification = body["notification"]
            rejected_pushkeys = []
            
            # Spec-compliant notification format
            devices = notification.get("devices", [])
            for device in devices:
                pushkey = device.get("pushkey")
                app_id = device.get("app_id")
                
                if not pushkey or not app_id:
                    continue

                # Create pusher config for this device
                pusher_config = PusherConfig(
                    id=None,
                    user_name="@push_gateway:localhost",
                    profile_tag="",
                    kind="expo",
                    app_id=app_id,
                    app_display_name="Sayance",
                    device_display_name="Mobile Device",
                    pushkey=pushkey,
                    ts=0,
                    lang="en",
                    data={
                        "format": "event_id_only",
                    },
                    device_id="push_gateway",
                    enabled=True,
                    last_stream_ordering=0,
                    last_success=0,
                    failing_since=None,
                    access_token=None,
                )

                # Create the pusher
                pusher = ExpoPusher(self.hs, pusher_config)

                try:

                    # Extract notification data according to spec
                    event_id = notification.get("event_id")
                    room_id = notification.get("room_id")
                    sender_display_name = notification.get("sender_display_name")
                    room_name = notification.get("sender")
                    room_alias = notification.get("sender_display_name")
                    counts = notification.get("counts", {})
                    
                    success = await pusher.send_notification(
                        badge=body.get("badge", 1),
                        notification=body["notification"],
                        room_name=room_name,
                        room_alias=room_alias,
                        sender_display_name=sender_display_name,
                        event_id=event_id,
                        room_id=room_id,
                    )

                    if not success:
                        rejected_pushkeys.append(pushkey)
                    
                except Exception as e:
                    logger.exception("Error sending push notification")
                    rejected_pushkeys.append(pushkey)

            return HTTPStatus.OK if success else HTTPStatus.INTERNAL_SERVER_ERROR, {
                "rejected": rejected_pushkeys
            }
                
        except Exception as e:
            logger.exception("Error sending push notification")
            return HTTPStatus.INTERNAL_SERVER_ERROR, {
                "error": f"Internal server error: {str(e)}"
            }

def register_servlets(hs: "HomeServer", http_server: HttpServer) -> None:
    """Register the push gateway servlets."""
    PushGatewayServlet(hs).register(http_server) 