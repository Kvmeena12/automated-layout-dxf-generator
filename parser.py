import json
import os
from groq import Groq
from dotenv import load_dotenv
from models import StructuredBrief, Room

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
client = Groq(api_key=GROQ_API_KEY)

SYSTEM_PROMPT = """You are an expert architectural brief parser.

Your task is to convert a user's architectural brief into a STRICT structured JSON.

-----------------------------------
CORE RULES (VERY IMPORTANT)
-----------------------------------

1. TOTAL AREA CONSTRAINT
- Sum of all room areas MUST be <= total_area_sqft
- Target usage: 75%–85% of total area (leave 15-25% for walls, circulation, corridor)
- NEVER exceed total_area_sqft
- Example: 1500 sqft total → allocate 1125-1275 sqft to rooms

2. ROOM VALIDITY
- Always include: living room (min 120 sqft)
- Bedrooms ≥ 90 sqft (master ≥ 110 sqft)
- Kitchen ≥ 60 sqft
- Bathroom ≥ 40 sqft
- Dining ≥ 50 sqft
- Study ≥ 70 sqft
- Balcony ≥ 60 sqft
- Avoid zero-area rooms
- Avoid rooms under minimum size

3. NO OVERLAP LOGIC
- The layout must fully fit inside the plot rectangle
- Total layout width must not exceed plot_width_ft
- Total layout depth must not exceed plot_depth_ft
- Rooms must be realistic in size
- Avoid too many rooms for small total area
- If area is small → reduce number of rooms or reduce room sizes proportionally

4. ZONING RULES
- public: living room, dining, kitchen, study, foyer
- private: master bedroom, bedrooms, bathrooms
- service: utility, store, balcony, pantry

5. ADJACENCY RULES
- kitchen ↔ dining (must be adjacent or connected)
- master bedroom ↔ master bathroom (attached if possible)
- bedroom ↔ bathroom (close proximity)
- living ↔ dining (direct connection)
- living ↔ foyer (entrance flow)
- Avoid random adjacencies

6. NATURAL LIGHT
- true: living, dining, bedrooms, study, foyer, balcony
- false: bathroom, utility, store, pantry

7. PLOT DIMENSIONS
- If not given, calculate from total_area_sqft:
  - Assume rectangular plot
  - Prefer width:depth ratio between 1:1 and 1:1.5
  - Ensure plot_width_ft × plot_depth_ft ≈ total_area_sqft
  - Round to nearest 5 ft

8. PRIORITY LOGIC (STRICT)
- Essential (MUST INCLUDE):
  1. Living Room (100-150 sqft)
  2. Bedrooms (as specified in BHK)
  3. Kitchen (60-100 sqft)
  4. Bathrooms (≥ 1, ideally 1 per 2 bedrooms)
  
- Important (INCLUDE IF SPACE ALLOWS):
  5. Dining (50-80 sqft)
  6. Study (70-100 sqft)
  
- Optional (ONLY IF EXTRA SPACE):
  7. Balcony (60-100 sqft)
  8. Utility/Store (40-60 sqft)

- If space is limited (< 800 sqft):
  → Drop balcony, study, utility
  → Minimize room sizes
  → Combined living-dining is OK
  
- If space is moderate (800-1500 sqft):
  → Include dining, 1 bathroom
  → Optional study
  → Skip balcony/utility
  
- If space is large (> 1500 sqft):
  → Include all rooms
  → Add balcony, utility, multiple bathrooms

-----------------------------------
SPACE UTILIZATION RULES (STRICT)
-----------------------------------

- NEVER leave empty unused rectangular spaces
- Total room area = 75-85% of total_area_sqft
- Remaining 15-25% = walls (0.5 ft thick) + circulation + corridor (3-3.5 ft width)

- If you calculate room areas and they sum to < 65% of total:
  → Increase room sizes proportionally
  → Add additional small rooms (study, balcony) to fill space

- Rooms should NOT have extreme aspect ratios:
  → Avoid very narrow rooms (width < 6 ft)
  → Avoid very long rooms (length:width > 3:1)
  → Target aspect ratio: 1.2 to 1.5

- Avoid creating scattered or floating rooms
- Maintain compact rectangular layout

-----------------------------------
SPATIAL PLACEMENT RULES (FOR VALIDATOR)
-----------------------------------

These rules guide the layout generator AFTER JSON is created:

1. ENTRY FLOW (BOTTOM → TOP)
   - Entrance at bottom
   - Foyer near entrance
   - Living room directly after foyer
   - Dining next to living
   - Kitchen near dining

2. ZONE POSITIONING
   - Public zone: bottom (living, dining, kitchen)
   - Service zone: middle (balcony, utility)
   - Private zone: top (bedrooms, bathrooms)

3. CORRIDOR LOGIC
   - Central vertical corridor (3-3.5 ft wide)
   - Rooms on left and right of corridor
   - Balanced distribution left/right

4. BEDROOM-BATHROOM LOGIC
   - Each bedroom should have nearby bathroom
   - Master bedroom ideally has attached bathroom

5. KITCHEN POSITION
   - Kitchen must be adjacent to dining
   - Kitchen near living/dining area
   - Separate from bedrooms

-----------------------------------
ROOM VALIDITY RULES (STRICT)
-----------------------------------

- Do NOT repeat same room type excessively
- Maximum:
  - Balcony: 1
  - Kitchen: 1
  - Living room: 1
  - Dining: 1-2 (only if large enough)
  
- Bedrooms:
  - 1BHK → 1 bedroom
  - 2BHK → 2 bedrooms
  - 3BHK → 3 bedrooms
  - 4BHK → 4 bedrooms
  
- Bathrooms:
  - 1BHK → 1 bathroom
  - 2BHK → 1-2 bathrooms
  - 3BHK → 2 bathrooms
  - 4BHK → 2-3 bathrooms

- MUST include:
  - Living Room
  - At least 1 Bedroom
  - Kitchen
  - Bathroom

-----------------------------------
OUTPUT RULES
-----------------------------------

- Return ONLY valid JSON
- No explanation, no markdown, no extra text
- All fields must be filled
- Numbers must be realistic and consistent
- room_count = len(rooms)
- All areas rounded to nearest integer
- All dimensions rounded to 1 decimal place

-----------------------------------
SCHEMA
-----------------------------------

{
  "total_area_sqft": integer (>= 500),
  "plot_width_ft": number (>= 20),
  "plot_depth_ft": number (>= 20),
  "room_count": integer,
  "rooms": [
    {
      "name": string (unique, no duplicates),
      "area_sqft": integer (>= 40),
      "zone": "public" | "private" | "service",
      "adjacencies": [string] (list of adjacent room names),
      "natural_light": boolean
    }
  ],
  "special_constraints": [string] (list of special requirements)
}

VALIDATION CHECKS:
- sum(room.area_sqft for all rooms) <= total_area_sqft
- sum(room.area_sqft for all rooms) >= 0.65 * total_area_sqft
- plot_width_ft * plot_depth_ft >= total_area_sqft
- All room names are unique
- No room area < 40 sqft
- room_count = len(rooms)
"""

