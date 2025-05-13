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

import logging
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from synapse.server import HomeServer

logger = logging.getLogger(__name__)


class PhoneSMSSender:
    """Utility class for sending SMS verification codes.
    
    This is currently mocked but can be implemented to use real SMS providers
    like Twilio, Vonage, etc.
    """

    def __init__(self, hs: "HomeServer"):
        self.hs = hs
        self.config = hs.config

    async def send_verification_code(self, phone_number: str, code: str) -> bool:
        """Send a verification code to a phone number.
        
        Args:
            phone_number: The phone number to send the code to
            code: The verification code to send
            
        Returns:
            bool: True if the code was sent successfully, False otherwise
        """
        # This is where you would implement the actual SMS sending logic
        # For now, we just log that we would send it
        logger.info(f"MOCK SMS: Would send verification code {code} to {phone_number}")
        
        # In a real implementation, you might use Twilio, for example:
        # try:
        #     from twilio.rest import Client
        #     client = Client(self.config.twilio.account_sid, self.config.twilio.auth_token)
        #     message = client.messages.create(
        #         body=f"Your verification code is: {code}",
        #         from_=self.config.twilio.phone_number,
        #         to=phone_number
        #     )
        #     return True
        # except Exception as e:
        #     logger.error(f"Failed to send SMS: {e}")
        #     return False
        
        # For now, always return True as if it succeeded
        return True

    async def generate_verification_code(self) -> str:
        """Generate a verification code.
        
        In production, this would generate a random code.
        For testing, it always returns "123456".
        
        Returns:
            str: The generated verification code
        """
        # For now, always return the same code for testing
        return "123456"
        
        # In a real implementation, generate a random code:
        # import random
        # return ''.join(random.choices('0123456789', k=6)) 