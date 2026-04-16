"""
parser.py - HTML parsing functions for extracting article data.
Contains generic and site-specific parsing strategies for extracting
article links from listing pages and article details from article pages.
"""

import re
from urllib.parse import urlparse, urljoin

from bs4 import BeautifulSoup, Tag

from utils import (
    clean_text,
    get_soup,
    is_valid_article_url,
    make_absolute_url,
    infer_category,
    logger,
)


# ─────────────────────────────────────────────────────
# Generic article link extraction
# ─────────────────────────────────────────────────────
def extract_article_links_generic(soup: BeautifulSoup, base_url: str, site_domain: str, max_links: int = 10) -> list[str]:
    """
    Generic strategy: find <a> tags that look like article links.
    Filters by domain, path depth, and common heuristics.
    """
    links = set()
    if soup is None:
        return []

    for a_tag in soup.find_all("a", href=True):
        href = a_tag["href"]
        url = make_absolute_url(base_url, href)

        if is_valid_article_url(url, site_domain):
            links.add(url)

        if len(links) >= max_links:
            break

    return list(links)[:max_links]


# ─────────────────────────────────────────────────────
# Generic article content extraction
# ─────────────────────────────────────────────────────
def extract_article_generic(soup: BeautifulSoup, url: str) -> dict:
    """
    Generic article parser. Tries multiple common selectors used by most
    news websites to extract headline, author, date, and content.
    """
    article = {
        "headline": "",
        "author": "",
        "date": "",
        "content": "",
    }

    if soup is None:
        return article

    # ── Headline ──
    # Try <h1> first, then og:title, then <title>
    h1 = soup.find("h1")
    if h1:
        article["headline"] = clean_text(h1.get_text())
    else:
        og_title = soup.find("meta", property="og:title")
        if og_title and og_title.get("content"):
            article["headline"] = clean_text(og_title["content"])
        else:
            title_tag = soup.find("title")
            if title_tag:
                article["headline"] = clean_text(title_tag.get_text())

    # ── Author ──
    author_selectors = [
        {"name": "meta", "attrs": {"name": "author"}},
        {"name": "meta", "attrs": {"property": "article:author"}},
        {"name": "meta", "attrs": {"name": "byl"}},
        {"name": "span", "attrs": {"class": re.compile(r"author|byline|writer", re.I)}},
        {"name": "a", "attrs": {"class": re.compile(r"author|byline|writer", re.I)}},
        {"name": "div", "attrs": {"class": re.compile(r"author|byline|writer", re.I)}},
        {"name": "p", "attrs": {"class": re.compile(r"author|byline|writer", re.I)}},
        {"name": "span", "attrs": {"itemprop": "author"}},
        {"name": "a", "attrs": {"rel": "author"}},
    ]
    for selector in author_selectors:
        elem = soup.find(selector["name"], attrs=selector.get("attrs", {}))
        if elem:
            if elem.name == "meta":
                author = elem.get("content", "")
            else:
                author = elem.get_text()
            author = clean_text(author)
            if author and len(author) < 100:
                article["author"] = author
                break

    # ── Date ──
    date_selectors = [
        {"name": "meta", "attrs": {"property": "article:published_time"}},
        {"name": "meta", "attrs": {"name": "publish-date"}},
        {"name": "meta", "attrs": {"name": "date"}},
        {"name": "meta", "attrs": {"property": "og:article:published_time"}},
        {"name": "time", "attrs": {}},
        {"name": "span", "attrs": {"class": re.compile(r"date|time|publish", re.I)}},
        {"name": "div", "attrs": {"class": re.compile(r"date|time|publish", re.I)}},
        {"name": "p", "attrs": {"class": re.compile(r"date|time|publish", re.I)}},
    ]
    for selector in date_selectors:
        elem = soup.find(selector["name"], attrs=selector.get("attrs", {}))
        if elem:
            if elem.name == "meta":
                date_str = elem.get("content", "")
            elif elem.name == "time":
                date_str = elem.get("datetime", "") or elem.get_text()
            else:
                date_str = elem.get_text()
            date_str = clean_text(date_str)
            if date_str:
                article["date"] = date_str[:60]  # trim overly long dates
                break

    # ── Content ──
    content_selectors = [
        "article",
        '[itemprop="articleBody"]',
        ".article-body",
        ".article__body",
        ".article-content",
        ".story-body",
        ".story-content",
        ".post-content",
        ".entry-content",
        ".content-body",
        ".body-text",
        ".article__content",
        ".article-text",
        "#article-body",
        ".ssrcss-11r1m41-RichTextComponentWrapper",  # BBC
        ".zn-body__paragraph",        # CNN
        '[data-testid="article-body"]',  # Various
    ]

    content_parts = []
    for sel in content_selectors:
        container = soup.select_one(sel)
        if container:
            # Get all paragraphs within the container
            paragraphs = container.find_all("p")
            if paragraphs:
                for p in paragraphs:
                    text = clean_text(p.get_text())
                    if text and len(text) > 20:
                        content_parts.append(text)
                break

    # Fallback: get all <p> tags from the page
    if not content_parts:
        for p in soup.find_all("p"):
            text = clean_text(p.get_text())
            if text and len(text) > 40:
                content_parts.append(text)
            if len(content_parts) >= 20:
                break

    article["content"] = " ".join(content_parts)

    return article


