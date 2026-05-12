# JobSpy deployment notes

## Location

- Project path: `/Users/town/Projects/boss/ref/jobspy-deploy`
- Package: `python-jobspy`
- Import module: `jobspy`
- Python: `3.12.0` from `pyenv`

## Install or sync

```bash
cd /Users/town/Projects/boss/ref/jobspy-deploy
rtk env UV_CACHE_DIR=/Users/town/Projects/boss/ref/jobspy-deploy/.uv-cache uv sync
```

## Verification on 2026-05-12

```bash
cd /Users/town/Projects/boss/ref/jobspy-deploy
rtk .venv/bin/python smoke_import.py
```

Expected output:

```text
jobspy import ok
scrape_jobs callable: True
```

## Smoke scrape example

This calls external job sites, so results depend on network access and anti-bot behavior.

```bash
cd /Users/town/Projects/boss/ref/jobspy-deploy
rtk .venv/bin/python -c 'from jobspy import scrape_jobs; jobs = scrape_jobs(site_name=["indeed"], search_term="software engineer", location="New York, NY", results_wanted=5, country_indeed="usa"); print(jobs.head().to_string())'
```

