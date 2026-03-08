#!/usr/bin/env python3
"""
Security module for Blender MCP Server.

Provides authentication, rate limiting, and access control.
"""

import time
import hashlib
import secrets
from typing import Optional, Dict, Set
from collections import defaultdict
from dataclasses import dataclass, field

try:
    import bpy
    BLENDER_AVAILABLE = True
except ImportError:
    BLENDER_AVAILABLE = False


@dataclass
class ClientInfo:
    """Information about a connected client."""
    id: str
    authenticated: bool = False
    request_count: int = 0
    last_request: float = 0.0
    blocked_until: float = 0.0


class RateLimiter:
    """Token bucket rate limiter."""

    def __init__(self, max_requests: int = 100, window_seconds: float = 60.0):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: Dict[str, list] = defaultdict(list)

    def allow(self, client_id: str = "default") -> bool:
        """Check if request is allowed for client."""
        now = time.time()
        window_start = now - self.window_seconds

        # Clean old requests
        self.requests[client_id] = [
            req_time for req_time in self.requests[client_id]
            if req_time > window_start
        ]

        # Check if under limit
        if len(self.requests[client_id]) < self.max_requests:
            self.requests[client_id].append(now)
            return True

        return False

    def get_remaining(self, client_id: str = "default") -> int:
        """Get remaining requests in current window."""
        now = time.time()
        window_start = now - self.window_seconds

        current_count = len([
            req_time for req_time in self.requests[client_id]
            if req_time > window_start
        ])

        return max(0, self.max_requests - current_count)

    def reset(self, client_id: str = "default") -> None:
        """Reset rate limit for client."""
        self.requests[client_id] = []


class SecurityManager:
    """Security manager for MCP server."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        rate_limit: int = 100,
        block_duration: float = 60.0
    ):
        self.api_key = api_key
        self.rate_limiter = RateLimiter(max_requests=rate_limit)
        self.block_duration = block_duration
        self.clients: Dict[str, ClientInfo] = {}
        self.authenticated_clients: Set[str] = set()

        # If no API key provided, generate one
        if api_key is None:
            self.api_key = self._generate_api_key()

    @staticmethod
    def _generate_api_key() -> str:
        """Generate a secure API key."""
        return secrets.token_urlsafe(32)

    @staticmethod
    def hash_api_key(api_key: str) -> str:
        """Hash an API key for secure comparison."""
        return hashlib.sha256(api_key.encode()).hexdigest()

    def authenticate(self, api_key: str, client_id: str = "default") -> bool:
        """Authenticate a client with API key."""
        if not api_key:
            return False

        # Constant-time comparison
        provided_hash = self.hash_api_key(api_key)
        expected_hash = self.hash_api_key(self.api_key)

        if secrets.compare_digest(provided_hash, expected_hash):
            self.authenticated_clients.add(client_id)
            if client_id in self.clients:
                self.clients[client_id].authenticated = True
            return True

        return False

    def is_authenticated(self, client_id: str) -> bool:
        """Check if client is authenticated."""
        return client_id in self.authenticated_clients

    def check_rate_limit(self, client_id: str = "default") -> bool:
        """Check and update rate limit for client."""
        # Check if client is blocked
        if client_id in self.clients:
            client = self.clients[client_id]
            if time.time() < client.blocked_until:
                return False

        # Check rate limit
        if not self.rate_limiter.allow(client_id):
            # Block client temporarily
            if client_id in self.clients:
                self.clients[client_id].blocked_until = time.time() + self.block_duration
            return False

        # Update client info
        if client_id not in self.clients:
            self.clients[client_id] = ClientInfo(id=client_id)

        self.clients[client_id].request_count += 1
        self.clients[client_id].last_request = time.time()

        return True

    def get_rate_limit_info(self, client_id: str = "default") -> dict:
        """Get rate limit information for client."""
        return {
            "remaining": self.rate_limiter.get_remaining(client_id),
            "limit": self.rate_limiter.max_requests,
            "window": self.rate_limiter.window_seconds,
            "authenticated": self.is_authenticated(client_id),
        }

    def block_client(self, client_id: str, duration: Optional[float] = None) -> None:
        """Manually block a client."""
        if client_id not in self.clients:
            self.clients[client_id] = ClientInfo(id=client_id)

        duration = duration or self.block_duration
        self.clients[client_id].blocked_until = time.time() + duration

    def unblock_client(self, client_id: str) -> None:
        """Unblock a client."""
        if client_id in self.clients:
            self.clients[client_id].blocked_until = 0.0

    def revoke_access(self, client_id: str) -> None:
        """Revoke client access (logout)."""
        self.authenticated_clients.discard(client_id)
        if client_id in self.clients:
            self.clients[client_id].authenticated = False

    def get_api_key(self) -> str:
        """Get the current API key."""
        return self.api_key


class CommandWhitelist:
    """Command whitelist for access control."""

    def __init__(self, allowed: Optional[Set[str]] = None):
        self.allowed: Set[str] = allowed or set()
        self.denied: Set[str] = set()

    def allow(self, command: str) -> None:
        """Add command to allowed list."""
        self.allowed.add(command)
        self.denied.discard(command)

    def deny(self, command: str) -> None:
        """Add command to denied list."""
        self.denied.add(command)
        self.allowed.discard(command)

    def is_allowed(self, command: str) -> bool:
        """Check if command is allowed."""
        # If whitelist is empty, all commands are allowed
        if not self.allowed:
            return command not in self.denied

        return command in self.allowed and command not in self.denied

    def set_allowed(self, commands: Set[str]) -> None:
        """Set the complete allowed commands list."""
        self.allowed = commands.copy()

    def get_allowed(self) -> Set[str]:
        """Get the allowed commands list."""
        return self.allowed.copy()


# Dangerous commands that require confirmation
DANGEROUS_COMMANDS = {
    "clear_scene": "This will delete all objects from the scene",
    "delete_object": "This will delete an object",
}


def requires_confirmation(command: str) -> bool:
    """Check if a command requires confirmation."""
    return command in DANGEROUS_COMMANDS


def get_confirmation_message(command: str) -> str:
    """Get confirmation message for a command."""
    return DANGEROUS_COMMANDS.get(command, "This action may be destructive")


# Blender-specific security utilities
if BLENDER_AVAILABLE:
    class BlenderSecurity:
        """Blender-specific security utilities."""

        @staticmethod
        def save_undo_state() -> None:
            """Save current state for undo."""
            # This would integrate with Blender's undo system
            pass

        @staticmethod
        def restore_undo_state() -> None:
            """Restore to previous undo state."""
            # This would integrate with Blender's undo system
            pass

        @staticmethod
        def is_safe_operation(operation: str) -> bool:
            """Check if operation is safe to execute."""
            # Safe operations (read-only)
            safe_ops = {
                "get_scene_info",
                "get_object_info",
            }

            # Dangerous operations (require confirmation)
            dangerous_ops = {
                "clear_scene",
            }

            if operation in safe_ops:
                return True
            if operation in dangerous_ops:
                return False

            # Default: allow but log
            return True
