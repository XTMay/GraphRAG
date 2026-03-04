"""
Conversation Memory
===================

Manage conversation history across multiple sessions.

Teaching Points:
- Memory types: Buffer (full), Window (last N turns), Summary
- Session management: each user/conversation gets its own memory
- Sliding window prevents context overflow in long conversations
- Memory enables multi-turn interactions ("adjust that" → knows what "that" is)
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Message:
    """A single message in a conversation."""
    role: str  # "user" or "assistant"
    content: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


class ConversationMemory:
    """
    In-memory conversation store with sliding window.

    Usage:
        memory = ConversationMemory(max_turns=10)

        # Add messages
        memory.add_message("session-1", "user", "打开客厅灯")
        memory.add_message("session-1", "assistant", "好的，已为您打开客厅灯。")

        # Get history
        history = memory.get_history("session-1")

        # Get formatted context for LLM
        context = memory.get_context_string("session-1")

    Teaching Points:
        - max_turns limits memory to prevent token overflow
        - Each session is independent (multi-user support)
        - get_context_string() formats history for LLM consumption
    """

    def __init__(self, max_turns: int = 10):
        """
        Args:
            max_turns: Maximum number of conversation turns to keep.
                       One turn = one user message + one assistant response.
        """
        self.max_turns = max_turns
        # session_id -> list of Messages
        self._sessions: dict[str, list[Message]] = {}

    def add_message(self, session_id: str, role: str, content: str) -> None:
        """
        Add a message to a session's history.

        Args:
            session_id: Unique session identifier
            role: "user" or "assistant"
            content: Message text
        """
        if session_id not in self._sessions:
            self._sessions[session_id] = []

        self._sessions[session_id].append(
            Message(role=role, content=content)
        )

        # Apply sliding window (max_turns * 2 because each turn has 2 messages)
        max_messages = self.max_turns * 2
        if len(self._sessions[session_id]) > max_messages:
            self._sessions[session_id] = self._sessions[session_id][-max_messages:]

    def get_history(self, session_id: str) -> list[Message]:
        """
        Get conversation history for a session.

        Args:
            session_id: Session identifier

        Returns:
            List of Message objects (may be empty)
        """
        return self._sessions.get(session_id, [])

    def get_context_string(self, session_id: str) -> str:
        """
        Format conversation history as a string for LLM context.

        Args:
            session_id: Session identifier

        Returns:
            Formatted conversation history string.
            Returns empty string if no history.

        Teaching Point:
            The format matters for LLM understanding.
            We use a clear role-based format:
                User: message
                Assistant: message
        """
        history = self.get_history(session_id)
        if not history:
            return ""

        lines = ["[对话历史]"]
        for msg in history:
            role_label = "用户" if msg.role == "user" else "助手"
            lines.append(f"{role_label}: {msg.content}")

        return "\n".join(lines)

    def clear_session(self, session_id: str) -> None:
        """Clear all messages for a session."""
        self._sessions.pop(session_id, None)

    def get_all_sessions(self) -> list[str]:
        """Get all active session IDs."""
        return list(self._sessions.keys())

    def get_session_length(self, session_id: str) -> int:
        """Get number of messages in a session."""
        return len(self._sessions.get(session_id, []))


# Singleton instance for shared use
_default_memory: Optional[ConversationMemory] = None


def get_memory() -> ConversationMemory:
    """Get the shared memory instance."""
    global _default_memory
    if _default_memory is None:
        _default_memory = ConversationMemory()
    return _default_memory


if __name__ == "__main__":
    print("Testing ConversationMemory")
    print("=" * 50)

    memory = ConversationMemory(max_turns=3)

    # Simulate a conversation
    sid = "test-session"
    memory.add_message(sid, "user", "客厅有什么设备？")
    memory.add_message(sid, "assistant", "客厅有：吸顶灯、落地灯、智能电视、音箱、窗帘。")
    memory.add_message(sid, "user", "把灯调暗一点")
    memory.add_message(sid, "assistant", "好的，已将客厅吸顶灯调至20%亮度，落地灯调至30%亮度。")

    print("\nHistory:")
    for msg in memory.get_history(sid):
        print(f"  [{msg.role}] {msg.content}")

    print("\nContext String:")
    print(memory.get_context_string(sid))

    print(f"\nSession length: {memory.get_session_length(sid)} messages")
