"""Only the pinned registry surface used by the integration script."""

from dgr_hermes import JsonObject

class ToolRegistry:
    def get_entry(self, name: str, *, scope: str | None = None) -> object | None: ...
    def dispatch(self, name: str, args: JsonObject, *, scope: str | None = None) -> str: ...

registry: ToolRegistry
