"""
config.py - Central configuration for the News Scraper Project.
Contains all website definitions, scraper settings, and application constants.
"""

import os

# ─────────────────────────────────────────────
# Paths
# ─────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
CSV_FILE = os.path.join(DATA_DIR, "news.csv")

# Ensure data directory exists
os.makedirs(DATA_DIR, exist_ok=True)

# ─────────────────────────────────────────────
# Scraper Settings
# ─────────────────────────────────────────────
REQUEST_TIMEOUT = 8           # seconds (reduced for speed)
REQUEST_DELAY = (0.05, 0.15)  # minimal delay between requests (seconds)
MAX_ARTICLES_PER_SUB = 10     # max articles to scrape per sub-link
MAX_RETRIES = 1               # reduced retries for speed
SCRAPE_INTERVAL_HOURS = 1     # auto-scrape interval

# Concurrency settings
MAX_WORKERS_SITES = 8         # parallel sites at once
MAX_WORKERS_ARTICLES = 10     # parallel articles per site

# CSV columns
CSV_COLUMNS = [
    "headline", "author", "date", "content", "category",
    "source", "url", "sentiment", "sentiment_polarity",
    "scraped_at"
]

# ─────────────────────────────────────────────
# User-Agent headers
# ─────────────────────────────────────────────
DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

# ─────────────────────────────────────────────
# Website Definitions
# Each entry: {
#   "name": display name,
#   "scraper_key": key used to look up scraper function,
#   "main_link": main url,
#   "sub_links": list of category page urls,
# }
# ─────────────────────────────────────────────

# ═══════════════════════════════════════════════
# 1. INTERNATIONAL NEWS WEBSITES (15 Websites)
# ═══════════════════════════════════════════════

