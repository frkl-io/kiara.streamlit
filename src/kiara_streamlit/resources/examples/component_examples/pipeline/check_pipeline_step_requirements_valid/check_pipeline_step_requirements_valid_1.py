# -*- coding: utf-8 -*-

"""Create a simple 'logic nand' pipeline and check if the requirements for the last steps are fulfilled. Print out details if not.
"""

import streamlit as st

import kiara_streamlit

kiara_streamlit.init()

pipeline_structure = {
    "steps": [
        {"module_type": "logic.and", "step_id": "and"},
        {"module_type": "logic.not", "step_id": "not", "input_links": {"a": "and.y"}},
    ],
}

pipeline = st.kiara.create_pipeline(pipeline_structure)

missing_1 = st.kiara.check_pipeline_step_requirements_valid(
    pipeline=pipeline, step_id="not", render_details=True
)
if missing_1:
    st.write(f"Not ready yet: {missing_1}")
pipeline.inputs.set_values(and__a=True, and__b=True)
missing_2 = st.kiara.check_pipeline_step_requirements_valid(
    pipeline=pipeline, step_id="not", render_details=True
)
st.write(f"After setting of inputs: {missing_2}")
