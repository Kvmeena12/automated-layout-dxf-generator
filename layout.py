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

def create_corridor(plot_w, plot_h):
    corridor_width = 4
    return RoomLayout(
        name="Corridor",
        x=plot_w / 2 - corridor_width / 2,
        y=0,
        width=corridor_width,
        height=plot_h,
        zone="circulation"
    )

def create_foyer():
    return RoomLayout(
        name="Foyer",
        x=0,
        y=0,
        width=6,
        height=4,
        zone="public"
    )
def get_room_weight(name):
    name = name.lower()

    if "living" in name:
        return 5
    elif "bedroom" in name:
        return 4
    elif "kitchen" in name:
        return 3
    elif "bath" in name:
        return 2
    else:
        return 1


def generate_layout(brief: StructuredBrief) -> List[RoomLayout]:

    plot_w = brief.plot_width_ft
    plot_d = brief.plot_depth_ft

    WALL = 0.5
    corridor_width = 3
    corridor_x = plot_w * 0.35
    usable_width = (plot_w - corridor_width) / 2

    zone_order = ["public", "service", "private"]

    zones = {"public": [], "service": [], "private": []}
    for room in brief.rooms:
        zones[room.zone].append(room)

    layout: List[RoomLayout] = []
    zone_y = 0.0

    total_area = sum(r.area_sqft for r in brief.rooms)

    # 🔥 STEP 1: Calculate zone heights
    total_zone_height = 0
    zone_heights = {}

    for zone in zone_order:
        rooms = zones[zone]
        if not rooms:
            continue

        zone_area = sum(r.area_sqft for r in rooms)
        zone_h = max(8.0, (zone_area / total_area) * plot_d)
        zone_heights[zone] = zone_h
        total_zone_height += zone_h

    # 🔥 STEP 2: Scale to fit plot
    scale_h = plot_d / total_zone_height if total_zone_height > plot_d else 1.0

    # 🔥 STEP 3: Place rooms
    for zone in zone_order:
        rooms = zones[zone]
        if not rooms:
            continue

        zone_h = zone_heights[zone] * scale_h
        zone_area = sum(r.area_sqft for r in rooms)
        
        rooms_sorted = sorted(rooms, key=lambda r: r.area_sqft, reverse=True)
        rooms_sorted = sorted(
    rooms_sorted,
    key=lambda r: 0 if "bath" in r.name.lower() else 1
)

        cols = 2 if len(rooms_sorted) > 1 else 1

        for i, room in enumerate(rooms_sorted):
            col = i % cols
            row = i // cols

            row_rooms = [r for j, r in enumerate(rooms_sorted) if j // cols == row]
            row_area = sum(r.area_sqft for r in row_rooms)

            row_h = max(6.0, (row_area / zone_area) * zone_h)

            row_total_area = sum(r.area_sqft for r in row_rooms)
            row_total_weight = sum(get_room_weight(r.name) for r in row_rooms)
            room_weight = get_room_weight(room.name)
            room_fraction = room_weight / row_total_weight

            rw = max(5.0, usable_width * room_fraction - WALL * 2)
            MIN_WIDTH = {
    "living": 12,
    "bedroom": 10,
    "kitchen": 8,
    "bathroom": 5
                )
            for key in MIN_WIDTH:
                if key in room.name.lower():
                    rw = max(rw, MIN_WIDTH[key])

            # X position
            x_offset = 0.0
            for j in range(i):
                if j // cols == row and j % cols < col:
                    prev = rooms_sorted[j]
                    x_offset += usable_width * (prev.area_sqft / row_total_area)

            rx = x_offset + WALL

            # Y position
            ry_in_zone = 0.0
            for r_idx in range(row):
                prev_row = [r for j, r in enumerate(rooms_sorted) if j // cols == r_idx]
                prev_area = sum(r.area_sqft for r in prev_row)
                ry_in_zone += max(6.0, (prev_area / zone_area) * zone_h)

            ry = zone_y + ry_in_zone + WALL
            rh = row_h - WALL

            # 🔥 WIDTH FIX (split by corridor)
            left_limit = corridor_x - WALL
            right_limit = corridor_x + corridor_width + WALL
            
            if col == 0:
                rx = WALL + x_offset
                rw = min(rw, left_limit - rx)
            else:
                rx = right_limit + x_offset
                rw = min(rw, plot_w - rx - WALL)

            # 🔥 HARD BOUNDARY CHECK
            if rx<0:
                rx=WALL
            if rx + rw > plot_w:
                rw = plot_w - rx - WALL

            if ry + rh > plot_d:
                rh = plot_d - ry - WALL

            if rw < 3:
                rw = 3
            if rh < 3:
                rh = 3
                
            
            layout.append(RoomLayout(
                name=room.name,
                x=round(rx, 2),
                y=round(ry, 2),
                width=round(rw, 2),
                height=round(rh, 2),
                zone=zone,
                natural_light=room.natural_light
            ))

        zone_y += zone_h

    # 🔥 ADD FOYER + CORRIDOR
    layout.insert(0, create_foyer())

    layout.append(RoomLayout(
        name="Corridor",
        x=round(corridor_x, 2),
        y=0,
        width=corridor_width,
        height=plot_d,
        zone="circulation"
    ))

    return layout
