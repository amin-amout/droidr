"""
Conversational memory and session management for voice assistant.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class ConversationSession:
    """
    Manages conversational state and memory for the voice assistant.
    
    Attributes:
        active: Whether the session is currently active (listening without wake word)
        memory: List of conversation turns (user/assistant exchanges)
        max_memory_size: Maximum number of conversation turns to retain
        exit_phrases: Phrases that will end the session
        start_time: Timestamp when session became active
    """
    
    active: bool = False
    memory: List[Dict[str, str]] = field(default_factory=list)
    max_memory_size: int = 10
    exit_phrases: List[str] = field(default_factory=lambda: [
        "stop listening",
        "go to sleep",
        "exit",
        "goodbye",
        "bye",
        "stop"
    ])
    start_time: Optional[datetime] = None
    
    def activate(self) -> None:
        """
        Activate the session and reset memory.
        Called when wake word is detected.
        """
        self.active = True
        self.start_time = datetime.now()
        self.clear_memory()
        logger.info("Session activated")
    
    def deactivate(self) -> None:
        """
        Deactivate the session and clear memory.
        Called when user says exit phrase or session times out.
        """
        self.active = False
        self.start_time = None
        self.clear_memory()
        logger.info("Session deactivated")
    
    def add_to_memory(self, role: str, content: str) -> None:
        """
        Add a message to conversation memory.
        Automatically trims oldest messages if max size exceeded.
        
        Args:
            role: Either 'user' or 'assistant'
            content: The message content
        """
        self.memory.append({
            "role": role,
            "content": content
        })
        
        # Trim memory if it exceeds max size
        # Keep pairs of user/assistant exchanges
        if len(self.memory) > self.max_memory_size * 2:
            # Remove oldest pair
            self.memory = self.memory[2:]
        
        logger.debug(f"Added to memory [{role}]: {content[:50]}...")
    
    def clear_memory(self) -> None:
        """Clear all conversation memory."""
        self.memory.clear()
        logger.debug("Memory cleared")
    
    def get_memory_for_llm(self) -> List[Dict[str, str]]:
        """
        Get memory formatted for LLM consumption.
        
        Returns:
            List of message dicts with 'role' and 'content' keys
        """
        return self.memory.copy()
    
    def should_exit(self, text: str) -> bool:
        """
        Check if the given text matches any exit phrase.
        
        Args:
            text: User input text to check
            
        Returns:
            True if text matches an exit phrase
        """
        text_lower = text.lower().strip()
        for phrase in self.exit_phrases:
            if phrase.lower() in text_lower:
                logger.info(f"Exit phrase detected: {phrase}")
                return True
        return False
    
    def get_session_duration(self) -> Optional[float]:
        """
        Get the duration of current session in seconds.
        
        Returns:
            Duration in seconds, or None if session not active
        """
        if not self.active or not self.start_time:
            return None
        return (datetime.now() - self.start_time).total_seconds()
    
    def get_memory_context(self) -> str:
        """
        Get memory formatted as a string for context injection.
        
        Returns:
            Formatted conversation history string
        """
        if not self.memory:
            return ""
        
        context_parts = []
        for msg in self.memory:
            role = msg["role"].capitalize()
            content = msg["content"]
            context_parts.append(f"{role}: {content}")
        
        return "\n".join(context_parts)
