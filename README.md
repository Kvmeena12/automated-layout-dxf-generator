# AI Floor Plan Generator (AutoCAD DXF)

## 🔗 Repository
[https://github.com/Kvmeena12/automated-layout-dxf-generator](https://automated-layout-dxf-generator.streamlit.app/)

---

## Problem
Convert unstructured architectural brief into AutoCAD-ready floor plan.

---

## Solution
This system:
- Parses input text
- Generates structured layout
- Applies zoning (public/private/service)
- Adds corridor for circulation
- Places doors & windows
- Outputs DXF file

---

## Tech Stack
- Python
- ezdxf
- Rule-based layout engine

---

## Features
- 2BHK / 3BHK / 4BHK support
- Corridor-based design
- Automatic door/window placement
- Editable DXF output

---

## Tested: 
- Input : Design a 2BHK floor plan (900 sq ft 1200 sq ft) using STRICT HARD CONSTRAINTS.

HARD AREA CONSTRAINTS (NON-NEGOTIABLE)

- Living Room: MIN 150 sq ft (HIGHEST PRIORITY)
- Master Bedroom: MIN 120 sq ft + attached bathroom (40 sq ft)
- Second Bedroom: MIN 100 sq ft
- Kitchen: EXACT 90 sq ft
- Common Bathroom: MIN 40 sq ft
- Balcony: MIN 50 sq ft

SPACE CONTROL (CRITICAL)
- TOTAL circulation MUST be ≤ 80 sq ft
- Corridor width MUST be ≤ 4 ft
- REMOVE central corridor layout
- Use direct room-to-room connectivity
- Merge foyer into living room (NO separate foyer)


AUTO-ADJUSTMENT RULE
If space exceeds limit:
1. Reduce corridor FIRST
2. Remove foyer
3. Compact bedroom shapes
4. NEVER reduce living room or master bedroom below minimum

LAYOUT STRATEGY (MANDATORY)
- Entrance → Living Room (direct entry)
- Kitchen adjacent to living
- Bedrooms placed on one side (clustered)
- Bathrooms attached to walls for plumbing efficiency
- Avoid central spine corridor


VALIDATION STEP (VERY IMPORTANT):
Before final output:
- Recalculate all room areas
- Ensure ALL constraints satisfied
- If ANY constraint fails → regenerate layout


OUTPUT :
- Label all rooms with area
- Show dimensions
- Show North direction
- Show efficiency %

- output:
- <img width="696" height="503" alt="image" src="https://github.com/user-attachments/assets/8bbb301c-27af-4ee2-88a4-11e108a582e9" />