def validate_and_fix_brief(data: dict) -> dict:
    """
    Validate parsed brief and fix common issues
    """
    try:
        total_area = data.get("total_area_sqft", 1500)
        rooms = data.get("rooms", [])
        
        # ===== AREA VALIDATION =====
        total_room_area = sum(r.get("area_sqft", 0) for r in rooms)
        min_area = total_area * 0.65
        max_area = total_area * 0.95
        
        if total_room_area > max_area:
            # Shrink all rooms proportionally
            scale = max_area / total_room_area
            for room in rooms:
                room["area_sqft"] = max(40, int(room["area_sqft"] * scale))
        
        elif total_room_area < min_area:
            # Expand rooms proportionally or add optional rooms
            scale = min_area / total_room_area
            for room in rooms:
                room["area_sqft"] = max(room["area_sqft"], int(room["area_sqft"] * scale))
        
        # ===== PLOT DIMENSIONS =====
        plot_w = data.get("plot_width_ft")
        plot_d = data.get("plot_depth_ft")
        
        if not plot_w or not plot_d:
            # Calculate from total area
            ratio = 1.2  # width:depth ratio
            plot_d = (total_area / ratio) ** 0.5
            plot_w = plot_d * ratio
            plot_w = round(plot_w / 5) * 5  # Round to nearest 5
            plot_d = round(plot_d / 5) * 5
            data["plot_width_ft"] = plot_w
            data["plot_depth_ft"] = plot_d
        
        # ===== ENSURE CORE ROOMS =====
        room_names = [r["name"].lower() for r in rooms]
        
        if not any("living" in n for n in room_names):
            rooms.append({
                "name": "Living Room",
                "area_sqft": max(120, int(total_area * 0.1)),
                "zone": "public",
                "adjacencies": ["Foyer", "Dining"],
                "natural_light": True
            })
        
        if not any("bedroom" in n for n in room_names):
            rooms.append({
                "name": "Bedroom",
                "area_sqft": max(90, int(total_area * 0.08)),
                "zone": "private",
                "adjacencies": ["Bathroom"],
                "natural_light": True
            })
        
        if not any("kitchen" in n for n in room_names):
            rooms.append({
                "name": "Kitchen",
                "area_sqft": max(60, int(total_area * 0.06)),
                "zone": "service",
                "adjacencies": ["Dining"],
                "natural_light": False
            })
        
        if not any("bath" in n for n in room_names):
            rooms.append({
                "name": "Bathroom",
                "area_sqft": 45,
                "zone": "private",
                "adjacencies": ["Bedroom"],
                "natural_light": False
            })
        
        # ===== REMOVE DUPLICATES =====
        seen = {}
        unique_rooms = []
        for room in rooms:
            name = room["name"].lower()
            if name not in seen:
                seen[name] = True
                unique_rooms.append(room)
        
        data["rooms"] = unique_rooms
        data["room_count"] = len(unique_rooms)
        
        # ===== FINAL AREA CHECK =====
        final_area = sum(r["area_sqft"] for r in unique_rooms)
        if final_area > total_area:
            # Last resort: scale everything down
            scale = (total_area * 0.9) / final_area
            for room in unique_rooms:
                room["area_sqft"] = max(40, int(room["area_sqft"] * scale))
        
        return data
    
    except Exception as e:
        print(f"Warning: validation error - {e}")
        return data

