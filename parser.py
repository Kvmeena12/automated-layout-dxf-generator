import json
import os
from groq import Groq
from dotenv import load_dotenv
from models import StructuredBrief

load_dotenv()


GROQ_API_KEY = os.getenv("GROQ_API_KEY")
client = Groq(api_key=GROQ_API_KEY)
SYSTEM_PROMPT =  """You are an expert architectural brief parser.

Your task is to convert a user's architectural brief into a STRICT structured JSON.

-----------------------------------
CORE RULES (VERY IMPORTANT)
-----------------------------------

1. TOTAL AREA CONSTRAINT
- Sum of all room areas MUST be <= total_area_sqft
- Target usage: 75%–85% of total area (leave space for walls, circulation)
- NEVER exceed total_area_sqft

2. ROOM VALIDITY
- Always include: living room
- Bedrooms ≥ 90 sqft
- Kitchen ≥ 60 sqft
- Bathroom ≥ 40 sqft
- Dining ≥ 50 sqft
- Avoid very small or zero-area rooms

3. NO OVERLAP LOGIC
- The layout must fully fit inside the plot rectangle
- Total layout width must not exceed plot_width_ft
- Total layout depth must not exceed plot_depth_ft
- Rooms must be realistic in size
- Avoid too many rooms for small total area
- If area is small → reduce number of rooms

4. ZONING RULES
- public: living, dining, kitchen, study, foyer
- private: bedrooms, bathrooms
- service: utility, store, balcony

5. ADJACENCY RULES
- kitchen → dining
- bedroom → bathroom
- master bedroom → attached bathroom (if possible)
- living → dining
- Avoid random adjacencies

6. NATURAL LIGHT
- true: living, bedrooms, study
- false: bathroom, utility, store

7. PLOT DIMENSIONS
- If not given:
  - Assume rectangular plot
  - Maintain width:depth ratio between 1:1.1 and 1:1.5
  - Ensure area ≈ plot_width * plot_depth

8. PRIORITY LOGIC
- Prioritize essential rooms:
  living > bedrooms > kitchen > bathroom > dining > others
- If space is limited → drop low priority rooms (study, store)

-----------------------------------
SPACE UTILIZATION RULES (STRICT)
-----------------------------------

- The total layout must fully utilize the available plot area.
- Avoid leaving large unused or empty rectangular spaces.
- Distribute rooms evenly across the plot width and depth.

- If extra space remains:
  - Prefer adding functional rooms such as:
    - Study
    - Family lounge
    - Store room
  - Do NOT leave empty unused space.

- Rooms should expand proportionally to fill available space.

- Avoid creating narrow unused gaps or dead spaces.

-----------------------------------
ROOM VALIDITY RULES (STRICT)
-----------------------------------

- Do NOT repeat same room type excessively
- Maximum:
  - Balcony: 1
  - Kitchen: 1
  - Living: 1
- Bedrooms: based on BHK (2BHK → 2 bedrooms, etc.)
- MUST include:
  - Living Room
  - At least 1 Bedroom
  - Kitchen
  - Bathroom

If constraints conflict → prioritize essential rooms over balcony.
-----------------------------------
OUTPUT RULES
-----------------------------------

- Return ONLY valid JSON
- No explanation, no markdown, no extra text
- All fields must be filled
- Numbers must be realistic and consistent

-----------------------------------
SCHEMA
-----------------------------------

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
}
"""

def ensure_core_rooms(rooms):
    names = [r.name.lower() for r in rooms]

    def add_room(name, area, zone):
        rooms.append(RoomLayout(
            name=name,
            x=0, y=0, width=0, height=0,
            zone=zone,
            natural_light=True
        ))

    if not any("living" in n for n in names):
        add_room("Living Room", 120, "public")

    if not any("bedroom" in n for n in names):
        add_room("Bedroom", 100, "private")

    if not any("kitchen" in n for n in names):
        add_room("Kitchen", 70, "service")

    return rooms
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
