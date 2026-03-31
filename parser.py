import json
import os
from groq import Groq
from dotenv import load_dotenv
from models import StructuredBrief

load_dotenv()


GROQ_API_KEY = os.getenv("GROQ_API_KEY")
client = Groq(api_key=GROQ_API_KEY)
SYSTEM_PROMPT = """You are an expert architectural brief parser.
Convert the user's architectural brief into a structured JSON object.

Rules:
- Extract all rooms mentioned. Always add a living room if not explicitly stated.
- Infer reasonable area_sqft for each room, ensuring all rooms total <= total_area_sqft * 0.82
- Assign zone: "public" (living, dining, kitchen, study, entry), "private" (bedrooms, bathrooms), "service" (utility, store, garage)
- Infer adjacencies: kitchen->dining, master bedroom->master bathroom, bedroom->bathroom, etc.
- Set natural_light: true for living room, bedrooms, study. false for bathrooms, utility, store.
- If plot dimensions not given, infer a rectangle with width:depth ratio between 1:1.2 and 1:1.5

IMPORTANT: Return ONLY valid JSON. No markdown, no backticks, no explanation. Just the raw JSON object.

Schema:
{
  "total_area_sqft": number,
  "plot_width_ft": number,
  "plot_depth_ft": number,
  "rooms": [
    {
      "name": string,
      "area_sqft": number,
      "zone": "public" or "private" or "service",
      "adjacencies": [string],
      "natural_light": boolean
    }
  ],
  "special_constraints": [string]
}"""


def parse_brief(brief_text: str) -> StructuredBrief:
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",   # best free model on Groq for structured output
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": brief_text}
        ],
        temperature=0.1,      # low temperature = more consistent JSON output
        max_tokens=1000,
    )

    raw = response.choices[0].message.content.strip()

    # Strip markdown fences if model adds them
    if raw.startswith("```"):
        lines = raw.split("\n")
        raw = "\n".join(lines[1:-1])
        if raw.startswith("json"):
            raw = raw[4:].strip()

    # Sometimes model adds text before/after the JSON — extract just the JSON object
    start = raw.find("{")
    end = raw.rfind("}") + 1
    if start != -1 and end > start:
        raw = raw[start:end]

    data = json.loads(raw)
    return StructuredBrief(**data)


# Run this file directly to test your Groq key
if __name__ == "__main__":
    test_briefs = [
        "3BHK, 1500 sq ft, open kitchen, 1 study, maximize natural light",
        "2BHK apartment, 900 sq ft, combined living and dining, 1 bathroom",
        "4BHK villa, 3000 sq ft, master suite, formal living, large kitchen, utility room",
    ]

    for brief in test_briefs:
        print(f"\nBrief: {brief}")
        print("-" * 50)
        try:
            result = parse_brief(brief)
            rooms = [(r.name, f"{r.area_sqft:.0f} sqft", r.zone) for r in result.rooms]
            for name, area, zone in rooms:
                print(f"  {name:25s} {area:10s} [{zone}]")
            print(f"  Plot: {result.plot_width_ft}ft x {result.plot_depth_ft}ft")
            print("  ✓ OK")
        except json.JSONDecodeError as e:
            print(f"  ✗ JSON error: {e}")
        except Exception as e:
            print(f"  ✗ Error: {e}")
