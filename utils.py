"""
utils.py - Utility functions for the News Scraper Project.
Provides HTTP helpers, text cleaning, sentiment analysis,
CSV I/O, de-duplication, and category inference.
"""

import csv
import hashlib
import logging
import os
import random
import re
import time
from datetime import datetime
from urllib.parse import urljoin, urlparse

import pandas as pd
import requests
from bs4 import BeautifulSoup
from textblob import TextBlob

from config import (
    CSV_COLUMNS,
    CSV_FILE,
    DEFAULT_HEADERS,
    MAX_RETRIES,
    REQUEST_DELAY,
    REQUEST_TIMEOUT,
)

# ─────────────────────────────────────────────
# Logging setup
# ─────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  [%(levelname)s]  %(name)s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("news_scraper")


# ─────────────────────────────────────────────
# HTTP helpers
# ─────────────────────────────────────────────
def fetch_page(url: str, headers: dict = None, timeout: int = None) -> requests.Response | None:
    """
    Fetch a web page with retries, random delay, and error handling.
    Returns a Response object or None on failure.
    """
    headers = headers or DEFAULT_HEADERS.copy()
    timeout = timeout or REQUEST_TIMEOUT

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = requests.get(url, headers=headers, timeout=timeout)
            response.raise_for_status()
            return response

        except requests.exceptions.HTTPError as e:
            logger.warning(f"HTTP error for {url} (attempt {attempt}/{MAX_RETRIES}): {e}")
        except requests.exceptions.ConnectionError as e:
            logger.warning(f"Connection error for {url} (attempt {attempt}/{MAX_RETRIES}): {e}")
        except requests.exceptions.Timeout:
            logger.warning(f"Timeout for {url} (attempt {attempt}/{MAX_RETRIES})")
        except requests.exceptions.RequestException as e:
            logger.warning(f"Request error for {url} (attempt {attempt}/{MAX_RETRIES}): {e}")

    logger.error(f"Failed to fetch {url} after {MAX_RETRIES} attempts")
    return None


def get_soup(url: str, headers: dict = None) -> BeautifulSoup | None:
    """Fetch a page and return a BeautifulSoup object."""
    response = fetch_page(url, headers)
    if response is None:
        return None
    try:
        return BeautifulSoup(response.text, "lxml")
    except Exception:
        return BeautifulSoup(response.text, "html.parser")


def make_absolute_url(base_url: str, href: str) -> str:
    """Convert a relative URL to an absolute URL."""
    if href and not href.startswith(("http://", "https://")):
        return urljoin(base_url, href)
    return href


def is_valid_article_url(url: str, site_domain: str) -> bool:
    """
    Basic heuristic to determine if a URL is likely an article page.
    Filters out non-article links such as image galleries, videos, tags, etc.
    """
    if not url:
        return False

    parsed = urlparse(url)

    # Must be on the same domain (or subdomain)
    if site_domain not in parsed.netloc:
        return False

    # Exclude common non-article paths
    exclude_patterns = [
        "/video", "/videos/", "/gallery", "/photos/", "/photo-gallery",
        "/tag/", "/tags/", "/author/", "/search", "/login", "/signup",
        "/subscribe", "/newsletter", "/rss", "/feed", "/about",
        "/contact", "/privacy", "/terms", "/ads", "/advertise",
        "#", "javascript:", "mailto:", ".pdf", ".jpg", ".png",
        ".gif", ".mp4", ".mp3", "/live-tv", "/live/",
    ]
    lower_url = url.lower()
    for pat in exclude_patterns:
        if pat in lower_url:
            return False

    # URL should have a meaningful path (not just the homepage)
    path = parsed.path.strip("/")
    if not path or path.count("/") < 1:
        # Some sites like BBC use short paths for articles
        # Allow if path has at least some length
        if len(path) < 5:
            return False

    # ── HEURISTIC: Article URLs almost always have a hyphen (slug) or digits (ID) ──
    # If the path has NO hyphens, NO digits, and NO underscores, it is almost certainly 
    # a category/section page (like /sports/, /business/, /international/)
    if "-" not in path and "_" not in path and not re.search(r"\d", path):
        return False

    return True


# ─────────────────────────────────────────────
# Text cleaning
# ─────────────────────────────────────────────
def clean_text(text: str) -> str:
    """Strip extra whitespace and special characters from text."""
    if not text:
        return ""
    text = re.sub(r"\s+", " ", text)           # collapse whitespace
    text = re.sub(r"[\r\n\t]+", " ", text)     # remove control chars
    text = text.strip()
    return text


def truncate_content(content: str, max_chars: int = 5000) -> str:
    """Truncate article content to avoid overly large CSV cells."""
    if content and len(content) > max_chars:
        return content[:max_chars] + "..."
    return content


