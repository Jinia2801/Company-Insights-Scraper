import logging
import os
import random
import time
import re
import requests
from datetime import datetime

from config import (
    USER_AGENTS,
    DEFAULT_HEADERS,
    MAX_RETRIES,
    REQUEST_TIMEOUT,
    MIN_DELAY,
    MAX_DELAY,
    LOG_DIR,
)


def setup_logging():
    os.makedirs(LOG_DIR, exist_ok=True)

    log_file = os.path.join(LOG_DIR, f"scraper_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-7s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            logging.FileHandler(log_file, encoding="utf-8"),
            logging.StreamHandler(),  # also print to console
        ],
    )
    logging.info("Logging started - log file: %s", log_file)


def get_random_headers():
    """Pick a random user-agent and return full headers dict."""
    headers = DEFAULT_HEADERS.copy()
    headers["User-Agent"] = random.choice(USER_AGENTS)
    return headers


def polite_delay():
    """Wait a random amount of time between requests (be nice to the server)."""
    wait_time = random.uniform(MIN_DELAY, MAX_DELAY)
    logging.debug("Waiting %.1f seconds before next request...", wait_time)
    time.sleep(wait_time)


def make_request(url, session=None, retries=MAX_RETRIES):
    """
    Fetch a URL with retry logic and random headers.
    Returns the Response object or None if all retries fail.
    """
    requester = session if session else requests

    for attempt in range(1, retries + 1):
        try:
            headers = get_random_headers()
            response = requester.get(url, headers=headers, timeout=REQUEST_TIMEOUT)

            # check for common blocking responses
            if response.status_code == 429:
                wait = 10 * attempt  # wait longer each time we get rate-limited
                logging.warning("Rate limited (429) on %s - waiting %ds", url, wait)
                time.sleep(wait)
                continue

            if response.status_code == 403:
                logging.warning("Forbidden (403) on %s - attempt %d/%d", url, attempt, retries)
                time.sleep(5 * attempt)
                continue

            response.raise_for_status()
            return response

        except requests.exceptions.Timeout:
            logging.warning("Timeout on %s - attempt %d/%d", url, attempt, retries)
            time.sleep(3)

        except requests.exceptions.ConnectionError:
            logging.warning("Connection error on %s - attempt %d/%d", url, attempt, retries)
            time.sleep(5)

        except requests.exceptions.RequestException as e:
            logging.error("Request failed for %s: %s", url, str(e))
            time.sleep(3)

    logging.error("All %d retries failed for: %s", retries, url)
    return None


def safe_text(element, default="N/A"):
    """Safely get text from a BeautifulSoup element without crashing."""
    if element is None:
        return default
    text = element.get_text(strip=True)
    return text if text else default


def safe_attr(element, attr, default="N/A"):
    """Safely get an attribute from a BeautifulSoup element."""
    if element is None:
        return default
    return element.get(attr, default)


def clean_text(text):
    """Remove extra whitespace and newlines from text."""
    if not text or text == "N/A":
        return text
    cleaned = re.sub(r"\s+", " ", text).strip()
    return cleaned


def parse_review_count(text):
    """
    Convert review count text like '1.1L Reviews' or '48.8k Reviews' to a number.
    Returns the string representation or 'N/A' if parsing fails.
    """
    if not text or text == "N/A":
        return "N/A"

    text = text.strip().lower()

    match = re.search(r"([\d.]+)\s*(k|l)?", text)
    if not match:
        return text

    number = float(match.group(1))
    suffix = match.group(2)

    if suffix == "k":
        number = int(number * 1000)
    elif suffix == "l":
        number = int(number * 100000)
    else:
        number = int(number)

    return str(number)


def extract_rating_value(text):
    """Pull out a numeric rating like '3.9' from text. Returns 'N/A' if not found."""
    if not text or text == "N/A":
        return "N/A"
    match = re.search(r"(\d+\.?\d*)", str(text))
    return match.group(1) if match else "N/A"


def get_timestamp():
    """Return current timestamp string for the scraped_at column."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
