import json
import logging
import re
import requests
from bs4 import BeautifulSoup

from config import BASE_URL, LISTING_URL, TOTAL_PAGES
from helpers import (
    make_request,
    polite_delay,
    safe_text,
    safe_attr,
    clean_text,
    parse_review_count,
    extract_rating_value,
    get_timestamp,
)
def build_listing_url(page_num):
    """Build the URL for a specific listing page number."""
    if page_num == 1:
        return LISTING_URL
    return f"{LISTING_URL}?page={page_num}"


def scrape_listing_page(page_num, session):
    """
    Scrape a single listing page and return a list of companies.
    Each company is a dict with 'name' and 'profile_url'.
    """
    url = build_listing_url(page_num)
    logging.info("Scraping listing page %d: %s", page_num, url)

    response = make_request(url, session=session)
    if response is None:
        logging.error("Failed to fetch listing page %d", page_num)
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    companies = []

    company_cards = soup.find_all("div", class_="companyCardWrapper")

    if not company_cards:
        logging.warning("No company cards found on page %d", page_num)
        return []

    for card in company_cards:
        company = extract_company_from_card(card)
        if company:
            companies.append(company)

    logging.info("Found %d companies on page %d", len(companies), page_num)
    return companies


def extract_company_from_card(card):
    """Pull company name and profile URL from a single company card element."""
    h2_tag = card.find("h2")
    name = safe_text(h2_tag) if h2_tag else None

    if not name or name == "N/A":
        meta_name = card.find("meta", attrs={"itemprop": "name"})
        name = meta_name.get("content", "").strip() if meta_name else None

    if not name:
        return None
    meta_url = card.find("meta", attrs={"itemprop": "url"})
    if meta_url:
        profile_url = meta_url.get("content", "")
    else:
        reviews_link = card.find("a", href=re.compile(r"/reviews/(.+)-reviews"))
        if reviews_link:
            match = re.search(r"/reviews/(.+)-reviews", reviews_link.get("href", ""))
            if match:
                slug = match.group(1)
                profile_url = f"{BASE_URL}/overview/{slug}-overview"
            else:
                return None
        else:
            return None

    if profile_url.startswith("/"):
        profile_url = BASE_URL + profile_url

    return {"name": name, "profile_url": profile_url}


def scrape_all_listings(session):
    """Scrape all listing pages and return combined list of companies."""
    all_companies = []

    for page_num in range(1, TOTAL_PAGES + 1):
        companies = scrape_listing_page(page_num, session)
        all_companies.extend(companies)
        if page_num < TOTAL_PAGES:
            polite_delay()

    seen_urls = set()
    unique_companies = []
    for company in all_companies:
        if company["profile_url"] not in seen_urls:
            seen_urls.add(company["profile_url"])
            unique_companies.append(company)

    logging.info("Total unique companies found: %d", len(unique_companies))
    return unique_companies

def scrape_company_detail(company, session):
    """
    Scrape a single company's detail/overview page.
    Returns a dict with all the extracted fields.
    """
    url = company["profile_url"]
    name = company["name"]
    logging.info("Scraping details for: %s", name)

    response = make_request(url, session=session)
    if response is None:
        logging.error("Failed to fetch detail page for %s", name)
        return build_empty_result(name, url)

    soup = BeautifulSoup(response.text, "html.parser")
    page_text = response.text

    # try to get structured data from __NUXT__ or JSON-LD
    json_data = try_extract_from_json(soup, page_text)

    # extract each field with fallbacks
    result = {
        "company_name": name,
        "profile_url": url,
        "overall_rating": extract_overall_rating(soup, json_data),
        "total_reviews": extract_total_reviews(soup, json_data),
        "industry": extract_industry(soup, json_data),
        "description": extract_description(soup, json_data),
        "scraped_at": get_timestamp(),
    }

    # extract key sub-ratings
    key_ratings = extract_key_ratings(soup, json_data)
    result.update(key_ratings)

    logging.info("  -> Rating: %s | Reviews: %s | Industry: %s",
                 result["overall_rating"], result["total_reviews"], result["industry"])
    return result


