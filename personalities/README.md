# AI Personality System

This directory contains personality files that define the behavior and communication style of the ASI One Agentic Chat system.

## How to Use

### 1. Using the Default Personality
The system comes with a built-in professional personality. Simply run:
```bash
python agentic_chat.py
```

### 2. Using a Custom Personality File
To use a custom personality, provide the file path as the second argument:
```bash
python agentic_chat.py asi1-agentic personalities/friendly_assistant.txt
```

### 3. Available Personality Files

**Standard Personalities:**
- **friendly_assistant.txt** - A warm, enthusiastic assistant that uses emojis and casual language
- **professional_expert.txt** - A formal, expert-level assistant with precise communication
- **creative_collaborator.txt** - An innovative assistant focused on creative problem-solving

**Ridiculous/Testing Personalities:**
- **ridiculous_pirate.txt** - Captain Bytebeard, a dramatic pirate who speaks in pirate slang 🏴‍☠️
- **formal_butler.txt** - Jeeves, an overly formal Victorian-era butler with perfect etiquette
- **hyperactive_puppy.txt** - Buddy, an extremely excited puppy with infinite energy 🐕

### 4. Creating Your Own Personality

Create a new text file with your desired personality description. The system prompt should include:

- **Role definition**: What kind of assistant you are
- **Personality traits**: Communication style, tone, characteristics
- **Capabilities**: What you can do (this part is usually consistent)
- **Behavior guidelines**: How you should interact with users
- **Goals**: What you're trying to achieve

Example structure:
```
You are a [role description] with access to the Agentverse marketplace.

Your personality traits:
- [trait 1]
- [trait 2]
- [trait 3]

Your capabilities include:
- Discovering and working with agents from the Agentverse marketplace
- [other capabilities...]

When helping users:
- [guideline 1]
- [guideline 2]
- [guideline 3]

[Additional instructions...]
```

### 5. Commands

Once in the chat, you can use these commands:
- `/personality` or `/persona` - View the current personality/system prompt
- `/help` - Show all available commands
- `/clear` - Clear conversation (preserves personality)
- `/quit` - Exit the chat

### 6. Tips

- Personality files should be plain text (.txt) files
- Keep personality descriptions focused and clear
- The system will automatically include agent capabilities
- Personality is preserved across conversation clears
- You can change personality by restarting with a different file

## Examples

### Friendly Assistant
```bash
python agentic_chat.py asi1-agentic personalities/friendly_assistant.txt
```

### Professional Expert
```bash
python agentic_chat.py asi1-fast-agentic personalities/professional_expert.txt
```

### Creative Collaborator
```bash
python agentic_chat.py asi1-extended-agentic personalities/creative_collaborator.txt
```

### Ridiculous Personalities (for testing)
```bash
# Pirate personality
python agentic_chat.py asi1-agentic personalities/ridiculous_pirate.txt

# Formal butler personality
python agentic_chat.py asi1-fast-agentic personalities/formal_butler.txt

# Hyperactive puppy personality
python agentic_chat.py asi1-extended-agentic personalities/hyperactive_puppy.txt
```
