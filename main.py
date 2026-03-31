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
    "2BHK Compact": "2BHK apartment, 900 sq ft, combined living and dining, 1 bathroom, balcony",
    "4BHK Luxury": "4BHK villa, 3000 sq ft, master bedroom with ensuite, formal living, family lounge, large kitchen, utility room",
}

sample_choice = st.selectbox("Or pick a sample brief:", ["Custom..."] + list(SAMPLES.keys()))
default_text = SAMPLES.get(sample_choice, "") if sample_choice != "Custom..." else ""

brief_text = st.text_area(
    "Architectural brief:",
    value=default_text,
    height=100,
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
