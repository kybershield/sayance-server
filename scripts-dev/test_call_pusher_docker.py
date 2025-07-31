#!/usr/bin/env python3
"""
Test script for CallPusher in Docker environment.
This script tests the CallPusher with proper secrets access from the mounted /data/secrets directory.
"""

import asyncio
import logging
import os
import sys
from typing import Dict, Any

# Add the synapse directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from synapse.app.homeserver import setup as setup_homeserver
from synapse.config.homeserver import HomeServerConfig
from synapse.push.callpusher import CallPusher
from synapse.push import PusherConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_call_pusher_docker():
    """Test CallPusher with Docker secrets access."""
    
    # Test configuration for Docker environment
    test_config = {
        "server_name": "test.example.com",
        "database": {
            "name": "sqlite3",
            "args": {
                "database": ":memory:"
            }
        },
        "listeners": [
            {
                "port": 8008,
                "bind_addresses": ["::"],
                "type": "http",
                "resources": [
                    {"names": ["client"]}
                ]
            }
        ]
    }
    
    # Create a minimal homeserver config
    config = HomeServerConfig()
    config.parse_config_dict(test_config, "", "")
    
    # Create homeserver
    hs = await setup_homeserver(
        config.server_name,
        config=config,
        version_string="test"
    )
    
    # Test pusher configuration with Docker secrets paths
    pusher_config = PusherConfig(
        id=None,
        user_name="@test:example.com",
        profile_tag="",
        kind="call",
        app_id="com.example.app",
        app_display_name="Test App",
        device_display_name="Test Device",
        pushkey="test_device_token",
        ts=0,
        lang="en",
        data={
            "apn_key_id": "5JMA4TNN47",  # From your AuthKey filename
            "apn_team_id": "YOUR_TEAM_ID",  # Replace with your actual team ID
            "apn_key_file": "/data/secrets/AuthKey_5JMA4TNN47.p8",
            "fcm_credentials_file": "/data/secrets/google-services.json",
            "fcm_project_id": "YOUR_FIREBASE_PROJECT_ID",  # Replace with your actual project ID
        },
        device_id="test_device",
        enabled=True,
        last_stream_ordering=0,
        last_success=0,
        failing_since=None,
        access_token=None,
    )
    
    try:
        # Test file path resolution
        logger.info("Testing file path resolution...")
        
        # Check if secrets directory exists
        secrets_dir = "/data/secrets"
        if os.path.exists(secrets_dir):
            logger.info(f"Secrets directory exists: {secrets_dir}")
            files = os.listdir(secrets_dir)
            logger.info(f"Files in secrets directory: {files}")
        else:
            logger.warning(f"Secrets directory not found: {secrets_dir}")
        
        # Check specific files
        apn_key_path = "/data/secrets/AuthKey_5JMA4TNN47.p8"
        fcm_creds_path = "/data/secrets/google-services.json"
        
        if os.path.exists(apn_key_path):
            logger.info(f"APN key file found: {apn_key_path}")
        else:
            logger.error(f"APN key file not found: {apn_key_path}")
            
        if os.path.exists(fcm_creds_path):
            logger.info(f"FCM credentials file found: {fcm_creds_path}")
        else:
            logger.error(f"FCM credentials file not found: {fcm_creds_path}")
        
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
        logger.error("In Docker, ensure your secrets are mounted at /data/secrets/")
        
    finally:
        await hs.get_reactor().stop()

if __name__ == "__main__":
    asyncio.run(test_call_pusher_docker()) 