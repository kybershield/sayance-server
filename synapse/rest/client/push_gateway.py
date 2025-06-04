import logging
from http import HTTPStatus
from typing import Tuple, TYPE_CHECKING
import re

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

    # PATTERNS = [re.compile("^/_matrix/push/v1/notify$")]
    
    PATTERNS = client_patterns("/push/notify$")  # This will create /_matrix/client/v3/push/notify
    
    def __init__(self, hs: "HomeServer"):
        super().__init__()
        self.hs = hs
        self.auth = hs.get_auth()
        self.store = hs.get_datastores().main
        
    async def on_POST(self, request: SynapseRequest) -> Tuple[int, JsonDict]:
        """Handle POST requests to the push gateway.
        
        Args:
            request: The HTTP request.
            
        Returns:
            A tuple of (response code, response object).
        """
        requester = await self.auth.get_user_by_req(request)
        body = parse_json_object_from_request(request)
        
        required_fields = ["pushkey", "app_id", "notification"]
        missing_fields = [field for field in required_fields if field not in body]
        if missing_fields:
            return HTTPStatus.BAD_REQUEST, {
                "error": f"Missing required fields: {', '.join(missing_fields)}"
            }
            
        try:
            pusher_config = PusherConfig(
                id=None,  # Will be generated
                user_name=requester.user.to_string(),
                profile_tag="",  # We don't use profile tags for Expo
                kind="expo",
                app_id=body["app_id"],
                app_display_name=body.get("app_display_name", "Sayance"),
                device_display_name=body.get("device_display_name", "Mobile Device"),
                pushkey=body["pushkey"],
                ts=0,  # Will be set by the store
                lang=body.get("lang", "en"),
                data={
                    "format": "event_id_only",
                },
                device_id=requester.device_id,
                enabled=True,
                last_stream_ordering=0,  # Starting from the beginning
                last_success=0,  # No previous success
                failing_since=None,  # Not failing yet
                access_token=requester.access_token_id,  # Get from the requester
            )

            # Create the pusher
            pusher = ExpoPusher(self.hs, pusher_config)
            
            success = await pusher.send_notification(
                badge=body.get("badge", 1),
                notification=body["notification"],
                room_name=body.get("room_name"),
                room_alias=body.get("room_alias"),
                sender_display_name=body.get("sender_display_name"),
                event_id=body.get("event_id"),
                room_id=body.get("room_id"),
            )
            
            return HTTPStatus.OK if success else HTTPStatus.INTERNAL_SERVER_ERROR, {
                "success": success
            }
                
        except Exception as e:
            logger.exception("Error sending push notification")
            return HTTPStatus.INTERNAL_SERVER_ERROR, {
                "error": f"Internal server error: {str(e)}"
            }

def register_servlets(hs: "HomeServer", http_server: HttpServer) -> None:
    """Register the push gateway servlets."""
    PushGatewayServlet(hs).register(http_server) 