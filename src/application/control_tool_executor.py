from contracts.tool_executor import Tool, ToolCall, ToolExecutor, ToolResult


class ControlToolExecutor:
    async def get_tools(self) -> list[Tool]:
        return [
            Tool(
                name="agent_finish",
                description="Сообщить, что цель задачи проверена и полностью выполнена.",
                input_schema={
                    "type": "object",
                    "properties": {"summary": {"type": "string"}},
                    "required": ["summary"],
                    "additionalProperties": False,
                },
            ),
            Tool(
                name="agent_request_user",
                description="Запросить у пользователя недостающую информацию и приостановить задачу.",
                input_schema={
                    "type": "object",
                    "properties": {"question": {"type": "string"}},
                    "required": ["question"],
                    "additionalProperties": False,
                },
            ),
        ]

    async def execute(self, command: ToolCall) -> ToolResult:
        return ToolResult(True, command.arguments)
