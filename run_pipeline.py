"""
CAMX 2026 GTM Pipeline — Master Runner
========================================
Runs the full pipeline end-to-end:
  Step 1: Scrape exhibitors from CAMX 2026 (MapYourShow)
  Step 2: Enrich each company (LinkedIn URL, homepage signals)
  Step 3: Generate personalized first lines via Claude API
  Step 4: Export to CSV + optionally upload to Google Sheets

Usage:
  # Minimal (no API keys needed — uses fallback logic):
  python run_pipeline.py

  # Full (all enrichment + AI generation):
  ANTHROPIC_KEY=sk-... SERPAPI_KEY=... python run_pipeline.py

  # With Google Sheets upload:
  ANTHROPIC_KEY=sk-... GOOGLE_CREDS_JSON=creds.json SHEET_ID=xxx python run_pipeline.py
"""

import os, json, time
from pathlib import Path


def step1_scrape() -> list[dict]:
    print("\n" + "═"*60)
    print("STEP 1: Scraping CAMX 2026 Exhibitors")
    print("═"*60)
    from scraper import scrape_exhibitors, save_outputs, OUTPUT_FILE
    exhibitors = scrape_exhibitors()
    save_outputs(exhibitors)
    return exhibitors


def step2_enrich(exhibitors: list[dict]) -> list[dict]:
    print("\n" + "═"*60)
    print("STEP 2: Enriching Companies")
    print("═"*60)
    from enrichment import enrich
    enriched = enrich(exhibitors)
    Path("camx2026_exhibitors_enriched.json").write_text(
        json.dumps(enriched, indent=2)
    )
    print(f"Enriched {len(enriched)} companies")
    return enriched


def step3_personalize(enriched: list[dict]) -> list[dict]:
    print("\n" + "═"*60)
    print("STEP 3: Generating Personalized First Lines")
    print("═"*60)
    from personalization import run_personalization, save_csv
    final = run_personalization(enriched)
    Path("camx2026_final.json").write_text(json.dumps(final, indent=2))
    save_csv(final)
    return final


def step4_sheets(final: list[dict]) -> None:
    creds  = os.getenv("GOOGLE_CREDS_JSON", "")
    sheet  = os.getenv("SHEET_ID", "")
    print("\n" + "═"*60)
    print("STEP 4: Google Sheets Upload")
    print("═"*60)
    if creds and sheet:
        from sheets_upload import upload_to_sheets
        url = upload_to_sheets(final, sheet, creds)
        print(f"✓ Sheet URL: {url}")
    else:
        print("ℹ  Skipping Sheets upload (GOOGLE_CREDS_JSON and SHEET_ID not set)")
        print("   Import camx2026_final.csv manually via File → Import in Google Sheets")


def print_summary(final: list[dict]) -> None:
    print("\n" + "═"*60)
    print("PIPELINE COMPLETE — SAMPLE OUTPUT")
    print("═"*60)
    for company in final[:5]:
        print(f"\n🏢  {company['company_name']}")
        print(f"    Website:   {company.get('website','')}")
        print(f"    LinkedIn:  {company.get('linkedin_url','')}")
        print(f"    Signal:    {company.get('signal','')[:100]}")
        print(f"    First Line: {company.get('personalized_first_line','')}")
    print("\n" + "─"*60)
    print(f"Total companies: {len(final)}")
    print(f"Output files:")
    print(f"  camx2026_exhibitors_raw.json      ← raw scraped data")
    print(f"  camx2026_exhibitors_enriched.json ← + LinkedIn, meta, signals")
    print(f"  camx2026_final.json               ← + personalized first lines")
    print(f"  camx2026_final.csv                ← ready for Google Sheets")


if __name__ == "__main__":
    start = time.time()

    exhibitors = step1_scrape()
    enriched   = step2_enrich(exhibitors)
    final      = step3_personalize(enriched)
    step4_sheets(final)
    print_summary(final)

    elapsed = time.time() - start
    print(f"\n⏱  Total time: {elapsed:.1f}s")
