from dataclasses import dataclass
from typing import Protocol

from contracts.tool_executor import ToolCall


@dataclass
class SecurityDecision:
    allowed: bool
    reason: str


@dataclass
class SecurityContext:
    goal: str = ""


class SecurityChecker(Protocol):
    def check(self, goal: str, action: ToolCall) -> SecurityDecision: ...