INTERNATIONAL_SITES = [
    # ── 01. BBC NEWS ──
    {
        "name": "BBC News",
        "scraper_key": "bbc",
        "main_link": "https://www.bbc.com/news",
        "sub_links": [
            "https://www.bbc.com/news",
            "https://www.bbc.com/sport",
            "https://www.bbc.com/news/business",
            "https://www.bbc.com/news/technology",
            "https://www.bbc.com/news/health",
            "https://www.bbc.com/culture",
            "https://www.bbc.com/travel",
            "https://www.bbc.com/future/earth",
            "https://www.bbc.com/news/world",
            "https://www.bbc.com/news/politics",
            "https://www.bbc.com/news/science_and_environment",
            "https://www.bbc.com/news/entertainment_and_arts",
            "https://www.bbc.com/news/education",
        ],
    },
    # ── 02. CNN ──
    {
        "name": "CNN",
        "scraper_key": "cnn",
        "main_link": "https://edition.cnn.com/",
        "sub_links": [
            "https://edition.cnn.com/world",
            "https://edition.cnn.com/politics",
            "https://edition.cnn.com/business",
            "https://edition.cnn.com/health",
            "https://edition.cnn.com/entertainment",
            "https://edition.cnn.com/tech",
            "https://edition.cnn.com/style",
            "https://edition.cnn.com/travel",
            "https://edition.cnn.com/sport",
            "https://edition.cnn.com/us",
            "https://edition.cnn.com/climate",
            "https://edition.cnn.com/weather",
            "https://edition.cnn.com/science",
        ],
    },
    # ── 03. REUTERS ──
    {
        "name": "Reuters",
        "scraper_key": "reuters",
        "main_link": "https://www.reuters.com/",
        "sub_links": [
            "https://www.reuters.com/world/",
            "https://www.reuters.com/business/",
            "https://www.reuters.com/markets/",
            "https://www.reuters.com/technology/",
            "https://www.reuters.com/legal/",
            "https://www.reuters.com/breakingviews/",
            "https://www.reuters.com/lifestyle/",
            "https://www.reuters.com/science/",
            "https://www.reuters.com/sports/",
            "https://www.reuters.com/sustainability/",
        ],
    },
    # ── 04. AL JAZEERA ──
    {
        "name": "Al Jazeera",
        "scraper_key": "aljazeera",
        "main_link": "https://www.aljazeera.com/",
        "sub_links": [
            "https://www.aljazeera.com/news/",
            "https://www.aljazeera.com/middle-east/",
            "https://www.aljazeera.com/africa/",
            "https://www.aljazeera.com/asia/",
            "https://www.aljazeera.com/us-canada/",
            "https://www.aljazeera.com/latin-america/",
            "https://www.aljazeera.com/europe/",
            "https://www.aljazeera.com/economy/",
            "https://www.aljazeera.com/science/",
            "https://www.aljazeera.com/sports/",
            "https://www.aljazeera.com/features/",
            "https://www.aljazeera.com/opinion/",
            "https://www.aljazeera.com/climate-crisis/",
            "https://www.aljazeera.com/tag/human-rights/",
        ],
    },
    # ── 05. THE GUARDIAN ──
    {
        "name": "The Guardian",
        "scraper_key": "guardian",
        "main_link": "https://www.theguardian.com/international",
        "sub_links": [
            "https://www.theguardian.com/world",
            "https://www.theguardian.com/uk-news",
            "https://www.theguardian.com/politics",
            "https://www.theguardian.com/business",
            "https://www.theguardian.com/technology",
            "https://www.theguardian.com/science",
            "https://www.theguardian.com/environment",
            "https://www.theguardian.com/global-development",
            "https://www.theguardian.com/culture",
            "https://www.theguardian.com/sport",
            "https://www.theguardian.com/lifeandstyle",
            "https://www.theguardian.com/commentisfree",
            "https://www.theguardian.com/film",
            "https://www.theguardian.com/music",
            "https://www.theguardian.com/travel",
            "https://www.theguardian.com/fashion",
            "https://www.theguardian.com/food",
        ],
    },
    # ── 06. THE NEW YORK TIMES ──
    {
        "name": "The New York Times",
        "scraper_key": "nytimes",
        "main_link": "https://www.nytimes.com/",
        "sub_links": [
            "https://www.nytimes.com/section/world",
            "https://www.nytimes.com/section/us",
            "https://www.nytimes.com/section/politics",
            "https://www.nytimes.com/section/business",
            "https://www.nytimes.com/section/technology",
            "https://www.nytimes.com/section/science",
            "https://www.nytimes.com/section/health",
            "https://www.nytimes.com/section/sports",
            "https://www.nytimes.com/section/arts",
            "https://www.nytimes.com/section/style",
            "https://www.nytimes.com/section/food",
            "https://www.nytimes.com/section/travel",
            "https://www.nytimes.com/section/opinion",
            "https://www.nytimes.com/section/climate",
            "https://www.nytimes.com/section/education",
            "https://www.nytimes.com/section/obituaries",
            "https://www.nytimes.com/section/realestate",
        ],
    },
    # ── 07. THE WASHINGTON POST ──
    {
        "name": "The Washington Post",
        "scraper_key": "washingtonpost",
        "main_link": "https://www.washingtonpost.com/",
        "sub_links": [
            "https://www.washingtonpost.com/world/",
            "https://www.washingtonpost.com/politics/",
            "https://www.washingtonpost.com/business/",
            "https://www.washingtonpost.com/technology/",
            "https://www.washingtonpost.com/sports/",
            "https://www.washingtonpost.com/entertainment/",
            "https://www.washingtonpost.com/lifestyle/",
            "https://www.washingtonpost.com/climate-environment/",
            "https://www.washingtonpost.com/health/",
            "https://www.washingtonpost.com/science/",
            "https://www.washingtonpost.com/opinions/",
            "https://www.washingtonpost.com/education/",
            "https://www.washingtonpost.com/national/",
            "https://www.washingtonpost.com/dc-md-va/",
        ],
    },
    # ── 08. BLOOMBERG ──
    {
        "name": "Bloomberg",
        "scraper_key": "bloomberg",
        "main_link": "https://www.bloomberg.com/",
        "sub_links": [
            "https://www.bloomberg.com/markets",
            "https://www.bloomberg.com/economics",
            "https://www.bloomberg.com/industries",
            "https://www.bloomberg.com/technology",
            "https://www.bloomberg.com/politics",
            "https://www.bloomberg.com/wealth",
            "https://www.bloomberg.com/pursuits",
            "https://www.bloomberg.com/green",
            "https://www.bloomberg.com/citylab",
            "https://www.bloomberg.com/crypto",
            "https://www.bloomberg.com/opinion",
            "https://www.bloomberg.com/businessweek",
        ],
    },
    # ── 09. AP NEWS ──
    {
        "name": "AP News",
        "scraper_key": "apnews",
        "main_link": "https://apnews.com/",
        "sub_links": [
            "https://apnews.com/world-news",
            "https://apnews.com/us-news",
            "https://apnews.com/politics",
            "https://apnews.com/sports",
            "https://apnews.com/entertainment",
            "https://apnews.com/technology",
            "https://apnews.com/business",
            "https://apnews.com/science",
            "https://apnews.com/health",
            "https://apnews.com/lifestyle",
            "https://apnews.com/oddities",
            "https://apnews.com/climate-and-environment",
        ],
    },
    # ── 10. CNBC ──
    {
        "name": "CNBC",
        "scraper_key": "cnbc",
        "main_link": "https://www.cnbc.com/world/",
        "sub_links": [
            "https://www.cnbc.com/world/",
            "https://www.cnbc.com/business/",
            "https://www.cnbc.com/markets/",
            "https://www.cnbc.com/technology/",
            "https://www.cnbc.com/investing/",
            "https://www.cnbc.com/politics/",
            "https://www.cnbc.com/health-and-science/",
            "https://www.cnbc.com/personal-finance/",
            "https://www.cnbc.com/real-estate/",
            "https://www.cnbc.com/economy/",
            "https://www.cnbc.com/cryptoworld/",
        ],
    },
    # ── 11. FOX NEWS ──
    {
        "name": "Fox News",
        "scraper_key": "foxnews",
        "main_link": "https://www.foxnews.com/",
        "sub_links": [
            "https://www.foxnews.com/politics",
            "https://www.foxnews.com/us",
            "https://www.foxnews.com/world",
            "https://www.foxnews.com/media",
            "https://www.foxnews.com/entertainment",
            "https://www.foxnews.com/sports",
            "https://www.foxnews.com/lifestyle",
            "https://www.foxnews.com/science",
            "https://www.foxnews.com/health",
            "https://www.foxnews.com/opinion",
            "https://www.foxnews.com/tech",
            "https://www.foxnews.com/weather",
            "https://www.foxnews.com/category/us/crime",
        ],
    },
    # ── 12. SKY NEWS ──
    {
        "name": "Sky News",
        "scraper_key": "skynews",
        "main_link": "https://news.sky.com/",
        "sub_links": [
            "https://news.sky.com/uk",
            "https://news.sky.com/world",
            "https://news.sky.com/politics",
            "https://news.sky.com/us",
            "https://news.sky.com/climate",
            "https://news.sky.com/science-and-tech",
            "https://news.sky.com/business",
            "https://news.sky.com/entertainment",
            "https://news.sky.com/strange-news",
        ],
    },
    # ── 13. ABC NEWS ──
    {
        "name": "ABC News",
        "scraper_key": "abcnews",
        "main_link": "https://abcnews.go.com/",
        "sub_links": [
            "https://abcnews.go.com/US",
            "https://abcnews.go.com/Politics",
            "https://abcnews.go.com/International",
            "https://abcnews.go.com/Health",
            "https://abcnews.go.com/Entertainment",
            "https://abcnews.go.com/Technology",
            "https://abcnews.go.com/Sports",
            "https://abcnews.go.com/Business",
            "https://abcnews.go.com/Weather",
            "https://abcnews.go.com/US/Crime",
            "https://abcnews.go.com/Science",
        ],
    },
    # ── 14. CBS NEWS ──
    {
        "name": "CBS News",
        "scraper_key": "cbsnews",
        "main_link": "https://www.cbsnews.com/",
        "sub_links": [
            "https://www.cbsnews.com/us/",
            "https://www.cbsnews.com/world/",
            "https://www.cbsnews.com/politics/",
            "https://www.cbsnews.com/entertainment/",
            "https://www.cbsnews.com/health/",
            "https://www.cbsnews.com/science/",
            "https://www.cbsnews.com/tech/",
            "https://www.cbsnews.com/sports/",
            "https://www.cbsnews.com/crime/",
            "https://www.cbsnews.com/moneywatch/",
        ],
    },
    # ── 15. USA TODAY ──
    {
        "name": "USA Today",
        "scraper_key": "usatoday",
        "main_link": "https://www.usatoday.com/",
        "sub_links": [
            "https://www.usatoday.com/news/nation/",
            "https://www.usatoday.com/news/world/",
            "https://www.usatoday.com/news/politics/",
            "https://www.usatoday.com/sports/",
            "https://www.usatoday.com/entertainment/",
            "https://www.usatoday.com/life/",
            "https://www.usatoday.com/money/",
            "https://www.usatoday.com/tech/",
            "https://www.usatoday.com/travel/",
            "https://www.usatoday.com/news/health/",
            "https://www.usatoday.com/news/science/",
            "https://www.usatoday.com/news/education/",
            "https://www.usatoday.com/weather/",
            "https://www.usatoday.com/opinion/",
        ],
    },
]