# ═══════════════════════════════════════════════════════
# SITE-SPECIFIC LINK EXTRACTORS
# These override the generic strategy for better accuracy
# ═══════════════════════════════════════════════════════

# ── BBC ──
def extract_links_bbc(soup, base_url, max_links=10):
    links = set()
    for a in soup.find_all("a", href=True):
        href = a["href"]
        url = make_absolute_url(base_url, href)
        if re.search(r"bbc\.com/news/articles/|bbc\.com/sport/", url):
            links.add(url)
        elif re.search(r"bbc\.com/news/[a-z]+-\d+", url):
            links.add(url)
        if len(links) >= max_links:
            break
    return list(links)[:max_links]


def extract_article_bbc(soup, url):
    article = extract_article_generic(soup, url)
    # BBC-specific overrides
    if not article["content"]:
        blocks = soup.find_all("div", {"data-component": "text-block"})
        parts = []
        for block in blocks:
            for p in block.find_all("p"):
                text = clean_text(p.get_text())
                if text:
                    parts.append(text)
        article["content"] = " ".join(parts)
    return article


# ── CNN ──
def extract_links_cnn(soup, base_url, max_links=10):
    links = set()
    for a in soup.find_all("a", href=True):
        href = a["href"]
        url = make_absolute_url("https://edition.cnn.com", href)
        if re.search(r"cnn\.com/\d{4}/\d{2}/\d{2}/", url):
            links.add(url)
        if len(links) >= max_links:
            break
    return list(links)[:max_links]


def extract_article_cnn(soup, url):
    article = extract_article_generic(soup, url)
    if not article["content"]:
        paragraphs = soup.find_all("p", class_=re.compile(r"paragraph"))
        parts = [clean_text(p.get_text()) for p in paragraphs if clean_text(p.get_text())]
        article["content"] = " ".join(parts)
    return article


# ── Reuters ──
def extract_links_reuters(soup, base_url, max_links=10):
    links = set()
    for a in soup.find_all("a", href=True):
        href = a["href"]
        url = make_absolute_url("https://www.reuters.com", href)
        parsed = urlparse(url)
        path = parsed.path.strip("/")
        # Reuters articles have date patterns in path
        if re.search(r"\d{4}-\d{2}-\d{2}", path) or (path.count("/") >= 2 and "reuters.com" in parsed.netloc):
            if is_valid_article_url(url, "reuters.com"):
                links.add(url)
        if len(links) >= max_links:
            break
    return list(links)[:max_links]


def extract_article_reuters(soup, url):
    article = extract_article_generic(soup, url)
    if not article["content"]:
        body = soup.find("div", class_=re.compile(r"article-body|ArticleBody", re.I))
        if body:
            parts = [clean_text(p.get_text()) for p in body.find_all("p") if clean_text(p.get_text())]
            article["content"] = " ".join(parts)
    return article


# ── Al Jazeera ──
def extract_links_aljazeera(soup, base_url, max_links=10):
    links = set()
    for a in soup.find_all("a", href=True):
        href = a["href"]
        url = make_absolute_url("https://www.aljazeera.com", href)
        if re.search(r"aljazeera\.com/news/\d{4}|aljazeera\.com/[a-z-]+/\d{4}", url):
            links.add(url)
        elif is_valid_article_url(url, "aljazeera.com") and url.count("/") >= 4:
            links.add(url)
        if len(links) >= max_links:
            break
    return list(links)[:max_links]


def extract_article_aljazeera(soup, url):
    article = extract_article_generic(soup, url)
    if not article["content"]:
        main_content = soup.find("main")
        if main_content:
            parts = [clean_text(p.get_text()) for p in main_content.find_all("p") if len(clean_text(p.get_text())) > 20]
            article["content"] = " ".join(parts)
    return article


# ── The Guardian ──
def extract_links_guardian(soup, base_url, max_links=10):
    links = set()
    for a in soup.find_all("a", href=True):
        href = a["href"]
        url = make_absolute_url("https://www.theguardian.com", href)
        # Guardian articles have date patterns
        if re.search(r"theguardian\.com/.+/\d{4}/[a-z]{3}/\d{2}/", url):
            links.add(url)
        if len(links) >= max_links:
            break
    return list(links)[:max_links]


