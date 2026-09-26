# Integration-only host typing

These partial stubs describe only the Hermes surface exercised by
`scripts/check_hermes_integration.py`, pinned to upstream commit
`f97608f178d1ffeca59860195ab7da295f7c8e5f`. They are not a replacement for
upstream types and are not shipped in the package. Keep them aligned with the
pinned host when updating integration compatibility. CI still loads and dispatches
against the actual installed package and actual upstream checkout; stub success
alone does not establish host compatibility.
