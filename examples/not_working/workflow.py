# -*- coding: utf-8 -*-

import streamlit as st
from kiara.pipeline.controller.batch import BatchControllerManual

import kiara_streamlit
from kiara_streamlit import KiaraStreamlit

kiara_streamlit.init()

st.set_page_config(page_title="Kiara experiment: dynamic workflow", layout="centered")

ktx: KiaraStreamlit = st.get_ktx()

module_type = "/home/markus/projects/dharpa/kiara_modules.playground/examples/pipelines/topic_modeling_end_to_end_fail.json"

workflow = ktx.create_workflow(workflow_alias="topic_modeling", module_type=module_type)
pipeline_inputs = workflow.pipeline.inputs
structure = workflow.structure

# for inp, value in structure.pipeline_inputs.items():
#     st.header(inp)
#     st.write(value.connected_inputs)

done_inputs = []

hide_non_input_steps = True

headers = {}
outputs = {}

workflow_status = st.empty()
workflow_current = st.empty()

for stage in structure.processing_stages:
    for step_id in stage:

        step = structure.get_step(step_id)
        step_inputs = {}
        for inp, value in structure.pipeline_inputs.items():
            for ci in value.connected_inputs:
                if ci.step_id == step.step_id and inp not in done_inputs:
                    step_inputs[inp] = pipeline_inputs[inp]
                    done_inputs.append(inp)

        if step_inputs or not hide_non_input_steps:
            st.markdown(" --- ")
            header_em = st.empty()
            headers[step.step_id] = header_em
            header_em.markdown(f"### Step: *{step.step_id}*")

        if step_inputs:

            op_inputs = ktx.valueset_input(value_set=step_inputs)
            values = {}
            for k, v in op_inputs.items():
                if v:
                    values[k] = v.get_value_data()
            workflow.inputs.set_values(**values)

        if step_inputs or not hide_non_input_steps:
            exp = st.expander("Step outputs")

            em = exp.empty()
            outputs[step_id] = em

for idx, stage in enumerate(structure.processing_stages):

    controller: BatchControllerManual = workflow.controller
    workflow_current.write(f"Processing stage {idx + 1}")
    failed = False
    try:
        controller.process_stage(idx + 1)
    except Exception as e:
        print(e)
        failed = True

    for step_id in stage:
        if step_id not in outputs.keys():
            continue

        step_outputs = workflow.pipeline.get_step_outputs(step_id)
        ktx.valueset_info(step_outputs, container=outputs[step_id])

    if failed:
        break

for step_id, status in workflow.get_current_state().step_states.items():

    if step_id in headers.keys():
        headers[step_id].markdown(f"### Step: *{step.step_id}* ({status.name})")

workflow_current.write("Processing finished")
ktx.valueset_info(workflow.outputs)
