# Contributing

Keep this repository limited to code and its related installation, usage, API, testing, and maintenance documentation. Requirements, implementation prompts, design reviews, errata, roadmaps, backlogs, and other planning records belong in private repositories.

Use a pull request for changes. The required repository check and an independent approval must pass before merging. Do not commit credentials, customer data, or generated local databases.

Run `python3 scripts/check_repository.py` before submitting a change. The check rejects recognized planning paths in tracked files and verifies local file links in the README and contribution guide. It cannot determine whether arbitrary prose is planning material; reviewers must check content as well.
