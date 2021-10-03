# -*- coding: utf-8 -*-
import os

import streamlit as st
from kiara.pipeline.controller.batch import BatchControllerManual

import kiara_streamlit
from kiara_streamlit import KiaraStreamlit

kiara_streamlit.init()

pipeline_file = os.path.join(
    os.path.dirname(__file__), "topic_modeling_end_to_end.json"
)

ktx: KiaraStreamlit = st.get_ktx()


workflow = ktx.create_workflow("topic_modeling", pipeline_file)
pipeline = workflow.pipeline

controller: BatchControllerManual = pipeline.controller

current_stage = 1
steps = pipeline.get_steps_by_stage()

# st.write(steps)

# st.write(pipeline.inputs)
# for k, v in pipeline.inputs._value_slots.items():
#     refs = pipeline._value_refs[v]
#     st.write(k)
#     st.write(refs)

last_stage_valid = False


for idx, (stage, inputs) in enumerate(pipeline.get_pipeline_inputs_by_stage().items()):

    exp = st.expander(f"Workflow part: {idx+1}")

    if last_stage_valid:
        processing_stage = 1
        while processing_stage < stage:
            exp.write(f"Processing stage: {processing_stage}")
            # controller.process_stage(stage - 1)
            processing_stage = processing_stage + 1

    # st.header(f"Stage: {stage}")
    stage_inputs = {}
    defaults = {}
    for inp in inputs:

        value = pipeline.inputs.get(inp)
        defaults[inp] = value.value_schema.default
        stage_inputs[inp] = value

    value_set = ktx.valueset_input(
        stage_inputs, defaults=defaults, key=f"inputs_stage_{stage}", container=exp
    )
    for k, v in value_set.items():
        if v is not None:
            pipeline.inputs.set_values(**value_set)

    last_stage_valid = True
    for inp in inputs:
        valid = pipeline.inputs.get(inp).is_set
        if not valid:
            last_stage_valid = False
            break

    # rich_print(workflow.current_state)
