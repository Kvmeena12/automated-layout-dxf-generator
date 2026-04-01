from models import StructuredBrief, RoomLayout
from typing import List
import math

ADJACENCY_RULES = {
    "bedroom": ["bathroom", "corridor"],
    "kitchen": ["dining"],
    "living": ["foyer", "dining"],
    "bathroom": ["bedroom"],
}

ROOM_PRIORITY = {
    "living": 5,
    "master bedroom": 5,
    "bedroom": 4,
    "kitchen": 4,
    "bathroom": 3,
    "dining": 3,
    "study": 2,
    "balcony": 2,
}
def is_overlap(r1, r2):
    return (
        r1.x < r2.x + r2.width and
        r1.x + r1.width > r2.x and
        r1.y < r2.y + r2.height and
        r1.y + r1.height > r2.y
    )
def place_room(room, placed_rooms, start_x, start_y):
    x = start_x   # ✅ FIX
    y = start_y   # ✅ FIX

    while True:
        overlap = False

        for r in placed_rooms:
            if (
                x < r.x + r.width and
                x + room.width > r.x and
                y < r.y + r.height and
                y + room.height > r.y
            ):
                overlap = True
                break

        if not overlap:
            return x, y

        # shift right
        x += 2

        # move to next row
        if x > 30:
            x = 0
            y += 2

def get_room_weight(name):
    """Get priority weight for room sizing"""
    name = name.lower()
    if "living" in name:
        return 6
    elif "kitchen" in name:
        return 5
    elif "master" in name or "bedroom" in name:
        return 4
    elif "bath" in name:
        return 2
    elif "dining" in name:
        return 3
    else:
        return 1

def get_min_dimensions(room_name):
    """Define minimum width and aspect ratio for each room type"""
    name = room_name.lower()
    
    if "living" in name:
        return {"min_w": 14, "min_h": 12, "aspect": 1.2}
    elif "kitchen" in name:
        return {"min_w": 9, "min_h": 8, "aspect": 1.1}
    elif "master" in name:
        return {"min_w": 12, "min_h": 11, "aspect": 1.1}
    elif "bedroom" in name:
        return {"min_w": 10, "min_h": 9, "aspect": 1.1}
    elif "bath" in name:
        return {"min_w": 5, "min_h": 6, "aspect": 0.8}
    elif "dining" in name:
        return {"min_w": 10, "min_h": 9, "aspect": 1.1}
    elif "study" in name:
        return {"min_w": 8, "min_h": 8, "aspect": 1.0}
    else:
        return {"min_w": 6, "min_h": 6, "aspect": 1.0}

def create_foyer(plot_w, plot_h):
    """Create foyer at entry"""
    return RoomLayout(
        name="Foyer",
        x=0.5,
        y=plot_h - 4.5,
        width=6.5,
        height=4,
        zone="public"
    )

def create_corridor(plot_w, plot_h):
    """Create central corridor"""
    corridor_width = 3.0
    return RoomLayout(
        name="Corridor",
        x=plot_w / 2 - corridor_width / 2,
        y=0,
        width=corridor_width,
        height=plot_h,
        zone="circulation"
    )

def check_overlaps(layout: List[RoomLayout]) -> List[tuple]:
    """
    Check for overlaps between rooms
    Returns list of overlapping room pairs
    """
    overlaps = []
    for i in range(len(layout)):
        for j in range(i + 1, len(layout)):
            r1 = layout[i]
            r2 = layout[j]
            
            # Check if rectangles overlap
            # No overlap if one is completely left/right/above/below the other
            if not (r1.x + r1.width <= r2.x or r2.x + r2.width <= r1.x or
                    r1.y + r1.height <= r2.y or r2.y + r2.height <= r1.y):
                overlaps.append((r1.name, r2.name))
    
    return overlaps

