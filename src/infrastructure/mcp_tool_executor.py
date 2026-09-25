import json

from mcp import Client, Tool as MCPTool
from mcp_types import CallToolResult, TextContent, ImageContent

from contracts.tool_executor import ToolCall, ToolResult, Tool

class MCPToolExecutor:

    def __init__(
            self,
            client: Client
    ):
        self._client = client


    async def execute(self, tool_call: ToolCall) -> ToolResult:
        try:
            result = await self._client.call_tool(tool_call.name, tool_call.arguments)
        except Exception as e:
            return ToolResult(success=False, data=None, error=str(e))
        error = "\n".join(
            block.text for block in result.content if isinstance(block, TextContent)
        ) if result.is_error else None
        return ToolResult(success=not result.is_error, data=result, error=error)

    async def get_tools(self) -> list[Tool]:
        tools = await self._client.list_tools()
        return [_mcp_tool_to_tool(tool) for tool in tools.tools]


def _mcp_tool_to_tool(tool: MCPTool) -> Tool:
    return Tool(
        name=tool.name,
        description=tool.description or "",
        input_schema=tool.input_schema
    )

