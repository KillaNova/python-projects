"""
Web Scraper — prices, news, job listings
Uses requests + BeautifulSoup. Run in one of three modes:
  python main.py prices  --url <url> --selector <css>
  python main.py news
  python main.py jobs    --keyword <kw> --location <loc>
"""

import argparse
import json
import sys
from datetime import datetime

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    sys.exit("Install dependencies first:\n  pip install requests beautifulsoup4")

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    )
}


# ── helpers ───────────────────────────────────────────────────────────────────

def get_soup(url: str) -> BeautifulSoup:
    resp = requests.get(url, headers=HEADERS, timeout=15)
    resp.raise_for_status()
    return BeautifulSoup(resp.text, "html.parser")


def print_json(data) -> None:
    print(json.dumps(data, indent=2, ensure_ascii=False))


# ── prices ────────────────────────────────────────────────────────────────────

def scrape_prices(url: str, selector: str) -> list[dict]:
    """
    Generic price scraper.  Point it at any product-listing page and give
    a CSS selector that matches the price elements.
    Example:
      --url "https://books.toscrape.com" --selector ".price_color"
    """
    soup = get_soup(url)
    results = []
    for el in soup.select(selector):
        text = el.get_text(strip=True)
        results.append({"price_text": text, "source": url})
    return results


# ── news ──────────────────────────────────────────────────────────────────────

def scrape_hn_news(limit: int = 20) -> list[dict]:
    """Scrapes top stories from Hacker News front page (no API key needed)."""
    soup = get_soup("https://news.ycombinator.com/")
    items = []
    for row in soup.select("tr.athing")[:limit]:
        title_tag = row.select_one(".titleline > a")
        if not title_tag:
            continue
        rank_tag = row.select_one(".rank")
        score_row = row.find_next_sibling("tr")
        score_tag = score_row.select_one(".score") if score_row else None
        items.append({
            "rank": rank_tag.get_text(strip=True).rstrip(".") if rank_tag else "?",
            "title": title_tag.get_text(strip=True),
            "url": title_tag.get("href", ""),
            "score": score_tag.get_text(strip=True) if score_tag else "n/a",
        })
    return items


# ── jobs ──────────────────────────────────────────────────────────────────────

def scrape_remotive_jobs(keyword: str = "", limit: int = 20) -> list[dict]:
    """
    Scrapes remote job listings from Remotive (remotive.com/remote-jobs).
    Filter by keyword if provided.
    """
    url = "https://remotive.com/remote-jobs"
    if keyword:
        url += f"?search={requests.utils.quote(keyword)}"
    soup = get_soup(url)
    jobs = []
    for card in soup.select("li.job-list-item")[:limit]:
        title_tag = card.select_one("h2, .position")
        company_tag = card.select_one(".company_name, .company")
        tag_els = card.select(".tag")
        link_tag = card.select_one("a")
        jobs.append({
            "title": title_tag.get_text(strip=True) if title_tag else "N/A",
            "company": company_tag.get_text(strip=True) if company_tag else "N/A",
            "tags": [t.get_text(strip=True) for t in tag_els],
            "url": "https://remotive.com" + link_tag["href"] if link_tag and link_tag.get("href") else "",
        })
    return jobs


# ── CLI ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Web scraper: prices | news | jobs")
    sub = parser.add_subparsers(dest="mode", required=True)

    p_prices = sub.add_parser("prices", help="Scrape prices from a product page")
    p_prices.add_argument("--url", required=True, help="Page URL")
    p_prices.add_argument("--selector", default=".price", help="CSS selector for price elements")
    p_prices.add_argument("--limit", type=int, default=50)

    p_news = sub.add_parser("news", help="Top stories from Hacker News")
    p_news.add_argument("--limit", type=int, default=20)

    p_jobs = sub.add_parser("jobs", help="Remote job listings from Remotive")
    p_jobs.add_argument("--keyword", default="", help="Filter by keyword")
    p_jobs.add_argument("--limit", type=int, default=20)

    args = parser.parse_args()
    print(f"# Scraped at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    if args.mode == "prices":
        data = scrape_prices(args.url, args.selector)
        print_json(data[:args.limit])

    elif args.mode == "news":
        data = scrape_hn_news(args.limit)
        print_json(data)

    elif args.mode == "jobs":
        data = scrape_remotive_jobs(args.keyword, args.limit)
        print_json(data)


if __name__ == "__main__":
    main()
