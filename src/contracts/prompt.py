from typing import Protocol


class SystemPrompt(Protocol):
    _system_prompt: str

    @property
    def system_prompt(self) -> str: ...