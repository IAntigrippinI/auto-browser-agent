RESET = "\033[0m"
AGENT_COLOR = "\033[37m"      # светло-серый
LLM_COLOR = "\033[90m"        # тёмно-серый
SECURITY_COLOR = "\033[94m"   # голубо-синий
FUNCTION_COLOR = "\033[97m"   # белый


def agent(text: str) -> None:
    print(f"{AGENT_COLOR}{text}{RESET}")


def llm(text: str) -> None:
    print(f"{LLM_COLOR}{text}{RESET}")


def security(text: str) -> None:
    print(f"{SECURITY_COLOR}{text}{RESET}")


def function_call(name: str, arguments: dict) -> None:
    details = {
        "browser_navigate": ("страница", arguments.get("url")),
        "browser_find": ("поиск", arguments.get("query")),
        "tools_get_description": ("tools", arguments.get("names")),
    }.get(name)
    suffix = f" — {details[0]}: {details[1]}" if details and details[1] else ""
    print(f"{FUNCTION_COLOR}Call function: {name}{suffix}{RESET}")
