# AmbitionBox Company Scraper

A Python-based web scraper built using requests and BeautifulSoup to extract company data from AmbitionBox. The scraper collects company names, ratings, reviews, industries, descriptions, and category-wise ratings, then stores the cleaned data in CSV format.

---

## What It Does

- Scrapes the **first 5 pages** of AmbitionBox's company listings
- Visits each company's **overview page** to extract detailed info
- Exports a **clean, structured CSV** multiple company-related fields
- Handles missing data, retries, and rate-limiting gracefully

## Data Fields Collected

| Field | Description |
|-------|-------------|
| `company_name` | Name of the company |
| `profile_url` | Direct link to the company's AmbitionBox page |
| `overall_rating` | Overall rating out of 5 |
| `total_reviews` | Total number of employee reviews |
| `industry` | Industry/sector the company belongs to |
| `description` | Brief company description |
| `rating_job_security` | Job security sub-rating |
| `rating_work_life_balance` | Work-life balance sub-rating |
| `rating_salary` | Salary & benefits sub-rating |
| `rating_work_satisfaction` | Work satisfaction sub-rating |
| `rating_promotions` | Promotions/appraisal sub-rating |
| `rating_skill_development` | Skill development sub-rating |
| `rating_company_culture` | Company culture sub-rating |
| `scraped_at` | Timestamp when the data was collected |

## Tech Stack

- **Python 3.8+**
- **requests** — HTTP requests with session management
- **BeautifulSoup4** — HTML parsing
- **pandas** — Data cleaning and CSV export
- **logging** — Built-in logging system

## Project Structure

```
ambitionbox-scraper/
├── main.py              # Entry point - run this to start
├── config.py            # All settings and constants
├── helpers.py           # Utility functions (requests, text cleaning)
├── scraper.py           # Core scraping logic (listing + detail pages)
├── cleaner.py           # Data cleaning and CSV export
├── requirements.txt     # Python dependencies
├── .gitignore           # Files to exclude from git
├── README.md            # This file
├── data/                # Output CSV files (auto-created)
└── logs/                # Log files (auto-created)
```

##  Setup & Usage

### 1. Clone the repository

```bash
git clone https://github.com/yourusername/ambitionbox-scraper.git
cd ambitionbox-scraper
```

### 2. Create a virtual environment (recommended)

```bash
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Mac/Linux
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the scraper

```bash
python main.py
```

The scraper will:
1. Scrape company listings from 5 pages
2. Visit each company's detail page
3. Save results to `data/ambitionbox_companies.csv`

##  Configuration

All settings are in `config.py`:

| Setting | Default | Description |
|---------|---------|-------------|
| `TOTAL_PAGES` | 5 | Number of listing pages to scrape |
| `MIN_DELAY` | 2 | Minimum delay between requests (seconds) |
| `MAX_DELAY` | 5 | Maximum delay between requests (seconds) |
| `MAX_RETRIES` | 3 | Retry attempts for failed requests |
| `REQUEST_TIMEOUT` | 15 | Request timeout in seconds |

## Request Handling

- **Random User-Agent rotation** across 5 different browsers
- **Random delays** between requests (2-5 seconds)
- **Session reuse** to mimic real browser behavior
- **Retry logic** Retry handling for failed requests
- **Realistic headers** (Accept, Accept-Language, etc.)

##  Data Quality

- Removes duplicate entries automatically
- Normalizes ratings to consistent format (e.g., `3.9`)
- Handles missing data with `N/A` placeholder
- Saves both raw and cleaned versions of the data
- Uses UTF-8-BOM encoding for Excel compatibility

##  Logging

Every run creates a timestamped log file in the `logs/` directory. Logs include:
- Request URLs and response status
- Companies found per page
- Errors and retries
- Final summary with data quality stats

##  Disclaimer

This scraper is built for **educational purposes only**. Please respect AmbitionBox's Terms of Service and `robots.txt`. Use responsibly and don't overload their servers.

