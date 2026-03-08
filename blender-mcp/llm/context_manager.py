#!/usr/bin/env python3
"""
Conversation Context Management for Blender MCP.

Manages conversation history, context awareness, and multi-turn interactions.
"""

import json
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import hashlib


class ContextType(Enum):
    """Types of context information."""
    SCENE = "scene"
    OBJECT = "object"
    ACTION = "action"
    USER_PREF = "user_pref"
    HISTORY = "history"


@dataclass
class ContextItem:
    """A single context item."""
    type: ContextType
    key: str
    value: Any
    timestamp: float = field(default_factory=time.time)
    expires: Optional[float] = None
    importance: int = 5  # 1-10 scale

    def is_expired(self) -> bool:
        """Check if context item is expired."""
        if self.expires is None:
            return False
        return time.time() > self.expires


@dataclass
class ConversationTurn:
    """A single turn in the conversation."""
    role: str  # 'user' or 'assistant'
    content: str
    timestamp: float = field(default_factory=time.time)
    tool_calls: List[Dict] = field(default_factory=list)
    tool_results: List[Dict] = field(default_factory=list)
    context_snapshot: Dict = field(default_factory=dict)


class ConversationContext:
    """Manages conversation context and history."""

    def __init__(self, max_history: int = 50, context_ttl: float = 3600):
        self.max_history = max_history
        self.context_ttl = context_ttl  # Time to live for context items
        
        self.turns: List[ConversationTurn] = []
        self.context_items: Dict[str, ContextItem] = {}
        self.session_id = self._generate_session_id()
        self.user_preferences: Dict[str, Any] = {}

    def _generate_session_id(self) -> str:
        """Generate a unique session ID."""
        return hashlib.md5(f"{time.time()}-{id(self)}".encode()).hexdigest()[:12]

    def add_turn(self, role: str, content: str, 
                 tool_calls: Optional[List[Dict]] = None,
                 tool_results: Optional[List[Dict]] = None):
        """Add a conversation turn."""
        turn = ConversationTurn(
            role=role,
            content=content,
            tool_calls=tool_calls or [],
            tool_results=tool_results or [],
            context_snapshot=self.get_context_summary()
        )
        self.turns.append(turn)

        # Trim history if needed
        if len(self.turns) > self.max_history:
            self.turns = self.turns[-self.max_history:]

    def set_context(self, key: str, value: Any, context_type: ContextType,
                   importance: int = 5, ttl: Optional[float] = None):
        """Set a context item."""
        self.context_items[key] = ContextItem(
            type=context_type,
            key=key,
            value=value,
            importance=importance,
            expires=time.time() + (ttl or self.context_ttl)
        )

    def get_context(self, key: str) -> Optional[Any]:
        """Get a context item by key."""
        item = self.context_items.get(key)
        if item and not item.is_expired():
            return item.value
        return None

    def remove_context(self, key: str):
        """Remove a context item."""
        if key in self.context_items:
            del self.context_items[key]

    def cleanup_expired(self):
        """Remove expired context items."""
        expired = [k for k, v in self.context_items.items() if v.is_expired()]
        for key in expired:
            del self.context_items[key]

    def get_context_summary(self) -> Dict:
        """Get a summary of current context."""
        self.cleanup_expired()
        return {
            "session_id": self.session_id,
            "turn_count": len(self.turns),
            "context_count": len(self.context_items),
            "recent_objects": self.get_recent_objects(),
            "last_action": self.get_last_action()
        }

    def get_recent_objects(self, limit: int = 10) -> List[str]:
        """Get names of recently created/modified objects."""
        objects = []
        for turn in reversed(self.turns):
            for tool_call in turn.tool_calls:
                if tool_call.get("name") in ("create_object", "modify_object"):
                    name = tool_call.get("params", {}).get("name")
                    if name and name not in objects:
                        objects.append(name)
                        if len(objects) >= limit:
                            return objects
        return objects

    def get_last_action(self) -> Optional[str]:
        """Get the last action performed."""
        for turn in reversed(self.turns):
            if turn.tool_calls:
                return turn.tool_calls[-1].get("name")
        return None

    def get_history_for_llm(self, include_context: bool = True) -> List[Dict]:
        """Get conversation history formatted for LLM."""
        messages = []

        # Add context summary as system message
        if include_context:
            context_summary = self.get_context_summary()
            messages.append({
                "role": "system",
                "content": f"""Current session context:
- Session ID: {context_summary['session_id']}
- Turns so far: {context_summary['turn_count']}
- Recent objects: {', '.join(context_summary['recent_objects']) or 'none'}
- Last action: {context_summary['last_action'] or 'none'}

Refer to these objects by name when the user says 'it', 'that', 'the object', etc."""
            })

        # Add conversation turns
        for turn in self.turns:
            messages.append({
                "role": turn.role,
                "content": turn.content
            })

            # Include tool results for assistant turns
            if turn.role == "assistant" and turn.tool_results:
                tool_results_str = json.dumps(turn.tool_results, indent=2)
                messages.append({
                    "role": "system",
                    "content": f"Tool execution results:\n{tool_results_str}"
                })

        return messages

    def resolve_reference(self, reference: str) -> Optional[str]:
        """
        Resolve a reference like 'it', 'that', 'the cube' to an object name.
        
        Args:
            reference: The reference to resolve
            
        Returns:
            The resolved object name or None
        """
        reference = reference.lower().strip()

        # Direct object name
        if reference in self.get_recent_objects():
            return reference

        # Pronoun resolution - get most recent object
        if reference in ("it", "that", "the object", "this"):
            recent = self.get_recent_objects(limit=1)
            return recent[0] if recent else None

        # Type-based resolution
        for obj in self.get_recent_objects():
            if reference in obj.lower():
                return obj

        return None

    def set_user_preference(self, key: str, value: Any):
        """Set a user preference."""
        self.user_preferences[key] = value
        self.set_context(f"pref_{key}", value, ContextType.USER_PREF, importance=8)

    def get_user_preference(self, key: str, default: Any = None) -> Any:
        """Get a user preference."""
        return self.user_preferences.get(key, default)

    def export_session(self) -> Dict:
        """Export session data."""
        return {
            "session_id": self.session_id,
            "timestamp": time.time(),
            "turns": [
                {
                    "role": t.role,
                    "content": t.content,
                    "tool_calls": t.tool_calls,
                    "tool_results": t.tool_results
                }
                for t in self.turns
            ],
            "context_items": {
                k: {"type": v.type.value, "value": v.value}
                for k, v in self.context_items.items()
            },
            "user_preferences": self.user_preferences
        }

    def import_session(self, data: Dict):
        """Import session data."""
        self.session_id = data.get("session_id", self._generate_session_id())
        
        self.turns = [
            ConversationTurn(
                role=t["role"],
                content=t["content"],
                tool_calls=t.get("tool_calls", []),
                tool_results=t.get("tool_results", [])
            )
            for t in data.get("turns", [])
        ]

        for key, item_data in data.get("context_items", {}).items():
            self.context_items[key] = ContextItem(
                type=ContextType(item_data.get("type", "object")),
                key=key,
                value=item_data["value"]
            )

        self.user_preferences = data.get("user_preferences", {})


