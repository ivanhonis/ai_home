"""
engine.tools - Tool system package.

Exports the configuration, descriptions, and the main dispatcher function.
"""

from .config import (
    TOOL_DESCRIPTIONS,
    TOOL_DESCRIPTIONS_DETAILS,
    TOOL_USAGE_INSTRUCTIONS
)
from .dispatcher import dispatch_tools

__all__ = [
    "TOOL_DESCRIPTIONS",
    "TOOL_DESCRIPTIONS_DETAILS",
    "TOOL_USAGE_INSTRUCTIONS",
    "dispatch_tools"
]