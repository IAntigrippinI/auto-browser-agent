import json

from openai import OpenAI

from contracts.security import SecurityDecision
from contracts.tool_executor import ToolCall


class OpenAIMCPSecurityChecker:
    def __init__(self, *, api_key: str, base_url: str, model: str):
        self._client = OpenAI(api_key=api_key, base_url=base_url)
        self._model = model

    def check(self, goal: str, action: ToolCall) -> SecurityDecision:
        prompt = (
            "Ты security-agent. Сначала проверь, соответствует ли действие цели. "
            "Ответь двумя строками: первая только ALLOW или DENY, вторая — короткая причина. "
            "Обычные переходы, клики, ввод текста "
            "и отправка формы разрешены, если они логично помогают цели. "
            "Обычный browser_click с ref или target разрешай, если аргументы не описывают опасность. "
            "Удаление, отправка сообщений и оплата разрешены, если они явно "
            "требуются целью. DENY кредит, заём или новое финансовое обязательство, "
            "если цель явно не требует именно этого. Также DENY неожиданную выдачу "
            "разрешений. Если действие явно нужно для цели, разреши его.\n"
            f"Цель: {goal[:1000]}\n"
            f"Действие: {action.name}\n"
            f"Аргументы: {json.dumps(action.arguments, ensure_ascii=False)[:1200]}\n"
            f"Намерение основного агента: {action.reason or 'не указано'}"
        )
        try:
            response = self._client.responses.create(
                model=self._model,
                instructions="Первая строка ответа должна быть ровно ALLOW или DENY. Вторая строка — причина.",
                input=prompt,
                max_output_tokens=32,
            )
            raw = _response_text(response)
            print(f"Checker LLM: {raw}")
            if not raw:
                return _fallback_decision(goal, action)
            lines = [line.strip(" -*") for line in raw.splitlines() if line.strip()]
            decision = lines[0].upper() if lines else "DENY"
            allowed = decision.startswith("ALLOW")
            reason = " ".join(lines[1:]).strip() or raw or (
                "пустой ответ checker; намерение основного агента: "
                f"{action.reason or 'не указано'}"
            )
            return SecurityDecision(allowed, reason)
        except Exception as error:
            return _fallback_decision(goal, action, str(error))


def _response_text(response) -> str:
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


def _fallback_decision(goal: str, action: ToolCall, error: str | None = None) -> SecurityDecision:
    action_text = json.dumps(action.arguments, ensure_ascii=False).lower()
    dangerous_tools = {"browser_run_code_unsafe"}
    dangerous_words = ("кредит", "заём", "loan", "credit", "пароль")

    if action.name in dangerous_tools:
        return SecurityDecision(
            False,
            "действие выполняет произвольный код и требует отдельного разрешения",
        )
    if any(word in action_text for word in dangerous_words):
        return SecurityDecision(
            False,
            "аргументы содержат чувствительное действие или данные",
        )

    suffix = f" ({error})" if error else ""
    return SecurityDecision(
        True,
        f"checker не вернул текст; явного опасного признака не найдено{suffix}",
    )
