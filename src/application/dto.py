from dataclasses import dataclass, field


@dataclass
class AgentStep:
    name: str # tool name
    completed: bool
    result: str # Описание результата от LLM


@dataclass
class TaskMemory:
    facts: dict[str, dict[str, str]] = field(default_factory=dict)
