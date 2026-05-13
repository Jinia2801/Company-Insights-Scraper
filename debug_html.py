# Debug: extract __NEXT_DATA__ JSON from a Next.js-rendered company page
import requests
import json
from bs4 import BeautifulSoup

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
}

url = "https://www.ambitionbox.com/overview/infosys-overview"
resp = requests.get(url, headers=headers, timeout=15)
soup = BeautifulSoup(resp.text, "html.parser")

# find __NEXT_DATA__
next_tag = soup.find("script", id="__NEXT_DATA__")
if next_tag and next_tag.string:
    data = json.loads(next_tag.string)
    
    # explore the structure
    page_props = data.get("props", {}).get("pageProps", {})
    print("Top-level keys in pageProps:", list(page_props.keys()))
    
    # look for company data
    for key in page_props:
        val = page_props[key]
        if isinstance(val, dict):
            print(f"\n  {key} (dict) keys: {list(val.keys())[:15]}")
            # look for rating-related keys
            for subkey in val:
                if any(kw in subkey.lower() for kw in ["rating", "review", "description", "industry", "about"]):
                    subval = val[subkey]
                    if isinstance(subval, (str, int, float)):
                        print(f"    {subkey}: {str(subval)[:100]}")
                    elif isinstance(subval, dict):
                        print(f"    {subkey} (dict): {list(subval.keys())}")
                    elif isinstance(subval, list) and len(subval) > 0:
                        print(f"    {subkey} (list of {len(subval)}): first={subval[0]}")
        elif isinstance(val, str) and len(val) < 200:
            print(f"\n  {key}: {val}")
else:
    print("No __NEXT_DATA__ found")
    # check for other script patterns
    for script in soup.find_all("script"):
        if script.string and len(script.string) > 500:
            text = script.string[:200]
            if "props" in text or "pageProps" in text or "rating" in text.lower():
                print(f"Interesting script: {text}")
