# JobSpy deployment

This directory is an isolated `uv` project for JobSpy.

## Environment

- Python: `3.12.0` from `pyenv`
- Package: `python-jobspy`
- Import module: `jobspy`
- Local virtualenv: `.venv`
- Local uv cache: `.uv-cache`

## Install or sync

Run from this directory:

```bash
rtk env UV_CACHE_DIR=/Users/town/Projects/boss/ref/jobspy-deploy/.uv-cache uv sync
```

If `uv` panics on macOS `system-configuration` in the sandbox, run the same command with network/non-sandbox approval, or use the already-created `.venv`.

## Minimal verification

```bash
rtk .venv/bin/python smoke_import.py
```

Expected output:

```text
jobspy import ok
scrape_jobs callable: True
```

## Smoke scrape example

This calls external job sites, so results and failures depend on network access and site anti-bot behavior:

```bash
rtk .venv/bin/python -c 'from jobspy import scrape_jobs; jobs = scrape_jobs(site_name=["indeed"], search_term="software engineer", location="New York, NY", results_wanted=5, country_indeed="usa"); print(jobs.head().to_string())'
```
