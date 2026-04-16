"""
database.py - MongoDB integration for the News Scraper Project.
Provides connection management, CRUD operations, and data migration utilities.
Database: news_scraper | Collection: articles
"""

import logging
from datetime import datetime
from pymongo import MongoClient, DESCENDING
from pymongo.errors import ConnectionFailure, DuplicateKeyError

logger = logging.getLogger("news_scraper")

# ─────────────────────────────────────────────
# MongoDB Configuration
# ─────────────────────────────────────────────
MONGO_URI = "mongodb://localhost:27017/"
DB_NAME = "news_scraper"
COLLECTION_NAME = "articles"
SOURCES_COLLECTION = "sources"


# ─────────────────────────────────────────────
# Connection Management
# ─────────────────────────────────────────────
_client = None
_db = None
_collection = None
_sources_collection = None


def get_client():
    """Get or create the MongoDB client (singleton)."""
    global _client
    if _client is None:
        try:
            _client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
            # Test connection
            _client.admin.command("ping")
            logger.info(f"Connected to MongoDB at {MONGO_URI}")
        except ConnectionFailure as e:
            logger.error(f"Could not connect to MongoDB: {e}")
            _client = None
            raise
    return _client


def get_db():
    """Get the news_scraper database."""
    global _db
    if _db is None:
        client = get_client()
        _db = client[DB_NAME]
    return _db


def get_collection():
    """Get the articles collection with indexes."""
    global _collection
    if _collection is None:
        db = get_db()
        _collection = db[COLLECTION_NAME]
        # Create indexes for fast querying and dedup
        _collection.create_index("url", unique=True, sparse=True)
        _collection.create_index("headline")
        _collection.create_index("source")
        _collection.create_index("category")
        _collection.create_index("sentiment")
        _collection.create_index("scraped_at")
        _collection.create_index([("scraped_at", DESCENDING)]) # New Performance Index
        _collection.create_index(
            [("source", 1), ("category", 1), ("scraped_at", DESCENDING)]
        )
    return _collection


def get_sources_collection():
    """Get the sources configuration collection."""
    global _sources_collection
    if _sources_collection is None:
        db = get_db()
        _sources_collection = db[SOURCES_COLLECTION]
        _sources_collection.create_index("scraper_key", unique=True)
    return _sources_collection


def is_connected() -> bool:
    """Check if MongoDB is reachable."""
    try:
        client = get_client()
        client.admin.command("ping")
        return True
    except Exception:
        return False


