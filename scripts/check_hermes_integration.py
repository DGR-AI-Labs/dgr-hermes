"""Run against an explicitly provided Hermes checkout via PYTHONPATH.

Requires this package and the word-report example installed in the same Python
as Hermes. Uses only temporary profile configuration and real host registration.
"""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch


def main():
    """Exercise the actual pinned host using an isolated temporary profile."""
    with tempfile.TemporaryDirectory(prefix="dgr-hermes-integration-") as directory:
        os.environ["HERMES_HOME"] = directory
        Path(directory, "config.yaml").write_text(
            """plugins:
  enabled: [dgr_hermes]
  entries:
    dgr_hermes:
      settings:
        enabled_modules: [text_metrics, word_report]
"""
        )
        # Hermes resolves its profile on import, after HERMES_HOME is isolated.
        from hermes_cli.plugins import (  # pylint: disable=import-outside-toplevel
            PluginManager,
            PluginManifest,
        )
        from tools.registry import registry  # pylint: disable=import-outside-toplevel

        manager = PluginManager()
        manifest = PluginManifest(name="dgr_hermes", source="entrypoint", version="0.1.0.dev0")
        manager._load_plugin(manifest)  # pylint: disable=protected-access
        # Pinned-host integration deliberately tests its loader and ownership state.
        loaded = manager._plugins["dgr_hermes"]  # pylint: disable=protected-access
        assert loaded.enabled and not loaded.error, loaded.error
        names = ("dgr_ext_text_metrics_count", "dgr_ext_word_report_unique")
        for name in names:
            assert registry.get_entry(name, scope=manager.scope_key) is not None
        result = json.loads(
            registry.dispatch(names[0], {"text": "Hello world"}, scope=manager.scope_key)
        )
        assert result["result"] == {"characters": 11, "words": 2, "lines": 1}, result
        result = json.loads(
            registry.dispatch(names[1], {"text": "Hello hello world"}, scope=manager.scope_key)
        )
        assert result["result"] == {"unique_words": 2}, result
        assert manager.unload("dgr_hermes")
        for name in names:
            assert registry.get_entry(name, scope=manager.scope_key) is None
        # Reload with every module disabled must not bring old registrations back.
        with patch("hermes_cli.plugins.PluginContext.get_config", return_value=[]):
            manager._load_plugin(manifest)  # pylint: disable=protected-access
        for name in names:
            assert registry.get_entry(name, scope=manager.scope_key) is None
        manager.unload("dgr_hermes")
        print(
            "PASS: actual Hermes entry-point load, both module dispatches, unload and disabled reload"
        )


if __name__ == "__main__":
    main()
