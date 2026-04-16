"""
app.py - Flask web application for the News Scraper Project.
Provides a modern web UI to browse, search, and filter scraped news articles.
Includes automatic scheduled scraping every 1 hour.
"""

import os
import sys
import threading
from datetime import datetime

from flask import Flask, render_template, request, jsonify
from apscheduler.schedulers.background import BackgroundScheduler

from config import (
    SCRAPE_INTERVAL_HOURS,
)
from database import (
    get_all_articles, get_article_by_url, get_stats, get_unique_values,
    get_all_sources, update_source_status, update_source_interval,
    get_trending_keywords, get_sentiment_heatmap, get_velocity_data,
    get_source_polarization, get_momentum_data,
    get_recent_news, get_historical_data, get_geostat_data, get_summary_data
)
from scraper import scrape_all_sites
from utils import logger

# ─────────────────────────────────────────────
# Flask App Setup
# ─────────────────────────────────────────────
app = Flask(__name__)
app.config["SECRET_KEY"] = "news-scraper-secret-key-2024"




# ─────────────────────────────────────────────
# Scheduled Scraping
# ─────────────────────────────────────────────
def scheduled_scrape():
    """Background job: scrape all sites."""
    logger.info("Scheduled scrape triggered.")
    try:
        scrape_all_sites()
    except Exception as e:
        logger.error(f"Scheduled scrape failed: {e}")


# Initialize scheduler
scheduler = BackgroundScheduler(daemon=True)
scheduler.add_job(
    scheduled_scrape,
    "interval",
    hours=1,
    id="auto_scrape",
    name="Auto Scrape All Sites",
    next_run_time=None,
)
scheduler.start()


