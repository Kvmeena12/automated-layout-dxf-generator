# pipeline.py

from constraints import validate_and_normalize, validate_output
from llm_parser import llm_generate
from layout_engine import generate_layout


def hard_constraint_check(brief):
    total_area = brief.total_area_sqft
    used_area = sum(r.area_sqft for r in brief.rooms)

    if used_area > total_area * 1.2:
        return False, "Severe area overflow"

    if len(brief.rooms) == 0:
        return False, "No rooms"

    return True, "OK"


def generate_with_retry(prompt, max_retries=3):
    for attempt in range(max_retries):
        brief = llm_generate(prompt)

        valid, msg = hard_constraint_check(brief)

        if valid:
            return brief

        prompt = prompt + "\nEnsure total room area fits within given area."

    raise ValueError("Failed to generate valid JSON")


def run_pipeline(prompt):
    # Step 1: LLM + retry
    brief = generate_with_retry(prompt)

    # Step 2: Normalize
    brief = validate_and_normalize(brief)

    # Step 3: Layout
    layout = generate_layout(brief)

    # Step 4: Final validation
    result = validate_output(brief, layout)

    return brief, layout, result