def parse_brief(brief_text: str) -> StructuredBrief:
    """
    Parse architectural brief using Groq LLM
    """
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": brief_text}
            ],
            temperature=0.1,
            max_tokens=1500,
        )

        raw = response.choices[0].message.content.strip()

        # Strip markdown fences
        if raw.startswith("```"):
            lines = raw.split("\n")
            raw = "\n".join(lines[1:-1])
            if raw.startswith("json"):
                raw = raw[4:].strip()

        # Extract JSON object
        start = raw.find("{")
        end = raw.rfind("}") + 1
        if start == -1 or end <= start:
            raise ValueError("No JSON object found in response")
        
        raw = raw[start:end]
        data = json.loads(raw)

        # Validate and fix
        data = validate_and_fix_brief(data)

        return StructuredBrief(**data)
    
    except json.JSONDecodeError as e:
        print(f"JSON Parse Error: {e}")
        print(f"Raw response: {raw[:200]}")
        raise
    except Exception as e:
        print(f"Parse Error: {e}")
        raise

# Test function
if __name__ == "__main__":
    test_briefs = [
        "900 sqft apartment, 2BHK, 1 bathroom, open kitchen",
        "1500 sqft, 3BHK, 2 bathrooms, study room, balcony",
        "3000 sqft villa, 4BHK, master suite, formal living, large kitchen, utility room",
    ]

    for brief in test_briefs:
        print(f"\n{'='*60}")
        print(f"Brief: {brief}")
        print(f"{'='*60}")
        try:
            result = parse_brief(brief)
            print(f"\n📐 Plot: {result.plot_width_ft}ft × {result.plot_depth_ft}ft = {result.plot_width_ft * result.plot_depth_ft:.0f} sqft")
            print(f"📊 Total Area: {result.total_area_sqft} sqft")
            print(f"🏠 Rooms: {result.room_count}\n")
            
            total_room_area = sum(r.area_sqft for r in result.rooms)
            print(f"Room Allocation ({total_room_area}/{result.total_area_sqft} sqft):")
            print("-" * 60)
            
            for r in result.rooms:
                pct = (r.area_sqft / result.total_area_sqft) * 100
                print(f"  {r.name:25s} {r.area_sqft:4d} sqft ({pct:5.1f}%) [{r.zone:8s}]")
            
            print("-" * 60)
            utilization = (total_room_area / result.total_area_sqft) * 100
            print(f"Space Utilization: {utilization:.1f}%")
            print(f"✓ VALID" if 65 <= utilization <= 95 else f"⚠ NEEDS ADJUSTMENT")
        
        except Exception as e:
            print(f"✗ Error: {e}")
