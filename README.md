# 📰 News Scraper Intelligence Platform

A professional-grade, full-stack intelligence suite that collects, analyzes, and visualizes global narratives from **40+ news websites** worldwide. This platform transforms raw headlines into geospatial intelligence, temporal trends, and AI-powered summaries.

> **Zero API Dependency** — Powered by a high-performance custom crawling engine using `requests` + `BeautifulSoup`.

---

## 🌟 Intelligence Modules

1.  **Geospatial Intelligence (Map)**: Interactive world map showing global mention intensity. Click any country to instantly retrieve localized news.
2.  **Temporal Analysis (Trends)**: Multi-scale news velocity tracking (Minutes/Hours/Days/Months) to monitor narrative momentum.
3.  **Narrative Synthesis (AI Brief)**: An AI-powered knowledge hub that generates narrative overviews and cross-source summaries.
4.  **Macro Dashboard**: Real-time analytics on sentiment distribution, source reliability, and category-level coverage.
5.  **Control Center**: Advanced administrative dashboard to manage scrapers, toggle sources, and adjust crawl frequencies.

---

## 📁 Project Structure

```
news_scraper_project/
├── app.py                 # Flask Server & Intelligence APIs
├── database.py            # MongoDB Operations & Aggregation Pipelines
├── scraper.py             # Multi-threaded Crawling Orchestrator
├── config.py              # Scraper Configurations & User-Agent Rotation
├── parser.py              # Heuristic-based HTML Extraction Engine
├── utils.py               # Sentiment Analysis & Text Processing Logic
├── templates/             # Premium Dark-Theme UI Templates
│   ├── map.html           # Interactive World Map
│   ├── summary.html       # AI Synthesis Hub (Explorer)
│   ├── trends.html        # Macro Analytics & Velocity Charts
│   ├── scrape.html        # Scraper Mission Control
│   └── index.html         # Real-time News Feed
└── static/
    ├── css/style.css      # Premium Glassmorphism Design System
    └── js/main.js         # Reactive Frontend Logic
```

---

## 🚀 Setup & Installation

### Prerequisites
- Python 3.10+
- **MongoDB** (Local or Atlas)
- NLTK Tokenizers

### Quick Start (Windows)
```powershell
# 1. Clone & Navigate
cd news_scraper_project

# 2. Virtual Env
python -m venv venv
venv\Scripts\activate

# 3. Dependencies
pip install -r requirements.txt

# 4. Intelligence Init
python -c "import nltk; nltk.download('punkt'); nltk.download('punkt_tab')"

# 5. Start Platform
python app.py
```

---

## 🎯 Advanced Features

### Engine Intelligence
- **High-Velocity Scraping**: Multi-threaded parallel execution across 40+ targets.
- **Anti-Blocking System**: Integrated User-Agent rotation and request throttling.
- **Adaptive Parsing**: Site-specific parsers with a global heuristic fallback.

### Semantic Analysis
- **Sentiment Engine**: Real-time polarity scoring (Positive/Neutral/Negative).
- **Geographic Tagging**: Automatic detection of national entities in headlines.
- **Deduplication**: SHA-256 based fingerprinting to prevent data redundancy.

### Data Architecture
- **MongoDB Aggregation**: Complex pipelines for multi-scale time-series data.
- **Persistence**: Efficient storage of full-text articles and source metadata.

---

## 🔧 Technology Stack

| Layer | Technologies |
| :--- | :--- |
| **Backend** | Python, Flask, APScheduler |
| **Data Engine** | MongoDB, PyMongo, Regex |
| **Extraction** | Requests, BeautifulSoup, LXML |
| **Intelligence** | TextBlob (Sentiment), NLTK |
| **Visuals** | Chart.js, jsVectorMap, Glassmorphism CSS |
| **Typography** | Google Fonts (Inter, Outfit) |

---

## 🤖 AI Collaborative Credit

This project was developed through a high-level collaboration with cutting-edge AI models:
- **Claude 3.5 Sonnet**: Primary architect for UI/UX design, geospatial integration, and layout.
- **GPT-4o**: Logic orchestration, scraper persistence, and threading optimization.
- **GLM-4**: Aggregation pipeline refinement and database scaling.

---

## ⚠️ Disclaimer
Educational use only. Respect `robots.txt` and website Terms of Service. All content belongs to respective publishers.

## 📝 License
MIT License. Free for research and personal investigation.

