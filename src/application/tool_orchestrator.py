from contracts.tool_executor import Tool, ToolCall, ToolExecutor, ToolResult


class ToolOrchestrator:
    _DESCRIPTION_TOOL = "tools_get_description"

    def __init__(self, executors: list[ToolExecutor]):
        self._executors = executors
        self._tools: dict[str, Tool] = {}
        self._owners: dict[str, ToolExecutor] = {}
        self._loaded: set[str] = set()

    async def get_tools(self) -> list[Tool]:
        if not self._tools:
            for executor in self._executors:
                for tool in await executor.get_tools():
                    self._tools[tool.name] = tool
                    self._owners[tool.name] = executor

        tools = []
        for name, tool in self._tools.items():
            if name in self._loaded:
                tools.append(tool)
            else:
                tools.append(Tool(
                    name=name,
                    description=(tool.description or "")[:180],
                    input_schema={
                        "type": "object",
                        "additionalProperties": True,
                    },
                ))

        tools.append(Tool(
            name=self._DESCRIPTION_TOOL,
            description="Загрузить подробное описание и схему одного или нескольких tools перед вызовом.",
            input_schema={
                "type": "object",
                "properties": {
                    "names": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["names"],
                "additionalProperties": False,
            },
        ))
        return tools

    async def execute(self, command: ToolCall) -> ToolResult:
        if command.name == self._DESCRIPTION_TOOL:
            names = command.arguments.get("names", [])
            selected = [self._tools[name] for name in names if name in self._tools]
            self._loaded.update(tool.name for tool in selected)
            return ToolResult(True, {
                "tools": [
                    {
                        "name": tool.name,
                        "description": tool.description,
                        "input_schema": tool.input_schema,
                    }
                    for tool in selected
                ],
            })

        owner = self._owners.get(command.name)
        if owner is None:
            return ToolResult(False, None, f"Неизвестный tool: {command.name}")
        return await owner.execute(command)
