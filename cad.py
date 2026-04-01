import ezdxf
from ezdxf.enums import TextEntityAlignment
from ezdxf.colors import RGB
from models import RoomLayout, StructuredBrief
from config import DXF_LAYERS
from typing import List

# True RGB colors — renders correctly in ALL viewers
ZONE_RGB = {
    "public":  (255, 255, 200),   # warm yellow
    "service": (200, 240, 200),   # soft green
    "private": (200, 220, 255),   # soft blue
}

WALL_THICKNESS = 0.4   # feet (~5 inches)
FURNITURE_LAYER = "FURNITURE"


# ── Solid hatch with true RGB color ───────────────────────────────────
def add_solid_hatch(msp, x, y, w, h, zone, layer):
    rgb = ZONE_RGB.get(zone, (220, 220, 220))
    hatch = msp.add_hatch(dxfattribs={"layer": layer})
    hatch.set_solid_fill()
    hatch.dxf.true_color = RGB(rgb[0], rgb[1], rgb[2])
    hatch.paths.add_polyline_path(
        [(x, y), (x + w, y), (x + w, y + h), (x, y + h)],
        is_closed=True
    )


# ── Text label helper ──────────────────────────────────────────────────
def add_label(msp, text, x, y, height, layer, color=7,
              align=TextEntityAlignment.MIDDLE_CENTER):
    t = msp.add_text(
        text,
        dxfattribs={"layer": layer, "height": height, "color": color}
    )
    t.set_placement((x, y), align=align)
    return t


# ── Double-line wall box ───────────────────────────────────────────────
def add_wall_box(msp, x, y, w, h, layer="WALLS"):
    msp.add_lwpolyline(
        [(x, y), (x+w, y), (x+w, y+h), (x, y+h), (x, y)],
        dxfattribs={"layer": layer, "lineweight": 40, "closed": True}
    )
    t = WALL_THICKNESS
    if w > t * 3 and h > t * 3:
        msp.add_lwpolyline(
            [(x+t, y+t), (x+w-t, y+t), (x+w-t, y+h-t), (x+t, y+h-t), (x+t, y+t)],
            dxfattribs={"layer": layer, "lineweight": 15, "closed": True}
        )


# ── Door placement ─────────────────────────────────────────────────────
def add_door(msp, room, wall="bottom"):
    x, y, w, h = room.x, room.y, room.width, room.height

    if wall == "bottom" and w >= 4.0:
        door_w = min(2.8, w * 0.28)
        dx = x + (w - door_w) / 2
        msp.add_arc(center=(dx, y), radius=door_w,
                    start_angle=0, end_angle=90,
                    dxfattribs={"layer": "DOORS", "lineweight": 20})
        msp.add_line((dx, y), (dx + door_w, y),
                     dxfattribs={"layer": "DOORS", "lineweight": 20})

    elif wall == "right" and h >= 4.0:
        door_w = min(2.8, h * 0.28)
        dy = y + (h - door_w) / 2
        msp.add_arc(center=(x + w, dy), radius=door_w,
                    start_angle=90, end_angle=180,
                    dxfattribs={"layer": "DOORS", "lineweight": 20})
        msp.add_line((x+w, dy), (x+w, dy + door_w),
                     dxfattribs={"layer": "DOORS", "lineweight": 20})

    elif wall == "left" and h >= 4.0:
        door_w = min(2.8, h * 0.28)
        dy = y + (h - door_w) / 2
        msp.add_arc(center=(x, dy), radius=door_w,
                    start_angle=0, end_angle=90,
                    dxfattribs={"layer": "DOORS", "lineweight": 20})
        msp.add_line((x, dy), (x, dy + door_w),
                     dxfattribs={"layer": "DOORS", "lineweight": 20})

    elif wall == "top" and w >= 4.0:
        door_w = min(2.8, w * 0.28)
        dx = x + (w - door_w) / 2
        msp.add_arc(center=(dx, y + h), radius=door_w,
                    start_angle=270, end_angle=360,
                    dxfattribs={"layer": "DOORS", "lineweight": 20})
        msp.add_line((dx, y+h), (dx + door_w, y+h),
                     dxfattribs={"layer": "DOORS", "lineweight": 20})


