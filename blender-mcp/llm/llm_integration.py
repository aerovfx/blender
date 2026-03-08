#!/usr/bin/env python3
"""
LLM Integration Module for Blender MCP.

Provides integration with:
- Anthropic Claude
- OpenAI GPT-4
- Local LLMs (via Ollama, etc.)
"""

import json
import os
from typing import Optional, List, Dict, Any, Generator
from dataclasses import dataclass, field
from abc import ABC, abstractmethod


@dataclass
class LLMMessage:
    """A message in the conversation."""
    role: str  # 'user', 'assistant', 'system'
    content: str


@dataclass
class LLMResponse:
    """Response from an LLM."""
    content: str
    tool_calls: List[Dict[str, Any]] = field(default_factory=list)
    raw_response: Any = None
    model: str = ""
    usage: Dict[str, int] = field(default_factory=dict)


class BaseLLMProvider(ABC):
    """Abstract base class for LLM providers."""

    @abstractmethod
    def chat(self, messages: List[LLMMessage], tools: Optional[List[Dict]] = None) -> LLMResponse:
        """Send a chat message and get response."""
        pass

    @abstractmethod
    def chat_stream(self, messages: List[LLMMessage], tools: Optional[List[Dict]] = None) -> Generator[str, None, None]:
        """Stream chat response."""
        pass


class ClaudeProvider(BaseLLMProvider):
    """Anthropic Claude provider."""

    def __init__(self, api_key: Optional[str] = None, model: str = "claude-3-5-sonnet-20241022"):
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        self.model = model
        self.base_url = "https://api.anthropic.com/v1/messages"

        if not self.api_key:
            raise ValueError("Anthropic API key not provided")

    def chat(self, messages: List[LLMMessage], tools: Optional[List[Dict]] = None) -> LLMResponse:
        """Send message to Claude."""
        try:
            import anthropic
        except ImportError:
            raise ImportError("Install anthropic-sdk: pip install anthropic")

        client = anthropic.Anthropic(api_key=self.api_key)

        # Convert messages to Claude format
        system_message = ""
        claude_messages = []

        for msg in messages:
            if msg.role == "system":
                system_message = msg.content
            else:
                claude_messages.append({
                    "role": msg.role,
                    "content": msg.content
                })

        # Build request
        request = {
            "model": self.model,
            "max_tokens": 4096,
            "messages": claude_messages,
        }

        if system_message:
            request["system"] = system_message

        if tools:
            request["tools"] = tools

        # Send request
        response = client.messages.create(**request)

        # Parse response
        content = ""
        tool_calls = []

        for block in response.content:
            if block.type == "text":
                content += block.text
            elif block.type == "tool_use":
                tool_calls.append({
                    "id": block.id,
                    "name": block.name,
                    "input": block.input
                })

        return LLMResponse(
            content=content,
            tool_calls=tool_calls,
            raw_response=response,
            model=self.model,
            usage={
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens
            }
        )

    def chat_stream(self, messages: List[LLMMessage], tools: Optional[List[Dict]] = None) -> Generator[str, None, None]:
        """Stream response from Claude."""
        try:
            import anthropic
        except ImportError:
            raise ImportError("Install anthropic-sdk: pip install anthropic")

        client = anthropic.Anthropic(api_key=self.api_key)

        # Convert messages
        system_message = ""
        claude_messages = []

        for msg in messages:
            if msg.role == "system":
                system_message = msg.content
            else:
                claude_messages.append({
                    "role": msg.role,
                    "content": msg.content
                })

        request = {
            "model": self.model,
            "max_tokens": 4096,
            "messages": claude_messages,
        }

        if system_message:
            request["system"] = system_message

        if tools:
            request["tools"] = tools

        # Stream
        with client.messages.stream(**request) as stream:
            for text in stream.text_stream:
                yield text


class GPTProvider(BaseLLMProvider):
    """OpenAI GPT provider."""

    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4-turbo-preview"):
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self.model = model

        if not self.api_key:
            raise ValueError("OpenAI API key not provided")

    def chat(self, messages: List[LLMMessage], tools: Optional[List[Dict]] = None) -> LLMResponse:
        """Send message to GPT."""
        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError("Install openai: pip install openai")

        client = OpenAI(api_key=self.api_key)

        # Convert messages
        openai_messages = []
        for msg in messages:
            openai_messages.append({
                "role": msg.role,
                "content": msg.content
            })

        # Build request
        request = {
            "model": self.model,
            "messages": openai_messages,
        }

        if tools:
            request["tools"] = [{"type": "function", "function": t} for t in tools]
            request["tool_choice"] = "auto"

        # Send request
        response = client.chat.completions.create(**request)

        # Parse response
        choice = response.choices[0]
        content = choice.message.content or ""
        tool_calls = []

        if choice.message.tool_calls:
            for tc in choice.message.tool_calls:
                tool_calls.append({
                    "id": tc.id,
                    "name": tc.function.name,
                    "arguments": json.loads(tc.function.arguments)
                })

        return LLMResponse(
            content=content,
            tool_calls=tool_calls,
            raw_response=response,
            model=self.model,
            usage={
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens
            }
        )

    def chat_stream(self, messages: List[LLMMessage], tools: Optional[List[Dict]] = None) -> Generator[str, None, None]:
        """Stream response from GPT."""
        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError("Install openai: pip install openai")

        client = OpenAI(api_key=self.api_key)

        openai_messages = [{"role": m.role, "content": m.content} for m in messages]

        request = {
            "model": self.model,
            "messages": openai_messages,
            "stream": True
        }

        if tools:
            request["tools"] = [{"type": "function", "function": t} for t in tools]

        stream = client.chat.completions.create(**request)

        for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content