def extract_article_guardian(soup, url):
    article = extract_article_generic(soup, url)
    if not article["content"]:
        body = soup.find("div", id="maincontent") or soup.find("div", class_=re.compile(r"article-body", re.I))
        if body:
            parts = [clean_text(p.get_text()) for p in body.find_all("p") if len(clean_text(p.get_text())) > 20]
            article["content"] = " ".join(parts)
    return article


# ── NYTimes ──
def extract_links_nytimes(soup, base_url, max_links=10):
    links = set()
    for a in soup.find_all("a", href=True):
        href = a["href"]
        url = make_absolute_url("https://www.nytimes.com", href)
        if re.search(r"nytimes\.com/\d{4}/\d{2}/\d{2}/", url):
            links.add(url)
        if len(links) >= max_links:
            break
    return list(links)[:max_links]


def extract_article_nytimes(soup, url):
    article = extract_article_generic(soup, url)
    if not article["content"]:
        body = soup.find("section", attrs={"name": "articleBody"})
        if body:
            parts = [clean_text(p.get_text()) for p in body.find_all("p") if clean_text(p.get_text())]
            article["content"] = " ".join(parts)
    return article


# ── Washington Post ──
def extract_links_washingtonpost(soup, base_url, max_links=10):
    links = set()
    for a in soup.find_all("a", href=True):
        href = a["href"]
        url = make_absolute_url("https://www.washingtonpost.com", href)
        if re.search(r"washingtonpost\.com/.+/\d{4}/\d{2}/\d{2}/", url):
            links.add(url)
        if len(links) >= max_links:
            break
    return list(links)[:max_links]


def extract_article_washingtonpost(soup, url):
    article = extract_article_generic(soup, url)
    if not article["content"]:
        body = soup.find("div", class_=re.compile(r"article-body", re.I))
        if body:
            parts = [clean_text(p.get_text()) for p in body.find_all("p") if clean_text(p.get_text())]
            article["content"] = " ".join(parts)
    return article


# ── Bloomberg ──
def extract_links_bloomberg(soup, base_url, max_links=10):
    links = set()
    for a in soup.find_all("a", href=True):
        href = a["href"]
        url = make_absolute_url("https://www.bloomberg.com", href)
        if re.search(r"bloomberg\.com/(news|opinion)/(articles|features|newsletters)/", url):
            links.add(url)
        elif is_valid_article_url(url, "bloomberg.com") and url.count("/") >= 4:
            links.add(url)
        if len(links) >= max_links:
            break
    return list(links)[:max_links]


def extract_article_bloomberg(soup, url):
    return extract_article_generic(soup, url)


# ── AP News ──
def extract_links_apnews(soup, base_url, max_links=10):
    links = set()
    for a in soup.find_all("a", href=True):
        href = a["href"]
        url = make_absolute_url("https://apnews.com", href)
        if re.search(r"apnews\.com/article/", url):
            links.add(url)
        if len(links) >= max_links:
            break
    return list(links)[:max_links]


def extract_article_apnews(soup, url):
    article = extract_article_generic(soup, url)
    if not article["content"]:
        body = soup.find("div", class_=re.compile(r"RichTextStoryBody", re.I))
        if body:
            parts = [clean_text(p.get_text()) for p in body.find_all("p") if clean_text(p.get_text())]
            article["content"] = " ".join(parts)
    return article


# ── CNBC ──
def extract_links_cnbc(soup, base_url, max_links=10):
    links = set()
    for a in soup.find_all("a", href=True):
        href = a["href"]
        url = make_absolute_url("https://www.cnbc.com", href)
        if re.search(r"cnbc\.com/\d{4}/\d{2}/\d{2}/", url):
            links.add(url)
        if len(links) >= max_links:
            break
    return list(links)[:max_links]


def extract_article_cnbc(soup, url):
    article = extract_article_generic(soup, url)
    if not article["content"]:
        body = soup.find("div", class_=re.compile(r"ArticleBody|FeaturedContent", re.I))
        if body:
            parts = [clean_text(p.get_text()) for p in body.find_all("p") if clean_text(p.get_text())]
            article["content"] = " ".join(parts)
    return article


# ── Fox News ──
def extract_links_foxnews(soup, base_url, max_links=10):
    links = set()
    for a in soup.find_all("a", href=True):
        href = a["href"]
        url = make_absolute_url("https://www.foxnews.com", href)
        if re.search(r"foxnews\.com/[a-z]+/[a-z0-9-]+$", url):
            if is_valid_article_url(url, "foxnews.com"):
                links.add(url)
        if len(links) >= max_links:
            break
    return list(links)[:max_links]


