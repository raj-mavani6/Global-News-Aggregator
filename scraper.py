"""
scraper.py - Main scraping orchestrator for the News Scraper Project.
Uses ThreadPoolExecutor for FAST parallel scraping across sites and articles.
"""

import sys
import time
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from urllib.parse import urlparse

from config import MAX_ARTICLES_PER_SUB, MAX_WORKERS_SITES, MAX_WORKERS_ARTICLES
from parser import SCRAPER_REGISTRY, extract_article_links_generic, extract_article_generic
from database import get_all_sources
from utils import (
    get_soup,
    infer_category,
    save_articles,
    logger,
)


def _fetch_single_article(article_url, article_extractor, name, category):
    """Worker function: fetch and parse a single article URL."""
    try:
        article_soup = get_soup(article_url)
        if article_soup is None:
            return None

        if article_extractor:
            article_data = article_extractor(article_soup, article_url)
        else:
            article_data = extract_article_generic(article_soup, article_url)

        if not article_data.get("headline"):
            return None

        # ── Set metadata fields ──
        article_data["source"] = name
        article_data["url"] = article_url
        article_data["category"] = category

        # ── Enforce defaults for missing fields ──
        if not article_data.get("author") or article_data["author"].strip() == "":
            article_data["author"] = "Unknown"
        if not article_data.get("date") or article_data["date"].strip() == "":
            article_data["date"] = "N/A"
        if not article_data.get("content") or article_data["content"].strip() == "":
            article_data["content"] = ""

        logger.info(f"    ✓ {article_data['headline'][:70]}...")
        return article_data

    except Exception as e:
        logger.error(f"    ✗ Error parsing {article_url}: {e}")
        return None


def scrape_site(site_config: dict) -> list[dict]:
    """
    Scrape a single news website using parallel article fetching.
    """
    name = site_config["name"]
    scraper_key = site_config["scraper_key"]
    sub_links = site_config["sub_links"]

    if scraper_key in SCRAPER_REGISTRY:
        link_extractor, article_extractor = SCRAPER_REGISTRY[scraper_key]
    else:
        link_extractor = None
        article_extractor = None

    site_domain = urlparse(site_config["main_link"]).netloc.replace("www.", "")
    articles = []

    logger.info(f"{'='*50}")
    logger.info(f"Scraping: {name} ({len(sub_links)} sub-links)")
    logger.info(f"{'='*50}")

    for sub_link in sub_links:
        try:
            category = infer_category(sub_link)
            logger.info(f"  Sub: {sub_link} [{category}]")

            soup = get_soup(sub_link)
            if soup is None:
                logger.warning(f"  Could not fetch: {sub_link}")
                continue

            if link_extractor:
                article_urls = link_extractor(soup, sub_link, MAX_ARTICLES_PER_SUB)
            else:
                article_urls = extract_article_links_generic(
                    soup, sub_link, site_domain, MAX_ARTICLES_PER_SUB
                )

            logger.info(f"  Found {len(article_urls)} article links")

            if not article_urls:
                continue

            # ── PARALLEL article fetching ──
            with ThreadPoolExecutor(max_workers=MAX_WORKERS_ARTICLES) as executor:
                futures = {
                    executor.submit(
                        _fetch_single_article, url, article_extractor, name, category
                    ): url
                    for url in article_urls
                }
                for future in as_completed(futures):
                    result = future.result()
                    if result:
                        articles.append(result)

        except Exception as e:
            logger.error(f"  Error processing sub-link {sub_link}: {e}")
            continue

    logger.info(f"  Total from {name}: {len(articles)}")
    return articles


