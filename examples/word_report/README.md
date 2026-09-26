# Separately packaged word-report module

This functional example counts unique case-insensitive whitespace-separated words. Punctuation is retained. It uses no network, filesystem or credentials.

From the repository root, in Hermes's Python environment:

```sh
python -m pip install .
python -m pip install ./examples/word_report
```

Add `word_report` to `plugins.entries.dgr_hermes.settings.enabled_modules`, keeping `dgr_hermes` enabled, then restart Hermes. Call `dgr_ext_word_report_unique` with `{"text": "Hello hello world"}`. The result is `{"unique_words": 2}` inside the adapter's JSON response envelope.

Copy this package structure for your own module, choose unique package/module/tool names, declare a `dgr_hermes.modules` entry point and implement a version1 factory. See the [API guide](../../docs/modules.md). Installed modules remain disabled until explicitly selected.
