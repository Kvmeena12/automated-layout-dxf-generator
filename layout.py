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
    corridor_width = 3.5
    return RoomLayout(
        name="Corridor",
        x=plot_w / 2 - corridor_width / 2,
        y=0,
        width=corridor_width,
        height=plot_h,
        zone="circulation"
    )

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
    corridor_width = 3.5
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
            
            room_x = WALL
            room_y = left_y + WALL
            
            # Hard boundaries
            if room_y + room_h > zone_y + zone_h:
                room_h = zone_y + zone_h - room_y - WALL
            
            room_h = max(room_h, get_min_dimensions(room.name)["min_h"])
            room_w = max(room_w, get_min_dimensions(room.name)["min_w"])
            
            # Ensure within bounds
            if room_x + room_w > corridor_x - WALL:
                room_w = corridor_x - room_x - WALL
            
            if room_w >= 5 and room_h >= 5:
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
            
            room_x = corridor_x + corridor_width + WALL
            room_y = right_y + WALL
            
            # Hard boundaries
            if room_y + room_h > zone_y + zone_h:
                room_h = zone_y + zone_h - room_y - WALL
            
            room_h = max(room_h, get_min_dimensions(room.name)["min_h"])
            room_w = max(room_w, get_min_dimensions(room.name)["min_w"])
            
            # Ensure within bounds
            if room_x + room_w > plot_w - WALL:
                room_w = plot_w - room_x - WALL
            
            if room_w >= 5 and room_h >= 5:
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
    
    return layout
