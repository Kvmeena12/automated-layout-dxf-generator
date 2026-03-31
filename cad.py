import ezdxf
from ezdxf.enums import TextEntityAlignment
from models import RoomLayout, StructuredBrief
from config import DXF_LAYERS
from typing import List

# AutoCAD color index — these render cleanly in all viewers
# Full list: gohtx.com/acadcolors.php
ZONE_COLORS = {
    "public":  "230,230,180",   # pale yellow
    "service": "180,230,180",   # pale green
    "private": "180,210,240",   # pale blue
}

ZONE_ACI = {
    "public":  8,   # light gray
    "service": 3,   # green (soft)
    "private": 5,   # blue (soft)
}

ZONE_LABEL = {
    "public":  "PUBLIC ZONE",
    "service": "SERVICE ZONE",
    "private": "PRIVATE ZONE",
}


def add_solid_hatch(msp, x, y, w, h, color_index, layer):
   
    return 

from ezdxf.enums import TextEntityAlignment

def add_label(msp, text, x, y, height, layer, color=7, align=TextEntityAlignment.MIDDLE_CENTER):
    t = msp.add_text(
        text,
        dxfattribs={
            "layer": layer,
            "height": height,
            "color": color
        }
    )
    t.set_placement((x, y), align=align)
    return t

# Replace the door section inside the "for room in layout" loop with this:
def add_door(msp, room, wall="bottom"):
    x, y, w, h = room.x, room.y, room.width, room.height
    door_w = min(2.8, w * 0.28)
    

    if wall == "bottom" and w >= 4.0:
        dx = x + (w - door_w) / 2
        msp.add_arc(
            center=(dx, y), radius=door_w,
            start_angle=0, end_angle=90,
            dxfattribs={"layer": "DOORS", "lineweight": 20}
        )
        msp.add_line((dx, y), (dx + door_w, y),
            dxfattribs={"layer": "DOORS", "lineweight": 20})
    

    elif wall == "left" and h >= 4.0:
        door_w = min(2.8, h * 0.28)
        dy = y + (h - door_w) / 2

        msp.add_arc(
        center=(x, dy),
        radius=door_w,
        start_angle=180,
        end_angle=270,
        dxfattribs={"layer": "DOORS", "lineweight": 20}
    )

        msp.add_line(
        (x, dy), (x, dy + door_w),
        dxfattribs={"layer": "DOORS", "lineweight": 20}
    )

def add_main_entrance(msp, room):
    x, y, w, h = room.x, room.y, room.width, room.height

    # Bottom center entrance
    if w >= 6.0:
        door_w = min(3.5, w * 0.3)
        dx = x + (w - door_w) / 2

        msp.add_arc(
            center=(dx, y),
            radius=door_w,
            start_angle=0,
            end_angle=90,
            dxfattribs={"layer": "DOORS", "lineweight": 30}
        )

        msp.add_line(
            (dx, y), (dx + door_w, y),
            dxfattribs={"layer": "DOORS", "lineweight": 30}
        )
def add_smart_windows(msp, room, plot_w, plot_h):
    x, y, w, h = room.x, room.y, room.width, room.height

    # Only place window if room touches outer boundary

    # TOP WALL
    if y + h >= plot_h - 0.1:
        win_w = min(w * 0.5, 5.0)
        win_x = x + (w - win_w) / 2
        win_y = y + h

        msp.add_line((win_x, win_y), (win_x + win_w, win_y),
                     dxfattribs={"layer": "WINDOWS", "lineweight": 40})

    # BOTTOM WALL
    elif y <= 0.1:
        win_w = min(w * 0.5, 5.0)
        win_x = x + (w - win_w) / 2
        win_y = y

        msp.add_line((win_x, win_y), (win_x + win_w, win_y),
                     dxfattribs={"layer": "WINDOWS", "lineweight": 40})

    # LEFT WALL
    elif x <= 0.1:
        win_h = min(h * 0.5, 5.0)
        win_y = y + (h - win_h) / 2
        win_x = x

        msp.add_line((win_x, win_y), (win_x, win_y + win_h),
                     dxfattribs={"layer": "WINDOWS", "lineweight": 40})

    # RIGHT WALL
    elif x + w >= plot_w - 0.1:
        win_h = min(h * 0.5, 5.0)
        win_y = y + (h - win_h) / 2
        win_x = x + w

        msp.add_line((win_x, win_y), (win_x, win_y + win_h),
                     dxfattribs={"layer": "WINDOWS", "lineweight": 40})
