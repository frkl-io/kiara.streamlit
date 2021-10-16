# -*- coding: utf-8 -*-

"""Create a simple 'logic nand' pipeline, set invalid values via the 'set_pipeline_inputs' method twice, once with invalid and once with valid data.

Using the 'render_errors' argument prompts the component to print out an error message that explains which input is invalid, and why.
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

invalid_result = st.kiara.set_pipeline_inputs(
    pipeline=pipeline,
    inputs={"and__a": "invalid_input", "and__b": True},
    render_errors=True,
)
st.write("Invalid inputs result:")
st.write(invalid_result)

valid_result = st.kiara.set_pipeline_inputs(
    pipeline=pipeline, inputs={"and__a": True, "and__b": True}, render_errors=True
)
st.write("Valid inputs result:")
st.write(valid_result)