def extract_article_foxnews(soup, url):
    article = extract_article_generic(soup, url)
    if not article["content"]:
        body = soup.find("div", class_=re.compile(r"article-body", re.I))
        if body:
            parts = [clean_text(p.get_text()) for p in body.find_all("p") if clean_text(p.get_text())]
            article["content"] = " ".join(parts)
    return article


# ── Sky News ──
def extract_links_skynews(soup, base_url, max_links=10):
    links = set()
    for a in soup.find_all("a", href=True):
        href = a["href"]
        url = make_absolute_url("https://news.sky.com", href)
        if re.search(r"news\.sky\.com/story/", url):
            links.add(url)
        if len(links) >= max_links:
            break
    return list(links)[:max_links]


def extract_article_skynews(soup, url):
    article = extract_article_generic(soup, url)
    if not article["content"]:
        body = soup.find("div", class_=re.compile(r"sdc-article-body", re.I))
        if body:
            parts = [clean_text(p.get_text()) for p in body.find_all("p") if clean_text(p.get_text())]
            article["content"] = " ".join(parts)
    return article


# ── ABC News ──
def extract_links_abcnews(soup, base_url, max_links=10):
    links = set()
    for a in soup.find_all("a", href=True):
        href = a["href"]
        url = make_absolute_url("https://abcnews.go.com", href)
        if re.search(r"abcnews\.go\.com/.+/story\?id=", url):
            links.add(url)
        elif re.search(r"abcnews\.go\.com/[A-Za-z]+/.+/\d+", url):
            links.add(url)
        if len(links) >= max_links:
            break
    return list(links)[:max_links]


def extract_article_abcnews(soup, url):
    return extract_article_generic(soup, url)


# ── CBS News ──
def extract_links_cbsnews(soup, base_url, max_links=10):
    links = set()
    for a in soup.find_all("a", href=True):
        href = a["href"]
        url = make_absolute_url("https://www.cbsnews.com", href)
        if re.search(r"cbsnews\.com/news/", url):
            links.add(url)
        if len(links) >= max_links:
            break
    return list(links)[:max_links]


def extract_article_cbsnews(soup, url):
    article = extract_article_generic(soup, url)
    if not article["content"]:
        body = soup.find("section", class_=re.compile(r"content__body", re.I))
        if body:
            parts = [clean_text(p.get_text()) for p in body.find_all("p") if clean_text(p.get_text())]
            article["content"] = " ".join(parts)
    return article


# ── USA Today ──
def extract_links_usatoday(soup, base_url, max_links=10):
    links = set()
    for a in soup.find_all("a", href=True):
        href = a["href"]
        url = make_absolute_url("https://www.usatoday.com", href)
        if re.search(r"usatoday\.com/story/", url):
            links.add(url)
        if len(links) >= max_links:
            break
    return list(links)[:max_links]


def extract_article_usatoday(soup, url):
    return extract_article_generic(soup, url)


# ═══════════════════════════════════════════════════════
# INDIAN NEWS SITE PARSERS
# ═══════════════════════════════════════════════════════

# ── Times of India ──
def extract_links_timesofindia(soup, base_url, max_links=10):
    links = set()
    for a in soup.find_all("a", href=True):
        href = a["href"]
        url = make_absolute_url("https://timesofindia.indiatimes.com", href)
        if re.search(r"indiatimes\.com/.+/articleshow/\d+", url):
            links.add(url)
        if len(links) >= max_links:
            break
    return list(links)[:max_links]


def extract_article_timesofindia(soup, url):
    article = extract_article_generic(soup, url)
    if not article["content"]:
        body = soup.find("div", class_=re.compile(r"_s30J|artText|article_content", re.I))
        if body:
            parts = [clean_text(p.get_text()) for p in body.find_all("p") if clean_text(p.get_text())]
            article["content"] = " ".join(parts) if parts else clean_text(body.get_text())
    return article


# ── The Hindu ──
def extract_links_thehindu(soup, base_url, max_links=10):
    links = set()
    for a in soup.find_all("a", href=True):
        href = a["href"]
        url = make_absolute_url("https://www.thehindu.com", href)
        if re.search(r"thehindu\.com/.+/article\d+\.ece", url):
            links.add(url)
        if len(links) >= max_links:
            break
    return list(links)[:max_links]


def extract_article_thehindu(soup, url):
    article = extract_article_generic(soup, url)
    if not article["content"]:
        body = soup.find("div", class_=re.compile(r"article-body|articlebodycontent", re.I))
        if body:
            parts = [clean_text(p.get_text()) for p in body.find_all("p") if clean_text(p.get_text())]
            article["content"] = " ".join(parts)
    return article