def generate_layout(brief: StructuredBrief) -> List[RoomLayout]:
    """
    Generate optimal floor layout using improved space allocation
    - Minimizes wasted space
    - Balances room distribution
    - Respects minimum dimensions
    - Proper corridor integration
    """
    
    plot_w = brief.plot_width_ft
    plot_d = brief.plot_depth_ft
    WALL = 0.5
    
    # ===== ZONE SETUP =====
    zones = {"public": [], "service": [], "private": []}
    for room in brief.rooms:
        zones[room.zone].append(room)
    
    total_area = sum(r.area_sqft for r in brief.rooms)
    
    # ===== CORRIDOR DIMENSIONS =====
    corridor_width = 3.0
    corridor_x = (plot_w - corridor_width) / 2
    left_width = corridor_x - WALL
    right_width = plot_w - (corridor_x + corridor_width) - WALL
    usable_width = min(left_width, right_width)
    
    # ===== CALCULATE ZONE HEIGHTS =====
    zone_heights = {}
    total_zone_height = 0
    
    for zone_name in ["public", "service", "private"]:
        rooms = zones[zone_name]
        if not rooms:
            continue
        
        zone_area = sum(r.area_sqft for r in rooms)
        # Allocate height proportional to zone area
        zone_h = (zone_area / total_area) * plot_d
        zone_heights[zone_name] = max(zone_h, 10)
        total_zone_height += zone_heights[zone_name]
    
    # Scale zones to fit plot depth
    if total_zone_height > plot_d:
        scale = plot_d / total_zone_height
        for zone_name in zone_heights:
            zone_heights[zone_name] *= scale
    
    # ===== PLACE ROOMS =====
    layout = []
    placed_rooms = []
    zone_y = 0
    
    for zone_name in ["public", "service", "private"]:
        rooms = zones[zone_name]
        if not rooms:
            continue
        
        zone_h = zone_heights[zone_name]
        zone_area = sum(r.area_sqft for r in rooms)
        
        # Sort by area (largest first) then by weight
        rooms_sorted = sorted(
            rooms,
            key=lambda r: (-r.area_sqft, -get_room_weight(r.name))
        )
       
        
        # ===== LAYOUT STRATEGY: 2-COLUMN GRID =====
        # Distribute rooms across left and right of corridor
        left_rooms = []
        right_rooms = []
        
        for i, room in enumerate(rooms_sorted):
            if i % 2 == 0:
                left_rooms.append(room)
            else:
                right_rooms.append(room)
        
        # Calculate actual heights for left and right
        left_area = sum(r.area_sqft for r in left_rooms)
        right_area = sum(r.area_sqft for r in right_rooms)
        total_side_area = left_area + right_area
        
        left_zone_h = (left_area / total_side_area) * zone_h if total_side_area > 0 else zone_h
        right_zone_h = (right_area / total_side_area) * zone_h if total_side_area > 0 else zone_h
        
        # ===== PLACE LEFT SIDE ROOMS =====
        left_y = zone_y
        for room in left_rooms:
            room_h = max(8, (room.area_sqft / left_area) * left_zone_h) if left_area > 0 else 8
            room_w = max(room.area_sqft / room_h, get_min_dimensions(room.name)["min_w"])
            room_w = min(room_w, usable_width - WALL)
            
            # LEFT SIDE: Must be to the LEFT of corridor
            room.x, room.y = place_room(room, placed_rooms, x, y)
            placed_rooms.append(room)
            
            # CRITICAL: Hard boundaries - PRIORITY: STAY WITHIN PLOT
            # Constrain to plot depth FIRST
            if room_y + room_h > plot_d:
                room_h = plot_d - room_y - WALL
            
            # Then constrain to zone
            if room_y + room_h > zone_y + zone_h:
                room_h = zone_y + zone_h - room_y - WALL
            
            # Constrain to left side boundary (before corridor)
            max_left_x = corridor_x - WALL - 0.5
            if room_x + room_w > max_left_x:
                room_w = max_left_x - room_x
            
            # Ensure minimum size
            room_h = max(room_h, 5)
            room_w = max(room_w, 5)
            
            # Final safety check - clamp all values
            room_y = max(WALL, min(room_y, plot_d - room_h - WALL))
            room_w = min(room_w, max_left_x - room_x)
            room_h = min(room_h, plot_d - room_y - WALL)
            
            if room_w >= 4 and room_h >= 4:
                layout.append(RoomLayout(
                    name=room.name,
                    x=round(room_x, 2),
                    y=round(room_y, 2),
                    width=round(room_w, 2),
                    height=round(room_h, 2),
                    zone=zone_name,
                    natural_light=room.natural_light
                ))
            
            left_y += room_h + WALL
        
        # ===== PLACE RIGHT SIDE ROOMS =====
        right_y = zone_y
        for room in right_rooms:
            room_h = max(8, (room.area_sqft / right_area) * right_zone_h) if right_area > 0 else 8
            room_w = max(room.area_sqft / room_h, get_min_dimensions(room.name)["min_w"])
            room_w = min(room_w, usable_width - WALL)
            
            # RIGHT SIDE: Must be to the RIGHT of corridor
            room_x = corridor_x + corridor_width + WALL
            room_y = right_y + WALL
            
            # CRITICAL: Hard boundaries - PRIORITY: STAY WITHIN PLOT
            # Constrain to plot depth FIRST
            if room_y + room_h > plot_d:
                room_h = plot_d - room_y - WALL
            
            # Then constrain to zone
            if room_y + room_h > zone_y + zone_h:
                room_h = zone_y + zone_h - room_y - WALL
            
            # Constrain to right boundary (after corridor)
            max_right_x = plot_w - WALL
            if room_x + room_w > max_right_x:
                room_w = max_right_x - room_x
            
            # Ensure minimum size
            room_h = max(room_h, 5)
            room_w = max(room_w, 5)
            
            # Final safety check - clamp all values
            room_y = max(WALL, min(room_y, plot_d - room_h - WALL))
            room_x = max(corridor_x + corridor_width + WALL, min(room_x, plot_w - room_w - WALL))
            room_w = min(room_w, plot_w - room_x - WALL)
            room_h = min(room_h, plot_d - room_y - WALL)
            
            if room_w >= 4 and room_h >= 4:
                layout.append(RoomLayout(
                    name=room.name,
                    x=round(room_x, 2),
                    y=round(room_y, 2),
                    width=round(room_w, 2),
                    height=round(room_h, 2),
                    zone=zone_name,
                    natural_light=room.natural_light
                ))
            
            right_y += room_h + WALL
        
        zone_y += zone_h
    
    # ===== ADD CIRCULATION =====
    # Add corridor
    layout.append(RoomLayout(
        name="Corridor",
        x=round(corridor_x, 2),
        y=0,
        width=corridor_width,
        height=plot_d,
        zone="circulation"
    ))
    
    # Add foyer
    layout.append(RoomLayout(
        name="Foyer",
        x=0.5,
        y=plot_d - 4.5,
        width=6.5,
        height=4,
        zone="public"
    ))
    
    # ===== OVERLAP DETECTION =====
    overlaps = check_overlaps(layout)
    if overlaps:
        print(f"⚠️  WARNING: {len(overlaps)} overlaps detected:")
        for r1, r2 in overlaps:
            print(f"   - {r1} overlaps with {r2}")
    
    return layout
