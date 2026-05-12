#!/usr/bin/env python3
import argparse
import datetime as dt
import hashlib
import html
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any


REMOTE_DIR = Path(__file__).resolve().parents[1]
DEFAULT_OUT_DIR = REMOTE_DIR / "data"
USER_AGENT = "Mozilla/5.0 (compatible; RemoteJobsResearch/1.0)"

SOURCES = ("himalayas", "remotive", "remoteok")


def fetch_json(url: str, retries: int = 3) -> Any:
    req = urllib.request.Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": USER_AGENT,
        },
    )
    last_error = None
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                payload = resp.read().decode("utf-8", errors="replace")
                return json.loads(payload)
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            last_error = exc
            time.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"fetch failed: {url}: {last_error}")


def clean_text(value: Any) -> str:
    if value is None:
        return ""
    text = str(value)
    text = re.sub(r"<[^>]+>", " ", text)
    text = html.unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def list_values(values: Any) -> list[str]:
    if not values:
        return []
    if isinstance(values, str):
        return [values]
    if isinstance(values, (list, tuple, set)):
        return [clean_text(v) for v in values if clean_text(v)]
    return [clean_text(values)]


def epoch_to_date(value: Any) -> str:
    if value in (None, ""):
        return ""
    if isinstance(value, (int, float)):
        return dt.datetime.fromtimestamp(value, tz=dt.UTC).date().isoformat()
    return clean_text(value)


def salary_text(
    raw: Any = "",
    min_value: Any = None,
    max_value: Any = None,
    currency: Any = "",
    period: Any = "",
) -> str:
    if raw:
        return clean_text(raw)
    if min_value in (0, "0"):
        min_value = None
    if max_value in (0, "0"):
        max_value = None
    if min_value is None and max_value is None:
        return "未明确"
    prefix = clean_text(currency)
    suffix = f"/{clean_text(period)}" if period else ""
    if min_value is not None and max_value is not None:
        return f"{prefix} {min_value}-{max_value}{suffix}".strip()
    if min_value is not None:
        return f"{prefix} {min_value}+{suffix}".strip()
    return f"{prefix} {max_value}{suffix}".strip()


def stable_id(source: str, source_id: Any, url: str) -> str:
    if source_id not in (None, ""):
        return f"{source}:{source_id}"
    digest = hashlib.sha1(url.encode("utf-8")).hexdigest()[:16]
    return f"{source}:{digest}"


def normalize_job(
    *,
    source: str,
    source_id: Any,
    title: Any,
    company: Any,
    source_url: Any = "",
    remote: Any = "",
    employment_type: Any = "",
    salary: Any = "",
    date_posted: Any = "",
    categories: Any = None,
    job_url: Any = "",
    description: Any = "",
    raw: Any = None,
) -> dict[str, Any]:
    url = clean_text(job_url)
    clean_source_id = clean_text(source_id)
    return {
        "id": stable_id(source, clean_source_id, url),
        "source_job_id": clean_source_id,
        "title": clean_text(title),
        "company": clean_text(company),
        "source": source,
        "source_url": clean_text(source_url),
        "remote": clean_text(remote) or "全球远程",
        "type": clean_text(employment_type),
        "salary": clean_text(salary) or "未明确",
        "date_posted": epoch_to_date(date_posted),
        "categories": list_values(categories),
        "job_url": url,
        "description": clean_text(description),
        "raw": raw if raw is not None else {},
    }


def scrape_himalayas(keyword: str, limit: int) -> list[dict[str, Any]]:
    jobs: list[dict[str, Any]] = []
    page = 1
    while len(jobs) < limit:
        params = {"sort": "recent", "page": str(page)}
        if keyword:
            params["q"] = keyword
        url = "https://himalayas.app/jobs/api/search?" + urllib.parse.urlencode(params)
        data = fetch_json(url)
        items = data.get("jobs") or []
        if not items:
            break
        for item in items:
            salary = salary_text(
                min_value=item.get("minSalary"),
                max_value=item.get("maxSalary"),
                currency=item.get("currency"),
                period="year",
            )
            remote = ",".join(list_values(item.get("locationRestrictions"))) or "全球远程"
            categories = (item.get("categories") or []) + (item.get("seniority") or [])
            jobs.append(
                normalize_job(
                    source="himalayas",
                    source_id=item.get("guid") or item.get("applicationLink"),
                    title=item.get("title"),
                    company=item.get("companyName"),
                    source_url="https://himalayas.app",
                    remote=remote,
                    employment_type=item.get("employmentType"),
                    salary=salary,
                    date_posted=item.get("pubDate"),
                    categories=categories,
                    job_url=item.get("applicationLink") or item.get("guid"),
                    description=item.get("description") or item.get("excerpt"),
                    raw=item,
                )
            )
            if len(jobs) >= limit:
                break
        total = int(data.get("totalCount") or 0)
        if page * 20 >= total:
            break
        page += 1
        time.sleep(0.4)
    return jobs


def scrape_remotive(keyword: str, limit: int) -> list[dict[str, Any]]:
    params = {}
    if keyword:
        params["search"] = keyword
    url = "https://remotive.com/api/remote-jobs"
    if params:
        url += "?" + urllib.parse.urlencode(params)
    data = fetch_json(url)
    items = data.get("jobs") or []
    jobs = []
    for item in items[:limit]:
        categories = []
        if item.get("category"):
            categories.append(item.get("category"))
        categories.extend(item.get("tags") or [])
        jobs.append(
            normalize_job(
                source="remotive",
                source_id=item.get("id"),
                title=item.get("title"),
                company=item.get("company_name"),
                source_url="https://remotive.com",
                remote=item.get("candidate_required_location") or "全球远程",
                employment_type=item.get("job_type"),
                salary=salary_text(raw=item.get("salary")),
                date_posted=item.get("publication_date"),
                categories=categories,
                job_url=item.get("url"),
                description=item.get("description"),
                raw=item,
            )
        )
    return jobs


