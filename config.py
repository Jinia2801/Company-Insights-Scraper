import os

BASE_URL = "https://www.ambitionbox.com"
LISTING_URL = f"{BASE_URL}/list-of-companies"

TOTAL_PAGES = 5              
MIN_DELAY = 2                
MAX_DELAY = 5                
MAX_RETRIES = 3              
REQUEST_TIMEOUT = 15        

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
LOG_DIR = os.path.join(os.path.dirname(__file__), "logs")
OUTPUT_CSV = os.path.join(DATA_DIR, "ambitionbox_companies.csv")
RAW_CSV = os.path.join(DATA_DIR, "ambitionbox_raw.csv")       

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:126.0) Gecko/20100101 Firefox/126.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_5) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4.1 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 Edg/124.0.0.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
]

DEFAULT_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
}

CSV_COLUMNS = [
    "company_name",
    "profile_url",
    "overall_rating",
    "total_reviews",
    "industry",
    "description",
    "rating_job_security",
    "rating_work_life_balance",
    "rating_salary",
    "rating_work_satisfaction",
    "rating_promotions",
    "rating_skill_development",
    "rating_company_culture",
    "rating_management",
    "scraped_at",
]