class OllamaProvider(BaseLLMProvider):
    """Local LLM provider via Ollama."""

    def __init__(self, model: str = "llama2", host: str = "http://localhost:11434"):
        self.model = model
        self.host = host

    def chat(self, messages: List[LLMMessage], tools: Optional[List[Dict]] = None) -> LLMResponse:
        """Send message to local LLM via Ollama."""
        try:
            import requests
        except ImportError:
            raise ImportError("Install requests: pip install requests")

        # Convert messages
        ollama_messages = []
        for msg in messages:
            ollama_messages.append({
                "role": msg.role,
                "content": msg.content
            })

        request = {
            "model": self.model,
            "messages": ollama_messages,
            "stream": False
        }

        response = requests.post(f"{self.host}/api/chat", json=request)
        data = response.json()

        return LLMResponse(
            content=data.get("message", {}).get("content", ""),
            model=self.model,
            usage=data.get("prompt_eval_count", 0)
        )

    def chat_stream(self, messages: List[LLMMessage], tools: Optional[List[Dict]] = None) -> Generator[str, None, None]:
        """Stream response from local LLM."""
        try:
            import requests
        except ImportError:
            raise ImportError("Install requests: pip install requests")

        ollama_messages = [{"role": m.role, "content": m.content} for m in messages]

        request = {
            "model": self.model,
            "messages": ollama_messages,
            "stream": True
        }

        response = requests.post(f"{self.host}/api/chat", json=request, stream=True)

        for line in response.iter_lines():
            if line:
                data = json.loads(line)
                if content := data.get("message", {}).get("content"):
                    yield content


class LLMManager:
    """Manager for LLM providers and conversations."""

    def __init__(self, provider: Optional[str] = None, **kwargs):
        """
        Initialize LLM manager.

        Args:
            provider: Provider name ('claude', 'gpt', 'ollama')
            **kwargs: Provider-specific arguments
        """
        self.provider_name = provider or "claude"
        self.provider = self._create_provider(provider, **kwargs)
        self.messages: List[LLMMessage] = []
        self.system_message: Optional[str] = None
        self.tools: List[Dict] = []

    def _create_provider(self, provider: Optional[str], **kwargs) -> BaseLLMProvider:
        """Create the appropriate provider."""
        provider = (provider or "claude").lower()

        if provider == "claude":
            return ClaudeProvider(**kwargs)
        elif provider in ("gpt", "openai"):
            return GPTProvider(**kwargs)
        elif provider == "ollama":
            return OllamaProvider(**kwargs)
        else:
            raise ValueError(f"Unknown provider: {provider}")

    def set_system_message(self, message: str):
        """Set the system message for the conversation."""
        self.system_message = message

    def set_tools(self, tools: List[Dict]):
        """Set available tools for the LLM."""
        self.tools = tools

    def add_message(self, role: str, content: str):
        """Add a message to the conversation history."""
        self.messages.append(LLMMessage(role=role, content=content))

    def clear_history(self):
        """Clear conversation history."""
        self.messages = []

    def get_messages(self) -> List[LLMMessage]:
        """Get all messages including system message."""
        result = []
        if self.system_message:
            result.append(LLMMessage(role="system", content=self.system_message))
        result.extend(self.messages)
        return result

    def chat(self, user_message: str, execute_tools: bool = True, max_iterations: int = 5) -> LLMResponse:
        """
        Send a message and get response, optionally executing tools.

        Args:
            user_message: User's message
            execute_tools: Whether to execute tool calls
            max_iterations: Maximum tool execution iterations

        Returns:
            Final LLM response
        """
        self.add_message("user", user_message)

        iteration = 0
        final_content = ""

        while iteration < max_iterations:
            # Get response from LLM
            response = self.provider.chat(
                messages=self.get_messages(),
                tools=self.tools if self.tools else None
            )

            # Add assistant response to history
            self.add_message("assistant", response.content)

            # Check for tool calls
            if not response.tool_calls or not execute_tools:
                final_content = response.content
                break

            # Execute tool calls
            for tool_call in response.tool_calls:
                tool_result = self._execute_tool(tool_call)

                # Add tool result to conversation
                self.add_message("user", json.dumps({
                    "tool_call_id": tool_call.get("id"),
                    "result": tool_result
                }))

            iteration += 1

        return LLMResponse(
            content=final_content,
            model=response.model,
            usage=response.usage
        )

    def _execute_tool(self, tool_call: Dict) -> Dict:
        """Execute a tool call and return result."""
        # This would integrate with the Blender tools
        # For now, return a placeholder
        return {
            "status": "executed",
            "tool": tool_call.get("name"),
            "arguments": tool_call.get("input") or tool_call.get("arguments")
        }

    def chat_stream(self, user_message: str) -> Generator[str, None, None]:
        """Stream response from LLM."""
        self.add_message("user", user_message)

        for chunk in self.provider.chat_stream(
            messages=self.get_messages(),
            tools=self.tools if self.tools else None
        ):
            yield chunk

        # Add accumulated response to history
        # (Note: streaming doesn't give us the full response easily)


