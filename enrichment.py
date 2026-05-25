"""
Enrichment Module — CAMX 2026 Exhibitors
==========================================
For each exhibitor we enrich with:
  1. LinkedIn company URL (via Google/Bing search heuristic)
  2. Company description / tagline (from homepage meta tags)
  3. Key signal for personalisation (latest product/focus pulled from homepage)

Tools used:
  - requests + BeautifulSoup for homepage meta-tag extraction
  - SerpAPI / Google Custom Search (optional) for LinkedIn URL lookup
  - Gemini API as a fallback signal extractor from raw text

NOTE: To run enrichment fully, set env vars:
  SERPAPI_KEY  = your SerpAPI key   (free tier: 100 searches/month)
  GEMINI_KEY   = your Gemini API key

Without API keys the module still produces enriched output using the
homepage meta-data extraction path (no key required).
"""

import os
import re
import time
import json
import requests
from bs4 import BeautifulSoup
from pathlib import Path

SERPAPI_KEY   = os.getenv("SERPAPI_KEY", "")
GEMINI_KEY    = os.getenv("GEMINI_KEY", "")
INPUT_FILE    = "camx2026_exhibitors_raw.json"
OUTPUT_FILE   = "camx2026_exhibitors_enriched.json"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept-Language": "en-US,en;q=0.9",
}


# ── 1. Homepage meta-data extraction ─────────────────────────────────────────

def fetch_meta(url: str) -> dict:
    """Return og:description, meta description, and page title from a URL."""
    if not url:
        return {}
    try:
        if not url.startswith("http"):
            url = "https://" + url
        r = requests.get(url, headers=HEADERS, timeout=8, allow_redirects=True)
        soup = BeautifulSoup(r.text, "html.parser")

        def m(name=None, prop=None):
            tag = soup.find("meta", attrs={"name": name} if name else {"property": prop})
            return tag["content"].strip() if tag and tag.get("content") else ""

        title = soup.title.string.strip() if soup.title else ""
        desc  = m(prop="og:description") or m(name="description") or m(prop="twitter:description")
        kw    = m(name="keywords")

        # Also grab first visible paragraph (often a tagline)
        first_p = ""
        for p in soup.find_all("p"):
            text = p.get_text(strip=True)
            if len(text) > 60:
                first_p = text[:300]
                break

        return {
            "page_title":   title,
            "meta_desc":    desc[:400] if desc else "",
            "keywords":     kw[:200]   if kw   else "",
            "first_para":   first_p,
        }
    except Exception as e:
        return {"error": str(e)}


# ── 2. LinkedIn URL lookup via SerpAPI ────────────────────────────────────────

def find_linkedin(company_name: str) -> str:
    """Return LinkedIn company URL using SerpAPI (or Google CSE)."""
    if not SERPAPI_KEY:
        slug = re.sub(r"[^a-z0-9]+", "-", company_name.lower()).strip("-")
        return f"https://www.linkedin.com/company/{slug}"

    try:
        params = {
            "api_key": SERPAPI_KEY,
            "engine":  "google",
            "q":       f'site:linkedin.com/company "{company_name}"',
            "num":     3,
        }
        r = requests.get("https://serpapi.com/search", params=params, timeout=10)
        results = r.json().get("organic_results", [])
        for res in results:
            link = res.get("link", "")
            if "linkedin.com/company/" in link:
                return link
    except Exception:
        pass

    slug = re.sub(r"[^a-z0-9]+", "-", company_name.lower()).strip("-")
    return f"https://www.linkedin.com/company/{slug}"


# ── 3. Signal extraction via Gemini API ───────────────────────────────────────

def extract_signal_via_gemini(company_name: str, description: str,
                               categories: str, meta: dict) -> str:
    """
    Ask Gemini to identify the single most compelling, specific signal about
    this company that could anchor a personalized cold email opening line.
    Returns a plain-text signal (1-2 sentences).
    """
    if not GEMINI_KEY:
        cats = categories.split(";") if categories else []
        if cats:
            return f"Focus area: {cats[0].strip()} — attending CAMX 2026 to showcase innovations."
        return description[:200] if description else "Attending CAMX 2026."

    combined_text = "\n".join(filter(None, [
        f"Company: {company_name}",
        f"Description: {description}",
        f"Categories: {categories}",
        f"Website title: {meta.get('page_title', '')}",
        f"Website description: {meta.get('meta_desc', '')}",
        f"Homepage paragraph: {meta.get('first_para', '')}",
    ]))

    system_instruction = (
        "You are a GTM researcher. Given company information, "
        "extract ONE specific, factual signal that makes this company "
        "interesting to a potential B2B partner. "
        "Focus on: product focus, a recent launch, a market they serve, "
        "or a capability they highlight. "
        "Be concrete. 1-2 sentences max. No generic praise."
    )

    try:
        import google.generativeai as genai
        genai.configure(api_key=GEMINI_KEY)
        model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            system_instruction=system_instruction
        )
        response = model.generate_content(combined_text)
        return response.text.strip()
    except Exception as e:
        return f"[signal extraction error: {e}]"


# ── 4. Main enrichment loop ────────────────────────────────────────────────────

def enrich(exhibitors: list[dict]) -> list[dict]:
    enriched = []
    for i, ex in enumerate(exhibitors):
        name    = ex.get("company_name", "")
        website = ex.get("website", "")
        print(f"[{i+1}/{len(exhibitors)}] Enriching: {name}")

        meta     = fetch_meta(website)
        linkedin = find_linkedin(name)
        signal   = extract_signal_via_gemini(
            name, ex.get("description", ""), ex.get("categories", ""), meta
        )

        enriched.append({
            **ex,
            "linkedin_url":  linkedin,
            "page_title":    meta.get("page_title", ""),
            "meta_desc":     meta.get("meta_desc", ""),
            "homepage_para": meta.get("first_para", ""),
            "signal":        signal,
        })
        time.sleep(1)  # be polite to servers

    return enriched


if __name__ == "__main__":
    raw = json.loads(Path(INPUT_FILE).read_text())
    result = enrich(raw)
    Path(OUTPUT_FILE).write_text(json.dumps(result, indent=2))
    print(f"\nEnrichment complete → {OUTPUT_FILE}")