# ── Hindustan Times ──
def extract_links_hindustantimes(soup, base_url, max_links=10):
    links = set()
    for a in soup.find_all("a", href=True):
        href = a["href"]
        url = make_absolute_url("https://www.hindustantimes.com", href)
        if re.search(r"hindustantimes\.com/.+-\d+\.html", url):
            links.add(url)
        elif re.search(r"hindustantimes\.com/.+/101\d+", url):
            links.add(url)
        if len(links) >= max_links:
            break
    return list(links)[:max_links]


def extract_article_hindustantimes(soup, url):
    article = extract_article_generic(soup, url)
    if not article["content"]:
        body = soup.find("div", class_=re.compile(r"storyDetail|detail|story-details", re.I))
        if body:
            parts = [clean_text(p.get_text()) for p in body.find_all("p") if clean_text(p.get_text())]
            article["content"] = " ".join(parts)
    return article


# ── Indian Express ──
def extract_links_indianexpress(soup, base_url, max_links=10):
    links = set()
    for a in soup.find_all("a", href=True):
        href = a["href"]
        url = make_absolute_url("https://indianexpress.com", href)
        if re.search(r"indianexpress\.com/article/", url):
            links.add(url)
        if len(links) >= max_links:
            break
    return list(links)[:max_links]


def extract_article_indianexpress(soup, url):
    article = extract_article_generic(soup, url)
    if not article["content"]:
        body = soup.find("div", id="pcl-full-content") or soup.find("div", class_=re.compile(r"full-details", re.I))
        if body:
            parts = [clean_text(p.get_text()) for p in body.find_all("p") if clean_text(p.get_text())]
            article["content"] = " ".join(parts)
    return article


# ── NDTV ──
def extract_links_ndtv(soup, base_url, max_links=10):
    links = set()
    for a in soup.find_all("a", href=True):
        href = a["href"]
        url = make_absolute_url("https://www.ndtv.com", href)
        if re.search(r"ndtv\.com/.+-\d{6,}", url):
            links.add(url)
        if len(links) >= max_links:
            break
    return list(links)[:max_links]


def extract_article_ndtv(soup, url):
    article = extract_article_generic(soup, url)
    if not article["content"]:
        body = soup.find("div", id="ins_storybody") or soup.find("div", class_=re.compile(r"story__content|Art_Body", re.I))
        if body:
            parts = [clean_text(p.get_text()) for p in body.find_all("p") if clean_text(p.get_text())]
            article["content"] = " ".join(parts)
    return article


# ── India Today ──
def extract_links_indiatoday(soup, base_url, max_links=10):
    links = set()
    for a in soup.find_all("a", href=True):
        href = a["href"]
        url = make_absolute_url("https://www.indiatoday.in", href)
        if re.search(r"indiatoday\.in/.+/story/", url):
            links.add(url)
        if len(links) >= max_links:
            break
    return list(links)[:max_links]


def extract_article_indiatoday(soup, url):
    article = extract_article_generic(soup, url)
    if not article["content"]:
        body = soup.find("div", class_=re.compile(r"story__content|description", re.I))
        if body:
            parts = [clean_text(p.get_text()) for p in body.find_all("p") if clean_text(p.get_text())]
            article["content"] = " ".join(parts)
    return article


# ── News18 ──
def extract_links_news18(soup, base_url, max_links=10):
    links = set()
    for a in soup.find_all("a", href=True):
        href = a["href"]
        url = make_absolute_url("https://www.news18.com", href)
        if re.search(r"news18\.com/.+/\d{6,}", url):
            links.add(url)
        elif re.search(r"news18\.com/.+-\d+\.html", url):
            links.add(url)
        if len(links) >= max_links:
            break
    return list(links)[:max_links]


def extract_article_news18(soup, url):
    article = extract_article_generic(soup, url)
    if not article["content"]:
        body = soup.find("div", id="article-body") or soup.find("div", class_=re.compile(r"article_content|story-detail", re.I))
        if body:
            parts = [clean_text(p.get_text()) for p in body.find_all("p") if clean_text(p.get_text())]
            article["content"] = " ".join(parts)
    return article


# ── Zee News ──
def extract_links_zeenews(soup, base_url, max_links=10):
    links = set()
    for a in soup.find_all("a", href=True):
        href = a["href"]
        url = make_absolute_url("https://zeenews.india.com", href)
        if re.search(r"zeenews\.india\.com/.+/\d{6,}", url):
            links.add(url)
        elif re.search(r"zeenews\.india\.com/.+-\d+\.html", url):
            links.add(url)
        if len(links) >= max_links:
            break
    return list(links)[:max_links]


