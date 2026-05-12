# QuickApply deployment notes

## Repository

- Upstream: `https://github.com/qpwm06/QuickApply`
- Local path: `/Users/town/Projects/boss/ref/QuickApply`
- Tracked commit: `5c4fbf41717cb3d2ca50ad2726b80ac945bbaf72`

## Local setup

```bash
cd /Users/town/Projects/boss/ref/QuickApply
rtk uv sync --dev
rtk uv run python scripts/seed_demo_data.py --replace
```

The project requires Python `>=3.12,<3.13`; `uv` selected pyenv CPython `3.12.0` locally.

## Run

```bash
cd /Users/town/Projects/boss/ref/QuickApply
rtk uv run python main.py
```

Open:

```text
http://127.0.0.1:5273/dashboard
```

## Docker

```bash
cd /Users/town/Projects/boss/ref/QuickApply
rtk docker compose up -d --build
rtk docker compose run --rm quickapply uv run python scripts/seed_demo_data.py --replace
```

## Verification on 2026-05-12

- `rtk uv sync --dev`: success
- `rtk uv run python scripts/seed_demo_data.py --replace`: success
- `rtk uv run python main.py` then `rtk curl -I http://127.0.0.1:5273/dashboard`: returned `HTTP/1.1 200 OK`
- `rtk env PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 uv run python -m pytest -q`: `76 passed, 3 failed`

Failing upstream tests:

- `tests/test_config_tailor.py::test_tailor_service_session_prompt_uses_role_md_not_snapshot`
- `tests/test_routes.py::test_tailor_skill_detail_page_renders_codex_skill`
- `tests/test_routes.py::test_reveal_tailor_skill_route_uses_open_r_on_macos`

Failure theme: Tailor skill prompt/route expectations around `revision_advice`; core app startup and dashboard smoke test passed.

