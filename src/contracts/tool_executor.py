from dataclasses import dataclass
from typing import Protocol, Any


@dataclass
class ToolCall:
    name: str
    arguments: dict
    call_id: str | None = None
    reason: str | None = None


@dataclass
class ToolResult:
    success: bool
    data: Any
    error: str | None = None

@dataclass
class Tool:
    name: str
    description: str | None
    input_schema: dict[str, Any]


class ToolExecutor(Protocol):
    async def execute(self, command: ToolCall) -> ToolResult: ...

    async def get_tools(self) -> list[Tool]: ...