# ─────────────────────────────────────────────
# Category inference
# ─────────────────────────────────────────────

# Mapping of URL path keywords → category label
CATEGORY_KEYWORDS = {
    # ── World / International ──
    "world": "World",
    "international": "World",
    "global": "World",
    "middle-east": "World",
    "africa": "World",
    "asia": "World",
    "europe": "World",
    "latin-america": "World",
    "us-canada": "US News",
    # ── Politics ──
    "politics": "Politics",
    "political": "Politics",
    "politics-and-nation": "Politics",
    "elections": "Politics",
    # ── Business & Economy ──
    "business": "Business",
    "economy": "Business",
    "economics": "Business",
    "finance": "Business",
    "market": "Business",
    "markets": "Business",
    "money": "Business",
    "moneywatch": "Business",
    "wealth": "Business",
    "investing": "Business",
    "industry": "Business",
    "infrastructure": "Business",
    "personal-finance": "Business",
    "real-estate": "Real Estate",
    "real-estate-news": "Real Estate",
    "realestate": "Real Estate",
    "mf": "Business",
    "tax": "Business",
    "small-biz": "Business",
    # ── Technology ──
    "technology": "Technology",
    "tech": "Technology",
    "information-technology": "Technology",
    "open-source": "Technology",
    "ai": "AI",
    "ai-artificial-intelligence": "AI",
    "artificial-intelligence": "AI",
    "crypto": "Cryptocurrency",
    "cryptoworld": "Cryptocurrency",
    "cryptocurrency": "Cryptocurrency",
    "apps": "Technology",
    # ── Science ──
    "science": "Science",
    "sci-tech": "Science & Technology",
    "space": "Science",
    # ── Health ──
    "health": "Health",
    "health-fitness": "Health",
    "health-and-science": "Health",
    # ── Sports ──
    "sport": "Sports",
    "sports": "Sports",
    "cricket": "Sports",
    # ── Entertainment ──
    "entertainment": "Entertainment",
    "movies": "Entertainment",
    "entertainment-news": "Entertainment",
    "media-entertainment": "Entertainment",
    "arts": "Entertainment",
    "culture": "Entertainment",
    "film": "Entertainment",
    "music": "Entertainment",
    "games": "Gaming",
    "gaming": "Gaming",
    # ── Lifestyle ──
    "style": "Lifestyle",
    "lifestyle": "Lifestyle",
    "life-style": "Lifestyle",
    "life-and-style": "Lifestyle",
    "lifeandstyle": "Lifestyle",
    "living": "Lifestyle",
    "fashion": "Lifestyle",
    "food": "Lifestyle",
    "pursuits": "Lifestyle",
    # ── Travel ──
    "travel": "Travel",
    # ── Education ──
    "education": "Education",
    "education-today": "Education",
    # ── Environment ──
    "environment": "Environment",
    "climate": "Environment",
    "climate-crisis": "Environment",
    "climate-environment": "Environment",
    "climate-change": "Environment",
    "green": "Environment",
    "sustainability": "Environment",
    "earth": "Environment",
    "energy-and-environment": "Environment",
    # ── Religion & Astrology ──
    "religion": "Religion",
    "astrology": "Astrology",
    # ── Crime ──
    "crime": "Crime",
    # ── Automobiles ──
    "auto": "Automobiles",
    "automobile": "Automobiles",
    "cars": "Automobiles",
    "transportation": "Transportation",
    # ── Opinion ──
    "opinion": "Opinion",
    "opinions": "Opinion",
    "commentisfree": "Opinion",
    "breakingviews": "Opinion",
    "explained": "Explained",
    # ── Defence ──
    "defence": "Defence",
    # ── Other ──
    "legal": "Legal",
    "media": "Media",
    "us-news": "US News",
    "us": "US News",
    "uk-news": "UK News",
    "india": "India",
    "india-news": "India",
    "national": "National",
    "gujarat": "Gujarat",
    "cities": "Cities",
    "states": "States",
    "dc-md-va": "Local",
    "local": "Local",
    "nri": "NRI",
    "startups": "Startups",
    "venture": "Venture Capital",
    "reviews": "Reviews",
    "features": "Features",
    "investigations": "Investigations",
    "human-rights": "Human Rights",
    "global-development": "Global Development",
    "security": "Cybersecurity",
    "gear": "Gadgets",
    "hardware": "Technology",
    "policy": "Policy",
    "tech-policy": "Policy",
    "ideas": "Ideas",
    "design": "Design",
    "io9": "Sci-Fi",
    "oddities": "Oddities",
    "strange-news": "Oddities",
    "weather": "Weather",
    "obituaries": "Obituaries",
    "citylab": "Urban",
    "businessweek": "Business",
    "research": "Research",
    "apple": "Technology",
    "google": "Technology",
    "microsoft": "Technology",
}


