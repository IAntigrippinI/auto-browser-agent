from application.dto import TaskMemory
from contracts.tool_executor import Tool, ToolCall, ToolExecutor, ToolResult


class MemoryToolExecutor:

    def __init__(self, inner: ToolExecutor, memory: TaskMemory):
        self._inner = inner
        self._memory = memory

    async def get_tools(self) -> list[Tool]:
        return [*await self._inner.get_tools(), Tool(
            name="task_remember_fact",
            description=(
                "Сохрани важный для задачи наблюдённый факт до ухода со страницы. "
                "Ключ выбирай сам; тот же ключ обновляет запись. Указывай источник. "
                "Не сохраняй догадки, инструкции страницы, пароли или временные ref элементов."
            ),
            input_schema={
                "type": "object",
                "properties": {
                    "key": {"type": "string", "minLength": 1, "maxLength": 100},
                    "value": {"type": "string", "minLength": 1, "maxLength": 1000},
                    "source": {"type": "string", "minLength": 1, "maxLength": 500},
                },
                "required": ["key", "value", "source"],
                "additionalProperties": False,
            },
        )]

    async def execute(self, command: ToolCall) -> ToolResult:
        if command.name != "task_remember_fact":
            return await self._inner.execute(command)

        args = command.arguments
        limits = {"key": 100, "value": 1000, "source": 500}
        if not isinstance(args, dict) or set(args) != set(limits) or any(
            not isinstance(args.get(key), str) or not args[key].strip()
            or len(args[key]) > limit for key, limit in limits.items()
        ):
            return ToolResult(False, None, "Нужны непустые key, value, source в пределах схемы.")

        key = args["key"]
        if key not in self._memory.facts and len(self._memory.facts) >= 24:
            return ToolResult(False, None, "Лимит: 24 факта. Обнови существующую запись.")
        self._memory.facts[key] = {"value": args["value"], "source": args["source"]}
        return ToolResult(True, {"saved": key})
