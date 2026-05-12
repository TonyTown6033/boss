# Remote Data Layout

`remote/data` stores remote job data as JSON-first artifacts.

## Current Data

- `latest/raw_remote_jobs.json`: latest fetched multi-source payload.
- `latest/normalized_remote_jobs.json`: latest normalized jobs used by screening.
- `latest/screened_remote_jobs.json`: latest screening output.

## Snapshots

- `snapshots/raw/`: timestamped fetched payloads.
- `snapshots/normalized/`: timestamped normalized jobs.
- `snapshots/screened/`: timestamped screening outputs.

## Archives

`archives/legacy/` keeps pre-restructure CSV, Markdown, and JSON files for traceability.

- `boss/`: historical BOSS CSV exports.
- `remotejobscn/`: historical RemoteJobsCN exports.
- `remote_jobs/`: historical multi-source exports.
- `reports/`: historical Markdown screening and analysis reports.

Long-term data should be JSON. CSV and Markdown should be treated as legacy archives or generated exports.
