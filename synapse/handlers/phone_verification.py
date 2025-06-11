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
import re

if TYPE_CHECKING:
    from synapse.server import HomeServer

logger = logging.getLogger(__name__)


class PhoneSMSSender:
    """Utility class for sending SMS verification codes using ClickSend.
    
    This implementation uses the ClickSend SMS API to send verification codes
    to phone numbers during registration and login flows.
    """

    def __init__(self, hs: "HomeServer"):
        self.hs = hs
        self.config = hs.config
        self._clicksend_client = None
        
        # Initialize ClickSend client if enabled
        if self.config.sms.clicksend_enabled:
            try:
                import clicksend_client
                from clicksend_client.rest import ApiException
                
                # Configure ClickSend authentication
                configuration = clicksend_client.Configuration()
                configuration.username = self.config.sms.clicksend_username
                configuration.password = self.config.sms.clicksend_api_key
                
                # Create SMS API instance
                self._clicksend_client = clicksend_client.SMSApi(
                    clicksend_client.ApiClient(configuration)
                )
                self._clicksend_exception = ApiException
                
                logger.info("ClickSend SMS client initialized successfully")
                
            except ImportError:
                logger.error("ClickSend client library not installed. Install with: pip install clicksend-client")
                self._clicksend_client = None
            except Exception as e:
                logger.error(f"Failed to initialize ClickSend client: {e}")
                self._clicksend_client = None

    def _normalize_phone_number(self, phone_number: str, country_code: Optional[str] = None) -> Optional[str]:
        """Normalize a phone number to E164 format.
        
        Args:
            phone_number: The phone number to normalize
            country_code: Optional country code (ISO 3166-1 alpha-2)
            
        Returns:
            str: The phone number in E164 format, or None if invalid
        """
        try:
            import phonenumbers
            from phonenumbers import NumberParseException
            
            # Remove any whitespace and special characters except +
            cleaned_number = re.sub(r'[^\d+]', '', phone_number.strip())
            
            # If the number doesn't start with +, try to add it
            if not cleaned_number.startswith('+'):
                cleaned_number = '+' + cleaned_number
            
            # Parse the phone number
            try:
                parsed_number = phonenumbers.parse(cleaned_number, country_code)
            except NumberParseException:
                # If parsing with country code fails, try without
                parsed_number = phonenumbers.parse(cleaned_number, None)
            
            # Validate the number
            if phonenumbers.is_valid_number(parsed_number):
                # Format as E164
                return phonenumbers.format_number(parsed_number, phonenumbers.PhoneNumberFormat.E164)
            else:
                logger.warning(f"Invalid phone number: {phone_number}")
                return None
                
        except ImportError:
            logger.warning("phonenumbers library not available, falling back to basic validation")
            # Fallback to basic E164 validation
            return self._basic_e164_format(phone_number)
        except Exception as e:
            logger.warning(f"Error parsing phone number {phone_number}: {e}")
            return self._basic_e164_format(phone_number)

    def _basic_e164_format(self, phone_number: str) -> Optional[str]:
        """Basic E164 formatting as fallback.
        
        Args:
            phone_number: The phone number to format
            
        Returns:
            str: The phone number in E164 format, or None if invalid
        """
        # Remove any whitespace and special characters except +
        cleaned_number = re.sub(r'[^\d+]', '', phone_number.strip())
        
        # If the number doesn't start with +, add it
        if not cleaned_number.startswith('+'):
            cleaned_number = '+' + cleaned_number
        
        # Basic E164 validation: +[country code][number] (max 15 digits total)
        e164_pattern = r'^\+[1-9]\d{1,14}$'
        if re.match(e164_pattern, cleaned_number):
            return cleaned_number
        else:
            return None

    def _validate_e164_format(self, phone_number: str) -> bool:
        """Validate that the phone number is in E164 format.
        
        Args:
            phone_number: The phone number to validate
            
        Returns:
            bool: True if the phone number is in correct E164 format
        """
        # E164 format: +[country code][number] (max 15 digits total)
        e164_pattern = r'^\+[1-9]\d{1,14}$'
        return bool(re.match(e164_pattern, phone_number))

    async def send_verification_code(self, phone_number: str, code: str, country_code: Optional[str] = None) -> bool:
        """Send a verification code to a phone number using ClickSend.
        
        Args:
            phone_number: The phone number to send the code to
            code: The verification code to send
            country_code: Optional country code for parsing (ISO 3166-1 alpha-2)
            
        Returns:
            bool: True if the code was sent successfully, False otherwise
        """
        # Normalize phone number to E164 format
        normalized_number = self._normalize_phone_number(phone_number, country_code)
        if not normalized_number:
            logger.error(f"Could not normalize phone number {phone_number} to E164 format")
            return False
        
        logger.debug(f"Normalized phone number {phone_number} to {normalized_number}")
        
        # Check if ClickSend is enabled and configured
        if not self.config.sms.clicksend_enabled:
            logger.info(f"MOCK SMS: Would send verification code {code} to {normalized_number}")
            return True
            
        if not self._clicksend_client:
            logger.error("ClickSend client not available. Check configuration and dependencies.")
            return False

        try:
            import clicksend_client
            from clicksend_client import SmsMessage, SmsMessageCollection
            
            # Create SMS message
            message_body = f"Your verification code is: {code}"
            
            sms_message = SmsMessage(
                source=self.config.sms.clicksend_sender_id,
                body=message_body,
                to=normalized_number
            )
            
            sms_messages = SmsMessageCollection(messages=[sms_message])
            
            # Send the SMS
            logger.debug(f"Sending SMS verification code to {normalized_number}")
            api_response = self._clicksend_client.sms_send_post(sms_messages)
            
            # Check response
            if hasattr(api_response, 'response_code') and api_response.response_code == "SUCCESS":
                logger.info(f"SMS verification code sent successfully to {normalized_number}")
                return True
            else:
                logger.error(f"Failed to send SMS. Response: {api_response}")
                return False
                
        except self._clicksend_exception as e:
            logger.error(f"ClickSend API error when sending SMS to {normalized_number}: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error when sending SMS to {normalized_number}: {e}")
            return False

    async def generate_verification_code(self) -> str:
        """Generate a verification code.
        
        In production, this generates a random 6-digit code.
        For testing/mock mode, it always returns "123456".
        
        Returns:
            str: The generated verification code
        """
        # If ClickSend is disabled (mock mode), always return the same code for testing
        if not self.config.sms.clicksend_enabled:
            return "123456"
        
        # Generate a random 6-digit code for production
        import random
        return ''.join(random.choices('0123456789', k=6)) 