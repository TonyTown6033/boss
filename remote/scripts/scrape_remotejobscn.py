#!/usr/bin/env python3
import csv
import datetime as dt
import html
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


BASE_URL = "https://remotejobscn.com"
OUT_DIR = Path("data")
USER_AGENT = "Mozilla/5.0 (compatible; RemoteJobsCNResearch/1.0)"


def fetch(url: str, retries: int = 3) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    last_error = None
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=25) as resp:
                return resp.read().decode("utf-8", errors="replace")
        except (urllib.error.URLError, TimeoutError) as exc:
            last_error = exc
            time.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"fetch failed: {url}: {last_error}")


def clean_text(value: str) -> str:
    value = re.sub(r"<[^>]+>", " ", value)
    value = html.unescape(value)
    return re.sub(r"\s+", " ", value).strip()


def extract_job_links(page_html: str) -> list[str]:
    ids = re.findall(r'href="(/jobs/[0-9a-f-]{36})"', page_html)
    seen = set()
    links = []
    for path in ids:
        url = urllib.parse.urljoin(BASE_URL, path)
        if url not in seen:
            seen.add(url)
            links.append(url)
    return links


def extract_json_ld(page_html: str) -> dict:
    blocks = re.findall(
        r'<script\s+type="application/ld\+json">(.*?)</script>',
        page_html,
        flags=re.S,
    )
    for block in blocks:
        try:
            data = json.loads(html.unescape(block))
        except json.JSONDecodeError:
            continue
        if data.get("@type") == "JobPosting":
            return data
    return {}


def extract_dl_value(page_html: str, label: str) -> str:
    pattern = (
        r"<dt[^>]*>\s*"
        + re.escape(label)
        + r"\s*</dt>\s*<dd[^>]*>(.*?)</dd>"
    )
    match = re.search(pattern, page_html, flags=re.S)
    return clean_text(match.group(1)) if match else ""


def extract_tags(page_html: str) -> list[str]:
    tags = re.findall(
        r'<meta\s+property="article:tag"\s+content="([^"]+)"',
        page_html,
    )
    return [html.unescape(tag) for tag in tags]


def scrape_listing_pages(max_pages: int = 10) -> tuple[list[str], list[dict]]:
    seen = set()
    links = []
    pages = []

    for page in range(1, max_pages + 1):
        url = BASE_URL if page == 1 else f"{BASE_URL}/?page={page}"
        page_html = fetch(url)
        page_links = extract_job_links(page_html)
        pages.append({"page": page, "url": url, "job_count": len(page_links)})

        new_count = 0
        for link in page_links:
            if link not in seen:
                seen.add(link)
                links.append(link)
                new_count += 1

        has_next = f'href="/?page={page + 1}"' in page_html
        print(f"page={page} found={len(page_links)} new={new_count} total={len(links)}")
        if not has_next:
            break
        time.sleep(0.3)

    return links, pages


def scrape_job(url: str) -> dict:
    page_html = fetch(url)
    data = extract_json_ld(page_html)
    job_id = url.rstrip("/").split("/")[-1]
    org = data.get("hiringOrganization") or {}

    return {
        "id": job_id,
        "title": data.get("title", ""),
        "company": org.get("name", ""),
        "source": extract_dl_value(page_html, "来源"),
        "source_url": org.get("sameAs", ""),
        "remote": extract_dl_value(page_html, "Remote"),
        "type": extract_dl_value(page_html, "Type") or data.get("employmentType", ""),
        "salary": extract_dl_value(page_html, "Salary"),
        "date_posted": data.get("datePosted", ""),
        "valid_through": data.get("validThrough", ""),
        "categories": extract_tags(page_html),
        "description": data.get("description", ""),
        "direct_apply": data.get("directApply"),
        "job_url": url,
        "status": "published" if "状态：<!-- -->published" in page_html or "状态：published" in clean_text(page_html) else "",
    }


def write_outputs(jobs: list[dict], pages: list[dict]) -> dict:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    stamp = dt.datetime.now(dt.UTC).strftime("%Y%m%d_%H%M%S")
    base = OUT_DIR / f"remotejobscn_jobs_{stamp}"

    payload = {
        "source": BASE_URL,
        "scraped_at_utc": dt.datetime.now(dt.UTC).isoformat(),
        "listing_pages": pages,
        "count": len(jobs),
        "jobs": jobs,
    }
    json_path = base.with_suffix(".json")
    csv_path = base.with_suffix(".csv")
    md_path = base.with_suffix(".md")

    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    fieldnames = [
        "id",
        "title",
        "company",
        "source",
        "source_url",
        "remote",
        "type",
        "salary",
        "date_posted",
        "categories",
        "job_url",
        "description",
    ]
    with csv_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for job in jobs:
            row = dict(job)
            row["categories"] = ",".join(job.get("categories") or [])
            writer.writerow(row)

    lines = [
        "# RemoteJobsCN Jobs",
        "",
        f"- source: {BASE_URL}",
        f"- scraped_at_utc: {payload['scraped_at_utc']}",
        f"- count: {len(jobs)}",
        "",
    ]
    for i, job in enumerate(jobs, 1):
        categories = ", ".join(job.get("categories") or [])
        lines.extend(
            [
                f"## {i}. {job.get('title') or '(untitled)'}",
                "",
                f"- company: {job.get('company')}",
                f"- source: {job.get('source')}",
                f"- date_posted: {job.get('date_posted')}",
                f"- remote: {job.get('remote')}",
                f"- type: {job.get('type')}",
                f"- salary: {job.get('salary')}",
                f"- categories: {categories}",
                f"- job_url: {job.get('job_url')}",
                f"- source_url: {job.get('source_url')}",
                "",
                clean_text(job.get("description") or ""),
                "",
            ]
        )
    md_path.write_text("\n".join(lines), encoding="utf-8")

    latest_json = OUT_DIR / "remotejobscn_jobs_latest.json"
    latest_csv = OUT_DIR / "remotejobscn_jobs_latest.csv"
    latest_md = OUT_DIR / "remotejobscn_jobs_latest.md"
    latest_json.write_text(json_path.read_text(encoding="utf-8"), encoding="utf-8")
    latest_csv.write_text(csv_path.read_text(encoding="utf-8"), encoding="utf-8")
    latest_md.write_text(md_path.read_text(encoding="utf-8"), encoding="utf-8")

    return {
        "json": str(json_path),
        "csv": str(csv_path),
        "md": str(md_path),
        "latest_json": str(latest_json),
        "latest_csv": str(latest_csv),
        "latest_md": str(latest_md),
    }


def main() -> int:
    links, pages = scrape_listing_pages()
    jobs = []
    for index, url in enumerate(links, 1):
        print(f"job={index}/{len(links)} {url}")
        jobs.append(scrape_job(url))
        time.sleep(0.2)

    outputs = write_outputs(jobs, pages)
    print(json.dumps({"count": len(jobs), "outputs": outputs}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
