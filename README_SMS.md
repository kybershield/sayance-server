# SMS Phone Verification with ClickSend

This document explains how to set up and use ClickSend for SMS phone verification in Synapse. The phone verification system allows users to register and log in using their phone numbers, similar to WhatsApp's onboarding flow.

## Features

- **Phone Registration**: Users can register new accounts using only their phone number
- **Phone Login**: Existing users can log in using their phone number  
- **OTP Verification**: Secure 6-digit verification codes sent via SMS
- **E164 Validation**: Automatic phone number format validation
- **Graceful Fallback**: Falls back to mock SMS when ClickSend is disabled

## Prerequisites

1. **ClickSend Account**: Sign up at [https://www.clicksend.com/](https://www.clicksend.com/)
2. **API Credentials**: Get your username and API key from the ClickSend dashboard
3. **Credits**: Ensure your ClickSend account has sufficient credits for sending SMS

## Installation

### 1. Install ClickSend Client

Choose one of these options:

```bash
# Option 1: Install with SMS support included
pip install matrix-synapse[sms]

# Option 2: Install just the ClickSend client
pip install clicksend-client
```

### 2. Configure Synapse

Add the following to your `homeserver.yaml`:

```yaml
sms:
  clicksend_enabled: true
  clicksend_username: "your_email@example.com"
  clicksend_api_key: "your_api_key_here"
  clicksend_sender_id: "+1234567890"  # Your phone number or alpha tag
```

### 3. Restart Synapse

Restart your Synapse homeserver to load the new configuration.

## Configuration Options

| Option | Required | Description | Example |
|--------|----------|-------------|---------|
| `clicksend_enabled` | No | Enable/disable SMS sending | `true` or `false` |
| `clicksend_username` | Yes* | Your ClickSend username | `"user@example.com"` |
| `clicksend_api_key` | Yes* | Your ClickSend API key | `"your-api-key"` |
| `clicksend_sender_id` | Yes* | Phone number or alpha tag | `"+1234567890"` or `"MyApp"` |

*Required when `clicksend_enabled` is `true`

### Sender ID Options

- **Phone Number**: Use your dedicated number in E.164 format (e.g., `"+61412345678"`)
- **Alpha Tag**: Use a custom sender name (e.g., `"MyApp"`, `"Support"`)
  - 3-11 characters long
  - Letters, numbers, and plus signs only
  - Recipients cannot reply to alpha tags

## API Endpoints

The phone verification system provides two new endpoints:

### 1. Request Verification Code

```
POST /_matrix/client/r0/register/phone/requestToken
```

Request body:
```json
{
  "phone_number": "+1234567890",
  "country": "US",
  "client_secret": "unique_client_secret",
  "send_attempt": 1
}
```

Response:
```json
{
  "sid": "session_id_for_verification"
}
```

### 2. Verify Code and Complete Registration/Login

```
POST /_matrix/client/r0/register/phone/verify
```

Request body:
```json
{
  "sid": "session_id_from_requestToken",
  "otp": "123456",
  "username": "desired_username",
  "display_name": "User Display Name"
}
```

Response (Registration):
```json
{
  "user_id": "@user:example.com",
  "access_token": "access_token_here",
  "device_id": "device_id_here",
  "home_server": "example.com"
}
```

Response (Login):
```json
{
  "user_id": "@existing_user:example.com",
  "access_token": "access_token_here", 
  "device_id": "device_id_here",
  "home_server": "example.com"
}
```

## Flow Examples

### Registration Flow

1. **User enters phone number** → Client calls `/register/phone/requestToken`
2. **System sends OTP** → ClickSend delivers SMS with verification code
3. **User enters OTP** → Client calls `/register/phone/verify` with code
4. **Account created** → User receives access token and can use Synapse

### Login Flow

1. **User enters phone number** → Client calls `/register/phone/requestToken`
2. **System detects existing user** → ClickSend delivers SMS with verification code  
3. **User enters OTP** → Client calls `/register/phone/verify` with code
4. **User logged in** → User receives access token and can use Synapse

## Testing

### Development Mode

When ClickSend is disabled (`clicksend_enabled: false`), the system runs in mock mode:

- SMS sending is logged but not actually sent
- OTP verification still works normally
- Useful for development and testing

### Verification Code

- **Production**: Random 6-digit codes (e.g., "847293")
- **Development**: Can be configured to use fixed code "123456"

## Troubleshooting

### Common Issues

1. **"ClickSend client library not installed"**
   ```bash
   pip install clicksend-client
   ```

2. **"Phone number not in correct E164 format"**
   - Ensure phone numbers start with `+` and country code
   - Example: `+61412345678` (Australia), `+1234567890` (US)

3. **"Failed to send SMS"**
   - Check ClickSend account credits
   - Verify API credentials are correct
   - Check ClickSend dashboard for delivery status

4. **"Invalid session"**
   - OTP sessions expire after 10 minutes
   - Request a new verification code

### Logs

Enable debug logging to troubleshoot SMS issues:

```yaml
loggers:
    synapse.handlers.phone_verification:
        level: DEBUG
```

### Rate Limiting

The system includes built-in rate limiting to prevent abuse:
- Uses existing Synapse rate limiting infrastructure
- Prevents rapid OTP requests from same IP/phone

## Security Considerations

- **OTP Expiry**: Verification codes expire after 10 minutes
- **E164 Validation**: Phone numbers must be in correct international format
- **Rate Limiting**: Prevents spam and abuse
- **Session Management**: Each verification attempt gets unique session ID
- **No Password Required**: Phone verification can work without traditional passwords

## Cost Considerations

- ClickSend charges per SMS sent
- Typical cost: $0.08-0.15 USD per SMS (varies by country)
- Consider implementing additional rate limiting for cost control
- Monitor usage via ClickSend dashboard

## Support

- **ClickSend Documentation**: [https://developers.clicksend.com/](https://developers.clicksend.com/)
- **ClickSend Support**: Available via their dashboard
- **Synapse Community**: Matrix rooms for Synapse support 