# ── Smart windows — outer walls only ──────────────────────────────────
def add_smart_windows(msp, room, plot_w, plot_h):
    x, y, w, h = room.x, room.y, room.width, room.height
    placed = False

    def draw_h(wx, wy, ww):
        msp.add_line((wx, wy), (wx+ww, wy),
                     dxfattribs={"layer": "WINDOWS", "lineweight": 40})
        msp.add_line((wx+0.2, wy-0.3), (wx+ww-0.2, wy-0.3),
                     dxfattribs={"layer": "WINDOWS", "lineweight": 20})
        msp.add_line((wx+0.2, wy-0.6), (wx+ww-0.2, wy-0.6),
                     dxfattribs={"layer": "WINDOWS", "lineweight": 12})
        for ex in [wx+0.2, wx+ww-0.2]:
            msp.add_line((ex, wy), (ex, wy-0.6),
                         dxfattribs={"layer": "WINDOWS", "lineweight": 12})

    def draw_v(wx, wy, wh):
        msp.add_line((wx, wy), (wx, wy+wh),
                     dxfattribs={"layer": "WINDOWS", "lineweight": 40})
        msp.add_line((wx+0.3, wy+0.2), (wx+0.3, wy+wh-0.2),
                     dxfattribs={"layer": "WINDOWS", "lineweight": 20})
        msp.add_line((wx+0.6, wy+0.2), (wx+0.6, wy+wh-0.2),
                     dxfattribs={"layer": "WINDOWS", "lineweight": 12})

    if abs((y + h) - plot_h) < 0.5 and not placed:
        win_w = min(w * 0.55, 6.0)
        draw_h(x + (w - win_w) / 2, y + h, win_w)
        placed = True

    if y < 0.5 and not placed:
        win_w = min(w * 0.55, 6.0)
        draw_h(x + (w - win_w) / 2, y + 0.6, win_w)
        placed = True

    if x < 0.5 and not placed:
        win_h = min(h * 0.55, 6.0)
        draw_v(x, y + (h - win_h) / 2, win_h)
        placed = True

    if abs((x + w) - plot_w) < 0.5 and not placed:
        win_h = min(h * 0.55, 6.0)
        draw_v(x + w - 0.6, y + (h - win_h) / 2, win_h)


