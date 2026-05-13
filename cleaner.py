import logging
import os
import re
import pandas as pd

from config import CSV_COLUMNS, DATA_DIR, OUTPUT_CSV, RAW_CSV


def clean_dataframe(df):
    """
    Clean up the scraped data before saving.
    Handles missing values, formatting, and consistency.
    """
    logging.info("Cleaning data... (%d rows)", len(df))

    df = df.copy()

    for col in df.columns:
        if df[col].dtype == "object":
            df[col] = df[col].apply(lambda x: x.strip() if isinstance(x, str) else x)

    df.replace({"": "N/A", "None": "N/A", "none": "N/A", "null": "N/A", "nan": "N/A"}, inplace=True)

    df["company_name"] = df["company_name"].apply(clean_company_name)

    rating_cols = [col for col in df.columns if col.startswith("rating_")]
    for col in rating_cols:
        df[col] = df[col].apply(normalize_rating)

    df["overall_rating"] = df["overall_rating"].apply(normalize_rating)

    if "description" in df.columns:
        df["description"] = df["description"].apply(
            lambda x: x[:500] + "..." if isinstance(x, str) and len(x) > 500 else x
        )

    before = len(df)
    df.drop_duplicates(subset=["company_name", "profile_url"], keep="first", inplace=True)
    after = len(df)
    if before != after:
        logging.info("Removed %d duplicate rows", before - after)

    existing_cols = [col for col in CSV_COLUMNS if col in df.columns]
    extra_cols = [col for col in df.columns if col not in CSV_COLUMNS]
    df = df[existing_cols + extra_cols]

    logging.info("Cleaning done. Final rows: %d", len(df))
    return df


def clean_company_name(name):
    """Clean up company name formatting."""
    if not isinstance(name, str) or name == "N/A":
        return name

    name = re.sub(r"\s+", " ", name).strip()

    name = name.strip("•·-|")

    return name


def normalize_rating(value):
    """Make sure rating values are consistent - either a number like '3.9' or 'N/A'."""
    if not isinstance(value, str):
        value = str(value)

    value = value.strip()

    if value in ("N/A", "", "None", "nan"):
        return "N/A"

    match = re.search(r"(\d+\.?\d*)", value)
    if match:
        num = float(match.group(1))
        if 0 <= num <= 5:
            return f"{num:.1f}"
        return "N/A"

    return "N/A"


def save_to_csv(results_list):
    """Save the results to CSV files (raw + cleaned versions)."""
    os.makedirs(DATA_DIR, exist_ok=True)

    if not results_list:
        logging.error("No data to save!")
        return None

    df = pd.DataFrame(results_list)

    df.to_csv(RAW_CSV, index=False, encoding="utf-8-sig")
    logging.info("Raw data saved to: %s", RAW_CSV)

    df_clean = clean_dataframe(df)
    df_clean.to_csv(OUTPUT_CSV, index=False, encoding="utf-8-sig")
    logging.info("Cleaned data saved to: %s", OUTPUT_CSV)

    print_summary(df_clean)

    return df_clean


def print_summary(df):
    """Print a nice summary of what we scraped."""
    logging.info("=" * 50)
    logging.info("SCRAPING SUMMARY")
    logging.info("=" * 50)
    logging.info("Total companies scraped: %d", len(df))

    has_rating = df["overall_rating"].apply(lambda x: x != "N/A").sum()
    logging.info("Companies with ratings:  %d (%.0f%%)", has_rating, (has_rating / len(df)) * 100 if len(df) > 0 else 0)

    has_desc = df["description"].apply(lambda x: x != "N/A").sum()
    logging.info("Companies with descriptions: %d", has_desc)

    has_industry = df["industry"].apply(lambda x: x != "N/A").sum()
    logging.info("Companies with industry info: %d", has_industry)

    logging.info("=" * 50)
