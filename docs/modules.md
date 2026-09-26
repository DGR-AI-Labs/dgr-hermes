# Contributor modules

A module is an installed Python package exposing a factory in the `dgr_hermes.modules` entry-point group. The factory returns `Module(name, tools, api_version=1)`. Each `Tool` declares a name, description, JSON object parameter schema and synchronous handler. Handlers take one argument dictionary and return a JSON-serializable value.

```python
from dgr_hermes import Module, Tool

def greeting(arguments):
    if set(arguments) != {"name"} or not isinstance(arguments["name"], str):
        raise ValueError("Expected name")
    return {"greeting": "Hello " + arguments["name"]}

def create_module():
    return Module("greeting", (Tool(
        "hello", "Produce a greeting locally",
        {"type": "object", "properties": {"name": {"type": "string"}},
         "required": ["name"], "additionalProperties": False}, greeting,
    ),))
```

Package metadata:

```toml
[project.entry-points."dgr_hermes.modules"]
greeting = "my_package:create_module"
```

Install the package into Hermes's Python environment and add `greeting` to `plugins.entries.dgr_hermes.settings.enabled_modules`. The tool is named `dgr_ext_greeting_hello`. Module/tool names start with a lowercase ASCII letter, contain only lowercase letters, digits or underscores, and have at most 24 characters. Factories must match their entry-point names. Duplicate enabled names, duplicate installed entry points, incompatible API versions and collisions with the bundled module cause registration to fail. No package installation happens automatically.

## Lifecycle and errors

An empty allowlist performs no discovery or imports. Disabled packages' entry points are never loaded by this adapter. All selected names are resolved and all declarations validated before any tool registration. Successful registrations belong to Hermes's ownership ledger; Hermes disposes them when the plugin unloads. On partial registration failure the adapter attempts cleanup of every handle it acquired. No hot reload protocol is provided by this package; restart Hermes after configuration changes.

Handlers receive a deep copy of tool arguments, without the Hermes context or dispatch metadata. Each handler must validate input values and sizes: the adapter verifies a JSON object schema declaration, but is not a general JSON Schema validator. Tool outputs are JSON strings containing `ok`, `module`, and either `result` or `error: module_failed`. Handler exceptions and non-JSON results return this generic error, without echoing input or exception text. Hermes's own logs, module logging and process termination are outside this error-output contract. Async handlers are unsupported in API1.

## Trust and contribution boundary

Entry-point factories and handlers are arbitrary Python. The adapter provides namespacing and explicit enablement, not process isolation, filesystem restrictions or network blocking. Enabled modules can exercise the operating-system permissions of Hermes. Do not install third-party modules beside secrets they must not access. Factory import-time side effects cannot be rolled back by unregistering tools.

API1 is for supporting local functionality. The shipped code exposes no provider client, credential store, decision callback, token minting, approval grant or execution hook. Modules must not introduce consequential actions through this interface or represent a module result as an authorization decision. Effects require a separately reviewed integration with the actual execution boundary. A module's self-description is not proof of its behavior.

Review contributions for bounded inputs, no unexpected import-time behavior, dependency provenance, deterministic local tests, conflicts and failure cleanup. Keep plans and review records in the private repositories; publish only code and related documentation here. See the installable [word-report example](../examples/word_report/README.md).

## Host integration check

With the plugin and example installed, check out Hermes at `f97608f178d1ffeca59860195ab7da295f7c8e5f` and run:

```sh
python -m pip install -r tests/requirements-hermes.txt
PYTHONPATH=/path/to/hermes python scripts/check_hermes_integration.py
```

The check creates a temporary Hermes profile, loads the installed plugin through Hermes's actual entry-point loader, dispatches both sample tools, unloads them, and reloads with an empty module list. CI runs this check against the immutable host pin. It does not start a model session or call any external provider.