# ── Furniture symbols ──────────────────────────────────────────────────
def add_furniture(msp, room):
    x, y, w, h = room.x, room.y, room.width, room.height
    name = room.name.lower()

    if "master bedroom" in name or ("bedroom" in name and w >= 8):
        # Double bed
        bed_w = min(w * 0.55, 6.0)
        bed_h = min(h * 0.45, 7.0)
        bx = x + (w - bed_w) / 2
        by = y + (h - bed_h) / 2
        msp.add_lwpolyline(
            [(bx, by), (bx+bed_w, by), (bx+bed_w, by+bed_h), (bx, by+bed_h), (bx, by)],
            dxfattribs={"layer": FURNITURE_LAYER, "lineweight": 18}
        )
        msp.add_line((bx, by+bed_h*0.8), (bx+bed_w, by+bed_h*0.8),
                     dxfattribs={"layer": FURNITURE_LAYER, "lineweight": 25})
        for px in [bx + bed_w*0.15, bx + bed_w*0.55]:
            msp.add_lwpolyline(
                [(px, by+bed_h*0.82), (px+bed_w*0.28, by+bed_h*0.82),
                 (px+bed_w*0.28, by+bed_h*0.95), (px, by+bed_h*0.95), (px, by+bed_h*0.82)],
                dxfattribs={"layer": FURNITURE_LAYER, "lineweight": 10}
            )

    elif "bedroom" in name:
        # Single bed
        bed_w = min(w * 0.5, 4.5)
        bed_h = min(h * 0.45, 6.5)
        bx = x + (w - bed_w) / 2
        by = y + h * 0.1
        msp.add_lwpolyline(
            [(bx, by), (bx+bed_w, by), (bx+bed_w, by+bed_h), (bx, by+bed_h), (bx, by)],
            dxfattribs={"layer": FURNITURE_LAYER, "lineweight": 18}
        )
        msp.add_line((bx, by+bed_h*0.8), (bx+bed_w, by+bed_h*0.8),
                     dxfattribs={"layer": FURNITURE_LAYER, "lineweight": 22})

    elif "living" in name:
        # L-sofa
        sw = min(w * 0.7, 8.0)
        sh = min(h * 0.22, 2.8)
        sx, sy = x + w*0.1, y + h*0.55
        msp.add_lwpolyline(
            [(sx, sy), (sx+sw, sy), (sx+sw, sy+sh), (sx, sy+sh), (sx, sy)],
            dxfattribs={"layer": FURNITURE_LAYER, "lineweight": 18}
        )
        msp.add_lwpolyline(
            [(sx, sy+sh), (sx+sh, sy+sh), (sx+sh, sy+sh*2.0), (sx, sy+sh*2.0), (sx, sy+sh)],
            dxfattribs={"layer": FURNITURE_LAYER, "lineweight": 18}
        )
        # Coffee table
        tw = min(w * 0.3, 4.0)
        th = min(h * 0.12, 2.0)
        tx = x + (w - tw) / 2
        ty = y + h * 0.3
        msp.add_lwpolyline(
            [(tx, ty), (tx+tw, ty), (tx+tw, ty+th), (tx, ty+th), (tx, ty)],
            dxfattribs={"layer": FURNITURE_LAYER, "lineweight": 12}
        )

    elif "kitchen" in name:
        cw = w - 1.0
        msp.add_lwpolyline(
            [(x+0.5, y+0.4), (x+0.5+cw, y+0.4),
             (x+0.5+cw, y+2.2), (x+0.5, y+2.2), (x+0.5, y+0.4)],
            dxfattribs={"layer": FURNITURE_LAYER, "lineweight": 18}
        )
        msp.add_circle(center=(x + w*0.6, y+1.3), radius=0.6,
                       dxfattribs={"layer": FURNITURE_LAYER, "lineweight": 12})
        for hx in [x + w*0.25, x + w*0.4]:
            msp.add_circle(center=(hx, y+1.3), radius=0.4,
                           dxfattribs={"layer": FURNITURE_LAYER, "lineweight": 10})

    elif "dining" in name:
        tw = min(w * 0.55, 5.0)
        th = min(h * 0.45, 4.0)
        tx = x + (w - tw) / 2
        ty = y + (h - th) / 2
        msp.add_lwpolyline(
            [(tx, ty), (tx+tw, ty), (tx+tw, ty+th), (tx, ty+th), (tx, ty)],
            dxfattribs={"layer": FURNITURE_LAYER, "lineweight": 18}
        )
        chair_w = min(tw / 3, 1.5)
        for i in range(2):
            cx2 = tx + tw*0.2 + i*tw*0.45
            for cy_off in [ty+th+0.1, ty-0.8]:
                msp.add_lwpolyline(
                    [(cx2, cy_off), (cx2+chair_w, cy_off),
                     (cx2+chair_w, cy_off+0.7), (cx2, cy_off+0.7), (cx2, cy_off)],
                    dxfattribs={"layer": FURNITURE_LAYER, "lineweight": 10}
                )

    elif any(k in name for k in ["bath", "toilet", "wash"]):
        msp.add_ellipse(
            center=(x + w*0.25, y + h*0.75),
            major_axis=(0, 0.9), ratio=0.6,
            dxfattribs={"layer": FURNITURE_LAYER, "lineweight": 12}
        )
        msp.add_lwpolyline(
            [(x+0.2, y+h*0.88), (x+1.8, y+h*0.88),
             (x+1.8, y+h*0.98), (x+0.2, y+h*0.98), (x+0.2, y+h*0.88)],
            dxfattribs={"layer": FURNITURE_LAYER, "lineweight": 15}
        )
        msp.add_lwpolyline(
            [(x+0.3, y+0.3), (x+1.8, y+0.3),
             (x+1.8, y+1.6), (x+0.3, y+1.6), (x+0.3, y+0.3)],
            dxfattribs={"layer": FURNITURE_LAYER, "lineweight": 15}
        )
        msp.add_circle(center=(x+1.05, y+0.95), radius=0.35,
                       dxfattribs={"layer": FURNITURE_LAYER, "lineweight": 10})

    elif "study" in name:
        dw = min(w * 0.55, 5.0)
        dh = min(h * 0.2, 2.2)
        msp.add_lwpolyline(
            [(x+0.4, y+h-dh-0.4), (x+0.4+dw, y+h-dh-0.4),
             (x+0.4+dw, y+h-0.4), (x+0.4, y+h-0.4), (x+0.4, y+h-dh-0.4)],
            dxfattribs={"layer": FURNITURE_LAYER, "lineweight": 18}
        )
        msp.add_circle(center=(x + 0.4 + dw/2, y + h - dh - 1.2),
                       radius=0.7,
                       dxfattribs={"layer": FURNITURE_LAYER, "lineweight": 12})

    elif "balcony" in name:
        for pts in [
            [(x+0.3, y+0.3), (x+w-0.3, y+0.3)],
            [(x+0.3, y+0.3), (x+0.3, y+h-0.3)],
            [(x+w-0.3, y+0.3), (x+w-0.3, y+h-0.3)],
        ]:
            msp.add_line(*pts, dxfattribs={"layer": FURNITURE_LAYER, "lineweight": 25})