def try_extract_from_json(soup, html_text):
    """
    Try to extract structured data from script tags.
    AmbitionBox uses Nuxt.js, so data may be in window.__NUXT__.
    Also check JSON-LD (schema.org) structured data.
    """
    data = {}

    # check for JSON-LD structured data
    json_ld_tags = soup.find_all("script", type="application/ld+json")
    for tag in json_ld_tags:
        try:
            parsed = json.loads(tag.string)
            if isinstance(parsed, dict):
                # check if this has aggregateRating (company page schema)
                if "aggregateRating" in parsed:
                    data["json_ld"] = parsed
                elif "@type" in parsed:
                    data["json_ld"] = parsed
            elif isinstance(parsed, list):
                for item in parsed:
                    if isinstance(item, dict) and "aggregateRating" in item:
                        data["json_ld"] = item
                        break
                if "json_ld" not in data and parsed:
                    data["json_ld"] = parsed[0]
        except (json.JSONDecodeError, TypeError):
            continue

    return data


def extract_overall_rating(soup, json_data):
    """Extract overall company rating."""

    # try JSON-LD first
    if "json_ld" in json_data:
        ld = json_data["json_ld"]

        if isinstance(ld, dict) and "aggregateRating" in ld:
            val = ld["aggregateRating"].get("ratingValue")

            if val:
                return str(val)

    # search page text
    page_text = soup.get_text(" ", strip=True)

    # pattern:
    # 3.7 based on 73.5k Reviews
    match = re.search(
        r"(\d\.\d)\s*based on",
        page_text,
        re.I
    )

    if match:
        return match.group(1)

    # fallback:
    # 3.4 /5
    match = re.search(
        r"(\d\.\d)\s*/\s*5",
        page_text
    )

    if match:
        return match.group(1)

    return "N/A"


def extract_total_reviews(soup, json_data):
    """Get the total number of reviews."""

    # try JSON-LD
    if "json_ld" in json_data:
        ld = json_data["json_ld"]
        if isinstance(ld, dict) and "aggregateRating" in ld:
            count = ld["aggregateRating"].get("reviewCount") or ld["aggregateRating"].get("ratingCount")
            if count:
                return str(count)

    # find the reviews link text (e.g., "1.1L Reviews" or "48.8k Reviews")
    reviews_links = soup.find_all("a", href=re.compile(r"/reviews/"))
    for link in reviews_links:
        text = safe_text(link)
        if re.search(r"[\d.]+[kKlL]?\s*Review", text, re.I):
            return parse_review_count(text)

    # look for text matching "X Reviews" pattern anywhere
    review_text = soup.find(string=re.compile(r"[\d.,]+[kKlL]?\s*Reviews?", re.I))
    if review_text:
        return parse_review_count(review_text.strip())

    return "N/A"


def extract_industry(soup, json_data):
    """Get the industry/sector of the company."""

    # look for industry links that end with "-companies-in-india"
    industry_links = soup.find_all("a", href=re.compile(r"[-\w]+-companies-in-india$"))
    if industry_links:
        industries = []
        seen = set()
        for link in industry_links:
            text = safe_text(link)
            if text and text != "N/A" and len(text) < 80 and text.lower() not in seen:
                seen.add(text.lower())
                industries.append(text)
        if industries:
            return " | ".join(industries[:5])  # cap at 5 industries

    return "N/A"


def extract_description(soup, json_data):
    """Extract company description/summary."""

    # Find company summary/about section
    headings = soup.find_all(
        string=re.compile(r"Company Summary|About", re.I)
    )

    for heading in headings:

        parent = heading.find_parent()

        if not parent:
            continue

        # Look through next elements
        next_elements = parent.find_all_next()

        for el in next_elements:

            text = safe_text(el)

            if not text or text == "N/A":
                continue

            # Skip short slogan/banner text
            if len(text) < 80:
                continue

            # Skip overly uppercase marketing lines
            if text.count(" ") < 8:
                continue

            # Prefer paragraph-like descriptions
            if "." in text or "," in text:

                cleaned = clean_text(text)

                # avoid duplicate SEO phrases
                if "Get an inside look of" in cleaned:
                    continue

                return cleaned[:500]

    return "N/A"


# --- Key ratings (salary, work-life balance, etc.) ---

