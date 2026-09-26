"""Separately packaged example module with no external I/O."""

from dgr_hermes import Module, Tool


def report(arguments):
    """Validate supplied text and count unique normalized words."""
    if not isinstance(arguments, dict) or set(arguments) != {"text"}:
        raise ValueError("Expected text")
    text = arguments["text"]
    if not isinstance(text, str) or len(text) > 100_000:
        raise ValueError("Invalid text")
    return {"unique_words": len(set(text.casefold().split()))}


def create_module():
    """Declare the separately packaged example tool."""
    return Module(
        "word_report",
        (
            Tool(
                "unique",
                "Count distinct case-insensitive whitespace-separated words; punctuation is retained.",
                {
                    "type": "object",
                    "properties": {"text": {"type": "string", "maxLength": 100_000}},
                    "required": ["text"],
                    "additionalProperties": False,
                },
                report,
            ),
        ),
    )
