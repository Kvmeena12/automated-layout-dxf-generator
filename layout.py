from models import StructuredBrief, RoomLayout
from typing import List
import math
from models import RoomLayout

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
def sort_rooms_by_priority(layout):
    return sorted(
        layout,
        key=lambda r: ROOM_PRIORITY.get(r.name.lower(), 1),
        reverse=True
    )
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

def generate_layout(brief: StructuredBrief) -> List[RoomLayout]:
  
    plot_w = brief.plot_width_ft
    plot_d = brief.plot_depth_ft
    corridor_width = 4
    corridor_x = plot_w / 2 - corridor_width / 2
    usable_width = plot_w - corridor_width

    WALL = 0.5
    CORRIDOR = 2.5

    # Zone order: public at bottom (y=0), service middle, private at top
    # This matches architectural convention — entry/living at front
    zone_order = ["public", "service", "private"]

    zones = {"public": [], "service": [], "private": []}
    for room in brief.rooms:
        zones[room.zone].append(room)

    layout: List[RoomLayout] = []
    zone_y = 0.0

    total_area = sum(r.area_sqft for r in brief.rooms)
    usable_depth = plot_d - (len([z for z in zone_order if zones[z]]) - 1) * CORRIDOR
    total_zone_height=0
    zone_heights={}
    for zone in zone_order:
        rooms = zones[zone]
        if not rooms:
            continue

        zone_area = sum(r.area_sqft for r in rooms)
        zone_h = max(8.0, (zone_area / total_area) * plot_d)
        zone_heights[zone] = zone_h
        total_zone_height += zone_h
    scale_h = plot_d / total_zone_height if total_zone_height > plot_d else 1.0

        # Sort rooms by area descending — largest room gets more space
    rooms_sorted = sorted(rooms, key=lambda r: r.area_sqft, reverse=True)

        # Place rooms in rows of 2
    cols = 2 if len(rooms_sorted) > 1 else 1
    rows_count = math.ceil(len(rooms_sorted) / cols)

        for i, room in enumerate(rooms_sorted):
            col = i % cols
            row = i // cols

            # Row height proportional to rooms in that row vs zone total
            row_rooms = [rooms_sorted[j] for j in range(len(rooms_sorted)) if j // cols == row]
            row_area = sum(r.area_sqft for r in row_rooms)
            row_h = max(6.0, (row_area / zone_area) * zone_h)
            # Column width proportional to room area vs row total
            row_total_area = sum(r.area_sqft for r in row_rooms)
            room_w_fraction = room.area_sqft / row_total_area if row_total_area > 0 else 1.0 / cols
            rw = max(5.0, usable_width * room_w_fraction - WALL * 2)

            # X position: accumulate widths of previous rooms in same row
            x_offset = 0.0
            for j in range(i):
                if j // cols == row and j % cols < col:
                    prev_room = rooms_sorted[j]
                    prev_fraction = prev_room.area_sqft / row_total_area
                    x_offset += usable_width * prev_fraction

            rx = x_offset + WALL
        
            # Calculate cumulative row y within zone
            ry_in_zone = 0.0
            for r_idx in range(row):
                prev_row_rooms = [rooms_sorted[j] for j in range(len(rooms_sorted)) if j // cols == r_idx]
                prev_row_area = sum(r.area_sqft for r in prev_row_rooms)
                ry_in_zone += max(6.0, (prev_row_area / zone_area) * zone_h)

            ry = zone_y + ry_in_zone + WALL
            if ry > plot_d:
                continue  # skip invalid room
            rh = row_h - WALL
            if col==0:
                rw=min(rw,corridor_x - rx - WALL)
            else:
                rw=min(rw,plot_w - rx - WALL)
            if rw<3.0:
                continue
            if rx < 0:
                rx = WALL
            if ry < 0:
                ry = WALL
            if rx + rw > plot_w:
                rw = plot_w - rx - WALL
            if ry + rh > plot_d:
                rh = plot_d - ry - WALL
            rw = max(3, rw)
            rh = max(3, rh)

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
