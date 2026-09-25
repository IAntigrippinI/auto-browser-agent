import json
from dataclasses import dataclass
from typing import List

from application.dto import AgentStep, TaskMemory
from application.console import agent, function_call, llm
from contracts.model_client import ModelClient
from contracts.security import SecurityContext
from contracts.tool_executor import ToolExecutor, Tool, ToolCall


class BrowserAgent:

    def __init__(
            self,
            llm: ModelClient,
            tool_executor: ToolExecutor,
            memory: TaskMemory | None = None,
            security_context: SecurityContext | None = None,
    ):
        self._llm = llm
        self._tool_executor = tool_executor
        self._memory = memory if memory is not None else TaskMemory()
        self._security_context = security_context
        self._steps: List[AgentStep] = []

    @property
    def token_usage(self) -> dict:
        return self._llm.token_usage

    async def run(
            self,
            prompt: str
    ):
       self._memory.facts.clear()
       if self._security_context is not None:
           self._security_context.goal = prompt
       return await self._run_loop(prompt)

    async def _run_loop(
            self,
            initial_input: str | None,
            *,
            continuation: str | None = None,
            initial_tool_results=None,
    ):
       tool_results = []
       if initial_tool_results:
           tool_results = initial_tool_results
       user_input = initial_input
       final_attempts = 0
       while True:
            print()
            tools = await self._tool_executor.get_tools()
            response = self._llm.chat(
                user_input=user_input,
                tools=tools,
                tool_results=tool_results,
                memory=self._memory.facts,
                continuation=continuation,
            )
            llm(f"LLM: {response.text}")
            if response.is_final:
                control_tools = {tool.name for tool in tools}
                if not {"agent_finish", "agent_request_user"}.issubset(control_tools):
                    agent("AGENT: completed")
                    return
                if final_attempts >= 1:
                    agent("AGENT: completed")
                    return
                final_attempts += 1
                continuation = (
                    "Не завершай задачу обычным текстом. Если цель выполнена, "
                    "вызови agent_finish. Если нужна информация, вызови agent_request_user."
                )
                user_input = None
                tool_results = []
                continue
            tool_results = []
            requested_user = False
            for fc in response.function_call:
                function_call(fc.name, fc.arguments)
                result = await self._tool_executor.execute(fc)
                tool_results.append((fc, result))
                if fc.name == "agent_finish":
                    agent(f"AGENT: completed — {fc.arguments.get('summary', '')}")
                    return
                if fc.name == "agent_request_user":
                    question = fc.arguments.get("question", "")
                    agent(f"AGENT: waiting for user — {question}")
                    continuation = input("Ваш ответ: ")
                    requested_user = True
                    break
            if requested_user:
                user_input = None
                continue
            user_input = None
            continuation = None

