"""Version 1 definitions for trusted, synchronous contributor modules."""

from collections.abc import Callable
from dataclasses import dataclass
from typing import TypeAlias

JsonValue: TypeAlias = str | int | float | bool | None | list["JsonValue"] | dict[str, "JsonValue"]
JsonObject: TypeAlias = dict[str, JsonValue]
ToolHandler: TypeAlias = Callable[[JsonObject], JsonValue]

API_VERSION = 1


@dataclass(frozen=True)
class Tool:
    """A tool accepting a JSON object and returning a JSON-serializable value.

    The handler validates its inputs; the schema describes the interface to Hermes.
    No host context, credentials or authorization objects are passed to the handler.
    """

    name: str
    description: str
    parameters: JsonObject
    handler: ToolHandler


@dataclass(frozen=True)
class Module:
    """Returned by an entry-point factory; name must match the entry-point name."""

    name: str
    tools: tuple[Tool, ...]
    api_version: int = API_VERSION
