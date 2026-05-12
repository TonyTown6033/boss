# boss reference deployments

This directory keeps deployable references for projects compared with `boss`.

## Projects

| Project | Path | Status |
| --- | --- | --- |
| boss | `/Users/town/Projects/boss/remote` | Local scripts verified with `uv run`; Remotive API scrape and screening smoke tests passed. |
| JobSpy | `jobspy-deploy/` | Isolated `uv` project installed with `python-jobspy`; import smoke test passed. |
| QuickApply | `QuickApply/` | Tracked as upstream submodule; dependencies installed locally, demo data seeded, dashboard returned `HTTP/1.1 200 OK`. |
| goremote.io | `goremote.io/` | Tracked as upstream submodule; source prepared, but runtime verification is blocked by missing legacy PHP/Vagrant environment. |

## Notes

Detailed deployment notes are under `deployment-notes/`.

The Python projects use `uv` and `pyenv`. Runtime artifacts such as `.venv`, caches, and local SQLite databases are intentionally ignored.

