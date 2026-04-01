# Streamlit app + pipeline orchestrator
import streamlit as st
import tempfile
import os
from cad import create_dxf
from pipeline import run_pipeline   # ✅ fix import (lowercase)

st.set_page_config(page_title="Brief → Floor Plan", layout="centered")
st.title("AI Floor Plan Generator")
st.caption("Paste an architectural brief → download a DXF floor plan")

# Sample briefs for easy demo
SAMPLES = {
   "3BHK Standard": "3BHK, 1500 sq ft, open kitchen, 1 study, maximize natural light",
    "2BHK Compact": 
    '''Design a 2BHK floor plan (900 sq ft 1200 sq ft) using STRICT HARD CONSTRAINTS.

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
- Show efficiency %''',
    "4BHK Luxury": "4BHK villa, 3000 sq ft, master bedroom with ensuite, formal living, family lounge, large kitchen, utility room",
}

sample_choice = st.selectbox("Or pick a sample brief:", ["Custom..."] + list(SAMPLES.keys()))
default_text = SAMPLES.get(sample_choice, "") if sample_choice != "Custom..." else ""

brief_text = st.text_area(
    "Architectural brief:",
    value=default_text,
    height=200,
)

if st.button("Generate Floor Plan", type="primary"):
    if not brief_text.strip():
        st.error("Please enter a brief.")
    else:
        with st.spinner("Generating optimized floor plan..."):
            try:
                # ✅ FULL PIPELINE (ONLY THIS)
                brief, layout, result = run_pipeline(brief_text)

                st.success(f"Parsed {len(brief.rooms)} rooms")

                with st.expander("Parsed brief (JSON)"):
                    st.json(brief.model_dump())

                with st.expander("Room layout coordinates"):
                    for room in layout:
                        st.write(f"**{room.name}**: ({room.x:.1f}, {room.y:.1f}) → "
                                 f"{room.width:.1f}ft × {room.height:.1f}ft "
                                 f"[{room.zone}]")

                # ✅ Show validation
                if not result["valid"]:
                    st.warning("⚠️ Layout issues detected:")
                    for issue in result["issues"]:
                        st.write(f"- {issue}")
                else:
                    st.success("✅ Layout valid")

            except Exception as e:
                st.error(f"Pipeline failed: {e}")
                st.stop()

        # ✅ DXF generation (use brief, not validated)
        with st.spinner("Drafting DXF..."):
            with tempfile.NamedTemporaryFile(suffix=".dxf", delete=False) as tmp:
                output_path = tmp.name

            create_dxf(brief, layout, output_path)

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
            st.info("Open in AutoCAD, LibreCAD, or DraftSight")

        st.balloons()
