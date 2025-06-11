# Copyright 2023 The Matrix.org Foundation C.I.C.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from typing import Any, Optional

from synapse.config._base import Config, ConfigError
from synapse.types import JsonDict


class SMSConfig(Config):
    section = "sms"

    def read_config(self, config: JsonDict, **kwargs: Any) -> None:
        sms_config = config.get("sms")
        if sms_config is None:
            sms_config = {}

        # ClickSend configuration
        self.clicksend_enabled = sms_config.get("clicksend_enabled", False)
        self.clicksend_username = sms_config.get("clicksend_username", None)
        self.clicksend_api_key = sms_config.get("clicksend_api_key", None)
        self.clicksend_sender_id = sms_config.get("clicksend_sender_id", None)
        
        # Validation
        if self.clicksend_enabled:
            if not self.clicksend_username:
                raise ConfigError("sms.clicksend_username is required when clicksend_enabled is true")
            if not self.clicksend_api_key:
                raise ConfigError("sms.clicksend_api_key is required when clicksend_enabled is true")
            if not self.clicksend_sender_id:
                raise ConfigError("sms.clicksend_sender_id is required when clicksend_enabled is true")

    def generate_config_section(self, **kwargs: Any) -> str:
        return """
        ## SMS ##
        
        # Configuration for sending SMS messages via ClickSend
        sms:
          # Set to true to enable SMS sending via ClickSend
          clicksend_enabled: false
          
          # Your ClickSend username (usually your email)
          #clicksend_username: "your_username@example.com"
          
          # Your ClickSend API key
          #clicksend_api_key: "your_api_key_here"
          
          # Sender ID for SMS messages (phone number or alpha tag)
          # This can be a phone number in E.164 format (e.g., "+1234567890")
          # or an alpha tag (e.g., "YourApp")
          #clicksend_sender_id: "+1234567890"
        """ 