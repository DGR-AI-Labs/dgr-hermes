# Contributing

Keep this repository limited to code and its related installation, usage, API, testing, and maintenance documentation. Requirements, implementation prompts, design reviews, errata, roadmaps, backlogs, and other planning records belong in private repositories.

Use a pull request for changes. The required repository check and an independent approval must pass before merging. Do not commit credentials, customer data, or generated local databases.

Run `python3 scripts/check_repository.py` before submitting a change. The check rejects recognized planning paths in tracked files and verifies local file links in the README and contribution guide. It cannot determine whether arbitrary prose is planning material; reviewers must check content as well.

Contributor modules use the [module API](docs/modules.md). Run `python -m unittest discover -s tests -v` after installing the package and `./examples/word_report`. The bundled module and separately packaged example must remain usable without credentials or network access.

CI requires Pylint **8.0/10 or higher in each first-party area**, and rejects every
error or fatal diagnostic regardless of score. The rating is a lint quality floor,
not a percentage of code compliance or a security assurance. Keep diagnostics
visible; any narrow suppression needs an explanation at the affected boundary.

To reproduce the gate, install `tests/requirements-lint.txt` and
`tests/requirements-hermes.txt`, and set `PYTHONPATH` to a Hermes checkout at
`f97608f178d1ffeca59860195ab7da295f7c8e5f`. Run these commands with the same Python
environment used to install this package and the contributor example:

```sh
python -m pylint --persistent=no --fail-under=8.0 --fail-on=E,F src/dgr_hermes
python -m pylint --persistent=no --fail-under=8.0 --fail-on=E,F examples/word_report/src/dgr_word_report
python -m pylint --persistent=no --fail-under=8.0 --fail-on=E,F scripts
python -m pylint --persistent=no --fail-under=8.0 --fail-on=E,F tests/test_modules.py
python scripts/check_hermes_integration.py
```

The upstream checkout resolves host imports and supplies the integration target;
it is not part of the first-party lint scope.