# ── Main DXF creation function ─────────────────────────────────────────
def create_dxf(brief: StructuredBrief, layout: List[RoomLayout], output_path: str):
    doc = ezdxf.new(dxfversion='R2010')
    doc.units = 2  # Feet
    msp = doc.modelspace()

    # Global dimension style settings
    std = doc.dimstyles.get("Standard")
    std.dxf.dimtxt = 0.8
    std.dxf.dimasz = 0.6
    std.dxf.dimexo = 0.3
    std.dxf.dimexe = 0.4
    std.dxf.dimgap = 0.25

    # Standard layers
    for layer_name, color_index in DXF_LAYERS.items():
        doc.layers.add(name=layer_name, color=color_index)

    doc.layers.add(name="HATCH_PUBLIC",  color=2)
    doc.layers.add(name="HATCH_SERVICE", color=3)
    doc.layers.add(name="HATCH_PRIVATE", color=4)
    doc.layers.add(name=FURNITURE_LAYER, color=6)

    pw = brief.plot_width_ft
    pd = brief.plot_depth_ft

    # Plot outer boundary — double wall
    for lw, offset in [(70, 0), (30, WALL_THICKNESS)]:
        o = offset
        msp.add_lwpolyline(
            [(o, o), (pw-o, o), (pw-o, pd-o), (o, pd-o), (o, o)],
            dxfattribs={"layer": "WALLS", "lineweight": lw, "closed": True}
        )

    # Draw each room
    for room in layout:
        x, y, w, h = room.x, room.y, room.width, room.height
        if w < 1.0 or h < 1.0:
            continue

        zone        = room.zone
        hatch_layer = f"HATCH_{zone.upper()}"

        # Color fill
        add_solid_hatch(msp, x, y, w, h, zone, hatch_layer)

        # Wall outline
        add_wall_box(msp, x, y, w, h)

        # Room name + area
        cx = x + w / 2
        cy = y + h / 2
        name_h = max(0.7, min(w * 0.07, h * 0.10, 1.6))
        add_label(msp, room.name.upper(), cx, cy + name_h * 0.7, name_h, "LABELS")
        area_val = round(w * h, 0)
        add_label(msp, f"{area_val:.0f} sqft", cx, cy - name_h * 0.3,
                  name_h * 0.6, "LABELS")

        # Door placement by room type
        name = room.name.lower()
        if "foyer" in name or "entrance" in name:
            add_door(msp, room, wall="bottom")
        elif "living" in name:
            add_door(msp, room, wall="bottom")
        elif any(k in name for k in ["bath", "toilet", "wash"]):
            add_door(msp, room, wall="left" if w < h else "bottom")
        elif zone == "private":
            add_door(msp, room, wall="right" if x + w < pw * 0.6 else "left")
        else:
            add_door(msp, room, wall="bottom")

        # Smart windows
        if room.natural_light or zone in ["public", "private"]:
            add_smart_windows(msp, room, pw, pd)

        # Furniture
        add_furniture(msp, room)

        # Dimensions — width
        if w >= 4.0:
            try:
                msp.add_linear_dim(
                    base=(x, y - 2.5),
                    p1=(x, y), p2=(x + w, y),
                    dxfattribs={"layer": "DIMENSIONS"}
                ).render()
            except Exception:
                pass
        # Height
        if h >= 4.0:
            try:
                msp.add_linear_dim(
                    base=(x + w + 2.0, y),
                    p1=(x + w, y), p2=(x + w, y + h),
                    angle=90,
                    dxfattribs={"layer": "DIMENSIONS"}
                ).render()
            except Exception:
                pass

    # Zone legend
    lx = pw + 2.5
    ly = pd
    add_label(msp, "ZONE LEGEND", lx + 2, ly - 1.0, 1.1, "LABELS",
              align=TextEntityAlignment.LEFT)
    msp.add_line((lx, ly-1.8), (lx+13, ly-1.8),
                 dxfattribs={"layer": "WALLS", "lineweight": 15})

    for i, (zone_key, zname, desc) in enumerate([
        ("public",  "PUBLIC ZONE",  "Living, Dining, Kitchen, Study"),
        ("private", "PRIVATE ZONE", "Bedrooms, Bathrooms"),
        ("service", "SERVICE ZONE", "Utility, Balcony, Store"),
    ]):
        row_y = ly - 3.5 - (i * 3.2)
        add_solid_hatch(msp, lx, row_y, 2.0, 1.5, zone_key, "LABELS")
        msp.add_lwpolyline(
            [(lx, row_y), (lx+2.0, row_y),
             (lx+2.0, row_y+1.5), (lx, row_y+1.5), (lx, row_y)],
            dxfattribs={"layer": "WALLS", "lineweight": 15}
        )
        add_label(msp, zname, lx+2.4, row_y+1.0, 0.75, "LABELS",
                  align=TextEntityAlignment.LEFT)
        add_label(msp, desc, lx+2.4, row_y+0.25, 0.55, "LABELS",
                  align=TextEntityAlignment.LEFT)

    # North arrow
    nx, ny = pw + 4.0, 4.0
    msp.add_line((nx, ny), (nx, ny+3.0),
                 dxfattribs={"layer": "LABELS", "lineweight": 25})
    msp.add_line((nx, ny+3.0), (nx-0.7, ny+1.5),
                 dxfattribs={"layer": "LABELS"})
    msp.add_line((nx, ny+3.0), (nx+0.7, ny+1.5),
                 dxfattribs={"layer": "LABELS"})
    add_label(msp, "N", nx, ny+4.2, 1.0, "LABELS")

    # Space efficiency stats
    total_placed = sum(
        r.width * r.height for r in layout if r.width > 1 and r.height > 1
    )
    efficiency  = round(total_placed / brief.total_area_sqft * 100) if brief.total_area_sqft > 0 else 0
    circulation = round(brief.total_area_sqft - total_placed)

    # Title block
    msp.add_lwpolyline(
        [(0, -1.0), (pw, -1.0), (pw, -8.5), (0, -8.5), (0, -1.0)],
        dxfattribs={"layer": "WALLS", "lineweight": 30}
    )
    msp.add_line((0, -4.5), (pw, -4.5),
                 dxfattribs={"layer": "WALLS", "lineweight": 15})

    add_label(msp, "FLOOR PLAN  --  AI GENERATED",
              pw / 2, -2.5, 1.3, "LABELS")
    add_label(msp,
              f"Total Area: {brief.total_area_sqft:.0f} sqft   |   "
              f"Plot: {pw:.0f} ft x {pd:.0f} ft   |   Scale: NTS",
              pw / 2, -5.5, 0.65, "LABELS")
    add_label(msp,
              f"Usable: {total_placed:.0f} sqft   |   "
              f"Walls + Circulation: {circulation} sqft   |   "
              f"Efficiency: {efficiency}%",
              pw / 2, -7.0, 0.6, "LABELS")

    doc.saveas(output_path)
    print(f"[OK] DXF saved -> {output_path}")
    return output_path
