"""
Local Intent Detection and Handling Module

This module intercepts simple user queries (time, weather) and handles them
locally without calling the LLM, providing faster responses.
"""

import re
from datetime import datetime
from typing import Optional


def detect_local_intent(text: str) -> Optional[dict]:
    """
    Detect if user text matches a local intent (time or weather).
    
    Args:
        text: The transcribed user text from STT
        
    Returns:
        Dictionary with intent details, or None if no local intent detected
    """
    text_lower = text.lower().strip()
    
    # Time intent patterns
    time_patterns = [
        r'\b(what|tell me|what\'?s)\s+(the\s+)?time\b',
        r'\bcurrent time\b',
        r'\btime now\b',
        r'\bwhat time is it\b',
    ]
    
    for pattern in time_patterns:
        if re.search(pattern, text_lower):
            return {"intent": "time.now"}
    
    # Weather intent patterns
    weather_patterns = [
        r'\b(what\'?s|how\'?s|tell me)\s+(the\s+)?weather\b',
        r'\bweather (today|now|currently)\b',
        r'\bcurrent weather\b',
        r'\bis it raining\b',
        r'\bweather in\b',
    ]
    
    for pattern in weather_patterns:
        if re.search(pattern, text_lower):
            # Try to extract location
            location = extract_location(text_lower)
            return {
                "intent": "weather.current",
                "location": location
            }
    
    return None


def extract_location(text: str) -> Optional[str]:
    """
    Extract location from user text using simple regex.
    
    Args:
        text: User text (lowercase)
        
    Returns:
        Location string or None
    """
    # Pattern: "weather in <location>"
    match = re.search(r'\b(?:weather|temperature|rain)\s+(?:in|at|for)\s+([a-zA-Z\s,]+?)(?:\?|$|\b(?:today|now|please))', text)
    if match:
        location = match.group(1).strip()
        return location.title()  # Capitalize location name
    
    return None


def get_current_time() -> str:
    """
    Get current time and format it as a natural language response.
    
    Returns:
        Natural language time string
    """
    now = datetime.now()
    time_str = now.strftime("%I:%M %p")
    # Remove leading zero from hour (e.g., "05:42 PM" -> "5:42 PM")
    if time_str[0] == '0':
        time_str = time_str[1:]
    
    return f"It is {time_str}."


def get_weather(location: Optional[str] = None) -> str:
    """
    Get weather information for a location.
    
    Currently returns a placeholder. Will be replaced with real API integration.
    
    Args:
        location: Location name, or None for default location
        
    Returns:
        Natural language weather description
    """
    # Always use Houilles, France regardless of location parameter
    location = "Houilles, 78800, France"
    
    # TODO: Replace with real weather API call
    # For now, return a realistic placeholder
    return f"The weather in {location} is currently cloudy with a temperature of 12 degrees Celsius. There's a slight breeze from the west."


def handle_local_intent(intent_data: dict) -> str:
    """
    Execute a local intent and generate a response.
    
    Args:
        intent_data: Dictionary returned by detect_local_intent()
        
    Returns:
        Natural language response text ready for TTS
    """
    intent_type = intent_data.get("intent")
    
    if intent_type == "time.now":
        return get_current_time()
    
    elif intent_type == "weather.current":
        location = intent_data.get("location")
        return get_weather(location)
    
    else:
        # Fallback for unknown intent types
        return "I'm not sure how to handle that request."


# Example usage for testing
if __name__ == "__main__":
    # Test time intent
    test_queries = [
        "what time is it",
        "tell me the time",
        "what's the weather",
        "weather in Paris",
        "how's the weather today",
        "is it raining",
        "hello there",  # Should return None
    ]
    
    print("=== Intent Detection Tests ===\n")
    for query in test_queries:
        intent = detect_local_intent(query)
        print(f"Query: '{query}'")
        print(f"Intent: {intent}")
        
        if intent:
            response = handle_local_intent(intent)
            print(f"Response: {response}")
        
        print()
