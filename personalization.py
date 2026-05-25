"""
Personalization Engine — CAMX 2026 Cold Email First Lines
Uses Gemini API to generate personalized cold email opening lines.
"""

import os, json, time
from pathlib import Path

GEMINI_KEY  = os.getenv("GEMINI_KEY", "")
INPUT_FILE  = "camx2026_exhibitors_enriched.json"
OUTPUT_FILE = "camx2026_final.json"
CSV_FILE    = "camx2026_final.csv"


#  THE PROMPT


SYSTEM_PROMPT = """
You are writing cold email opening lines for a GTM professional attending CAMX 2026
(the premier composites and advanced materials trade show, held in Atlanta, Sep 21-24).

Your job is to write ONE opening sentence — the very first line of a cold email —
to a company exhibiting at CAMX.

RULES (strict):
1. Anchor on ONE specific, real signal from the company data provided
   (e.g. a product type, a market they serve, a capability they highlight)
2. Bridge that signal to a concrete business angle: cost, speed, quality,
   scale, or market fit
3. Keep it under 35 words
4. Sound like a curious peer — not a pitch, not a compliment
5. Never use phrases like: "Love what you're doing", "Impressive work",
   "I came across your company", or "Reaching out because..."
6. Do NOT name the company in the first line
7. Do NOT ask for a meeting in this line
8. Output ONLY the single sentence — no preamble, no explanation

EXAMPLES OF GOOD OUTPUT:
- "Noticed you're highlighting lightweight composite solutions at CAMX —
   curious how you're positioning these for manufacturers trying to cut
   production costs without sacrificing strength."
- "Your focus on 3D-woven aerospace structures caught my attention —
   particularly how you're approaching the trade-off between cycle time
   and structural integrity for engine nacelles."

EXAMPLES OF BAD OUTPUT (never produce these):
- "Loved what your company is doing at CAMX." [generic praise]
- "I noticed Hexcel has a great booth at CAMX." [names company, generic]
- "Would love to connect and explore synergies." [buzzword, no signal]
"""

USER_PROMPT_TEMPLATE = """
Company data:
  Name:        {company_name}
  Description: {description}
  Categories:  {categories}
  Website:     {website}
  Signal:      {signal}
  Homepage:    {meta_desc}

Write the personalized opening line now.
"""


# ══════════════════════════════════════════════════════════════════════════════
#  GENERATION
# ══════════════════════════════════════════════════════════════════════════════

def generate_first_line(company: dict) -> str:
    """Call Gemini to generate one personalized opening line."""

    user_msg = USER_PROMPT_TEMPLATE.format(
        company_name = company.get("company_name", ""),
        description  = company.get("description", "")[:300],
        categories   = company.get("categories", ""),
        website      = company.get("website", ""),
        signal       = company.get("signal", ""),
        meta_desc    = company.get("meta_desc", "")[:200],
    )

    if not GEMINI_KEY:
        return _rule_based_line(company)

    try:
        import google.generativeai as genai
        genai.configure(api_key=GEMINI_KEY)
        model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            system_instruction=SYSTEM_PROMPT
        )
        response = model.generate_content(user_msg)
        return response.text.strip().strip('"')
    except Exception as e:
        return f"[generation error: {e}]"


def _rule_based_line(company: dict) -> str:
    """
    Rule-based first-line generator used when no Gemini key is available.
    """
    cats   = [c.strip() for c in company.get("categories", "").split(";") if c.strip()]
    desc   = company.get("description", "")
    signal = company.get("signal", "")

    primary = signal if len(signal) > 30 else (desc[:150] if desc else "")
    p = primary.lower()

    if "carbon fiber" in p and "automotive" in p:
        return ("Your push to bring carbon fiber into automotive at commercial scale "
                "is interesting — curious whether you're seeing OEMs pull forward "
                "spec adoption faster than the traditional 5-year product cycles.")
    elif "carbon fiber" in p and "aerospace" in p:
        return ("Noticed your carbon fiber work is concentrated in aerospace primary "
                "structures — wondering how you're approaching the qualification "
                "timeline challenge as OEMs accelerate next-gen airframe programs.")
    elif "wind" in p or "wind energy" in p:
        return ("Saw you're focused on wind energy composites — given how blade "
                "length has been pushing material cost per kWh targets, curious "
                "what the main trade-off is you're solving for at CAMX.")
    elif "thermoplastic" in p:
        return ("Your thermoplastic prepreg work caught my eye — particularly the "
                "potential for in-situ consolidation to cut autoclave cycle time; "
                "curious how Tier 1 aerostructures suppliers are responding.")
    elif "adhesive" in p or "adhesives" in p:
        return ("Noticed you're focused on structural adhesives for composite joining "
                "— curious whether the shift away from fasteners is accelerating "
                "on commercial narrowbody programs or still mostly defense-driven.")
    elif "distribution" in p or "distributor" in p:
        return ("Given you supply across wind, marine, and transportation, I'm "
                "curious how the supply-chain consolidation trend is changing what "
                "fabricators are actually asking you for at point of order.")
    elif "3d" in p and ("wov" in p or "braid" in p):
        return ("Your 3D woven structure capability is one of the harder manufacturing "
                "processes to scale — interested in how you're managing the tension "
                "between design freedom and repeatable quality at volume.")
    elif "marine" in p:
        return ("Noticed your composites focus includes marine — curious whether "
                "the infusion vs prepreg debate in that market has shifted now "
                "that cycle times matter more to recreational OEMs.")
    elif "smc" in p or "sheet molding" in p:
        return ("Your SMC work for commercial transportation caught my attention — "
                "particularly how you're competing against metal on total cost "
                "when volumes are below the threshold where tooling pays back quickly.")
    else:
        cat = cats[0] if cats else "composites"
        return (f"Noticed you're presenting {cat} solutions at CAMX — curious "
                f"what the specific application conversation you're expecting "
                f"to have most with OEMs and Tier 1s in Atlanta.")


# ══════════════════════════════════════════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════════════════════════════════════════

def run_personalization(companies: list[dict]) -> list[dict]:
    results = []
    for i, company in enumerate(companies):
        name = company.get("company_name", "")
        print(f"[{i+1}/{len(companies)}] Generating first line: {name}")
        line = generate_first_line(company)
        print(f"  → {line[:90]}...")
        results.append({**company, "personalized_first_line": line})
        time.sleep(0.5)
    return results


def save_csv(records: list[dict]) -> None:
    import csv
    fields = [
        "company_name", "booth", "website", "linkedin_url",
        "categories", "city", "state", "country",
        "description", "signal", "personalized_first_line",
    ]
    with open(CSV_FILE, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(records)
    print(f"CSV saved → {CSV_FILE}")


if __name__ == "__main__":
    data = json.loads(Path(INPUT_FILE).read_text())
    final = run_personalization(data)
    Path(OUTPUT_FILE).write_text(json.dumps(final, indent=2))
    save_csv(final)
    print(f"\nDone. {len(final)} companies processed.")
    print(f"JSON → {OUTPUT_FILE}")
    print(f"CSV  → {CSV_FILE}")