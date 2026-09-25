import json
from dataclasses import dataclass
from typing import List

from application.dto import AgentStep, TaskMemory
from contracts.model_client import ModelClient
from contracts.tool_executor import ToolExecutor, Tool, ToolCall


class BrowserAgent:

    def __init__(
            self,
            llm: ModelClient,
            tool_executor: ToolExecutor,
            memory: TaskMemory | None = None,
    ):
        self._llm = llm
        self._tool_executor = tool_executor
        self._memory = memory if memory is not None else TaskMemory()
        self._steps: List[AgentStep] = []

    @property
    def token_usage(self) -> dict:
        return self._llm.token_usage

    async def run(
            self,
            prompt: str
    ):
       self._memory.facts.clear()
       tool_results = []
       user_input = prompt
       tools = await self._tool_executor.get_tools()
       while True:
            response = self._llm.chat(
                user_input=user_input,
                tools=tools,
                tool_results=tool_results,
                memory=self._memory.facts,
            )
            print(f"LLM: {response.text}")
            if response.is_final:
                break
            tool_results = []
            for fc in response.function_call:
                print(f"Call function: {fc.name};\n")
                result = await self._tool_executor.execute(fc)
                tool_results.append((fc, result))
            user_input = None

