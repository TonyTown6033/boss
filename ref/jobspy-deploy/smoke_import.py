from jobspy import scrape_jobs


def main() -> None:
    print("jobspy import ok")
    print(f"scrape_jobs callable: {callable(scrape_jobs)}")


if __name__ == "__main__":
    main()
