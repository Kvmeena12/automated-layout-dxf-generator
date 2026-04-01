# Streamlit app + pipeline orchestrator
import streamlit as st
import tempfile
import os
from parser import parse_brief
from constraints import validate_and_normalize
from layout import generate_layout
from cad import create_dxf

st.set_page_config(page_title="Brief → Floor Plan", layout="centered")
st.title("AI Floor Plan Generator")
st.caption("Paste an architectural brief → download a DXF floor plan")

# Sample briefs for easy demo
SAMPLES = {
    "3BHK Standard": "3BHK, 1500 sq ft, open kitchen, 1 study, maximize natural light",
    "2BHK Compact": '''Design an optimized 2BHK flat floor plan with strict constraints.

Total Area: 900 sq ft  
Plot Size: 30 ft x 30 ft  
Shape: sqaure  


MANDATORY ROOM AREAS

- Living Room: 150–180 sq ft (PRIORITY, at entrance)
- Master Bedroom: 120–140 sq ft with attached bathroom (40 sq ft)
- Second Bedroom: 100–120 sq ft
- Kitchen: 90 sq ft (adjacent to living/dining)
- Common Bathroom: 40 sq ft (accessible from corridor/living)
- Balcony: 50 sq ft (attached to living room preferred)

SPACE OPTIMIZATION RULES

- Total circulation (corridor + passage) MUST be ≤ 80 sq ft
- Corridor width: 3 to 4 ft ONLY
- Efficiency MUST be ≥ 78%
- Avoid long central corridors
- Merge foyer into living room if needed (no separate foyer required)

LAYOUT LOGIC (VERY IMPORTANT)

- Entrance → Living Room → Bedrooms → Kitchen (logical flow)
- Public zone (Living) near entrance
- Private zone (Bedrooms) away from entrance
- Service zone (Kitchen + Bathrooms) grouped efficiently
- Bathrooms should share plumbing wall if possible


GEOMETRY & VALIDATION

- All rooms must be rectangular and non-overlapping
- Each room must display dimensions + area (sq ft)
- Maintain realistic wall thickness
- Ensure proper door placement and accessibility


VENTILATION & PRACTICALITY

- Each room must have at least one window
- Bathrooms must be on external walls OR ventilated
- Ensure furniture feasibility (bed, sofa, kitchen platform)

STRICT VALIDATION

Reject the layout if:
- Any room is missing
- Living room <150 sq ft
- Master bedroom <120 sq ft
- Any bathroom <35 sq ft
- Balcony <50 sq ft
- Circulation area >80 sq ft


OUTPUT FORMAT

- Labeled floor plan
- Each room clearly marked with name + area
- Include North direction
- Show dimensions of all rooms
- Display total usable area and efficiency''',
    "4BHK Luxury": "4BHK villa, 3000 sq ft, master bedroom with ensuite, formal living, family lounge, large kitchen, utility room",
}

sample_choice = st.selectbox("Or pick a sample brief:", ["Custom..."] + list(SAMPLES.keys()))
default_text = SAMPLES.get(sample_choice, "") if sample_choice != "Custom..." else ""

brief_text = st.text_area(
    "Architectural brief:",
    value=default_text,
    height=200,
    placeholder="e.g. 3BHK, 1500 sq ft, open kitchen, 1 study, maximize natural light"
)

if st.button("Generate Floor Plan", type="primary"):
    if not brief_text.strip():
        st.error("Please enter a brief.")
    else:
        with st.spinner("Parsing brief with AI..."):
            try:
                structured = parse_brief(brief_text)
                st.success(f"Parsed {len(structured.rooms)} rooms")
                
                with st.expander("Parsed brief (JSON)"):
                    st.json(structured.model_dump())
                
            except Exception as e:
                st.error(f"Parsing failed: {e}")
                st.stop()

        with st.spinner("Allocating areas and checking constraints..."):
            validated = validate_and_normalize(structured)

        with st.spinner("Generating layout..."):
            layout = generate_layout(validated)
            
            with st.expander("Room layout coordinates"):
                for room in layout:
                    st.write(f"**{room.name}**: ({room.x:.1f}, {room.y:.1f}) → "
                             f"{room.width:.1f}ft × {room.height:.1f}ft "
                             f"[{room.zone}]")

        with st.spinner("Drafting DXF..."):
            with tempfile.NamedTemporaryFile(suffix=".dxf", delete=False) as tmp:
                output_path = tmp.name
            
            create_dxf(validated, layout, output_path)
            
            with open(output_path, "rb") as f:
                dxf_bytes = f.read()
            os.unlink(output_path)

        st.success("Floor plan generated!")
        
        col1, col2 = st.columns(2)
        with col1:
            st.download_button(
                label="Download DXF",
                data=dxf_bytes,
                file_name="floor_plan.dxf",
                mime="application/dxf",
                type="primary"
            )
        with col2:
            st.info("Open in AutoCAD, LibreCAD, or DraftSight to view. "
                    "Or drag into AutoCAD Web at autodesk.com/products/autocad/web")
        
        st.balloons()
