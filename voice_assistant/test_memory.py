"""
Test script for conversational memory feature.
This demonstrates how the session memory works.
"""

from core.session import ConversationSession


def test_memory_management():
    """Test basic memory operations."""
    print("=== Testing ConversationSession ===\n")
    
    # Create session
    session = ConversationSession(max_memory_size=3)
    
    # Test activation
    print("1. Testing session activation:")
    assert not session.active
    session.activate()
    assert session.active
    print("   ✓ Session activated\n")
    
    # Test adding to memory
    print("2. Testing memory storage:")
    session.add_to_memory("user", "What's the weather?")
    session.add_to_memory("assistant", "It's sunny and 75 degrees.")
    session.add_to_memory("user", "Should I bring an umbrella?")
    session.add_to_memory("assistant", "No, you won't need one today.")
    
    memory = session.get_memory_for_llm()
    print(f"   Memory has {len(memory)} entries")
    for msg in memory:
        print(f"   - {msg['role']}: {msg['content']}")
    print()
    
    # Test memory trimming
    print("3. Testing memory trimming (max=3 turns = 6 messages):")
    session.add_to_memory("user", "What about tomorrow?")
    session.add_to_memory("assistant", "Tomorrow will be rainy.")
    session.add_to_memory("user", "Thanks!")
    session.add_to_memory("assistant", "You're welcome!")
    
    memory = session.get_memory_for_llm()
    print(f"   Memory trimmed to {len(memory)} entries")
    for msg in memory:
        print(f"   - {msg['role']}: {msg['content']}")
    assert len(memory) <= 6, "Memory should be trimmed to max size"
    print("   ✓ Old messages removed\n")
    
    # Test exit phrase detection
    print("4. Testing exit phrase detection:")
    test_phrases = [
        ("stop listening", True),
        ("please go to sleep", True),
        ("what's the time", False),
        ("goodbye for now", True),
        ("I need help", False)
    ]
    
    for phrase, should_exit in test_phrases:
        result = session.should_exit(phrase)
        status = "✓" if result == should_exit else "✗"
        print(f"   {status} '{phrase}' -> exit={result}")
    print()
    
    # Test context formatting
    print("5. Testing context formatting:")
    context = session.get_memory_context()
    print("   Formatted context:")
    print("   " + "\n   ".join(context.split("\n")))
    print()
    
    # Test deactivation
    print("6. Testing session deactivation:")
    session.deactivate()
    assert not session.active
    assert len(session.memory) == 0
    print("   ✓ Session deactivated and memory cleared\n")
    
    print("=== All tests passed! ===")


def demo_conversation_flow():
    """Demonstrate a typical conversation flow."""
    print("\n=== Conversation Flow Demo ===\n")
    
    session = ConversationSession(max_memory_size=5)
    
    conversation = [
        ("user", "Hey, what's your name?"),
        ("assistant", "I'm Jarvis, your voice assistant."),
        ("user", "Nice to meet you. Can you help me?"),
        ("assistant", "Of course! What do you need help with?"),
        ("user", "What's 5 plus 8?"),
        ("assistant", "That's 13."),
        ("user", "Thanks! And what was the first question I asked you?"),
        ("assistant", "You asked what my name is."),
    ]
    
    print("Simulating conversation:\n")
    session.activate()
    
    for role, content in conversation:
        session.add_to_memory(role, content)
        print(f"{role.upper()}: {content}")
    
    print(f"\n✓ Conversation stored with {len(session.get_memory_for_llm())} turns")
    print(f"✓ Session duration: {session.get_session_duration():.2f} seconds")
    
    print("\nTesting exit:")
    if session.should_exit("goodbye"):
        session.deactivate()
        print("✓ Session ended")


if __name__ == "__main__":
    test_memory_management()
    demo_conversation_flow()
