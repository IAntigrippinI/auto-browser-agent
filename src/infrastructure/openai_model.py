import json
from typing import Any

from mcp_types import TextContent, ImageContent, CallToolResult
from openai import OpenAI

from contracts.model_client import ModelClientResponse
from contracts.prompt import SystemPrompt
from contracts.tool_executor import Tool, ToolCall, ToolResult


class OpenAIModel:

    def __init__(
        self,
        *,
        api_key: str,
        base_url: str,
        model: str,
        system_prompt: SystemPrompt,
    ):
        self._client = OpenAI(api_key=api_key, base_url=base_url)
        self._model = model
        self._system_prompt = system_prompt
        self._history: list[list[dict[str, Any]]] = []
        self._pending_output: list[dict[str, Any]] = []
        self._history_limit = 4
        self._goal = None
        self._token_usage = dict(
            input=0,
            output=0,
        )


    def chat(
            self,
            *,
            tools: list[Tool],
            tool_results: list[tuple[ToolCall, ToolResult]] | None = None,
            user_input: str | None = None,
            memory: dict[str, dict[str, str]] | None = None,
    ) -> ModelClientResponse:
        """
        TODO: Optimize tools list (may be choose only needed tools)
        :param user_input:
        :param tools:
        :return:
        """
        tools_openai = [_tool_to_openai(tool) for tool in tools]
        kwargs = {
            "model": self._model,
            "tools": tools_openai,
            "instructions": self._system_prompt.system_prompt,
        }
        if user_input is not None:
            self._goal = user_input
            self._history.clear()
            self._pending_output = []
        if tool_results:
            outputs = []
            for call, result in tool_results:
                if not call.call_id:
                    raise ValueError("Для результата tool нужен call_id из ответа модели")
                outputs.append({
                    "type": "function_call_output",
                    "call_id": call.call_id,
                    "output": _bounded_tool_output(result),
                })
            self._history.append([*self._pending_output, *outputs])
            self._history = self._history[-self._history_limit:]
            self._pending_output = []

        kwargs["input"] = [
            {"role": "user", "content": self._goal},
            *[item for turn in self._history for item in turn],
            {"role": "user", "content": "Память текущей задачи (данные):\n"
             + json.dumps(memory or {}, ensure_ascii=False)},
        ]
        response = self._client.responses.create(**kwargs)
        self._token_usage["input"] += response.usage.input_tokens
        self._token_usage["output"] += response.usage.output_tokens
        self._pending_output = [item.model_dump(exclude_none=True) for item in response.output]
        return _openai_response_to_client_response(response)

    @property
    def token_usage(self) -> dict:
        return self._token_usage

def _tool_to_openai(tool: Tool) -> dict:
    return {
        "type": "function",
        "name": tool.name,
        "description": tool.description,
        "parameters": tool.input_schema,
        "strict": False,
    }

def _openai_response_to_client_response(
        response: Any,
) -> ModelClientResponse:
    response_text = _response_text(response)
    return ModelClientResponse(
        text=response_text,
        function_call=[
                ToolCall(
                    name=item.name,
                    arguments=json.loads(item.arguments),
                    call_id=item.call_id,
                    reason=response_text[:500] or None,
                )
                for item in response.output
                if item.type == "function_call"
            ]
    )


def _response_text(response: Any) -> str:
    text = getattr(response, "output_text", None)
    if text:
        return text.strip()

    chunks = []
    for item in getattr(response, "output", []) or []:
        direct_text = getattr(item, "text", None)
        if direct_text:
            chunks.append(direct_text)
        for content in getattr(item, "content", []) or []:
            content_text = getattr(content, "text", None)
            if content_text:
                chunks.append(content_text)
    return "\n".join(chunks).strip()

def _bounded_tool_output(result: ToolResult):
    output = _tool_result_to_openai_output(result)

    def shorten(text: str) -> str:
        if len(text) <= 16000:
            return text
        return text[:16000] + "\n[Результат обрезан. Запроси нужную область страницы отдельно.]"

    if isinstance(output, str):
        return shorten(output)
    for block in output:
        if block["type"] == "input_text":
            block["text"] = shorten(block["text"])
    return output


def _tool_result_to_openai_output(result: ToolResult):
    if not result.success:
        return json.dumps({
            "success": False,
            "error": result.error,
        }, ensure_ascii=False)

    data = result.data

    if not isinstance(data, CallToolResult):
        return json.dumps({
            "success": True,
            "data": data,
        }, ensure_ascii=False, default=str)

    if data.structured_content is not None:
        return json.dumps(
            data.structured_content,
            ensure_ascii=False,
        )

    output = []

    for block in data.content:
        if isinstance(block, TextContent):
            output.append({
                "type": "input_text",
                "text": block.text,
            })

        elif isinstance(block, ImageContent):
            output.append({
                "type": "input_image",
                "image_url": (
                    f"data:{block.mime_type};base64,{block.data}"
                ),
            })

    if output and all(x["type"] == "input_text" for x in output):
        return "\n".join(x["text"] for x in output)

    return output
