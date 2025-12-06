# core package initialization
from .audio import AudioManager
from .session import ConversationSession
from .speaker_id import SpeakerIdentifier
from .intents import detect_local_intent, handle_local_intent

__all__ = [
    "AudioManager",
    "ConversationSession",
    "SpeakerIdentifier",
    "detect_local_intent",
    "handle_local_intent",
]