#!/usr/bin/env python3
"""
Test script for CallPusher VoIP notifications.

This script demonstrates how to create and use a CallPusher for sending
VoIP push notifications for calls.

Usage:
    python scripts-dev/test_call_pusher.py
"""

import asyncio
import logging
import sys
import os

# Add the synapse directory to the path so we can import synapse modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from synapse.push import PusherConfig
from synapse.push.callpusher import CallPusher

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_call_pusher():
    """Test the CallPusher with a mock homeserver."""
    
    # Mock homeserver (you would use the real one in production)
    class MockHomeServer:
        def __init__(self):
            self.config = None
            self.clock = None
            
        def get_datastores(self):
            return None
            
        def get_clock(self):
            return None
    
    # Create pusher configuration for calls
    pusher_config = PusherConfig(
        id=None,
        user_name="@test_user:example.com",
        profile_tag="",
        kind="call",
        app_id="com.example.app",
        app_display_name="Test App",
        device_display_name="Test Device",
        pushkey="test_device_token_here",  # Replace with real device token
        ts=0,
        lang="en",
        data={
            "apn_key_id": "YOUR_APN_KEY_ID",  # Replace with your APN Key ID
            "apn_team_id": "YOUR_APN_TEAM_ID",  # Replace with your Team ID
            "apn_key_file": "/path/to/APNsAuthKey_KEYID.p8",  # Replace with path to your .p8 file
            "fcm_credentials_file": "/path/to/firebase-credentials.json",  # Replace with path to your FCM credentials
            "fcm_project_id": "YOUR_FCM_PROJECT_ID",  # Replace with your Firebase Project ID
        },
        device_id="test_device",
        enabled=True,
        last_stream_ordering=0,
        last_success=0,
        failing_since=None,
        access_token=None,
    )
    
    # Create mock homeserver
    hs = MockHomeServer()
    
    try:
        # Create CallPusher instance
        logger.info("Creating CallPusher...")
        pusher = CallPusher(hs, pusher_config)
        logger.info("CallPusher created successfully")
        
        # Test notification data
        notification_data = {
            "body": "Incoming call",
            "sender": "@caller:example.com",
            "type": "m.room.message",
        }
        
        # Test sending a call notification
        logger.info("Sending test call notification...")
        success = await pusher.send_notification(
            badge=1,
            notification=notification_data,
            room_name="Call with John Doe",
            room_id="!room123:example.com",
            event_id="$event123:example.com",
            sender_display_name="John Doe",
        )
        
        if success:
            logger.info("Call notification sent successfully!")
        else:
            logger.error("Failed to send call notification")
            
    except Exception as e:
        logger.error(f"Error testing CallPusher: {e}")
        logger.error("Make sure you have configured the APN and FCM credentials correctly")

def main():
    """Main function to run the test."""
    print("CallPusher Test Script")
    print("=====================")
    print()
    print("This script tests the CallPusher for VoIP notifications.")
    print("Make sure you have configured the APN and FCM credentials before running.")
    print()
    
    # Run the test
    asyncio.run(test_call_pusher())

if __name__ == "__main__":
    main() 