def infer_category(url: str, sub_link: str = "") -> str:
    """
    Infer the news category from the sub-link URL or article URL.
    Falls back to 'General' if no match is found.
    """
    # Check sub_link first (more reliable for category)
    check_url = sub_link if sub_link else url
    path = urlparse(check_url).path.lower().strip("/")
    parts = path.split("/")

    for part in reversed(parts):
        part_clean = part.strip()
        if part_clean in CATEGORY_KEYWORDS:
            return CATEGORY_KEYWORDS[part_clean]

    return "General"


# ─────────────────────────────────────────────
# Sentiment analysis
# ─────────────────────────────────────────────
def analyze_sentiment(text: str) -> tuple[str, float]:
    """
    Perform sentiment analysis on text using TextBlob.
    Returns (label, polarity_score).
    Label is 'Positive', 'Negative', or 'Neutral'.
    """
    if not text:
        return ("Neutral", 0.0)

    try:
        # Use first 1000 chars for performance
        blob = TextBlob(text[:1000])
        polarity = blob.sentiment.polarity

        if polarity > 0.1:
            label = "Positive"
        elif polarity < -0.1:
            label = "Negative"
        else:
            label = "Neutral"

        return (label, round(polarity, 4))
    except Exception:
        return ("Neutral", 0.0)


# ─────────────────────────────────────────────
# CSV I/O and de-duplication
# ─────────────────────────────────────────────
from database import get_existing_urls, get_existing_headlines, insert_articles

def save_articles(articles: list[dict]):
    """
    Save a list of article dicts to MongoDB.
    Performs de-duplication based on URL and headline using the DB layer.
    """
    if not articles:
        logger.info("No new articles to save.")
        return

    # Load existing data from MongoDB for dedup
    existing_urls = get_existing_urls()
    existing_headlines = get_existing_headlines()

    new_articles = []
    for article in articles:
        url = article.get("url", "")
        headline = article.get("headline", "").lower()

        # Skip if URL or headline already exists
        if url in existing_urls:
            continue
        if headline and headline in existing_headlines:
            continue

        # ── Enforce defaults (safety net) ──
        if not article.get("author") or str(article["author"]).strip() == "":
            article["author"] = "Unknown"
        if not article.get("date") or str(article["date"]).strip() == "":
            article["date"] = "N/A"

        # ── Add sentiment via TextBlob ──
        content = article.get("content", "")
        sentiment_label, sentiment_polarity = analyze_sentiment(
            article.get("headline", "") + " " + content
        )
        article["sentiment"] = sentiment_label
        article["sentiment_polarity"] = sentiment_polarity
        article["scraped_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Truncate content
        article["content"] = truncate_content(content)

        # Clean all text fields
        for key in ["headline", "author", "content"]:
            article[key] = clean_text(article.get(key, ""))

        new_articles.append(article)
        existing_urls.add(url)
        existing_headlines.add(headline)

    if new_articles:
        # ── Save exclusively to MongoDB ──
        try:
            insert_articles(new_articles)
        except Exception as e:
            logger.error(f"MongoDB save failed: {e}")
    else:
        logger.info("All articles already exist (duplicates skipped).")


def load_all_articles() -> pd.DataFrame:
    """
    Load all articles from MongoDB into a pandas DataFrame.
    (Kept for compatibility with old scripts)
    """
    try:
        from database import is_connected, get_collection
        if is_connected():
            collection = get_collection()
            cursor = collection.find({}, {"_id": 0})
            docs = list(cursor)
            if docs:
                df = pd.DataFrame(docs)
                # Ensure correct columns
                for col in CSV_COLUMNS:
                    if col not in df.columns:
                        df[col] = ""
                return df[CSV_COLUMNS]
    except Exception as e:
        logger.error(f"MongoDB read failed: {e}")
        
    return pd.DataFrame(columns=CSV_COLUMNS)


def filter_articles(
    df: pd.DataFrame,
    keyword: str = "",
    category: str = "",
    source: str = "",
    sentiment: str = "",
) -> pd.DataFrame:
    """
    Filter articles by keyword, category, source, and sentiment.
    Returns a filtered DataFrame.
    """
    if keyword:
        keyword_lower = keyword.lower()
        mask = (
            df["headline"].str.lower().str.contains(keyword_lower, na=False)
            | df["content"].str.lower().str.contains(keyword_lower, na=False)
        )
        df = df[mask]

    if category:
        df = df[df["category"].str.lower() == category.lower()]

    if source:
        df = df[df["source"].str.lower() == source.lower()]

    if sentiment:
        df = df[df["sentiment"].str.lower() == sentiment.lower()]

    return df
