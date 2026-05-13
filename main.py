import logging
import sys
import time
import requests

from config import TOTAL_PAGES, OUTPUT_CSV
from helpers import setup_logging, get_random_headers
from scraper import scrape_all_listings, scrape_all_details
from cleaner import save_to_csv


def create_session():
    """
    Create a requests Session for connection reuse.
    Sessions keep cookies and connections alive, which makes
    the scraper faster and look more like a real browser.
    """
    session = requests.Session()
    session.headers.update(get_random_headers())
    return session


def main():
    """Main function - runs the full scraping pipeline."""

    setup_logging()
    logging.info("=" * 60)
    logging.info("AmbitionBox Company Scraper - Starting")
    logging.info("=" * 60)
    logging.info("Pages to scrape: %d", TOTAL_PAGES)

    start_time = time.time()

    session = create_session()

    logging.info("-" * 40)
    logging.info("PHASE 1: Scraping listing pages...")
    logging.info("-" * 40)

    companies = scrape_all_listings(session)

    if not companies:
        logging.error("No companies found on listing pages. Exiting.")
        sys.exit(1)

    logging.info("Found %d companies to scrape details for", len(companies))

    logging.info("-" * 40)
    logging.info("PHASE 2: Scraping company detail pages...")
    logging.info("-" * 40)

    results = scrape_all_details(companies, session)

    logging.info("-" * 40)
    logging.info("PHASE 3: Cleaning data and saving CSV...")
    logging.info("-" * 40)

    df = save_to_csv(results)

    elapsed = time.time() - start_time
    minutes = int(elapsed // 60)
    seconds = int(elapsed % 60)

    logging.info("")
    logging.info("All done! Took %dm %ds", minutes, seconds)
    logging.info("Output saved to: %s", OUTPUT_CSV)
    logging.info("Total companies in final CSV: %d", len(df) if df is not None else 0)

    session.close()


if __name__ == "__main__":
    main()