# ─────────────────────────────────────────────
# Routes
# ─────────────────────────────────────────────
@app.route("/")
def index():
    """Home page: display latest news articles."""
    # Get filter parameters from URL
    keyword = request.args.get("keyword", "").strip()
    category = request.args.get("category", "").strip()
    source = request.args.get("source", "").strip()
    sentiment = request.args.get("sentiment", "").strip()
    page = request.args.get("page", 1, type=int)
    per_page = 20

    # Fetch paginated AND filtered articles directly from MongoDB
    articles, total = get_all_articles(
        keyword=keyword,
        category=category,
        source=source,
        sentiment=sentiment,
        page=page,
        per_page=per_page
    )

    total_pages = max(1, (total + per_page - 1) // per_page)
    page = max(1, min(page, total_pages))

    # Get unique categories and sources for filter dropdowns directly from MongoDB
    categories = get_unique_values("category")
    sources = get_unique_values("source")

    return render_template(
        "index.html",
        articles=articles,
        keyword=keyword,
        category=category,
        source=source,
        sentiment=sentiment,
        page=page,
        total_pages=total_pages,
        total=total,
        categories=categories,
        sources=sources,
    )


@app.route("/article")
def article_detail():
    """View a single article's full content."""
    url = request.args.get("url", "")
    article = get_article_by_url(url) if url else None
    return render_template("article.html", article=article)


@app.route("/api/search")
def api_search():
    """API endpoint for AJAX search."""
    keyword = request.args.get("keyword", "").strip()
    category = request.args.get("category", "").strip()
    source = request.args.get("source", "").strip()
    sentiment = request.args.get("sentiment", "").strip()
    page = request.args.get("page", 1, type=int)
    per_page = 20

    articles, total = get_all_articles(
        keyword=keyword,
        category=category,
        source=source,
        sentiment=sentiment,
        page=page,
        per_page=per_page
    )

    total_pages = max(1, (total + per_page - 1) // per_page)
    page = max(1, min(page, total_pages))

    return jsonify({
        "articles": articles,
        "total": total,
        "page": page,
        "total_pages": total_pages,
    })


@app.route("/api/stats")
def api_stats():
    """API endpoint returning dashboard statistics directly from MongoDB."""
    stats = get_stats()
    
    return jsonify({
        "total_articles": stats["total"],
        "total_sources": len(stats["sources"]),
        "total_categories": len(stats["categories"]),
        "sentiment_breakdown": stats["sentiments"],
        "source_counts": stats["sources"],
        "category_counts": stats["categories"],
    })


@app.route("/scrape", methods=["POST"])
def trigger_scrape():
    """Manually trigger a scrape (runs in background thread)."""
    # Site-group category (international, indian, regional, tech, all)
    group_category = request.form.get("category", "all")

    # Filters from Scrape page
    keyword = request.form.get("keyword", "").strip()
    source_filter = request.form.get("source_filter", "").strip()
    article_category = request.form.get("article_category", "").strip()
    sentiment_filter = request.form.get("sentiment_filter", "").strip()

    has_filters = bool(keyword or source_filter or article_category or sentiment_filter)

    def run_scrape():
        if has_filters:
            from scraper import scrape_with_filters
            scrape_with_filters(
                keyword=keyword,
                source_name=source_filter,
                article_category=article_category,
                sentiment_filter=sentiment_filter,
            )
        else:
            from scraper import scrape_by_category_name
            scrape_by_category_name(group_category)

    thread = threading.Thread(target=run_scrape, daemon=True)
    thread.start()

    # Build descriptive message
    parts = []
    if keyword:
        parts.append(f"keyword='{keyword}'")
    if source_filter:
        parts.append(f"source='{source_filter}'")
    if article_category:
        parts.append(f"category='{article_category}'")
    if sentiment_filter:
        parts.append(f"sentiment='{sentiment_filter}'")

    if parts:
        msg = f"Filtered scrape started ({', '.join(parts)})..."
    else:
        msg = f"Scraping '{group_category}' sites in background..."

    return jsonify({
        "status": "started",
        "message": msg,
    })


@app.route("/dashboard")
def dashboard():
    """Dashboard page showing statistics and charts."""
    return render_template("dashboard.html")


@app.route("/scrape-page")
def scrape_page():
    """Scrape page: UI for triggering scrapes with filters."""
    from utils import CATEGORY_KEYWORDS

    # Get all known categories from the CATEGORY_KEYWORDS mapping (full list)
    all_known_categories = sorted(set(CATEGORY_KEYWORDS.values()))

    # Also merge with any categories stored in MongoDB
    db_categories = get_unique_values("category")
    all_known_categories = sorted(set(all_known_categories) | set(db_categories))

    # Fetch all sites from database (Control Center driven)
    all_db_sites = get_all_sources()
    active_sources = sorted([s["name"] for s in all_db_sites])

    # Build site group data for the template
    def _site_list(group_name):
        sites = [s for s in all_db_sites if s.get("group") == group_name]
        return [
            {"name": s["name"], "key": s["scraper_key"], "subs": len(s["sub_links"]), "enabled": s.get("is_enabled", True)}
            for s in sites
        ]

    site_groups = {
        "international": _site_list("International"),
        "indian": _site_list("Indian"),
        "regional": _site_list("Regional"),
        "tech": _site_list("Technology"),
    }

    return render_template(
        "scrape.html",
        categories=all_known_categories,
        sources=active_sources,
        site_groups=site_groups,
    )


@app.route("/trends")
def trends_page():
    """Intelligence page: Trends & Keyword Analysis."""
    return render_template("trends.html")


@app.route("/api/trends")
def api_trends():
    """Aggregate trend data for advanced analytics."""
    scale = request.args.get("scale", "h") # Default to hourly
    keywords = get_trending_keywords(limit=20) 
    sentiment_map = get_sentiment_heatmap()
    velocity = get_velocity_data(scale=scale)
    polarization = get_source_polarization()
    momentum = get_momentum_data()
    
    return jsonify({
        "keywords": keywords,
        "sentiment_heatmap": sentiment_map,
        "velocity": velocity,
        "polarization": polarization,
        "momentum": momentum
    })


@app.route("/source-manager")
def source_manager():
    """Control Center: Manage news sources, toggle status, and intervals."""
    sources = get_all_sources()
    return render_template("source_manager.html", sources=sources)


@app.route("/api/source/toggle", methods=["POST"])
def toggle_source():
    """Toggle a news source on/off."""
    data = request.json
    key = data.get("key")
    enabled = data.get("enabled")
    if key is None or enabled is None:
        return jsonify({"status": "error", "message": "Missing data"}), 400
    
    success = update_source_status(key, enabled)
    return jsonify({"status": "success" if success else "error"})


@app.route("/api/source/interval", methods=["POST"])
def update_interval():
    """Update scraping frequency for a source."""
    data = request.json
    key = data.get("key")
    interval = data.get("interval")
    if key is None or interval is None:
        return jsonify({"status": "error", "message": "Missing data"}), 400
    
    success = update_source_interval(key, int(interval))
    return jsonify({"status": "success" if success else "error"})


# ─────────────────────────────────────────────
# Integration Routes: AI, Map, Archive
# ─────────────────────────────────────────────

@app.route("/ai-summary")
def ai_summary():
    """AI Summary Brief page."""
    return render_template("summary.html")


@app.route("/api/summary")
def api_summary():
    """API for summarized news trends."""
    summary = get_summary_data()
    return jsonify(summary)


@app.route("/api/article/summary")
def api_article_summary():
    """API for summarizing a specific article."""
    url = request.args.get("url", "")
    article = get_article_by_url(url)
    if not article:
        return jsonify({"error": "Article not found"}), 404
        
    return jsonify({
        "headline": article.get("headline", "Untitled"),
        "source": article.get("source", "Unknown"),
        "sentiment": article.get("sentiment", "Neutral"),
        "summary": article.get("summary") or article.get("content", "No content available.")[:500] + "...",
        "scraped_at": article.get("scraped_at", "")
    })


@app.route("/map")
def news_map():
    """Geospatial News Analysis page."""
    return render_template("map.html")


@app.route("/api/map")
def api_map_data():
    """API providing location-tagged news counts."""
    geo_data = get_geostat_data()
    return jsonify(geo_data)


@app.route("/scrape-site", methods=["POST"])
def trigger_scrape_site():
    """Scrape a single site by its scraper_key."""
    site_key = request.form.get("site_key", "")
    if not site_key:
        return jsonify({"status": "error", "message": "No site_key provided."})

    def run_scrape():
        from scraper import scrape_single_site
        scrape_single_site(site_key)

    thread = threading.Thread(target=run_scrape, daemon=True)
    thread.start()

    # Find the display name from DB
    sources = get_all_sources()
    display_name = next((s["name"] for s in sources if s["scraper_key"] == site_key), site_key)

    return jsonify({
        "status": "started",
        "message": f"Scraping '{display_name}' in background...",
    })


# ─────────────────────────────────────────────
# Template Filters
# ─────────────────────────────────────────────
@app.template_filter("truncate_words")
def truncate_words(text, length=30):
    """Truncate text to a given number of words."""
    if not text:
        return ""
    words = str(text).split()
    if len(words) > length:
        return " ".join(words[:length]) + "..."
    return text


@app.template_filter("sentiment_badge")
def sentiment_badge(sentiment):
    """Return CSS class for sentiment badge."""
    mapping = {
        "Positive": "badge-positive",
        "Negative": "badge-negative",
        "Neutral": "badge-neutral",
    }
    return mapping.get(sentiment, "badge-neutral")


# ─────────────────────────────────────────────
# Run
# ─────────────────────────────────────────────
if __name__ == "__main__":
    print("\n" + "=" * 50)
    print("  News Scraper - Web Dashboard")
    print("  http://127.0.0.1:5000")
    print("=" * 50 + "\n")
    app.run(debug=True, host="0.0.0.0", port=5000, use_reloader=False)
