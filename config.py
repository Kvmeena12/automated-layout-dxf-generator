# Constants (min room sizes, layer names, etc.)
# Minimum room sizes (sq ft)
MIN_ROOM_SIZES = {
    "bedroom": 100,
    "master bedroom": 140,
    "bathroom": 35,
    "kitchen": 80,
    "living room": 150,
    "dining": 80,
    "study": 60,
    "utility": 30,
}

CIRCULATION_FACTOR = 0.82  # 18% for walls, corridors, structure

# DXF Layer definitions: (name, color_index)
# AutoCAD color index: 1=red, 2=yellow, 3=green, 4=cyan, 5=blue, 6=magenta, 7=white
DXF_LAYERS = {
    "WALLS":       7,   # white/black
    "ROOMS":       3,   # green (room outlines)
    "LABELS":      3,   # white/black (text)
    "DIMENSIONS":  4,   # cyan
    "DOORS":       1,   # red
    "WINDOWS":     5,   # blue
    "FURNITURE":   6,   # magenta
}

SCALE = 12.0  # 1 foot = 12 DXF units (inches in CAD)