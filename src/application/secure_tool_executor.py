from contracts.security import SecurityChecker, SecurityContext
from contracts.tool_executor import Tool, ToolCall, ToolExecutor, ToolResult
from application.console import security


class SecureToolExecutor:
    _SAFE_TOOLS = {
        "browser_navigate",
        "browser_snapshot",
        "browser_find",
        "browser_wait_for",
    }

    def __init__(self, inner: ToolExecutor, checker: SecurityChecker, context: SecurityContext):
        self._inner = inner
        self._checker = checker
        self._context = context

    async def get_tools(self) -> list[Tool]:
        return await self._inner.get_tools()

    async def execute(self, command: ToolCall) -> ToolResult:
        if command.name in self._SAFE_TOOLS:
            security(f"SECURITY: ALLOW {command.name} (safe)")
            return await self._inner.execute(command)

        decision = self._checker.check(self._context.goal, command)
        status = "ALLOW" if decision.allowed else "DENY"
        reason = f" — {decision.reason[:120]}"
        security(f"SECURITY: {status} {command.name}{reason}")
        if not decision.allowed:
            return ToolResult(
                success=False,
                data=None,
                error=f"Security layer заблокировал действие: {decision.reason}",
            )

        return await self._inner.execute(command)