# ═══════════════════════════════════════════════
# 2. INDIAN NEWS WEBSITES (13 Websites)
# ═══════════════════════════════════════════════

INDIAN_SITES = [
    # ── 16. TIMES OF INDIA ──
    {
        "name": "Times of India",
        "scraper_key": "timesofindia",
        "main_link": "https://timesofindia.indiatimes.com/",
        "sub_links": [
            "https://timesofindia.indiatimes.com/india",
            "https://timesofindia.indiatimes.com/world",
            "https://timesofindia.indiatimes.com/business",
            "https://timesofindia.indiatimes.com/tech",
            "https://timesofindia.indiatimes.com/sports",
            "https://timesofindia.indiatimes.com/entertainment",
            "https://timesofindia.indiatimes.com/life-style",
            "https://timesofindia.indiatimes.com/education",
            "https://timesofindia.indiatimes.com/science",
            "https://timesofindia.indiatimes.com/life-style/health-fitness",
            "https://timesofindia.indiatimes.com/city",
            "https://timesofindia.indiatimes.com/auto",
            "https://timesofindia.indiatimes.com/travel",
            "https://timesofindia.indiatimes.com/nri",
        ],
    },
    # ── 17. THE HINDU ──
    {
        "name": "The Hindu",
        "scraper_key": "thehindu",
        "main_link": "https://www.thehindu.com/",
        "sub_links": [
            "https://www.thehindu.com/news/national/",
            "https://www.thehindu.com/news/international/",
            "https://www.thehindu.com/news/states/",
            "https://www.thehindu.com/news/cities/",
            "https://www.thehindu.com/business/",
            "https://www.thehindu.com/sport/",
            "https://www.thehindu.com/sci-tech/",
            "https://www.thehindu.com/life-and-style/",
            "https://www.thehindu.com/entertainment/",
            "https://www.thehindu.com/opinion/",
            "https://www.thehindu.com/education/",
            "https://www.thehindu.com/sci-tech/energy-and-environment/",
            "https://www.thehindu.com/elections/",
        ],
    },
    # ── 18. HINDUSTAN TIMES ──
    {
        "name": "Hindustan Times",
        "scraper_key": "hindustantimes",
        "main_link": "https://www.hindustantimes.com/",
        "sub_links": [
            "https://www.hindustantimes.com/india-news",
            "https://www.hindustantimes.com/world-news",
            "https://www.hindustantimes.com/cities",
            "https://www.hindustantimes.com/entertainment",
            "https://www.hindustantimes.com/cricket",
            "https://www.hindustantimes.com/sports",
            "https://www.hindustantimes.com/lifestyle",
            "https://www.hindustantimes.com/tech",
            "https://www.hindustantimes.com/business",
            "https://www.hindustantimes.com/education",
            "https://www.hindustantimes.com/health",
            "https://www.hindustantimes.com/india-news/politics",
            "https://www.hindustantimes.com/elections",
            "https://www.hindustantimes.com/auto",
        ],
    },
    # ── 19. INDIAN EXPRESS ──
    {
        "name": "Indian Express",
        "scraper_key": "indianexpress",
        "main_link": "https://indianexpress.com/",
        "sub_links": [
            "https://indianexpress.com/section/india/",
            "https://indianexpress.com/section/world/",
            "https://indianexpress.com/section/cities/",
            "https://indianexpress.com/section/business/",
            "https://indianexpress.com/section/sports/",
            "https://indianexpress.com/section/entertainment/",
            "https://indianexpress.com/section/technology/",
            "https://indianexpress.com/section/lifestyle/",
            "https://indianexpress.com/section/opinion/",
            "https://indianexpress.com/section/education/",
            "https://indianexpress.com/section/lifestyle/health/",
            "https://indianexpress.com/elections/",
            "https://indianexpress.com/section/research/",
            "https://indianexpress.com/section/explained/",
        ],
    },
    # ── 20. NDTV ──
    {
        "name": "NDTV",
        "scraper_key": "ndtv",
        "main_link": "https://www.ndtv.com/",
        "sub_links": [
            "https://www.ndtv.com/india-news",
            "https://www.ndtv.com/world-news",
            "https://www.ndtv.com/business",
            "https://www.ndtv.com/entertainment",
            "https://www.ndtv.com/sports",
            "https://www.ndtv.com/science",
            "https://www.ndtv.com/health",
            "https://www.ndtv.com/lifestyle",
            "https://www.ndtv.com/technology",
            "https://www.ndtv.com/education",
            "https://www.ndtv.com/elections",
            "https://www.ndtv.com/cities",
        ],
    },
    # ── 21. INDIA TODAY ──
    {
        "name": "India Today",
        "scraper_key": "indiatoday",
        "main_link": "https://www.indiatoday.in/",
        "sub_links": [
            "https://www.indiatoday.in/india",
            "https://www.indiatoday.in/world",
            "https://www.indiatoday.in/business",
            "https://www.indiatoday.in/tech",
            "https://www.indiatoday.in/movies",
            "https://www.indiatoday.in/sports",
            "https://www.indiatoday.in/lifestyle",
            "https://www.indiatoday.in/education-today",
            "https://www.indiatoday.in/health",
            "https://www.indiatoday.in/auto",
            "https://www.indiatoday.in/travel",
            "https://www.indiatoday.in/crime",
            "https://www.indiatoday.in/elections",
        ],
    },
    # ── 22. NEWS18 ──
    {
        "name": "News18",
        "scraper_key": "news18",
        "main_link": "https://www.news18.com/",
        "sub_links": [
            "https://www.news18.com/india/",
            "https://www.news18.com/world/",
            "https://www.news18.com/business/",
            "https://www.news18.com/tech/",
            "https://www.news18.com/movies/",
            "https://www.news18.com/sports/",
            "https://www.news18.com/lifestyle/",
            "https://www.news18.com/education/",
            "https://www.news18.com/politics/",
            "https://www.news18.com/lifestyle/health/",
            "https://www.news18.com/cricket/",
            "https://www.news18.com/auto/",
            "https://www.news18.com/tech/science/",
        ],
    },
    # ── 23. ZEE NEWS ──
    {
        "name": "Zee News",
        "scraper_key": "zeenews",
        "main_link": "https://zeenews.india.com/",
        "sub_links": [
            "https://zeenews.india.com/india",
            "https://zeenews.india.com/world",
            "https://zeenews.india.com/business",
            "https://zeenews.india.com/technology",
            "https://zeenews.india.com/entertainment",
            "https://zeenews.india.com/sports",
            "https://zeenews.india.com/health",
            "https://zeenews.india.com/lifestyle",
            "https://zeenews.india.com/science",
            "https://zeenews.india.com/automobile",
            "https://zeenews.india.com/education",
            "https://zeenews.india.com/cricket",
            "https://zeenews.india.com/elections",
        ],
    },
    # ── 24. ABP NEWS ──
    {
        "name": "ABP News",
        "scraper_key": "abpnews",
        "main_link": "https://news.abplive.com/",
        "sub_links": [
            "https://news.abplive.com/india-news",
            "https://news.abplive.com/world-news",
            "https://news.abplive.com/business",
            "https://news.abplive.com/sports",
            "https://news.abplive.com/entertainment",
            "https://news.abplive.com/technology",
            "https://news.abplive.com/lifestyle",
            "https://news.abplive.com/education",
            "https://news.abplive.com/health",
            "https://news.abplive.com/crime",
            "https://news.abplive.com/auto",
            "https://news.abplive.com/elections",
        ],
    },
    # ── 25. REPUBLIC WORLD ──
    {
        "name": "Republic World",
        "scraper_key": "republicworld",
        "main_link": "https://www.republicworld.com/",
        "sub_links": [
            "https://www.republicworld.com/india-news",
            "https://www.republicworld.com/world-news",
            "https://www.republicworld.com/business-news",
            "https://www.republicworld.com/sports-news",
            "https://www.republicworld.com/entertainment-news",
            "https://www.republicworld.com/technology-news",
            "https://www.republicworld.com/lifestyle",
            "https://www.republicworld.com/lifestyle/health",
            "https://www.republicworld.com/education",
            "https://www.republicworld.com/science",
            "https://www.republicworld.com/elections",
        ],
    },
    # ── 26. ECONOMIC TIMES ──
    {
        "name": "Economic Times",
        "scraper_key": "economictimes",
        "main_link": "https://economictimes.indiatimes.com/",
        "sub_links": [
            "https://economictimes.indiatimes.com/news/india",
            "https://economictimes.indiatimes.com/news/international",
            "https://economictimes.indiatimes.com/news/economy",
            "https://economictimes.indiatimes.com/markets",
            "https://economictimes.indiatimes.com/industry",
            "https://economictimes.indiatimes.com/tech",
            "https://economictimes.indiatimes.com/wealth",
            "https://economictimes.indiatimes.com/small-biz/startups",
            "https://economictimes.indiatimes.com/personal-finance",
            "https://economictimes.indiatimes.com/news/politics-and-nation",
            "https://economictimes.indiatimes.com/real-estate-news",
            "https://economictimes.indiatimes.com/mf",
            "https://economictimes.indiatimes.com/wealth/tax",
        ],
    },
    # ── 27. FINANCIAL EXPRESS ──
    {
        "name": "Financial Express",
        "scraper_key": "financialexpress",
        "main_link": "https://www.financialexpress.com/",
        "sub_links": [
            "https://www.financialexpress.com/economy/",
            "https://www.financialexpress.com/market/",
            "https://www.financialexpress.com/industry/",
            "https://www.financialexpress.com/money/",
            "https://www.financialexpress.com/business/",
            "https://www.financialexpress.com/infrastructure/",
            "https://www.financialexpress.com/business/technology/",
            "https://www.financialexpress.com/auto/",
            "https://www.financialexpress.com/defence/",
            "https://www.financialexpress.com/india-news/",
            "https://www.financialexpress.com/world-news/",
            "https://www.financialexpress.com/sports/",
            "https://www.financialexpress.com/entertainment/",
            "https://www.financialexpress.com/education/",
        ],
    },
    # ── 28. FIRSTPOST ──
    {
        "name": "Firstpost",
        "scraper_key": "firstpost",
        "main_link": "https://www.firstpost.com/",
        "sub_links": [
            "https://www.firstpost.com/india",
            "https://www.firstpost.com/world",
            "https://www.firstpost.com/business",
            "https://www.firstpost.com/entertainment",
            "https://www.firstpost.com/sports",
            "https://www.firstpost.com/tech",
            "https://www.firstpost.com/health",
            "https://www.firstpost.com/science",
            "https://www.firstpost.com/politics",
            "https://www.firstpost.com/living",
            "https://www.firstpost.com/auto",
            "https://www.firstpost.com/cricket",
            "https://www.firstpost.com/education",
        ],
    },
]

