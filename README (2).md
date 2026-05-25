#  CAMX 2026 GTM Automation Pipeline

> Automatically scrapes exhibitors from CAMX 2026, enriches company data, and generates personalized cold email first lines using AI — all exported to Google Sheets.

---

##  What This Does

This pipeline does in minutes what would take hours manually:

1. **Scrapes** all exhibiting companies from the CAMX 2026 trade show website
2. **Enriches** each company with LinkedIn URL, homepage description, and a key signal
3. **Generates** a personalized cold email opening line for each company using AI
4. **Exports** everything into a clean Google Sheet ready for outreach

---

##  System Architecture

```
CAMX 2026 Website (JS-rendered)
         ↓
    scraper.py          → captures hidden XHR calls via Selenium Wire
         ↓
  enrichment.py         → homepage meta-tags + LinkedIn URL construction
         ↓
personalization.py      → AI prompt generates personalized first lines
         ↓
 sheets_upload.py       → uploads final dataset to Google Sheets
```

---

##  Files

| File | What it does |
|------|-------------|
| `scraper.py` | Controls real Chrome browser, intercepts hidden API calls to get exhibitor data |
| `enrichment.py` | Visits each company website, extracts description, finds LinkedIn URL |
| `personalization.py` | Sends company data to AI with a structured prompt, gets personalized first lines |
| `sheets_upload.py` | Uploads final CSV to Google Sheets using service account |
| `run_pipeline.py` | Master runner — runs all 4 steps in one command |
| `camx2026_final.csv` | Final output — 15 companies with all enriched data + first lines |

---

##  The Personalization Prompt

The core of this project is a carefully designed prompt that generates first lines which feel human and specific — not generic.

**Three rules every first line must follow:**
- **ANCHOR** on one real signal (product, market, capability)
- **BRIDGE** to a business angle (cost, speed, scale, quality)
- **VOICE** that sounds like a curious peer, not a salesperson

**Example output:**
> *"Noticed you're bringing both carbon fiber AND prepregs to CAMX — curious how you're positioning integrated supply to aerospace Tier 1s who are trying to reduce vendor consolidation risk."*

See the `Prompt Design` tab in the Google Sheet for the full prompt.

---

##  Tech Stack

- **Python** — core language
- **Selenium Wire** — intercepts browser network traffic to scrape JS-rendered pages
- **requests + BeautifulSoup** — fetches and parses company homepages
- **Claude / Gemini API** — AI generation of personalized first lines
- **gspread** — Google Sheets API integration

---

## ⚙️ How to Run

```bash
# 1. Clone the repo
git clone https://github.com/YOURUSERNAME/camx-gtm-automation
cd camx-gtm-automation

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate        # Mac
venv\Scripts\activate           # Windows

# 3. Install dependencies
pip install requests beautifulsoup4 anthropic gspread google-auth selenium selenium-wire undetected-chromedriver

# 4. Set your API key
export GEMINI_API_KEY=sk-ant-...     # Mac
set GEMINI_API_KEY==sk-ant-...        # Windows

# 5. Run
python run_pipeline.py
```

---

##  Sample Output

| Company | Signal Used | Personalized First Line |
|---------|------------|------------------------|
| Hexcel Corporation | Integrated CF + prepreg supply | "Noticed you're bringing both carbon fiber AND prepregs to CAMX — curious how you're positioning integrated supply to aerospace Tier 1s reducing vendor consolidation risk." |
| Albany Engineered Composites | 3D woven jet engine structures | "Your 3D woven structures for jet engine fan blades are one of the harder processes to scale — curious how you're managing repeatability when the weave architecture is so geometry-specific." |
| Zoltek Companies | Commercial CF for wind + auto | "As the largest commercial-grade carbon fiber producer, curious how wind energy's cost-per-kilo pressure compares to what automotive OEMs are willing to pay now that carbon is moving from concept to spec." |

---

##  Why Selenium Wire?

The CAMX website is **JavaScript-rendered** — it loads company data through hidden API calls after the page opens. Normal Python requests just get an empty template (403 error).

Selenium Wire solves this by running a real Chrome browser and intercepting all network traffic. When the page fires its hidden search request, Selenium Wire captures the raw JSON response — giving us the complete exhibitor list.

---