# ============================================================================
# Blender-specific LLM Integration
# ============================================================================

class BlenderLLMAssistant:
    """LLM assistant specifically for Blender operations."""

    def __init__(self, llm_manager: LLMManager, blender_tools: Any = None):
        """
        Initialize Blender LLM assistant.

        Args:
            llm_manager: LLM manager instance
            blender_tools: Blender tools instance for execution
        """
        self.llm = llm_manager
        self.blender_tools = blender_tools
        self._setup_system_message()
        self._setup_tools()

    def _setup_system_message(self):
        """Setup system message for Blender assistance."""
        system_message = """You are a Blender 3D automation assistant. You help users create 3D content by translating natural language into Blender operations.

When a user asks you to create or modify 3D content:
1. Understand what they want to create
2. Break it down into specific Blender operations
3. Use the available tools to execute those operations
4. Confirm what was created

Available operations include:
- Creating primitives (cube, sphere, cylinder, cone, torus, plane)
- Creating lights (point, sun, spot, area)
- Creating cameras
- Modifying objects (move, rotate, scale)
- Applying materials
- Creating armatures and rigs
- Animation keyframing
- Rendering and export

Always be specific about what you're creating and where. Use appropriate coordinates and dimensions."""

        self.llm.set_system_message(system_message)

    def _setup_tools(self):
        """Setup tool definitions for the LLM."""
        tools = [
            {
                "name": "create_object",
                "description": "Create a 3D object in the scene",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "type": {
                            "type": "string",
                            "enum": ["cube", "sphere", "cylinder", "cone", "torus", "plane", "light", "camera"],
                            "description": "Type of object"
                        },
                        "location": {
                            "type": "array",
                            "items": {"type": "number"},
                            "description": "[x, y, z] position"
                        },
                        "name": {"type": "string", "description": "Object name"}
                    },
                    "required": ["type"]
                }
            },
            {
                "name": "modify_object",
                "description": "Modify an object's transform",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "description": "Object name"},
                        "location": {"type": "array", "items": {"type": "number"}},
                        "rotation": {"type": "array", "items": {"type": "number"}},
                        "scale": {"type": "array", "items": {"type": "number"}}
                    },
                    "required": ["name"]
                }
            },
            {
                "name": "get_scene_info",
                "description": "Get information about the current scene"
            },
            {
                "name": "set_material",
                "description": "Apply a material to an object",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "object_name": {"type": "string"},
                        "material_name": {"type": "string"},
                        "color": {"type": "array", "items": {"type": "number"}}
                    },
                    "required": ["object_name", "material_name"]
                }
            },
            {
                "name": "create_keyframe",
                "description": "Create an animation keyframe",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "object_name": {"type": "string"},
                        "frame": {"type": "integer"},
                        "location": {"type": "array", "items": {"type": "number"}}
                    },
                    "required": ["object_name", "frame"]
                }
            },
            {
                "name": "create_armature",
                "description": "Create a rig/armature for animation",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "rig_type": {"type": "string", "enum": ["simple", "humanoid"]}
                    },
                    "required": ["name"]
                }
            }
        ]

        self.llm.set_tools(tools)

    def execute(self, user_request: str) -> str:
        """
        Execute a user request.

        Args:
            user_request: Natural language request

        Returns:
            Response describing what was done
        """
        response = self.llm.chat(user_request, execute_tools=True)
        return response.content

    def create_scene_from_description(self, description: str) -> Dict:
        """
        Create a complete scene from a text description.

        Args:
            description: Description of the scene to create

        Returns:
            Information about created objects
        """
        # Parse the description and create objects
        response = self.llm.chat(f"""
Create a Blender scene based on this description: {description}

Break this down into specific create_object, modify_object, and set_material calls.
Execute each tool call to build the scene.
""")

        return {
            "description": description,
            "response": response.content
        }


# ============================================================================
# Factory Functions
# ============================================================================

def create_llm(provider: str = "claude", **kwargs) -> LLMManager:
    """Create an LLM manager instance."""
    return LLMManager(provider=provider, **kwargs)


def create_blender_assistant(provider: str = "claude", **kwargs) -> BlenderLLMAssistant:
    """Create a Blender LLM assistant."""
    llm = create_llm(provider=provider, **kwargs)
    return BlenderLLMAssistant(llm)