# ═══════════════════════════════════════════════
# 3. REGIONAL & GUJARATI NEWS WEBSITES (6 Websites)
# ═══════════════════════════════════════════════

REGIONAL_SITES = [
    # ── 29. DIVYA BHASKAR ──
    {
        "name": "Divya Bhaskar",
        "scraper_key": "divyabhaskar",
        "main_link": "https://www.divyabhaskar.co.in/",
        "sub_links": [
            "https://www.divyabhaskar.co.in/local/gujarat/",
            "https://www.divyabhaskar.co.in/national/",
            "https://www.divyabhaskar.co.in/international/",
            "https://www.divyabhaskar.co.in/business/",
            "https://www.divyabhaskar.co.in/sports/",
            "https://www.divyabhaskar.co.in/religion/",
            "https://www.divyabhaskar.co.in/entertainment/",
            "https://www.divyabhaskar.co.in/lifestyle/",
            "https://www.divyabhaskar.co.in/technology/",
            "https://www.divyabhaskar.co.in/health/",
            "https://www.divyabhaskar.co.in/education/",
            "https://www.divyabhaskar.co.in/astrology/",
            "https://www.divyabhaskar.co.in/automobile/",
            "https://www.divyabhaskar.co.in/crime/",
        ],
    },
    # ── 30. GUJARAT SAMACHAR ──
    {
        "name": "Gujarat Samachar",
        "scraper_key": "gujaratsamachar",
        "main_link": "https://www.gujaratsamachar.com/",
        "sub_links": [
            "https://www.gujaratsamachar.com/category/gujarat",
            "https://www.gujaratsamachar.com/category/national",
            "https://www.gujaratsamachar.com/category/international",
            "https://www.gujaratsamachar.com/category/sports",
            "https://www.gujaratsamachar.com/category/business",
            "https://www.gujaratsamachar.com/category/entertainment",
            "https://www.gujaratsamachar.com/category/health",
            "https://www.gujaratsamachar.com/category/technology",
            "https://www.gujaratsamachar.com/category/religion",
            "https://www.gujaratsamachar.com/category/lifestyle",
            "https://www.gujaratsamachar.com/category/education",
            "https://www.gujaratsamachar.com/category/crime",
        ],
    },
    # ── 31. SANDESH ──
    {
        "name": "Sandesh",
        "scraper_key": "sandesh",
        "main_link": "https://sandesh.com/",
        "sub_links": [
            "https://sandesh.com/gujarat",
            "https://sandesh.com/india",
            "https://sandesh.com/world",
            "https://sandesh.com/sports",
            "https://sandesh.com/business",
            "https://sandesh.com/entertainment",
            "https://sandesh.com/lifestyle",
            "https://sandesh.com/technology",
            "https://sandesh.com/health",
            "https://sandesh.com/religion",
            "https://sandesh.com/education",
            "https://sandesh.com/astrology",
            "https://sandesh.com/crime",
        ],
    },
    # ── 32. TV9 GUJARATI ──
    {
        "name": "TV9 Gujarati",
        "scraper_key": "tv9gujarati",
        "main_link": "https://tv9gujarati.com/",
        "sub_links": [
            "https://tv9gujarati.com/gujarat",
            "https://tv9gujarati.com/national",
            "https://tv9gujarati.com/international",
            "https://tv9gujarati.com/sports",
            "https://tv9gujarati.com/business",
            "https://tv9gujarati.com/entertainment",
            "https://tv9gujarati.com/technology",
            "https://tv9gujarati.com/health",
            "https://tv9gujarati.com/lifestyle",
            "https://tv9gujarati.com/religion",
            "https://tv9gujarati.com/education",
            "https://tv9gujarati.com/crime",
        ],
    },
    # ── 33. ABP ASMITA ──
    {
        "name": "ABP Asmita",
        "scraper_key": "abpasmita",
        "main_link": "https://gujarati.abplive.com/",
        "sub_links": [
            "https://gujarati.abplive.com/news/gujarat",
            "https://gujarati.abplive.com/news/india",
            "https://gujarati.abplive.com/news/world",
            "https://gujarati.abplive.com/news/business",
            "https://gujarati.abplive.com/news/sports",
            "https://gujarati.abplive.com/news/entertainment",
            "https://gujarati.abplive.com/news/technology",
            "https://gujarati.abplive.com/news/health",
            "https://gujarati.abplive.com/news/lifestyle",
            "https://gujarati.abplive.com/news/religion",
            "https://gujarati.abplive.com/news/education",
            "https://gujarati.abplive.com/news/crime",
            "https://gujarati.abplive.com/news/astrology",
        ],
    },
    # ── 34. ZEE 24 KALAK ──
    {
        "name": "Zee 24 Kalak",
        "scraper_key": "zee24kalak",
        "main_link": "https://zeenews.india.com/gujarati",
        "sub_links": [
            "https://zeenews.india.com/gujarati/gujarat",
            "https://zeenews.india.com/gujarati/india",
            "https://zeenews.india.com/gujarati/world",
            "https://zeenews.india.com/gujarati/business",
            "https://zeenews.india.com/gujarati/sports",
            "https://zeenews.india.com/gujarati/entertainment",
            "https://zeenews.india.com/gujarati/technology",
            "https://zeenews.india.com/gujarati/health",
            "https://zeenews.india.com/gujarati/lifestyle",
            "https://zeenews.india.com/gujarati/religion",
            "https://zeenews.india.com/gujarati/education",
            "https://zeenews.india.com/gujarati/crime",
            "https://zeenews.india.com/gujarati/astrology",
        ],
    },
]

