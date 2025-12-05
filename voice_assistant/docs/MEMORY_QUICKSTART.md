# Memory Feature Quick Reference

## Quick Start

1. **Start the assistant:**
   ```bash
   python3.10 main.py
   ```

2. **Activate session:**
   - Say: "Hey Jarvis"
   - Assistant responds and enters active mode

3. **Have a conversation:**
   - Speak naturally without repeating wake word
   - Assistant remembers context from earlier in conversation

4. **End session:**
   - Say: "goodbye" or "stop listening"
   - Memory clears, assistant returns to dormant mode

## Key Concepts

### Session States
- **Dormant**: 🔴 Waiting for wake word
- **Active**: 🟢 Continuous listening with memory

### Memory Behavior
- ✅ Remembers conversation within active session
- ✅ Automatically trims to configured size
- ✅ Clears when session ends
- ❌ Does NOT persist across sessions

## Common Commands

| Command | Effect |
|---------|--------|
| "Hey Jarvis" | Activate session |
| "goodbye" | End session |
| "stop listening" | End session |
| "go to sleep" | End session |
| "exit" | End session |

## Configuration Quick Edit

**File:** `config.yaml`

```yaml
session:
  max_memory_turns: 10  # Change this number
  exit_phrases:
    - "your custom phrase"  # Add custom phrases
```

## Testing Memory

```bash
# Run test script
python test_memory.py

# Expected output: All tests should pass ✓
```

## Example Conversations

### Multi-turn Math
```
👤 "Hey Jarvis"
🤖 "Yes? How can I help you?"

👤 "What's 10 plus 5?"
🤖 "That's 15."

👤 "Multiply that by 3"
🤖 "45."  ← Remembers "that" = 15

👤 "Goodbye"
🤖 "Goodbye! Let me know if you need anything."
```

### Context Retention
```
👤 "Hey Jarvis"
🤖 "Yes? How can I help you?"

👤 "I have a meeting at 2pm"
🤖 "Noted. Is there anything else you need?"

👤 "What time is my meeting?"
🤖 "Your meeting is at 2pm."  ← Remembers from earlier

👤 "Stop listening"
🤖 "Goodbye! Let me know if you need anything."
```

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Wake word not detected | Check microphone, verify model file |
| Can't exit session | Say exact phrase: "goodbye" or "stop listening" |
| No memory/context | Check config.yaml `max_memory_turns` > 0 |
| Session ends unexpectedly | Avoid words like "stop", "exit" in sentences |

## Files Modified

- ✅ `core/session.py` - Session management class
- ✅ `core/pipeline.py` - Main event loop with sessions
- ✅ `config.yaml` - Session configuration
- ✅ `test_memory.py` - Test suite
- ✅ `docs/memory_feature.md` - Full documentation

## Next Steps

1. Test the feature: `python3.10 main.py`
2. Try multi-turn conversations
3. Customize exit phrases in config.yaml
4. Adjust memory size as needed
5. Check logs for debugging: `INFO` level

## Memory Limits

| Turns | Total Messages | Typical Use Case |
|-------|---------------|------------------|
| 5 | 10 | Quick interactions |
| 10 | 20 | **Default - recommended** |
| 20 | 40 | Extended conversations |
| 50+ | 100+ | Not recommended (slow) |

## Performance Tips

✅ **Do:**
- Use 5-15 turns for best performance
- Clear sessions when done
- Keep responses concise

❌ **Don't:**
- Set memory too high (>20 turns)
- Leave sessions active indefinitely
- Store sensitive data in memory