def extract_article_zeenews(soup, url):
    article = extract_article_generic(soup, url)
    if not article["content"]:
        body = soup.find("div", class_=re.compile(r"article-content|article_content", re.I))
        if body:
            parts = [clean_text(p.get_text()) for p in body.find_all("p") if clean_text(p.get_text())]
            article["content"] = " ".join(parts)
    return article


# ── ABP News ──
def extract_links_abpnews(soup, base_url, max_links=10):
    links = set()
    for a in soup.find_all("a", href=True):
        href = a["href"]
        url = make_absolute_url("https://news.abplive.com", href)
        if re.search(r"abplive\.com/.+-\d+", url):
            links.add(url)
        if len(links) >= max_links:
            break
    return list(links)[:max_links]


def extract_article_abpnews(soup, url):
    return extract_article_generic(soup, url)


# ── Republic World ──
def extract_links_republicworld(soup, base_url, max_links=10):
    links = set()
    for a in soup.find_all("a", href=True):
        href = a["href"]
        url = make_absolute_url("https://www.republicworld.com", href)
        if is_valid_article_url(url, "republicworld.com") and url.count("/") >= 4:
            links.add(url)
        if len(links) >= max_links:
            break
    return list(links)[:max_links]


def extract_article_republicworld(soup, url):
    return extract_article_generic(soup, url)


# ── Economic Times ──
def extract_links_economictimes(soup, base_url, max_links=10):
    links = set()
    for a in soup.find_all("a", href=True):
        href = a["href"]
        url = make_absolute_url("https://economictimes.indiatimes.com", href)
        if re.search(r"economictimes\.indiatimes\.com/.+/articleshow/\d+", url):
            links.add(url)
        if len(links) >= max_links:
            break
    return list(links)[:max_links]


def extract_article_economictimes(soup, url):
    article = extract_article_generic(soup, url)
    if not article["content"]:
        body = soup.find("div", class_=re.compile(r"artText|article_content|Normal", re.I))
        if body:
            parts = [clean_text(p.get_text()) for p in body.find_all("p") if clean_text(p.get_text())]
            article["content"] = " ".join(parts) if parts else clean_text(body.get_text())
    return article


# ── Financial Express ──
def extract_links_financialexpress(soup, base_url, max_links=10):
    links = set()
    for a in soup.find_all("a", href=True):
        href = a["href"]
        url = make_absolute_url("https://www.financialexpress.com", href)
        if re.search(r"financialexpress\.com/.+/\d{6,}", url):
            links.add(url)
        if len(links) >= max_links:
            break
    return list(links)[:max_links]


def extract_article_financialexpress(soup, url):
    return extract_article_generic(soup, url)


# ── Firstpost ──
def extract_links_firstpost(soup, base_url, max_links=10):
    links = set()
    for a in soup.find_all("a", href=True):
        href = a["href"]
        url = make_absolute_url("https://www.firstpost.com", href)
        if re.search(r"firstpost\.com/.+-\d+\.html", url):
            links.add(url)
        elif is_valid_article_url(url, "firstpost.com") and url.count("/") >= 3:
            links.add(url)
        if len(links) >= max_links:
            break
    return list(links)[:max_links]


def extract_article_firstpost(soup, url):
    article = extract_article_generic(soup, url)
    if not article["content"]:
        body = soup.find("div", class_=re.compile(r"article-body|art-body|entry-content", re.I))
        if body:
            parts = [clean_text(p.get_text()) for p in body.find_all("p") if clean_text(p.get_text())]
            article["content"] = " ".join(parts)
    return article


# ═══════════════════════════════════════════════════════
# REGIONAL / GUJARATI NEWS SITE PARSERS
# ═══════════════════════════════════════════════════════

# ── Divya Bhaskar ──
def extract_links_divyabhaskar(soup, base_url, max_links=10):
    links = set()
    for a in soup.find_all("a", href=True):
        href = a["href"]
        url = make_absolute_url("https://www.divyabhaskar.co.in", href)
        if url.endswith(".html") and is_valid_article_url(url, "divyabhaskar.co.in"):
            links.add(url)
        if len(links) >= max_links:
            break
    return list(links)[:max_links]


def extract_article_divyabhaskar(soup, url):
    return extract_article_generic(soup, url)


# ── Gujarat Samachar ──
def extract_links_gujaratsamachar(soup, base_url, max_links=10):
    links = set()
    for a in soup.find_all("a", href=True):
        href = a["href"]
        url = make_absolute_url("https://www.gujaratsamachar.com", href)
        if is_valid_article_url(url, "gujaratsamachar.com") and url.count("/") >= 3:
            links.add(url)
        if len(links) >= max_links:
            break
    return list(links)[:max_links]