# ─────────────────────────────────────────────
# CRUD Operations
# ─────────────────────────────────────────────
def insert_articles(articles: list[dict]) -> int:
    """
    Insert multiple articles into MongoDB.
    Skips duplicates based on URL (unique index).
    Returns the count of newly inserted articles.
    """
    if not articles:
        return 0

    collection = get_collection()
    inserted_count = 0

    for article in articles:
        try:
            # Ensure required fields
            doc = {
                "headline": article.get("headline", ""),
                "author": article.get("author", "Unknown"),
                "date": article.get("date", "N/A"),
                "content": article.get("content", ""),
                "category": article.get("category", "General"),
                "source": article.get("source", ""),
                "url": article.get("url", ""),
                "sentiment": article.get("sentiment", "Neutral"),
                "sentiment_polarity": article.get("sentiment_polarity", 0.0),
                "scraped_at": article.get("scraped_at", datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
            }

            # Skip if URL is empty
            if not doc["url"]:
                continue

            collection.insert_one(doc)
            inserted_count += 1

        except DuplicateKeyError:
            # Article with this URL already exists — skip
            continue
        except Exception as e:
            logger.error(f"Error inserting article: {e}")
            continue

    logger.info(f"MongoDB: Inserted {inserted_count} new articles (skipped {len(articles) - inserted_count} duplicates)")
    return inserted_count


def get_all_articles(
    keyword: str = "",
    category: str = "",
    source: str = "",
    sentiment: str = "",
    page: int = 1,
    per_page: int = 12,
    sort_by: str = "scraped_at",
    sort_order: int = DESCENDING,
) -> tuple[list[dict], int]:
    """
    Query articles with optional filters and pagination.
    Returns (list_of_articles, total_count).
    """
    collection = get_collection()

    # Build query filter
    query = {}

    if keyword:
        # Search in headline and content (case-insensitive)
        query["$or"] = [
            {"headline": {"$regex": keyword, "$options": "i"}},
            {"content": {"$regex": keyword, "$options": "i"}},
        ]

    if category:
        query["category"] = {"$regex": f"^{category}$", "$options": "i"}

    if source:
        query["source"] = {"$regex": f"^{source}$", "$options": "i"}

    if sentiment:
        query["sentiment"] = {"$regex": f"^{sentiment}$", "$options": "i"}

    # Get total count
    total = collection.count_documents(query)

    # Fetch paginated results
    skip = (page - 1) * per_page
    cursor = (
        collection.find(query)
        .sort(sort_by, sort_order)
        .skip(skip)
        .limit(per_page)
    )

    articles = []
    for doc in cursor:
        doc["_id"] = str(doc["_id"])  # Convert ObjectId to string for JSON
        articles.append(doc)

    return articles, total


def get_unique_values(field: str) -> list[str]:
    """Get sorted unique values for a field (e.g., 'category', 'source', 'sentiment')."""
    collection = get_collection()
    try:
        values = collection.distinct(field)
        return sorted([v for v in values if v and str(v).strip()])
    except Exception:
        return []


def get_article_count() -> int:
    """Get total number of articles in the database."""
    try:
        collection = get_collection()
        return collection.count_documents({})
    except Exception:
        return 0


def get_article_by_url(url: str) -> dict | None:
    """Find a single article by its URL."""
    collection = get_collection()
    doc = collection.find_one({"url": url})
    if doc:
        doc["_id"] = str(doc["_id"])
    return doc


def url_exists(url: str) -> bool:
    """Check if an article URL already exists in the database."""
    collection = get_collection()
    return collection.count_documents({"url": url}, limit=1) > 0


def get_existing_urls() -> set:
    """Get all existing article URLs as a set (for bulk dedup)."""
    collection = get_collection()
    urls = collection.distinct("url")
    return set(urls)


def get_existing_headlines() -> set:
    """Get all existing headlines as a lowercase set (for bulk dedup)."""
    collection = get_collection()
    headlines = collection.distinct("headline")
    return set(h.lower() for h in headlines if h)


def delete_all_articles() -> int:
    """Delete all articles from the collection. Returns count deleted."""
    collection = get_collection()
    result = collection.delete_many({})
    logger.info(f"MongoDB: Deleted {result.deleted_count} articles")
    return result.deleted_count


def get_stats() -> dict:
    """Get database statistics for the dashboard."""
    collection = get_collection()

    total = collection.count_documents({})

    # Category distribution
    category_pipeline = [
        {"$group": {"_id": "$category", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
    ]
    categories = {doc["_id"]: doc["count"] for doc in collection.aggregate(category_pipeline) if doc["_id"]}

    # Source distribution
    source_pipeline = [
        {"$group": {"_id": "$source", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
    ]
    sources = {doc["_id"]: doc["count"] for doc in collection.aggregate(source_pipeline) if doc["_id"]}

    # Sentiment distribution
    sentiment_pipeline = [
        {"$group": {"_id": "$sentiment", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
    ]
    sentiments = {doc["_id"]: doc["count"] for doc in collection.aggregate(sentiment_pipeline) if doc["_id"]}

    return {
        "total": total,
        "categories": categories,
        "sources": sources,
        "sentiments": sentiments,
    }


# ─────────────────────────────────────────────
# Source Management
# ─────────────────────────────────────────────
def get_all_sources(group: str = None) -> list[dict]:
    """Fetch all source configurations from the DB."""
    coll = get_sources_collection()
    query = {"group": group} if group else {}
    cursor = coll.find(query).sort("name", 1)
    
    sources = []
    for doc in cursor:
        doc["_id"] = str(doc["_id"])
        sources.append(doc)
    return sources


def update_source_status(scraper_key: str, is_enabled: bool) -> bool:
    """Enable or disable a specific news source."""
    coll = get_sources_collection()
    result = coll.update_one(
        {"scraper_key": scraper_key},
        {"$set": {"is_enabled": is_enabled}}
    )
    return result.modified_count > 0


def update_source_interval(scraper_key: str, interval: int) -> bool:
    """Update how often a source is scraped (in hours)."""
    coll = get_sources_collection()
    result = coll.update_one(
        {"scraper_key": scraper_key},
        {"$set": {"interval_hours": interval}}
    )
    return result.modified_count > 0


def migrate_config_to_db():
    """Migrate sources from config.py to MongoDB if collection is empty."""
    from config import INTERNATIONAL_SITES, INDIAN_SITES, REGIONAL_SITES, TECH_SITES
    
    coll = get_sources_collection()
    if coll.count_documents({}) > 0:
        logger.info("Sources already exist in DB. Migration skipped.")
        return

    all_groups = [
        ("International", INTERNATIONAL_SITES),
        ("Indian", INDIAN_SITES),
        ("Regional", REGIONAL_SITES),
        ("Technology", TECH_SITES),
    ]

    count = 0
    for group_name, sites in all_groups:
        for site in sites:
            doc = {
                "name": site["name"],
                "scraper_key": site["scraper_key"],
                "main_link": site["main_link"],
                "sub_links": site["sub_links"],
                "group": group_name,
                "is_enabled": True,
                "interval_hours": 1, 
                "last_scraped": None
            }
            try:
                coll.insert_one(doc)
                count += 1
            except Exception as e:
                logger.error(f"Error migrating source {site['name']}: {e}")
    
    logger.info(f"Database: Migrated {count} sources to MongoDB.")


# ─────────────────────────────────────────────
# Trends and Intelligence
# ─────────────────────────────────────────────
def get_trending_keywords(limit: int = 50) -> list[dict]:
    """
    Extract and count frequent keywords from headlines.
    Excludes common 'stop words'.
    """
    collection = get_collection()
    
    pipeline = [
        {"$project": {"words": {"$split": ["$headline", " "]}}},
        {"$unwind": "$words"},
        {"$project": {"word": {"$toLower": "$words"}}},
        # Filter out short words and non-words
        {"$match": {"word": {"$regex": "^.{4,}$"}}},
        {"$group": {"_id": "$word", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": limit * 2} # Get more to filter stop words
    ]
    
    stop_words = {
        "this", "that", "with", "from", "your", "more", "about", "will", 
        "their", "there", "what", "when", "where", "into", "been", "were"
    }
    
    results = []
    for doc in collection.aggregate(pipeline):
        word = doc["_id"].strip(",.()\"':-")
        if word not in stop_words and len(word) > 3:
            results.append({"text": word, "size": doc["count"]})
            if len(results) >= limit:
                break
    return results


def get_sentiment_heatmap() -> list[dict]:
    """Group sentiment counts by category for heatmap visualization."""
    collection = get_collection()
    
    pipeline = [
        {"$group": {
            "_id": {
                "category": "$category",
                "sentiment": "$sentiment"
            },
            "count": {"$sum": 1}
        }},
        {"$sort": {"_id.category": 1, "count": -1}}
    ]
    
    # Transform to format: {category: {Positive: X, Negative: Y, Neutral: Z}}
    data = {}
    for doc in collection.aggregate(pipeline):
        cat = doc["_id"]["category"]
        sent = doc["_id"]["sentiment"]
        count = doc["count"]
        
        if cat not in data:
            data[cat] = {"Positive": 0, "Negative": 0, "Neutral": 0}
        data[cat][sent] = count
        
    # Flatten for easier JS usage
    flattened = []
    for cat, values in data.items():
        flattened.append({
            "category": cat,
            "positive": values["Positive"],
            "negative": values["Negative"],
            "neutral": values["Neutral"],
            "total": sum(values.values())
        })
    return flattened


# ─────────────────────────────────────────────
# Migration: CSV → MongoDB
# ─────────────────────────────────────────────
def migrate_csv_to_mongo(csv_path: str = None) -> int:
    """
    Import existing CSV data into MongoDB.
    Skips duplicates automatically via the unique URL index.
    """
    import pandas as pd
    from config import CSV_FILE

    if csv_path is None:
        csv_path = CSV_FILE

    try:
        df = pd.read_csv(csv_path, encoding="utf-8-sig")
    except Exception as e:
        logger.error(f"Could not read CSV: {e}")
        return 0

    if df.empty:
        logger.info("CSV is empty, nothing to migrate.")
        return 0

    articles = df.to_dict("records")

    # Fill defaults
    for article in articles:
        if not article.get("author") or str(article.get("author", "")).strip() == "" or str(article.get("author", "")) == "nan":
            article["author"] = "Unknown"
        if not article.get("date") or str(article.get("date", "")).strip() == "" or str(article.get("date", "")) == "nan":
            article["date"] = "N/A"
        if not article.get("sentiment") or str(article.get("sentiment", "")) == "nan":
            article["sentiment"] = "Neutral"
        if not article.get("sentiment_polarity") or str(article.get("sentiment_polarity", "")) == "nan":
            article["sentiment_polarity"] = 0.0

    count = insert_articles(articles)
    logger.info(f"Migration complete: {count} articles imported from CSV to MongoDB")
    return count


# ─────────────────────────────────────────────
# Advanced Intelligence Queries
# ─────────────────────────────────────────────

def get_recent_news(minutes: int = 15) -> list[dict]:
    """Fetch articles scraped in the last X minutes."""
    from datetime import timedelta
    collection = get_collection()
    
    # Calculate cutoff time
    cutoff = (datetime.now() - timedelta(minutes=minutes)).strftime("%Y-%m-%d %H:%M:%S")
    
    cursor = collection.find({"scraped_at": {"$gte": cutoff}}).sort("scraped_at", DESCENDING)
    
    results = []
    for doc in cursor:
        doc["_id"] = str(doc["_id"])
        results.append(doc)
    return results


def get_historical_data(offset_days: int = 0, offset_weeks: int = 0, offset_years: int = 0) -> list[dict]:
    """Fetch articles from a specific point in history (Archive/Time Machine)."""
    from datetime import timedelta
    collection = get_collection()
    
    target_date = datetime.now()
    if offset_days: target_date -= timedelta(days=offset_days)
    if offset_weeks: target_date -= timedelta(weeks=offset_weeks)
    if offset_years: target_date -= timedelta(days=365 * offset_years)
    
    date_str = target_date.strftime("%Y-%m-%d")
    
    # Query for articles on that specific date
    query = {"scraped_at": {"$regex": f"^{date_str}"}}
    cursor = collection.find(query).sort("scraped_at", DESCENDING).limit(50)
    
    results = []
    for doc in cursor:
        doc["_id"] = str(doc["_id"])
        results.append(doc)
    return results


def get_geostat_data() -> list[dict]:
    """Count mentions of countries/cities in headlines for the news map."""
    collection = get_collection()
    
    # Simple list of focus locations
    locations = {
        "India": ["India", "Delhi", "Mumbai", "Bangalore", "Chennai", "Kolkata", "Gujarat", "Ahmedabad", "Surat"],
        "USA": ["USA", "America", "US", "Washington", "New York", "California"],
        "UK": ["UK", "Britain", "London", "England"],
        "China": ["China", "Beijing", "Shanghai"],
        "Russia": ["Russia", "Moscow"],
        "Israel": ["Israel", "Gaza", "Palestine"],
        "Ukraine": ["Ukraine", "Kyiv"],
        "France": ["France", "Paris"],
        "Japan": ["Japan", "Tokyo"],
        "Australia": ["Australia", "Sydney"],
        "Germany": ["Germany", "Berlin"],
        "Canada": ["Canada", "Toronto"],
        "UAE": ["UAE", "Dubai", "Abu Dhabi"],
    }
    
    stats = []
    # In a real app we'd use a search engine or NLTK
    # This is an efficient way to get counts using MongoDB
    for country, keywords in locations.items():
        query = {"$or": [
            {"headline": {"$regex": kw, "$options": "i"}} for kw in keywords
        ]}
        count = collection.count_documents(query)
        if count > 0:
            stats.append({"country": country, "count": count})
            
    return stats


def get_summary_data() -> dict:
    """Enhanced grouping of top articles and narrative shifts."""
    collection = get_collection()
    
    # 1. Identify "Hot Topics" by counting word clusters in last 24h
    keywords = get_trending_keywords(limit=10)
    
    # 2. Get latest significant headlines per category for comparison
    categories = ["World", "Technology", "Business", "Sports", "Politics"]
    comparison = {}
    for cat in categories:
        top_doc = collection.find_one(
            {"category": {"$regex": f"^{cat}$", "$options": "i"}}, 
            sort=[("scraped_at", -1)]
        )
        if top_doc:
            comparison[cat] = {
                "headline": top_doc["headline"],
                "source": top_doc["source"],
                "sentiment": top_doc["sentiment"]
            }
            
    return {
        "trending": keywords,
        "latest_by_category": comparison
    }


def get_velocity_data(scale: str = "h") -> list[dict]:
    """Calculate news volume based on time scale (minute, hour, month, year)."""
    from datetime import timedelta
    collection = get_collection()
    now = datetime.now()
    
    # 1. Determine cutoff and project format
    if scale == 'm':
        cutoff = (now - timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S")
        project = {"$substr": ["$scraped_at", 11, 5]} # "HH:MM"
        match = {"scraped_at": {"$gte": cutoff}}
    elif scale == 'h':
        cutoff = (now - timedelta(hours=24)).strftime("%Y-%m-%d %H:00:00")
        project = {"$substr": ["$scraped_at", 11, 2]} # "HH"
        match = {"scraped_at": {"$gte": cutoff}}
    elif scale == 'd':
        cutoff = (now - timedelta(days=30)).strftime("%Y-%m-%d 00:00:00")
        project = {"$substr": ["$scraped_at", 5, 5]} # "MM-DD"
        match = {"scraped_at": {"$gte": cutoff}}
    elif scale == 'M':
        cutoff = (now - timedelta(days=365)).strftime("%Y-%m-01 00:00:00")
        project = {"$substr": ["$scraped_at", 0, 7]} # "YYYY-MM"
        match = {"scraped_at": {"$gte": cutoff}}
    elif scale == 'y':
        project = {"$substr": ["$scraped_at", 0, 4]} # "YYYY"
        match = {}
    else: # "all"
        project = {"$substr": ["$scraped_at", 0, 10]} # "YYYY-MM-DD"
        match = {}

    pipeline = [
        {"$match": match},
        {"$project": {"t": project}},
        {"$group": {"_id": "$t", "count": {"$sum": 1}}},
        {"$sort": {"_id": 1}}
    ]
    
    return list(collection.aggregate(pipeline))


def get_source_polarization() -> list[dict]:
    """Compare sentiment distribution across the top 10 sources."""
    collection = get_collection()
    
    # 1. Get top 10 sources by volume
    top_sources = [doc["_id"] for doc in collection.aggregate([
        {"$group": {"_id": "$source", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 10}
    ])]
    
    pipeline = [
        {"$match": {"source": {"$in": top_sources}}},
        {"$group": {
            "_id": {
                "source": "$source",
                "sentiment": "$sentiment"
            },
            "count": {"$sum": 1}
        }}
    ]
    
    # Transform to {Source: {Pos: X, Neg: Y, Neu: Z}}
    data = {}
    for doc in collection.aggregate(pipeline):
        src = doc["_id"]["source"]
        sent = doc["_id"]["sentiment"]
        count = doc["count"]
        if src not in data:
            data[src] = {"Positive": 0, "Negative": 0, "Neutral": 0}
        data[src][sent] = count
        
    return [{"source": s, "sentiment": v} for s, v in data.items()]


def get_momentum_data() -> dict:
    """Compare sentiment percentages between current vs previous week."""
    from datetime import timedelta
    collection = get_collection()
    
    now = datetime.now()
    this_week_start = (now - timedelta(days=7)).strftime("%Y-%m-%d %H:%M:%S")
    last_week_start = (now - timedelta(days=14)).strftime("%Y-%m-%d %H:%M:%S")
    
    def get_avg_sentiment(start, end):
        pipeline = [
            {"$match": {"scraped_at": {"$gte": start, "$lt": end}}},
            {"$group": {"_id": None, "avg": {"$avg": "$sentiment_polarity"}}}
        ]
        res = list(collection.aggregate(pipeline))
        return res[0]["avg"] if res else 0.0

    current = get_avg_sentiment(this_week_start, now.strftime("%Y-%m-%d %H:%M:%S"))
    previous = get_avg_sentiment(last_week_start, this_week_start)
    
    change = ((current - previous) / abs(previous) * 100) if previous != 0 else 0
    
    return {
        "current_score": round(current, 3),
        "previous_score": round(previous, 3),
        "change_percent": round(change, 1)
    }


# ─────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────
if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "migrate":
        print("Migrating CSV data to MongoDB...")
        count = migrate_csv_to_mongo()
        print(f"Done! {count} articles migrated.")
    elif len(sys.argv) > 1 and sys.argv[1] == "stats":
        stats = get_stats()
        print(f"Total articles: {stats['total']}")
        print(f"Categories: {stats['categories']}")
        print(f"Sources: {stats['sources']}")
        print(f"Sentiments: {stats['sentiments']}")
    elif len(sys.argv) > 1 and sys.argv[1] == "clear":
        count = delete_all_articles()
        print(f"Deleted {count} articles.")
    elif len(sys.argv) > 1 and sys.argv[1] == "setup":
        print("Setting up database collections and migrating sources...")
        migrate_config_to_db()
        print("Setup complete.")
    else:
        print("Usage:")
        print("  python database.py setup     - Initial DB setup and source migration")
        print("  python database.py migrate   - Import CSV data to MongoDB")
        print("  python database.py stats     - Show database statistics")
        print("  python database.py clear     - Delete all articles")
