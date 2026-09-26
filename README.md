# dgr-hermes

Opt-in contributor modules for Hermes Agent. Includes a usable text-metrics module and a separately packaged example. The authorization proxy and commerce execution gate are not implemented in this package.

## Install and enable

Use Python 3.11 or newer in the same environment as Hermes:

```sh
python -m pip install .
hermes plugins enable dgr_hermes
```

In the active Hermes profile's `config.yaml`, merge these settings with existing plugin configuration:

```yaml
plugins:
  enabled:
    - dgr_hermes
  entries:
    dgr_hermes:
      settings:
        enabled_modules:
          - text_metrics
```

Restart Hermes. The tool `dgr_ext_text_metrics_count` accepts `{"text": "Hello world"}` and returns character, word and line counts. With `enabled_modules: []` no modules load. Disabling a module takes effect after restart/reload of the plugin.

Modules are trusted Python packages running in the Hermes process, not sandboxed code. Install only reviewed packages. The provided examples do no network or filesystem I/O and need no credentials. This package does not grant authority to execute commerce actions.

See [module API and contributor guide](docs/modules.md), [example package](examples/word_report/README.md), and [contribution requirements](CONTRIBUTING.md).

## Checks

```sh
python -m pip install .
python -m pip install ./examples/word_report
python -m unittest discover -s tests -v
python3 scripts/check_repository.py
```

Hermes integration targets the plugin API inspected at `NousResearch/hermes-agent` commit `f97608f178d1ffeca59860195ab7da295f7c8e5f` (`v2026.9.24`). This is not a guarantee for every Hermes version or platform.
