"""Hermes adapter for explicit module selection. No decision or execution hooks."""
from copy import deepcopy
from importlib import metadata
import inspect
import json
import re
from typing import Protocol

from .api import API_VERSION, Module, Tool

ENTRY_POINT_GROUP = "dgr_hermes.modules"
BUILTIN = "text_metrics"
_NAME = re.compile(r"[a-z][a-z0-9_]{0,23}\Z")


class ModuleError(ValueError):
    """Invalid module configuration, declaration or registration."""


class Registration(Protocol):
    def dispose(self) -> None: ...


class Host(Protocol):
    def get_config(self, key: str, default=None): ...
    def register_tool(self, **kwargs) -> Registration | None: ...


def _selected(value):
    if not isinstance(value, list) or any(not isinstance(n, str) or not _NAME.fullmatch(n) for n in value):
        raise ModuleError("enabled_modules must be a list of module names")
    if len(set(value)) != len(value):
        raise ModuleError("Duplicate enabled module")
    return value


def _declaration(name, module):
    if not isinstance(module, Module) or module.name != name:
        raise ModuleError(f"Module factory must return Module(name={name!r})")
    if type(module.api_version) is not int or module.api_version != API_VERSION:
        raise ModuleError(f"Unsupported module API for {name}")
    if not isinstance(module.tools, tuple) or not module.tools:
        raise ModuleError(f"Module {name} must declare a nonempty tuple of tools")
    tools = []
    seen = set()
    for tool in module.tools:
        if not isinstance(tool, Tool) or not isinstance(tool.name, str) or not _NAME.fullmatch(tool.name):
            raise ModuleError(f"Invalid tool in {name}")
        full_name = f"dgr_ext_{name}_{tool.name}"
        if full_name in seen:
            raise ModuleError(f"Duplicate tool {full_name}")
        seen.add(full_name)
        if not isinstance(tool.description, str) or not tool.description.strip():
            raise ModuleError(f"Missing description for {full_name}")
        if (not callable(tool.handler) or inspect.iscoroutinefunction(tool.handler)
                or inspect.iscoroutinefunction(getattr(tool.handler, "__call__", None))):
            raise ModuleError(f"Tool {full_name} requires a synchronous handler")
        if not isinstance(tool.parameters, dict) or tool.parameters.get("type") != "object":
            raise ModuleError(f"Tool {full_name} requires an object parameter schema")
        try:
            schema = json.loads(json.dumps(tool.parameters, allow_nan=False))
        except (TypeError, ValueError) as exc:
            raise ModuleError(f"Tool {full_name} requires JSON parameters") from exc
        tools.append((full_name, tool, schema))
    return tools


def _handler(handler, module_name):
    def invoke(arguments, **_host_metadata):
        # Hermes metadata is deliberately not part of the contributor interface.
        try:
            if not isinstance(arguments, dict):
                raise ValueError("Expected object")
            result = handler(deepcopy(arguments))
            if inspect.isawaitable(result):
                if inspect.iscoroutine(result):
                    result.close()
                raise ValueError("Async result unsupported")
            return json.dumps({"ok": True, "module": module_name, "result": result}, allow_nan=False)
        except Exception:
            # Do not expose exception messages, arguments or module internals to tool output.
            return json.dumps({"ok": False, "module": module_name, "error": "module_failed"})
    return invoke


def register(ctx: Host):
    """Hermes entry point. Validate all declarations before registering any tool.

    No enabled modules means no entry-point discovery or module imports. Discovery
    reads package metadata only; selected external factories execute trusted Python.
    Hermes owns successful registrations and disposes them on plugin unload.
    """
    selected = _selected(ctx.get_config("enabled_modules", []))
    if not selected:
        return
    entries = metadata.entry_points(group=ENTRY_POINT_GROUP)
    factories = {}
    # Resolve every selected name before loading even the first external module.
    for name in selected:
        matches = [ep for ep in entries if ep.name == name]
        if name == BUILTIN:
            if matches:
                raise ModuleError("External module collides with bundled text_metrics")
            factories[name] = None
        elif len(matches) != 1:
            raise ModuleError(f"Module {name} must have exactly one installed entry point")
        else:
            factories[name] = matches[0]
    declarations = []
    for name in selected:
        if name == BUILTIN:
            from .modules.text_metrics import create_module
            factory = create_module
        else:
            factory = factories[name].load()
        if not callable(factory):
            raise ModuleError(f"Module {name} entry point must be a factory")
        declarations.extend((name, *tool) for tool in _declaration(name, factory()))
    names = [full_name for _, full_name, _, _ in declarations]
    if len(names) != len(set(names)):
        raise ModuleError("Module tool names collide after namespacing")
    handles = []
    try:
        for name, full_name, tool, parameters in declarations:
            handle = ctx.register_tool(
                name=full_name, toolset="dgr_hermes_extensions",
                schema={"name": full_name, "description": tool.description, "parameters": parameters},
                handler=_handler(tool.handler, name), description=tool.description,
                is_async=False, override=False,
            )
            if handle is None:
                raise ModuleError(f"Hermes refused registration of {full_name}")
            handles.append(handle)
    except BaseException:
        # Attempt every cleanup even if one host handle fails; preserve original error.
        for handle in reversed(handles):
            try:
                handle.dispose()
            except Exception:
                pass
        raise