RATING_CATEGORIES = {
    "job security": "rating_job_security",
    "work-life balance": "rating_work_life_balance",
    "work life balance": "rating_work_life_balance",
    "salary": "rating_salary",
    "salary & benefits": "rating_salary",
    "work satisfaction": "rating_work_satisfaction",
    "job satisfaction": "rating_work_satisfaction",
    "promotions": "rating_promotions",
    "promotions / appraisal": "rating_promotions",
    "appraisal": "rating_promotions",
    "skill development": "rating_skill_development",
    "company culture": "rating_company_culture",
    "culture": "rating_company_culture",
}


def extract_key_ratings(soup, json_data):
    """Extract individual category ratings like salary, job security, etc."""

    ratings = {
        "rating_job_security": "N/A",
        "rating_work_life_balance": "N/A",
        "rating_salary": "N/A",
        "rating_work_satisfaction": "N/A",
        "rating_promotions": "N/A",
        "rating_skill_development": "N/A",
        "rating_company_culture": "N/A",
        
    }

    # Strategy 1: look for the __NUXT__ data which sometimes has category ratings
    # embedded as part of the page data. The ratings show up in review links
    # on the overview page with pattern like /reviews/tcs-job-security-reviews-42

    # Strategy 2: look for rating bar items
    # the overview page has sections like "Highly Rated For: Job Security"
    # and "Critically Rated For: Promotions, Salary"
    # These don't have exact numbers but we can note them

    # Strategy 3: look for links to specific review categories
    # These links contain the category slug and sometimes a rating value
    category_patterns = {
        "job-security": "rating_job_security",
        "work-life-balance": "rating_work_life_balance",
        "salary": "rating_salary",
        "job-satisfaction": "rating_work_satisfaction",
        "appraisal": "rating_promotions",
        "skill-development": "rating_skill_development",
        "company-culture": "rating_company_culture",
        "management": "rating_management",
    }

    for pattern, field in category_patterns.items():
        link = soup.find("a", href=re.compile(rf"{pattern}-reviews"))
        if link:
            text = safe_text(link)
            val = extract_rating_value(text)
            if val != "N/A":
                ratings[field] = val

    # Strategy 4: extract from CSS class names like "bg-rating-3.5"
    # AmbitionBox uses Tailwind-like classes where the rating value is in the class
    rating_bars = soup.find_all(class_=re.compile(r"bg-rating-[\d.]+"))
    if rating_bars:
        # these are rating distribution bars (5-star, 4-star, etc.) - not category ratings
        # but they confirm the page has rating data
        pass

    # Strategy 5: look for text blocks with category name + number pattern
    page_text = soup.get_text(separator="\n")
    for category, field_name in RATING_CATEGORIES.items():
        if ratings[field_name] != "N/A":
            continue  # already found
        pattern = rf"{re.escape(category)}\s*[:\-]?\s*(\d+\.?\d*)"
        match = re.search(pattern, page_text, re.I)
        if match:
            num = float(match.group(1))
            if 0 < num <= 5:  # valid rating range
                ratings[field_name] = match.group(1)

    return ratings


def build_empty_result(name, url):
    """Return a result dict with all fields set to N/A (used when scraping fails)."""
    return {
        "company_name": name,
        "profile_url": url,
        "overall_rating": "N/A",
        "total_reviews": "N/A",
        "industry": "N/A",
        "description": "N/A",
        "rating_job_security": "N/A",
        "rating_work_life_balance": "N/A",
        "rating_salary": "N/A",
        "rating_work_satisfaction": "N/A",
        "rating_promotions": "N/A",
        "rating_skill_development": "N/A",
        "rating_company_culture": "N/A",
        "scraped_at": get_timestamp(),
    }


def scrape_all_details(companies, session):
    """Scrape detail pages for all companies in the list."""
    all_results = []
    total = len(companies)

    for i, company in enumerate(companies, 1):
        logging.info("--- [%d/%d] Processing: %s ---", i, total, company["name"])

        result = scrape_company_detail(company, session)
        all_results.append(result)

        # progress update every 10 companies
        if i % 10 == 0:
            logging.info("Progress: %d/%d companies scraped (%.0f%%)", i, total, (i / total) * 100)

        # delay between requests
        if i < total:
            polite_delay()

    return all_results
