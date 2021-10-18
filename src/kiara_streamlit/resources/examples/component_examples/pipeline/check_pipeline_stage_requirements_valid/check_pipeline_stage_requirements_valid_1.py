# -*- coding: utf-8 -*-

"""Create a simple 'logic nand' pipeline and check if the requirements for the last stage are fulfilled. Print out details if not.
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

ready = st.kiara.check_pipeline_stage_requirements_valid(
    pipeline=pipeline, stage=2, render_details=True
)
st.write(f"Ready (first try): {ready}")
pipeline.inputs.set_values(and__a=True, and__b=True)
ready_2 = st.kiara.check_pipeline_stage_requirements_valid(
    pipeline=pipeline, stage=2, render_details=True
)
st.write(f"Ready (second try): {ready_2}")
