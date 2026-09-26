# Runtime validation is required even when callers ignore public annotations.
# pyright: reportUnnecessaryIsInstance=false
"""A usable reference module: local text metrics without I/O or credentials."""

from ..api import JsonObject, Module, Tool

MAX_TEXT_LENGTH = 100_000


def measure(arguments: JsonObject) -> JsonObject:
    """Validate supplied text and return deterministic local counts."""
    if not isinstance(arguments, dict) or set(arguments) != {"text"}:
        raise ValueError("Expected exactly one field: text")
    text = arguments["text"]
    if not isinstance(text, str) or len(text) > MAX_TEXT_LENGTH:
        raise ValueError("text must be a string of at most 100000 characters")
    return {
        "characters": len(text),
        "words": len(text.split()),
        "lines": len(text.splitlines()),
    }


def create_module() -> Module:
    """Declare the bundled supporting tool."""
    return Module(
        name="text_metrics",
        tools=(
            Tool(
                name="count",
                description="Count Unicode characters, whitespace-separated words and lines in supplied text. No external I/O.",
                parameters={
                    "type": "object",
                    "properties": {"text": {"type": "string", "maxLength": MAX_TEXT_LENGTH}},
                    "required": ["text"],
                    "additionalProperties": False,
                },
                handler=measure,
            ),
        ),
    )
