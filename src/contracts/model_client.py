from dataclasses import dataclass
from typing import Protocol, Any, List

from application.dto import AgentStep
from contracts.tool_executor import Tool, ToolCall, ToolResult


@dataclass
class ModelClientResponse:
    function_call: List[ToolCall] | None
    text: str | None

    @property
    def is_final(self) -> bool:
        return not self.function_call


class ModelClient(Protocol):
    def chat(
            self,
            *,
            tools: list[Tool],
            tool_results: list[tuple[ToolCall, ToolResult]] | None = None,
            user_input: str | None = None,
            memory: dict[str, dict[str, str]] | None = None,
    ) -> ModelClientResponse: ...

    @property
    def token_usage(self) -> dict: ...