def scrape_all_sites(sites: list[dict] = None) -> int:
    """
    Scrape all sites IN PARALLEL and save results to CSV.
    """
    if sites is None:
        all_db_sites = get_all_sources()
        sites = [s for s in all_db_sites if s.get("is_enabled", True)]
        if not sites:
            logger.warning("No enabled sites found in database.")
            return 0

    all_articles = []
    start_time = time.time()

    logger.info(f"\n{'#'*60}")
    logger.info(f"Starting FAST parallel scrape at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"Total sites: {len(sites)} | Site workers: {MAX_WORKERS_SITES} | Article workers: {MAX_WORKERS_ARTICLES}")
    logger.info(f"{'#'*60}\n")

    # ── PARALLEL site scraping ──
    with ThreadPoolExecutor(max_workers=MAX_WORKERS_SITES) as executor:
        future_to_site = {
            executor.submit(scrape_site, site): site["name"]
            for site in sites
        }
        for future in as_completed(future_to_site):
            site_name = future_to_site[future]
            try:
                articles = future.result()
                all_articles.extend(articles)
                logger.info(f"✅ {site_name}: {len(articles)} articles")
            except Exception as e:
                logger.error(f"❌ {site_name} failed: {e}")
                traceback.print_exc()

    # Save all articles to CSV (with dedup)
    save_articles(all_articles)

    elapsed = time.time() - start_time
    logger.info(f"\n{'#'*60}")
    logger.info(f"Scrape complete!")
    logger.info(f"Total articles: {len(all_articles)}")
    logger.info(f"Time: {elapsed:.1f} seconds ({elapsed/60:.1f} min)")
    logger.info(f"{'#'*60}\n")

    return len(all_articles)


def scrape_single_site(scraper_key: str) -> int:
    """Scrape a single site by its scraper_key."""
    all_db_sites = get_all_sources()
    for site in all_db_sites:
        if site["scraper_key"] == scraper_key:
            articles = scrape_site(site)
            save_articles(articles)
            return len(articles)

    logger.error(f"No site found with scraper_key: {scraper_key}")
    return 0


def scrape_by_category_name(category: str) -> int:
    """
    Scrape sites matching a category group name:
    'international', 'indian', 'regional', 'tech', or 'all'.
    """
    all_db_sites = get_all_sources()
    
    if category.lower() == "all":
        sites = [s for s in all_db_sites if s.get("is_enabled", True)]
    else:
        # Match against the 'group' field in DB (case-insensitive)
        sites = [
            s for s in all_db_sites 
            if s.get("is_enabled", True) and s.get("group", "").lower() == category.lower()
        ]

    if not sites:
        logger.error(f"No enabled sites found for category: {category}")
        return 0

    return scrape_all_sites(sites)


def scrape_with_filters(
    keyword: str = "",
    source_name: str = "",
    article_category: str = "",
    sentiment_filter: str = "",
) -> int:
    """
    Smart filtered scraping:
      - source_name: only scrape that specific news site (e.g. "BBC News")
      - article_category: only scrape sub-links matching this category (e.g. "World", "Business")
      - keyword: after scraping, keep only articles whose headline/content contains this keyword
      - sentiment_filter: after scraping, keep only articles matching this sentiment

    All filters can be combined.
    """
    from utils import analyze_sentiment, clean_text, truncate_content

    start_time = time.time()

    all_db_sites = get_all_sources()
    
    # ── Step 1: Filter SITES by source name ──
    if source_name:
        sites = [s for s in all_db_sites if s["name"].lower() == source_name.lower()]
        if not sites:
            logger.error(f"No site found with name: {source_name}")
            return 0
        logger.info(f"🔍 Filtering to source: {source_name}")
    else:
        sites = [s for s in all_db_sites if s.get("is_enabled", True)]

    # ── Step 2: Filter SUB-LINKS by article category ──
    if article_category:
        filtered_sites = []
        cat_lower = article_category.lower()
        for site in sites:
            matching_subs = []
            for sub in site["sub_links"]:
                inferred = infer_category(sub).lower()
                if inferred == cat_lower or cat_lower in sub.lower():
                    matching_subs.append(sub)

            if matching_subs:
                site_copy = dict(site)
                site_copy["sub_links"] = matching_subs
                filtered_sites.append(site_copy)

        if not filtered_sites:
            # Fallback: if no sub-links match, scrape all sub-links from the filtered sites
            logger.warning(f"No sub-links match category '{article_category}', scraping all sub-links instead")
            filtered_sites = sites

        sites = filtered_sites
        logger.info(f"🔍 Filtering to category: {article_category} ({len(sites)} sites with matching sub-links)")

    # ── Step 3: Scrape the filtered sites ──
    total_subs = sum(len(s["sub_links"]) for s in sites)
    logger.info(f"\n{'#'*60}")
    logger.info(f"FILTERED SCRAPE | Sites: {len(sites)} | Sub-links: {total_subs}")
    logger.info(f"  Keyword: '{keyword or 'any'}' | Source: '{source_name or 'all'}' | Category: '{article_category or 'all'}' | Sentiment: '{sentiment_filter or 'all'}'")
    logger.info(f"{'#'*60}\n")

    all_articles = []

    with ThreadPoolExecutor(max_workers=MAX_WORKERS_SITES) as executor:
        future_to_site = {
            executor.submit(scrape_site, site): site["name"]
            for site in sites
        }
        for future in as_completed(future_to_site):
            site_name = future_to_site[future]
            try:
                articles = future.result()
                all_articles.extend(articles)
                logger.info(f"✅ {site_name}: {len(articles)} articles")
            except Exception as e:
                logger.error(f"❌ {site_name} failed: {e}")
                traceback.print_exc()

    logger.info(f"\n📦 Total scraped (before filters): {len(all_articles)}")

    # ── Step 4: Filter by KEYWORD ──
    if keyword:
        kw_lower = keyword.lower()
        before_count = len(all_articles)
        all_articles = [
            a for a in all_articles
            if kw_lower in a.get("headline", "").lower()
            or kw_lower in a.get("content", "").lower()
        ]
        logger.info(f"🔍 Keyword filter '{keyword}': {before_count} → {len(all_articles)} articles")

    # ── Step 5: Filter by SENTIMENT ──
    if sentiment_filter:
        # Need to compute sentiment first for filtering
        for article in all_articles:
            if "sentiment" not in article or not article["sentiment"]:
                from utils import analyze_sentiment
                content = article.get("content", "")
                label, polarity = analyze_sentiment(
                    article.get("headline", "") + " " + content
                )
                article["sentiment"] = label
                article["sentiment_polarity"] = polarity

        before_count = len(all_articles)
        all_articles = [
            a for a in all_articles
            if a.get("sentiment", "").lower() == sentiment_filter.lower()
        ]
        logger.info(f"🔍 Sentiment filter '{sentiment_filter}': {before_count} → {len(all_articles)} articles")

    # ── Step 6: Save results ──
    save_articles(all_articles)

    elapsed = time.time() - start_time
    logger.info(f"\n{'#'*60}")
    logger.info(f"Filtered scrape complete!")
    logger.info(f"Final articles saved: {len(all_articles)}")
    logger.info(f"Time: {elapsed:.1f}s ({elapsed/60:.1f} min)")
    logger.info(f"{'#'*60}\n")

    return len(all_articles)


# ─────────────────────────────────────────────
# CLI entry point
# ─────────────────────────────────────────────
if __name__ == "__main__":
    """
    Usage:
        python scraper.py                  # Scrape all sites (parallel)
        python scraper.py all              # Scrape all sites
        python scraper.py international    # International sites only
        python scraper.py indian           # Indian sites only
        python scraper.py regional         # Regional/Gujarati only
        python scraper.py tech             # Tech sites only
        python scraper.py --site bbc       # Single site
    """
    if len(sys.argv) > 1:
        arg = sys.argv[1]

        if arg == "--site" and len(sys.argv) > 2:
            site_key = sys.argv[2]
            print(f"Scraping single site: {site_key}")
            count = scrape_single_site(site_key)
        else:
            print(f"Scraping category: {arg}")
            count = scrape_by_category_name(arg)
    else:
        print("Scraping all enabled sites (parallel mode)...")
        count = scrape_all_sites()

    print(f"\nDone! {count} articles scraped.")