class ContextAwareAssistant:
    """LLM assistant with conversation context awareness."""

    def __init__(self, llm_manager, context: ConversationContext, 
                 blender_tools=None):
        self.llm = llm_manager
        self.context = context
        self.blender_tools = blender_tools

    def process_message(self, user_message: str) -> Dict:
        """
        Process a user message with full context awareness.
        
        Returns:
            Dict with response and any tool executions
        """
        # Resolve references in the message
        resolved_message = self._resolve_references(user_message)

        # Get conversation history for LLM
        messages = self.context.get_history_for_llm()
        messages.append({"role": "user", "content": resolved_message})

        # Get response from LLM
        response = self.llm.chat(resolved_message, execute_tools=True)

        # Add turn to context
        self.context.add_turn(
            role="user",
            content=user_message
        )
        self.context.add_turn(
            role="assistant",
            content=response.content,
            tool_calls=response.tool_calls
        )

        # Update context with any new objects
        self._update_context_from_response(response)

        return {
            "response": response.content,
            "tool_calls": response.tool_calls,
            "context": self.context.get_context_summary()
        }

    def _resolve_references(self, message: str) -> str:
        """Resolve references in the message."""
        resolved = message

        # Common reference patterns
        reference_words = ["it", "that", "this", "the object", "them"]
        words = resolved.split()

        for i, word in enumerate(words):
            if word.lower() in reference_words:
                resolved_obj = self.context.resolve_reference(word.lower())
                if resolved_obj:
                    words[i] = f"'{resolved_obj}'"

        return " ".join(words)

    def _update_context_from_response(self, response):
        """Update context based on tool execution results."""
        for tool_call in response.tool_calls:
            if tool_call.get("name") == "create_object":
                name = tool_call.get("input", {}).get("name")
                if name:
                    self.context.set_context(
                        f"object_{name}",
                        tool_call.get("input"),
                        ContextType.OBJECT,
                        importance=7
                    )


# Global context instance
_global_context: Optional[ConversationContext] = None


def get_context() -> ConversationContext:
    """Get the global context instance."""
    global _global_context
    if _global_context is None:
        _global_context = ConversationContext()
    return _global_context


def reset_context():
    """Reset the global context."""
    global _global_context
    _global_context = ConversationContext()
