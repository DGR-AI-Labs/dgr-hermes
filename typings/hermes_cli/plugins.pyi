"""Only the pinned host surface used by the integration script."""

class PluginManifest:
    def __init__(self, *, name: str, source: str, version: str) -> None: ...

class LoadedPlugin:
    enabled: bool
    error: str | None

class PluginManager:
    scope_key: str
    _plugins: dict[str, LoadedPlugin]
    def __init__(self) -> None: ...
    def _load_plugin(self, manifest: PluginManifest) -> None: ...
    def unload(self, name: str) -> bool: ...
