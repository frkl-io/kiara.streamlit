# -*- coding: utf-8 -*-

"""Create a simple 'logic nand' pipeline and display the pipeline status in different stages while inputs are set.
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

empty_pipeline_status = st.expander("Pipeline status (new pipeline)")
st.kiara.pipeline_status(pipeline=pipeline, container=empty_pipeline_status)

pipeline.inputs.set_value("and__a", True)
intermediate_pipeline_status = st.expander("Pipeline status (intermediate pipeline)")
st.kiara.pipeline_status(pipeline=pipeline, container=intermediate_pipeline_status)

pipeline.inputs.set_value("and__b", True)
finished_pipeline_status = st.expander("Pipeline status (finished pipeline)")
st.kiara.pipeline_status(pipeline=pipeline, container=finished_pipeline_status)

st.write("Result:")
st.write(pipeline.outputs.get_all_value_data())