def extract_article_gujaratsamachar(soup, url):
    return extract_article_generic(soup, url)


# ── Sandesh ──
def extract_links_sandesh(soup, base_url, max_links=10):
    links = set()
    for a in soup.find_all("a", href=True):
        href = a["href"]
        url = make_absolute_url("https://sandesh.com", href)
        if is_valid_article_url(url, "sandesh.com") and url.count("/") >= 3:
            links.add(url)
        if len(links) >= max_links:
            break
    return list(links)[:max_links]


def extract_article_sandesh(soup, url):
    return extract_article_generic(soup, url)


# ── TV9 Gujarati ──
def extract_links_tv9gujarati(soup, base_url, max_links=10):
    links = set()
    for a in soup.find_all("a", href=True):
        href = a["href"]
        url = make_absolute_url("https://tv9gujarati.com", href)
        if is_valid_article_url(url, "tv9gujarati.com") and url.count("/") >= 3:
            links.add(url)
        if len(links) >= max_links:
            break
    return list(links)[:max_links]


def extract_article_tv9gujarati(soup, url):
    return extract_article_generic(soup, url)


# ── ABP Asmita ──
def extract_links_abpasmita(soup, base_url, max_links=10):
    links = set()
    for a in soup.find_all("a", href=True):
        href = a["href"]
        url = make_absolute_url("https://gujarati.abplive.com", href)
        if re.search(r"gujarati\.abplive\.com/.+-\d+", url):
            links.add(url)
        elif is_valid_article_url(url, "abplive.com") and url.count("/") >= 3:
            links.add(url)
        if len(links) >= max_links:
            break
    return list(links)[:max_links]


def extract_article_abpasmita(soup, url):
    return extract_article_generic(soup, url)


# ── Zee 24 Kalak ──
def extract_links_zee24kalak(soup, base_url, max_links=10):
    links = set()
    for a in soup.find_all("a", href=True):
        href = a["href"]
        url = make_absolute_url("https://zeenews.india.com", href)
        if "gujarati" in url and is_valid_article_url(url, "zeenews.india.com") and url.count("/") >= 4:
            links.add(url)
        if len(links) >= max_links:
            break
    return list(links)[:max_links]


def extract_article_zee24kalak(soup, url):
    return extract_article_generic(soup, url)


# ═══════════════════════════════════════════════════════
# TECHNOLOGY NEWS SITE PARSERS
# ═══════════════════════════════════════════════════════

# ── TechCrunch ──
def extract_links_techcrunch(soup, base_url, max_links=10):
    links = set()
    for a in soup.find_all("a", href=True):
        href = a["href"]
        url = make_absolute_url("https://techcrunch.com", href)
        if re.search(r"techcrunch\.com/\d{4}/\d{2}/\d{2}/", url):
            links.add(url)
        if len(links) >= max_links:
            break
    return list(links)[:max_links]


def extract_article_techcrunch(soup, url):
    article = extract_article_generic(soup, url)
    if not article["content"]:
        body = soup.find("div", class_=re.compile(r"article-content|entry-content", re.I))
        if body:
            parts = [clean_text(p.get_text()) for p in body.find_all("p") if clean_text(p.get_text())]
            article["content"] = " ".join(parts)
    return article


# ── The Verge ──
def extract_links_theverge(soup, base_url, max_links=10):
    links = set()
    for a in soup.find_all("a", href=True):
        href = a["href"]
        url = make_absolute_url("https://www.theverge.com", href)
        if re.search(r"theverge\.com/\d{4}/\d{1,2}/\d{1,2}/", url):
            links.add(url)
        if len(links) >= max_links:
            break
    return list(links)[:max_links]


def extract_article_theverge(soup, url):
    article = extract_article_generic(soup, url)
    if not article["content"]:
        body = soup.find("div", class_=re.compile(r"article-content|entry-content|duet--article", re.I))
        if body:
            parts = [clean_text(p.get_text()) for p in body.find_all("p") if clean_text(p.get_text())]
            article["content"] = " ".join(parts)
    return article


# ── Wired ──
def extract_links_wired(soup, base_url, max_links=10):
    links = set()
    for a in soup.find_all("a", href=True):
        href = a["href"]
        url = make_absolute_url("https://www.wired.com", href)
        if re.search(r"wired\.com/story/", url):
            links.add(url)
        if len(links) >= max_links:
            break
    return list(links)[:max_links]


def extract_article_wired(soup, url):
    article = extract_article_generic(soup, url)
    if not article["content"]:
        body = soup.find("div", class_=re.compile(r"body__inner-container", re.I))
        if body:
            parts = [clean_text(p.get_text()) for p in body.find_all("p") if clean_text(p.get_text())]
            article["content"] = " ".join(parts)
    return article


