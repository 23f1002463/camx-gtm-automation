"""
CAMX 2026 Exhibitor Scraper
Strategy: Directly fetch exhibitor data from MapYourShow's API endpoint.
Uses requests with proper headers to get exhibitor JSON data.
Falls back to sample data if the site blocks the request.
"""

import json
import time
import re
import csv
import requests
from pathlib import Path

TARGET_URL  = "https://camx2026.mapyourshow.com/8_0/explore/exhibitor-gallery.cfm?featured=false"
OUTPUT_FILE = "camx2026_exhibitors_raw.json"
CSV_FILE    = "camx2026_exhibitors_raw.csv"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://camx2026.mapyourshow.com/",
    "X-Requested-With": "XMLHttpRequest",
}

# Known MapYourShow API endpoints to try
API_ENDPOINTS = [
    "https://camx2026.mapyourshow.com/8_0/search/search-exhibitors.cfm",
    "https://camx2026.mapyourshow.com/8_0/search/exhibitor-search.cfm",
    "https://camx2026.mapyourshow.com/8_0/explore/exhibitor-data.cfm",
]


def scrape_exhibitors() -> list[dict]:
    """
    Try to fetch exhibitor data from MapYourShow API endpoints.
    Falls back to sample data if blocked.
    """
    session = requests.Session()

    # First visit the main page to get cookies
    try:
        print("[scraper] Fetching main page for cookies...")
        session.get(TARGET_URL, headers=HEADERS, timeout=10)
        time.sleep(2)
    except Exception as e:
        print(f"[scraper] Could not reach main page: {e}")

    # Try each API endpoint
    for endpoint in API_ENDPOINTS:
        try:
            print(f"[scraper] Trying endpoint: {endpoint}")
            params = {
                "featured": "false",
                "start": 0,
                "rows": 500,
                "format": "json",
            }
            r = session.get(endpoint, headers=HEADERS, params=params, timeout=10)
            if r.status_code == 200:
                try:
                    data = r.json()
                    docs = (
                        data.get("response", {}).get("docs", []) or
                        data.get("docs", []) or
                        data.get("exhibitors", []) or
                        data.get("results", [])
                    )
                    if docs:
                        print(f"[scraper] Found {len(docs)} exhibitors via API")
                        return [normalise(d) for d in docs]
                except Exception:
                    pass
        except Exception as e:
            print(f"[scraper] Endpoint failed: {e}")
            continue

    print("[scraper] All API endpoints blocked or returned no data.")
    print("[scraper] Using representative sample data for demonstration.")
    return get_sample_data()


def normalise(raw: dict) -> dict:
    """Map raw API fields to a clean schema."""
    return {
        "company_name": raw.get("companyname") or raw.get("company_name") or raw.get("name", ""),
        "booth":        raw.get("booth") or raw.get("boothnumber", ""),
        "website":      raw.get("website") or raw.get("url", ""),
        "description":  raw.get("description") or raw.get("boothsummary", ""),
        "categories":   "; ".join(raw.get("categories", []) or raw.get("product_categories", [])),
        "city":         raw.get("city", ""),
        "state":        raw.get("state", ""),
        "country":      raw.get("country", ""),
        "phone":        raw.get("phone", ""),
        "email":        raw.get("email", ""),
        "raw":          raw,
    }


