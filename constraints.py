  # Area allocation + room minimums
from models import StructuredBrief, Room
from config import MIN_ROOM_SIZES, CIRCULATION_FACTOR
import math

def validate_and_normalize(brief: StructuredBrief) -> StructuredBrief:
    """
    Enforce minimum room sizes and normalize total area.
    Returns updated brief with valid room areas.
    """
    usable_area = brief.total_area_sqft * CIRCULATION_FACTOR
    rooms = brief.rooms

    # Step 1: Enforce minimums
    for room in rooms:
        room_key = room.name.lower()
        for key, min_size in MIN_ROOM_SIZES.items():
            if key in room_key:
                if room.area_sqft < min_size:
                    print(f"[WARN] {room.name} too small ({room.area_sqft} sqft), raising to {min_size}")
                    room.area_sqft = min_size
                break

    # Step 2: Scale to fit usable area
    total_assigned = sum(r.area_sqft for r in rooms)
    if total_assigned > usable_area:
        scale = usable_area / total_assigned
        print(f"[INFO] Scaling all rooms by {scale:.2f} to fit usable area {usable_area:.0f} sqft")
        for room in rooms:
            room.area_sqft = max(room.area_sqft * scale, 30)  # never below 30 sqft

    # Step 3: Infer plot dimensions if missing
    if not brief.plot_width_ft or not brief.plot_depth_ft:
        total_area = brief.total_area_sqft
        # Default aspect ratio 1:1.4 (width:depth) — typical urban plot
        brief.plot_width_ft = round(math.sqrt(total_area / 1.4), 1)
        brief.plot_depth_ft = round(total_area / brief.plot_width_ft, 1)

    return brief

def get_room_dimensions(area_sqft: float, aspect_ratio: float = 1.3) -> tuple[float, float]:
    """
    Given area and aspect ratio, return (width, height) in feet.
    aspect_ratio = height/width. Default slightly taller than wide.
    """
    width = math.sqrt(area_sqft / aspect_ratio)
    height = area_sqft / width
    return round(width, 1), round(height, 1)

# In constraints.py — add this validation function
def validate_output(brief: StructuredBrief, layout: List[RoomLayout]) -> dict:
    issues = []
    warnings = []
    
    # 1. Area check: sum of laid-out rooms should be ≤ plot area
    total_laid = sum(r.width * r.height for r in layout)
    plot_area = brief.plot_width_ft * brief.plot_depth_ft
    if total_laid > plot_area * 1.05:  # 5% tolerance
        issues.append(f"Layout area ({total_laid:.0f} sqft) exceeds plot ({plot_area:.0f} sqft)")
    
    # 2. All rooms placed (no orphans)
    parsed_names = {r.name for r in brief.rooms}
    placed_names = {r.name for r in layout}
    orphans = parsed_names - placed_names
    if orphans:
        warnings.append(f"Rooms not placed: {orphans}")
    
    # 3. No room overlaps (simplified: check bounding box)
    for i, r1 in enumerate(layout):
        for j, r2 in enumerate(layout):
            if i >= j: continue
            if (r1.x < r2.x + r2.width and r1.x + r1.width > r2.x and
                r1.y < r2.y + r2.height and r1.y + r1.height > r2.y):
                issues.append(f"Room overlap: {r1.name} and {r2.name}")
    
    # 4. Minimum room size enforcement
    for room in layout:
        if room.width * room.height < 25:  # 25 sqft absolute minimum
            warnings.append(f"{room.name} is very small: {room.width*room.height:.0f} sqft")
    
    return {"issues": issues, "warnings": warnings, "valid": len(issues) == 0}