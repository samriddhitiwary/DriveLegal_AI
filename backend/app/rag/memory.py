from collections import deque
from typing import Dict, List, Tuple
from app.config.settings import settings
from app.utils.logger import logger

class MemoryManager:
    """
    Manages session-based conversation histories in-memory.
    Keeps a sliding window of recent user and assistant interactions.
    """
    def __init__(self, window_size: int = 10):
        # Maps conversation_id -> deque of Tuple[user_message, assistant_message]
        # We store up to window_size interactions
        self.conversations: Dict[str, deque] = {}
        self.window_size = window_size

    def add_interaction(self, conversation_id: str, user_msg: str, assistant_msg: str):
        if not conversation_id:
            return
            
        if conversation_id not in self.conversations:
            self.conversations[conversation_id] = deque(maxlen=self.window_size)
            
        self.conversations[conversation_id].append((user_msg, assistant_msg))
        logger.info(
            f"Added interaction for conversation '{conversation_id}'. "
            f"Current history length: {len(self.conversations[conversation_id])}/{self.window_size}"
        )

    def get_history(self, conversation_id: str) -> List[Tuple[str, str]]:
        if not conversation_id or conversation_id not in self.conversations:
            return []
        return list(self.conversations[conversation_id])

    def get_history_string(self, conversation_id: str) -> str:
        history = self.get_history(conversation_id)
        if not history:
            return ""
            
        lines = []
        for user_msg, assistant_msg in history:
            lines.append(f"User: {user_msg}")
            lines.append(f"Assistant: {assistant_msg}")
        return "\n".join(lines)

    def clear_history(self, conversation_id: str):
        if conversation_id in self.conversations:
            self.conversations[conversation_id].clear()
            logger.info(f"Cleared history for conversation '{conversation_id}'")

# Global singleton memory store
memory_store = MemoryManager(window_size=settings.memory_window_size)