# ── Gizmodo ──
def extract_links_gizmodo(soup, base_url, max_links=10):
    links = set()
    for a in soup.find_all("a", href=True):
        href = a["href"]
        url = make_absolute_url("https://gizmodo.com", href)
        if is_valid_article_url(url, "gizmodo.com") and url.count("/") >= 3:
            links.add(url)
        if len(links) >= max_links:
            break
    return list(links)[:max_links]


def extract_article_gizmodo(soup, url):
    return extract_article_generic(soup, url)


# ── Ars Technica ──
def extract_links_arstechnica(soup, base_url, max_links=10):
    links = set()
    for a in soup.find_all("a", href=True):
        href = a["href"]
        url = make_absolute_url("https://arstechnica.com", href)
        if is_valid_article_url(url, "arstechnica.com") and url.count("/") >= 3:
            # Ars Technica articles are typically under /<section>/<slug>
            links.add(url)
        if len(links) >= max_links:
            break
    return list(links)[:max_links]


def extract_article_arstechnica(soup, url):
    article = extract_article_generic(soup, url)
    if not article["content"]:
        body = soup.find("div", class_=re.compile(r"article-content|post-content", re.I))
        if body:
            parts = [clean_text(p.get_text()) for p in body.find_all("p") if clean_text(p.get_text())]
            article["content"] = " ".join(parts)
    return article


# ═══════════════════════════════════════════════════════
# SCRAPER REGISTRY
# Maps scraper_key → (link_extractor, article_extractor)
# ═══════════════════════════════════════════════════════
SCRAPER_REGISTRY = {
    # International
    "bbc":             (extract_links_bbc, extract_article_bbc),
    "cnn":             (extract_links_cnn, extract_article_cnn),
    "reuters":         (extract_links_reuters, extract_article_reuters),
    "aljazeera":       (extract_links_aljazeera, extract_article_aljazeera),
    "guardian":         (extract_links_guardian, extract_article_guardian),
    "nytimes":         (extract_links_nytimes, extract_article_nytimes),
    "washingtonpost":  (extract_links_washingtonpost, extract_article_washingtonpost),
    "bloomberg":       (extract_links_bloomberg, extract_article_bloomberg),
    "apnews":          (extract_links_apnews, extract_article_apnews),
    "cnbc":            (extract_links_cnbc, extract_article_cnbc),
    "foxnews":         (extract_links_foxnews, extract_article_foxnews),
    "skynews":         (extract_links_skynews, extract_article_skynews),
    "abcnews":         (extract_links_abcnews, extract_article_abcnews),
    "cbsnews":         (extract_links_cbsnews, extract_article_cbsnews),
    "usatoday":        (extract_links_usatoday, extract_article_usatoday),
    # Indian
    "timesofindia":    (extract_links_timesofindia, extract_article_timesofindia),
    "thehindu":        (extract_links_thehindu, extract_article_thehindu),
    "hindustantimes":  (extract_links_hindustantimes, extract_article_hindustantimes),
    "indianexpress":   (extract_links_indianexpress, extract_article_indianexpress),
    "ndtv":            (extract_links_ndtv, extract_article_ndtv),
    "indiatoday":      (extract_links_indiatoday, extract_article_indiatoday),
    "news18":          (extract_links_news18, extract_article_news18),
    "zeenews":         (extract_links_zeenews, extract_article_zeenews),
    "abpnews":         (extract_links_abpnews, extract_article_abpnews),
    "republicworld":   (extract_links_republicworld, extract_article_republicworld),
    "economictimes":   (extract_links_economictimes, extract_article_economictimes),
    "financialexpress": (extract_links_financialexpress, extract_article_financialexpress),
    "firstpost":       (extract_links_firstpost, extract_article_firstpost),
    # Regional / Gujarati
    "divyabhaskar":    (extract_links_divyabhaskar, extract_article_divyabhaskar),
    "gujaratsamachar": (extract_links_gujaratsamachar, extract_article_gujaratsamachar),
    "sandesh":         (extract_links_sandesh, extract_article_sandesh),
    "tv9gujarati":     (extract_links_tv9gujarati, extract_article_tv9gujarati),
    "abpasmita":       (extract_links_abpasmita, extract_article_abpasmita),
    "zee24kalak":      (extract_links_zee24kalak, extract_article_zee24kalak),
    # Tech
    "techcrunch":      (extract_links_techcrunch, extract_article_techcrunch),
    "theverge":        (extract_links_theverge, extract_article_theverge),
    "wired":           (extract_links_wired, extract_article_wired),
    "gizmodo":         (extract_links_gizmodo, extract_article_gizmodo),
    "arstechnica":     (extract_links_arstechnica, extract_article_arstechnica),
}