# ═══════════════════════════════════════════════
# 4. TECHNOLOGY NEWS WEBSITES (5 Websites)
# ═══════════════════════════════════════════════

TECH_SITES = [
    # ── 35. TECHCRUNCH ──
    {
        "name": "TechCrunch",
        "scraper_key": "techcrunch",
        "main_link": "https://techcrunch.com/",
        "sub_links": [
            "https://techcrunch.com/category/startups/",
            "https://techcrunch.com/category/venture/",
            "https://techcrunch.com/category/artificial-intelligence/",
            "https://techcrunch.com/category/cryptocurrency/",
            "https://techcrunch.com/category/apps/",
            "https://techcrunch.com/category/security/",
            "https://techcrunch.com/category/hardware/",
            "https://techcrunch.com/category/transportation/",
            "https://techcrunch.com/category/media-entertainment/",
            "https://techcrunch.com/category/space/",
            "https://techcrunch.com/category/climate/",
        ],
    },
    # ── 36. THE VERGE ──
    {
        "name": "The Verge",
        "scraper_key": "theverge",
        "main_link": "https://www.theverge.com/",
        "sub_links": [
            "https://www.theverge.com/tech",
            "https://www.theverge.com/reviews",
            "https://www.theverge.com/science",
            "https://www.theverge.com/entertainment",
            "https://www.theverge.com/transportation",
            "https://www.theverge.com/ai-artificial-intelligence",
            "https://www.theverge.com/policy",
            "https://www.theverge.com/business",
            "https://www.theverge.com/apple",
            "https://www.theverge.com/google",
            "https://www.theverge.com/microsoft",
            "https://www.theverge.com/games",
        ],
    },
    # ── 37. WIRED ──
    {
        "name": "Wired",
        "scraper_key": "wired",
        "main_link": "https://www.wired.com/",
        "sub_links": [
            "https://www.wired.com/category/business/",
            "https://www.wired.com/category/gear/",
            "https://www.wired.com/category/culture/",
            "https://www.wired.com/category/science/",
            "https://www.wired.com/category/security/",
            "https://www.wired.com/category/tech/",
            "https://www.wired.com/tag/artificial-intelligence/",
            "https://www.wired.com/category/ideas/",
            "https://www.wired.com/category/health/",
            "https://www.wired.com/category/transportation/",
            "https://www.wired.com/category/politics/",
            "https://www.wired.com/tag/climate-change/",
        ],
    },
    # ── 38. GIZMODO ──
    {
        "name": "Gizmodo",
        "scraper_key": "gizmodo",
        "main_link": "https://gizmodo.com/",
        "sub_links": [
            "https://gizmodo.com/tech",
            "https://gizmodo.com/science",
            "https://gizmodo.com/io9",
            "https://gizmodo.com/reviews",
            "https://gizmodo.com/health",
            "https://gizmodo.com/artificial-intelligence",
            "https://gizmodo.com/science/space",
            "https://gizmodo.com/security",
            "https://gizmodo.com/climate",
            "https://gizmodo.com/politics",
            "https://gizmodo.com/entertainment",
            "https://gizmodo.com/gaming",
            "https://gizmodo.com/design",
        ],
    },
    # ── 39. ARS TECHNICA ──
    {
        "name": "Ars Technica",
        "scraper_key": "arstechnica",
        "main_link": "https://arstechnica.com/",
        "sub_links": [
            "https://arstechnica.com/technology/",
            "https://arstechnica.com/science/",
            "https://arstechnica.com/tech-policy/",
            "https://arstechnica.com/gaming/",
            "https://arstechnica.com/cars/",
            "https://arstechnica.com/ai/",
            "https://arstechnica.com/security/",
            "https://arstechnica.com/science/space/",
            "https://arstechnica.com/apple/",
            "https://arstechnica.com/health/",
            "https://arstechnica.com/information-technology/",
            "https://arstechnica.com/open-source/",
            "https://arstechnica.com/features/",
        ],
    },
]

# ─────────────────────────────────────────────
# Combine all sites
# ─────────────────────────────────────────────
ALL_SITES = INTERNATIONAL_SITES + INDIAN_SITES + REGIONAL_SITES + TECH_SITES
