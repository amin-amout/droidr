# Conversational Memory & Persistent Sessions

This feature enables your voice assistant to maintain conversation context within a session and remember previous exchanges.

## Overview

The assistant now supports two operational modes:

1. **Dormant Mode**: Waiting for wake word ("Hey Jarvis")
2. **Active Session Mode**: Continuously listening without requiring wake word

## Key Features

### 1. Session State Management

- **Wake Word Activation**: Say "Hey Jarvis" to start a session
- **Continuous Listening**: No need to repeat wake word during session
- **Exit Phrases**: End session with phrases like:
  - "stop listening"
  - "go to sleep"
  - "goodbye"
  - "exit"
  - "bye"
  - "stop"

### 2. Conversational Memory

- **Short-term Memory**: Remembers last N conversation turns (configurable)
- **Context Awareness**: LLM receives conversation history
- **Automatic Trimming**: Oldest messages removed when limit reached
- **Session Reset**: Memory clears when session ends

### 3. Natural Conversations

**Example conversation:**
```
User: "Hey Jarvis"
Jarvis: "Yes? How can I help you?"

User: "What's 5 plus 8?"
Jarvis: "That's 13."

User: "Can you multiply that by 2?"
Jarvis: "26."  [remembers "that" = 13]

User: "Thanks! Goodbye"
Jarvis: "Goodbye! Let me know if you need anything."
[Session ends, memory cleared]
```

## Architecture

### ConversationSession Class

Located in `core/session.py`

**Key Methods:**
- `activate()`: Start a new session and clear memory
- `deactivate()`: End session and clear memory
- `add_to_memory(role, content)`: Add user/assistant message
- `get_memory_for_llm()`: Get formatted conversation history
- `should_exit(text)`: Check if text matches exit phrase
- `get_memory_context()`: Format memory as string for LLM

**Attributes:**
- `active: bool`: Session state
- `memory: List[Dict]`: Conversation turns
- `max_memory_size: int`: Max turns to remember
- `exit_phrases: List[str]`: Phrases that end session

### Pipeline Flow

```
┌─────────────────────────────────────┐
│      Dormant Mode (Inactive)        │
│   Listening for Wake Word Only      │
└──────────────┬──────────────────────┘
               │ Wake word detected
               ▼
┌─────────────────────────────────────┐
│         Active Session              │
│   Continuous Listening              │
│   + Memory Context                  │
└──────────────┬──────────────────────┘
               │
               ├──► User speaks
               │    │
               │    ├──► Check exit phrase?
               │    │    │
               │    │    ├─Yes─► End session ──┐
               │    │    │                      │
               │    │    └─No──► Continue       │
               │    │                           │
               │    ├──► Add to memory          │
               │    ├──► Get LLM response       │
               │    ├──► Add response to memory │
               │    └──► Speak response         │
               │                                │
               └────────────────────────────────┘
```

## Configuration

### config.yaml

```yaml
session:
  max_memory_turns: 10  # Number of conversation turns to remember
  exit_phrases:
    - "stop listening"
    - "go to sleep"
    - "exit"
    - "goodbye"
    - "bye"
    - "stop"
```

### Memory Size

- **Turn**: One user message + one assistant response
- **max_memory_turns: 10** = remembers last 20 messages (10 user + 10 assistant)
- Older messages automatically removed when limit exceeded

## Implementation Details

### Memory Structure

Each memory entry is a dictionary:
```python
{
    "role": "user" | "assistant",
    "content": "message text"
}
```

### LLM Integration

When calling the LLM, the prompt includes:
1. System prompt (personality/instructions)
2. Conversation history from memory
3. Current user input

**Example prompt with memory:**
```
You are Jarvis, a helpful voice assistant...

Previous conversation:
User: What's the weather?
Assistant: It's sunny and 75 degrees.
User: Should I bring an umbrella?
Assistant: No, you won't need one today.

User: What about tomorrow?
Assistant:
```

### Session Lifecycle

1. **Start**: Wake word detected → `session.activate()`
2. **Active**: User speaks → Add to memory → Get response → Add to memory → Speak
3. **End**: Exit phrase detected → `session.deactivate()` → Clear memory

## Testing

Run the test script:
```bash
python test_memory.py
```

This will test:
- ✓ Session activation/deactivation
- ✓ Memory storage and retrieval
- ✓ Automatic memory trimming
- ✓ Exit phrase detection
- ✓ Context formatting

## Usage Examples

### Basic Interaction
```
User: "Hey Jarvis"
Jarvis: "Yes? How can I help you?"

User: "Set a reminder"
Jarvis: "What would you like me to remind you about?"

User: "Call mom at 3pm"
Jarvis: "I've set a reminder to call mom at 3pm."

User: "Goodbye"
Jarvis: "Goodbye! Let me know if you need anything."
```

### Context Awareness
```
User: "Hey Jarvis"
Jarvis: "Yes? How can I help you?"

User: "My name is Alice"
Jarvis: "Nice to meet you, Alice!"

User: "What's my name?"
Jarvis: "Your name is Alice."  [remembers from earlier]

User: "Stop listening"
Jarvis: "Goodbye! Let me know if you need anything."
```

## Future Enhancements

### Potential Improvements:
1. **Voice Activity Detection (VAD)**: Use webrtcvad for better speech detection
2. **Long-term Memory**: Persist important information across sessions
3. **User Profiles**: Remember user preferences and context
4. **Session Timeout**: Auto-end session after period of inactivity
5. **Multi-turn Planning**: Handle complex multi-step tasks
6. **Interrupt Handling**: Allow user to interrupt assistant mid-speech

## Troubleshooting

### Session won't activate
- Check wake word model is loaded correctly
- Verify microphone is working
- Check logs for "Wake word detected!"

### Memory not working
- Verify `session` section in config.yaml
- Check `max_memory_turns` is > 0
- Look for "Added to memory" in logs

### Exit phrases not working
- Verify STT is transcribing correctly
- Check exit phrases in config.yaml
- Try exact phrases: "stop listening", "goodbye"

## Best Practices

1. **Keep responses concise**: Voice output should be brief
2. **Test exit phrases**: Ensure users can easily end sessions
3. **Monitor memory size**: Large memory = slower LLM calls
4. **Handle silence**: Implement timeout for inactive sessions
5. **Graceful errors**: Handle LLM failures without breaking session

## Code Examples

### Custom Exit Phrases
```python
session = ConversationSession(
    max_memory_size=10,
    exit_phrases=["that's all", "I'm done", "stop"]
)
```

### Accessing Memory
```python
# Get all memory
history = session.get_memory_for_llm()

# Format as context string
context = session.get_memory_context()

# Check if should exit
if session.should_exit(user_text):
    session.deactivate()
```

### Session Duration
```python
duration = session.get_session_duration()
if duration and duration > 300:  # 5 minutes
    # Auto-end long sessions
    session.deactivate()
```

## Performance Notes

- **Memory overhead**: Minimal (few KB per session)
- **LLM latency**: Increases slightly with longer memory
- **Optimal memory size**: 5-10 turns for most use cases
- **CPU usage**: No significant impact from memory management
