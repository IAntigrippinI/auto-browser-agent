import os
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from application.agent import BrowserAgent
from application.dto import TaskMemory
from application.memory_tool_executor import MemoryToolExecutor
from config.settings import get_settings
from infrastructure.mcp_playwright_prompt import MCPPlaywrightPrompt
from infrastructure.mcp_tool_executor import MCPToolExecutor
from infrastructure.openai_model import OpenAIModel

from mcp import Client, StdioServerParameters

@asynccontextmanager
async def build_agent() -> AsyncIterator[BrowserAgent]:
    settings = get_settings()
    server = StdioServerParameters(
        command="npx.cmd",
        args=[
            "-y",
            "@playwright/mcp@latest",
            "--extension",
            "--snapshot-mode=none"
        ],
        env={
            **os.environ,
            "PLAYWRIGHT_MCP_EXTENSION_TOKEN": settings.playwright_token,
        },
    )

    async with Client(server) as client:

        memory = TaskMemory()
        tool_executor = MemoryToolExecutor(MCPToolExecutor(client), memory)
        system_prompt = MCPPlaywrightPrompt()
        client_model = OpenAIModel(
            api_key=settings.openai_api_key,
            model=settings.openai_model,
            base_url=settings.openai_base_url,
            system_prompt=system_prompt,
        )


        yield BrowserAgent(
            tool_executor=tool_executor,
            memory=memory,
            llm=client_model
        )
