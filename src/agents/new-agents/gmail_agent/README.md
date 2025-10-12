# Gmail Agent

An AI agent that enables you to send emails through Gmail using a simple, structured command format.

## What It Does

The Gmail Agent allows you to send emails by typing structured commands. It handles authentication with your Gmail account and sends emails on your behalf.

## Key Features

### 📧 Email Sending
- Send emails through your Gmail account
- Simple structured command format
- Optional subject lines (emails can be sent without subjects)
- Automatic validation and error checking

### 🔐 Secure Authentication
- Connects to your Gmail account securely
- One-time setup process
- Your credentials are stored safely

### 💬 Easy to Use
- Works through chat interface
- Clear error messages when something goes wrong
- Real-time feedback on email status

## How to Use

### Getting Started

1. **First Time Setup**
   - The agent will guide you through connecting to your Gmail account
   - You'll need to authenticate once through your browser
   - After setup, you can send emails immediately

### Command Format

To send an email, use this exact format:

```
send
to: recipient@example.com
subject: Email subject (optional)
content: Your message content here
```

### Examples

**Basic email without subject:**
```
send
to: john@example.com
content: Hi John, hope you're doing well!
```

**Email with subject:**
```
send
to: team@company.com
subject: Project Update
content: The project is on track and we'll be delivering on time.
```

**Multi-line content:**
```
send
to: client@business.com
subject: Proposal Review
content: Please review the attached proposal and let me know your thoughts. We can schedule a call to discuss any questions you might have.
```

### Important Notes

- **Required fields:** `to:` and `content:`
- **Optional field:** `subject:` (if omitted, email will be sent without a subject)
- **Format:** Each field must be on its own line
- **Command:** Must start with "send"

### What Happens When You Send

1. The agent validates your command format
2. Checks that the email address is valid
3. Sends the email through your Gmail account
4. Provides confirmation with message ID
5. Shows any errors if something goes wrong

### Common Errors

**Wrong format:**
```
❌ Command must start with 'send'. Expected format:

send
to: email@example.com
subject: Email subject (optional)
content: Email content
```

**Missing required fields:**
```
❌ Missing required field: 'to:' with valid email address
```

**Invalid email:**
```
❌ Invalid email format: not-an-email
```

### Rate Limits

- You can send up to 10 emails per hour
- If you exceed this limit, you'll get a clear message
- The limit resets every hour

## Troubleshooting

**Can't send emails?**
- Make sure you've completed the initial Gmail authentication
- Check that your command follows the exact format shown above
- Verify the recipient email address is correct

**Authentication issues?**
- The agent will provide a link to re-authenticate if needed
- Make sure you're using the same Gmail account you set up initially

**Still having problems?**
- Check the error message for specific guidance
- Make sure you're using the exact format: `send` on the first line, then `to:`, `subject:`, and `content:` on separate lines

---

*This agent is designed for secure, reliable email sending through Gmail with a focus on structured commands and clear error handling.*