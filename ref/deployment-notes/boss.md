# boss deployment notes

## Location

- Project path: `/Users/town/Projects/boss/remote`
- Runtime: Python via `uv` and `pyenv`
- Dependency profile: stdlib-only scripts

## Verification on 2026-05-12

Screening smoke test:

```bash
cd /Users/town/Projects/boss
rtk uv run python remote/scripts/screen_remotejobscn_jobs.py --input remote/data/latest/normalized_remote_jobs.json --out-json /private/tmp/boss_screened_remote_jobs.json --snapshot-dir /private/tmp/boss_screened_snapshots
```

Result:

```text
screened=9
json=/private/tmp/boss_screened_remote_jobs.json
snapshot=/private/tmp/boss_screened_snapshots/20260512_110512_remote_jobs.json
```

Live API scrape smoke test:

```bash
cd /Users/town/Projects/boss
rtk uv run python remote/scripts/scrape_remote_jobs.py --sources remotive --keyword python --limit 1 --out-dir /private/tmp/boss_remote_jobs
```

Result: success, `count=1`, no source errors.

## Common commands

```bash
cd /Users/town/Projects/boss
rtk uv run python remote/scripts/scrape_remote_jobs.py --sources all --keyword python --limit 50
rtk uv run python remote/scripts/screen_remotejobscn_jobs.py
```