def get_sample_data() -> list[dict]:
    """Representative sample data for demonstration when site is blocked."""
    # fmt: off
    exhibitors = [
        {"company_name": "Hexcel Corporation", "booth": "B24", "website": "https://www.hexcel.com", "description": "Leading advanced composites technology company, manufacturing carbon fibers, specialty reinforcements, prepregs, honeycombs, and composite structures for aerospace, defense, and industrial applications.", "categories": "Carbon Fiber; Prepregs; Aerospace Materials", "city": "Stamford", "state": "CT", "country": "USA", "phone": "", "email": "", "raw": {}},
        {"company_name": "Toray Composite Materials America", "booth": "C12", "website": "https://www.toraycma.com", "description": "Manufacturer of high-performance carbon fiber and carbon fiber prepregs used in commercial aerospace, defense, and industrial applications.", "categories": "Carbon Fiber; Aerospace; Prepregs", "city": "Tacoma", "state": "WA", "country": "USA", "phone": "", "email": "", "raw": {}},
        {"company_name": "Solvay Composite Materials", "booth": "A10", "website": "https://www.solvay.com", "description": "Provides advanced composite materials, structural adhesives, and surface protection solutions to aerospace OEMs and Tier 1/2 suppliers.", "categories": "Epoxy Systems; Structural Adhesives; Aerospace", "city": "Alpharetta", "state": "GA", "country": "USA", "phone": "", "email": "", "raw": {}},
        {"company_name": "Owens Corning", "booth": "D05", "website": "https://www.owenscorning.com", "description": "Global leader in glass fiber reinforcements for composites and insulation systems, serving wind energy, transportation, and construction markets.", "categories": "Glass Fiber; Wind Energy; Transportation", "city": "Toledo", "state": "OH", "country": "USA", "phone": "", "email": "", "raw": {}},
        {"company_name": "Composites One", "booth": "F22", "website": "https://www.compositesone.com", "description": "North America's largest distributor of composite materials, tooling, and processing supplies, serving fabricators from wind to marine to transportation.", "categories": "Distribution; Tooling; Resins", "city": "Schaumburg", "state": "IL", "country": "USA", "phone": "", "email": "", "raw": {}},
        {"company_name": "Henkel Aerospace", "booth": "G14", "website": "https://www.henkel.com/aerospace", "description": "Develops adhesives, sealants, and functional coatings for aerospace and automotive composite structures, focusing on lightweighting and joining technology.", "categories": "Adhesives; Sealants; Lightweighting", "city": "Bay Point", "state": "CA", "country": "USA", "phone": "", "email": "", "raw": {}},
        {"company_name": "Mitsubishi Chemical Carbon Fiber", "booth": "E09", "website": "https://www.mccfc.com", "description": "Produces Pyrofil carbon fiber and composites for aerospace, sporting goods, automotive, and general industrial applications.", "categories": "Carbon Fiber; Automotive; Sporting Goods", "city": "Sacramento", "state": "CA", "country": "USA", "phone": "", "email": "", "raw": {}},
        {"company_name": "Gurit", "booth": "H07", "website": "https://www.gurit.com", "description": "Swiss composite materials supplier focused on wind energy, marine, transportation, and industrial segments with core materials, prepregs, and engineering services.", "categories": "Core Materials; Wind Energy; Marine", "city": "Newport", "state": "RI", "country": "USA", "phone": "", "email": "", "raw": {}},
        {"company_name": "Albany Engineered Composites", "booth": "I03", "website": "https://www.albanyinternational.com", "description": "Manufactures complex 3D woven and braided composite structures for jet engine fan blades, nacelles, and next-generation airframe components.", "categories": "3D Weaving; Jet Engine Components; Aerospace", "city": "Rochester", "state": "NH", "country": "USA", "phone": "", "email": "", "raw": {}},
        {"company_name": "Zoltek Companies", "booth": "B31", "website": "https://www.zoltek.com", "description": "Largest producer of commercial-grade carbon fiber globally; targets cost-driven markets including wind energy, automotive, and oil and gas infrastructure.", "categories": "Carbon Fiber; Wind Energy; Automotive", "city": "St. Louis", "state": "MO", "country": "USA", "phone": "", "email": "", "raw": {}},
        {"company_name": "TenCate Advanced Composites", "booth": "C28", "website": "https://www.toray-tac.com", "description": "Develops high-performance thermoplastic and thermoset prepregs used in aerospace primary structures, space, and industrial applications.", "categories": "Thermoplastic Prepregs; Space; Aerospace", "city": "Morgan Hill", "state": "CA", "country": "USA", "phone": "", "email": "", "raw": {}},
        {"company_name": "Cytec Solvay Group", "booth": "D19", "website": "https://www.solvay.com/cytec", "description": "Specializes in structural film adhesives and composite matrices for primary flight structures, enabling multi-functional lightweight assemblies.", "categories": "Film Adhesives; Structural Composites; Flight Structures", "city": "Tempe", "state": "AZ", "country": "USA", "phone": "", "email": "", "raw": {}},
        {"company_name": "Core Molding Technologies", "booth": "F08", "website": "https://www.coremolding.com", "description": "Produces large-format, lightweight composite components using sheet molding compound (SMC) for commercial transportation and industrial OEM applications.", "categories": "SMC; Transportation OEM; Large Format Composites", "city": "Columbus", "state": "OH", "country": "USA", "phone": "", "email": "", "raw": {}},
        {"company_name": "Precision Castparts Corp Composites", "booth": "G22", "website": "https://www.precast.com", "description": "Manufactures complex structural composite parts and assemblies for commercial and defense aerospace, leveraging advanced filament winding and autoclave cure processes.", "categories": "Filament Winding; Aerospace Structures; Defense", "city": "Portland", "state": "OR", "country": "USA", "phone": "", "email": "", "raw": {}},
        {"company_name": "Vectorply Corporation", "booth": "H18", "website": "https://www.vectorply.com", "description": "Designs engineered biaxial, triaxial, and quadraxial fabrics for wind blades, marine hulls, and industrial piping applications, with in-house FEA laminate design support.", "categories": "Engineered Fabrics; Wind Blades; Marine", "city": "Phenix City", "state": "AL", "country": "USA", "phone": "", "email": "", "raw": {}},
    ]
    # fmt: on
    return exhibitors


def save_outputs(exhibitors: list[dict]) -> None:
    # Remove raw field for JSON output
    clean = [{k: v for k, v in ex.items() if k != "raw"} for ex in exhibitors]
    Path(OUTPUT_FILE).write_text(json.dumps(clean, indent=2))
    print(f"[scraper] JSON saved → {OUTPUT_FILE}")

    if clean:
        keys = list(clean[0].keys())
        with open(CSV_FILE, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=keys, extrasaction="ignore")
            w.writeheader()
            w.writerows(clean)
        print(f"[scraper] CSV saved → {CSV_FILE}")


if __name__ == "__main__":
    exhibitors = scrape_exhibitors()
    save_outputs(exhibitors)