def scrape_remoteok(keyword: str, limit: int) -> list[dict[str, Any]]:
    data = fetch_json("https://remoteok.com/api")
    items = data if isinstance(data, list) else []
    jobs = []
    needle = keyword.lower().strip()
    for item in items:
        if not isinstance(item, dict) or not item.get("position"):
            continue
        text = " ".join(
            [
                clean_text(item.get("position")),
                clean_text(item.get("company")),
                " ".join(list_values(item.get("tags"))),
                clean_text(item.get("description")),
            ]
        ).lower()
        if needle and needle not in text:
            continue
        categories = item.get("tags") or []
        jobs.append(
            normalize_job(
                source="remoteok",
                source_id=item.get("id") or item.get("slug"),
                title=item.get("position"),
                company=item.get("company"),
                source_url="https://remoteok.com",
                remote=item.get("location") or "全球远程",
                employment_type=item.get("type") or "",
                salary=salary_text(
                    raw=item.get("salary"),
                    min_value=item.get("salary_min"),
                    max_value=item.get("salary_max"),
                    currency="USD" if item.get("salary_min") or item.get("salary_max") else "",
                    period="year",
                ),
                date_posted=item.get("date"),
                categories=categories,
                job_url=item.get("url") or f"https://remoteok.com/remote-jobs/{item.get('id')}",
                description=item.get("description"),
                raw=item,
            )
        )
        if len(jobs) >= limit:
            break
    return jobs


def dedupe_jobs(jobs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen = set()
    result = []
    for job in jobs:
        key = job.get("job_url") or job.get("id")
        if key in seen:
            continue
        seen.add(key)
        result.append(job)
    return result


def write_outputs(jobs: list[dict[str, Any]], out_dir: Path, sources: list[str], errors: dict[str, str]) -> dict[str, str]:
    latest_dir = out_dir / "latest"
    raw_snapshot_dir = out_dir / "snapshots" / "raw"
    normalized_snapshot_dir = out_dir / "snapshots" / "normalized"
    for directory in [latest_dir, raw_snapshot_dir, normalized_snapshot_dir]:
        directory.mkdir(parents=True, exist_ok=True)

    stamp = dt.datetime.now(dt.UTC).strftime("%Y%m%d_%H%M%S")
    scraped_at = dt.datetime.now(dt.UTC).isoformat()

    payload = {
        "scraped_at_utc": scraped_at,
        "sources": sources,
        "count": len(jobs),
        "errors": errors,
        "jobs": jobs,
    }

    raw_snapshot = raw_snapshot_dir / f"{stamp}_remote_jobs.json"
    normalized_snapshot = normalized_snapshot_dir / f"{stamp}_remote_jobs.json"
    latest_raw = latest_dir / "raw_remote_jobs.json"
    latest_normalized = latest_dir / "normalized_remote_jobs.json"

    json_text = json.dumps(payload, ensure_ascii=False, indent=2)
    for path in [raw_snapshot, normalized_snapshot, latest_raw, latest_normalized]:
        path.write_text(json_text, encoding="utf-8")

    return {
        "raw_snapshot": str(raw_snapshot),
        "normalized_snapshot": str(normalized_snapshot),
        "latest_raw": str(latest_raw),
        "latest_normalized": str(latest_normalized),
    }


def parse_sources(value: str) -> list[str]:
    if value == "all":
        return list(SOURCES)
    sources = [part.strip().lower() for part in value.split(",") if part.strip()]
    unknown = sorted(set(sources) - set(SOURCES))
    if unknown:
        raise argparse.ArgumentTypeError(f"unknown sources: {', '.join(unknown)}")
    return sources


def main() -> int:
    parser = argparse.ArgumentParser(description="Scrape public remote job APIs into the JSON data layout.")
    parser.add_argument("--sources", type=parse_sources, default=list(SOURCES), help="Comma-separated sources: himalayas,remotive,remoteok, or all.")
    parser.add_argument("--keyword", default="python", help="Keyword used by supported sources and client-side filtering.")
    parser.add_argument("--limit", type=int, default=50, help="Maximum jobs per source.")
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR, help="Output directory.")
    parser.add_argument("--prefix", default="remote_jobs", help="Deprecated; kept for CLI compatibility.")
    args = parser.parse_args()

    jobs: list[dict[str, Any]] = []
    errors: dict[str, str] = {}

    source_funcs = {
        "himalayas": scrape_himalayas,
        "remotive": scrape_remotive,
        "remoteok": scrape_remoteok,
    }
    for source in args.sources:
        try:
            source_jobs = source_funcs[source](args.keyword, args.limit)
            print(f"source={source} count={len(source_jobs)}")
            jobs.extend(source_jobs)
        except Exception as exc:
            errors[source] = str(exc)
            print(f"source={source} error={exc}")

    jobs = dedupe_jobs(jobs)
    outputs = write_outputs(jobs, args.out_dir, args.sources, errors)
    print(json.dumps({"count": len(jobs), "errors": errors, "outputs": outputs}, ensure_ascii=False, indent=2))
    return 1 if errors and not jobs else 0


if __name__ == "__main__":
    raise SystemExit(main())
