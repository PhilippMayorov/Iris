# Gmail Agent

A uAgent that can send emails using the Gmail API. This agent provides a simple interface for sending emails programmatically through the Gmail service.

## Features

- Send emails using Gmail API
- OAuth2 authentication with Google Cloud
- Rate limiting and quota management
- Health check endpoints
- Error handling and status responses
- Support for custom sender addresses

## Prerequisites

1. **Google Cloud Account**: You need a Google Cloud account with billing enabled
2. **Gmail API**: The Gmail API must be enabled in your Google Cloud project
3. **Google Cloud CLI**: Install the gcloud CLI for authentication
4. **Python Dependencies**: Install the required Python packages

## Setup

### 1. Install Google Cloud CLI

Follow the official installation guide: https://cloud.google.com/sdk/docs/install

### 2. Authenticate with Google Cloud

```bash
gcloud auth login
gcloud auth application-default login
```

### 3. Enable Gmail API

```bash
gcloud services enable gmail.googleapis.com
```

### 4. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 5. Run Setup Script (Optional)

```bash
python setup_gmail.py
```

This script will check your setup and guide you through any missing steps.

## Usage

### Starting the Gmail Agent

```bash
python gmail_agent.py
```

The agent will start and display its address. Make note of this address for client connections.

### Sending Emails

#### Using the Test Client

1. Update the `GMAIL_AGENT_ADDRESS` in `test_gmail_client.py` with the actual agent address
2. Update the recipient email address in the test requests
3. Run the test client:

```bash
python test_gmail_client.py
```

#### Programmatic Usage

```python
from uagents import Agent, Context, Model

class EmailSendRequest(Model):
    to: str
    subject: str
    body: str
    from_email: str = None

class EmailStatusResponse(Model):
    status_code: int
    message_id: str = None
    error_message: str = None
    success: bool = False

# Create your agent
agent = Agent(name="My Agent", port=8001)

# Gmail agent address
GMAIL_AGENT_ADDRESS = "your_gmail_agent_address_here"

@agent.on_event("startup")
async def send_email(ctx: Context):
    request = EmailSendRequest(
        to="recipient@example.com",
        subject="Hello from Gmail Agent",
        body="This is a test email sent via the Gmail Agent!"
    )
    
    await ctx.send(GMAIL_AGENT_ADDRESS, request)

@agent.on_message(EmailStatusResponse)
async def handle_response(ctx: Context, sender: str, msg: EmailStatusResponse):
    if msg.success:
        ctx.logger.info(f"Email sent! Message ID: {msg.message_id}")
    else:
        ctx.logger.error(f"Failed to send email: {msg.error_message}")

if __name__ == "__main__":
    agent.run()
```

## API Reference

### EmailSendRequest

Request model for sending emails:

- `to` (str): Recipient email address
- `subject` (str): Email subject line
- `body` (str): Email body content
- `from_email` (str, optional): Sender email address (uses authenticated user if not provided)

### EmailStatusResponse

Response model after sending email:

- `status_code` (int): HTTP status code (200 for success, 500 for error)
- `message_id` (str, optional): Gmail message ID if successful
- `error_message` (str, optional): Error description if failed
- `success` (bool): Whether the email was sent successfully

## Configuration

### Environment Variables

- `AGENT_NAME`: Name of the agent (default: "Gmail Agent")
- `AGENT_SEED`: Seed phrase for agent identity
- `PORT`: Port for agent endpoint (default: 8000)

### Rate Limiting

The agent includes built-in rate limiting:
- 10 requests per hour by default
- Configurable through the QuotaProtocol

## Troubleshooting

### Common Issues

1. **Authentication Error**: Make sure you've run `gcloud auth application-default login`
2. **Gmail API Not Enabled**: Enable it with `gcloud services enable gmail.googleapis.com`
3. **Permission Denied**: Ensure your Google account has Gmail access
4. **Quota Exceeded**: The agent has rate limiting to prevent quota issues

### Debug Mode

Enable debug logging by setting the log level:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Testing Authentication

You can test your Gmail API setup with a simple script:

```python
import google.auth
from googleapiclient.discovery import build

try:
    creds, _ = google.auth.default()
    service = build("gmail", "v1", credentials=creds)
    profile = service.users().getProfile(userId="me").execute()
    print(f"Authenticated as: {profile['emailAddress']}")
except Exception as e:
    print(f"Authentication failed: {e}")
```

## Security Notes

- The agent uses OAuth2 for secure authentication
- Credentials are stored securely by Google Cloud
- Rate limiting prevents abuse
- All email sending is logged for audit purposes

## License

This project is part of the uAgent examples and follows the same licensing terms.
