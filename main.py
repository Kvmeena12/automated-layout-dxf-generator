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
    "2BHK Compact": '''Design a 2BHK flat floor plan (900 sq ft, 30x30 ft) with STRICT requirements:

Rooms (MANDATORY – do not skip any):
- Living Room: ≥150 sq ft
- Master Bedroom: ≥120 sq ft WITH attached bathroom (40 sq ft)
- Second Bedroom: ≥100 sq ft
- Kitchen: 90 sq ft
- Common Bathroom: 40 sq ft (accessible from living/corridor)
- Balcony: 50 sq ft

Bathroom Rules:
- Bathrooms MUST be clearly labeled as "Toilet/Bath"
- One bathroom MUST be attached to master bedroom
- One MUST be common (not inside any bedroom)
- Each bathroom size MUST be close to 40 sq ft
- Include door placement

Layout Constraints:
- No overlapping rooms
- Rectangular rooms only
- Proper corridor connectivity
- Show all dimensions clearly
- Maintain ventilation (bathrooms on external wall preferred)

Reject output if ANY room is missing.''',
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
