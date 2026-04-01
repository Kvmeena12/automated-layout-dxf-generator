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
- Input : 2BHK flat, 900 sq ft, living room minimum 200 sq ft, master bedroom 
minimum 150 sq ft, kitchen 100 sq ft, 2 bathrooms each 40 sq ft, 
balcony 50 sq ft, plot width 25ft, plot depth 40ft

- output:
- ![Click](https://github.com/user-attachments/assets/3cf69001-7147-4224-b23c-a7c7a83e08c3)