def create_dxf(brief: StructuredBrief, layout: List[RoomLayout], output_path: str):
    doc = ezdxf.new(dxfversion='R2010')
    doc.units = 2  # Feet
    msp = doc.modelspace()

    # ── Create layers ──────────────────────────────────────────────────
    for layer_name, color_index in DXF_LAYERS.items():
        doc.layers.add(name=layer_name, color=color_index)

    doc.layers.add(name="HATCH_PUBLIC",  color=51)
    doc.layers.add(name="HATCH_SERVICE", color=92)
    doc.layers.add(name="HATCH_PRIVATE", color=150)

    pw = brief.plot_width_ft
    pd = brief.plot_depth_ft

    # ── Plot outer boundary ────────────────────────────────────────────
    msp.add_lwpolyline(
        [(0, 0), (pw, 0), (pw, pd), (0, pd), (0, 0)],
        dxfattribs={"layer": "WALLS", "lineweight": 70, "closed": True}
    )

    # ── Draw each room ─────────────────────────────────────────────────
    for room in layout:
        x, y, w, h = room.x, room.y, room.width, room.height
        if w < 1.0 or h < 1.0:
            continue
        zone      = room.zone
        aci_color = ZONE_ACI.get(zone, 7)
        hatch_layer = f"HATCH_{zone.upper()}"
        
        # 1. Solid color fill
        add_solid_hatch(msp, x, y, w, h, aci_color, hatch_layer)
        # 2. Room wall outline
        msp.add_lwpolyline(
        [(x, y), (x + w, y), (x + w, y + h), (x, y + h), (x, y)],
        dxfattribs={"layer": "WALLS", "lineweight": 35, "closed": True}
    )
        # 3. Room name
        cx = x + w / 2
        cy = y + h / 2
        name_h = max(0.9, min(w * 0.07, h * 0.11, 1.8))
        add_label(msp, room.name.upper(), cx, cy + name_h * 0.7,
              name_h, "LABELS")

        # 4. Area
        area_val = round(w * h, 0)
        add_label(msp, f"{area_val:.0f} sqft", cx, cy - name_h * 0.3,
              name_h * 0.6, "LABELS")
        if "foyer" in room.name.lower():
            add_main_entrance(msp, room)
        
        elif "living" in room.name.lower():
            add_main_entrance(msp, room)
            
        elif any(k in room.name.lower() for k in ["bath", "toilet", "wash"]):
            x, y, w, h = room.x, room.y, room.width, room.height
            door_w = min(2.5, w * 0.25)
            dx = x + w*0.5-door_w/2
            dy=y+0.01
            msp.add_arc(
        center=(dx, y),
        radius=door_w,
        start_angle=180,
        end_angle=270,
        dxfattribs={"layer": "DOORS", "lineweight": 20}
    )
            msp.add_line(
        (dx, y), (dx + door_w, y),
        dxfattribs={"layer": "DOORS", "lineweight": 20}
    )
        elif room.zone == "private":
            add_door(msp, room, wall="bottom")
        
        else:
            add_door(msp, room, wall="bottom")

        # ✅ SMART WINDOWS
        add_smart_windows(msp, room, pw, pd)
        # 7. Dimension
        if w >= 5.0:
            try:
                msp.add_linear_dim(
                base=(x, y - 2.2),
                p1=(x, y),
                p2=(x + w, y),
                dxfattribs={"layer": "DIMENSIONS"}
            ).render()
            except Exception:
                pass

    # ── Zone legend (right side) ───────────────────────────────────────
    lx = pw + 2.5
    ly = pd

    add_label(msp, "ZONE LEGEND", lx + 2, ly - 1.0, 1.1, "LABELS",
              align=TextEntityAlignment.LEFT)

    # Separator line
    msp.add_line(
        (lx, ly - 1.8), (lx + 12, ly - 1.8),
        dxfattribs={"layer": "WALLS", "lineweight": 15}
    )

    legend_data = [
        ("PUBLIC ZONE",  "Living, Dining, Kitchen",  51),
        ("PRIVATE ZONE", "Bedrooms, Bathrooms",      150),
        ("SERVICE ZONE", "Utility, Balcony, Store",  92),
    ]

    for i, (name, desc, color) in enumerate(legend_data):
        row_y = ly - 3.5 - (i * 3.2)

        # Color swatch box
        add_solid_hatch(msp, lx, row_y, 1.8, 1.4, color, "LABELS")
        msp.add_lwpolyline(
            [(lx, row_y), (lx+1.8, row_y),
             (lx+1.8, row_y+1.4), (lx, row_y+1.4), (lx, row_y)],
            dxfattribs={"layer": "WALLS", "lineweight": 15}
        )

        # Zone name
        add_label(msp, name, lx + 2.2, row_y + 0.9,
                  0.75, "LABELS", align=TextEntityAlignment.LEFT)
        # Description
        add_label(msp, desc, lx + 2.2, row_y + 0.2,
                  0.55, "LABELS", align=TextEntityAlignment.LEFT)

    # ── North arrow (simple) ───────────────────────────────────────────
    nx, ny = pw + 3.5, 4.0
    msp.add_line((nx, ny), (nx, ny + 3),
                 dxfattribs={"layer": "LABELS", "lineweight": 25})
    msp.add_line((nx, ny + 3), (nx - 0.6, ny + 1.5),
                 dxfattribs={"layer": "LABELS"})
    msp.add_line((nx, ny + 3), (nx + 0.6, ny + 1.5),
                 dxfattribs={"layer": "LABELS"})
    add_label(msp, "N", nx, ny + 3.8, 0.9, "LABELS")

    # ── Title block ────────────────────────────────────────────────────
    # Border box
    msp.add_lwpolyline(
        [(0, -1), (pw, -1), (pw, -7), (0, -7), (0, -1)],
        dxfattribs={"layer": "WALLS", "lineweight": 30}
    )
    msp.add_line((0, -4), (pw, -4),
                 dxfattribs={"layer": "WALLS", "lineweight": 15})

    add_label(msp, " ",
              pw / 2, -2.3, 1.3, "LABELS")
    add_label(msp,
              f"Total Area: {brief.total_area_sqft:.0f} sqft   |   "
              f"Plot: {pw:.0f} ft x {pd:.0f} ft   |   Scale: NTS",
              pw / 2, -5.3, 0.65, "LABELS")

    doc.saveas(output_path)
    print(f"[OK] DXF saved → {output_path}")
    return output_path

