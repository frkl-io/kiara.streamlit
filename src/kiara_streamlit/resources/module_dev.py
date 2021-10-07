# -*- coding: utf-8 -*-
import json
import os
import typing

import streamlit as st
from kiara.data.values.value_set import SlottedValueSet
from kiara.operations import OperationType
from kiara.operations.sample import SampleValueOperationType
from kiara.processing import JobStatus

import kiara_streamlit

module_name: typing.Optional[str] = os.environ.get("DEV_MODULE_NAME", None)

if not module_name:
    page_title = "Module dev helper"
else:
    page_title = f"Module dev helper for: {module_name}"

st.set_page_config(
    page_title=page_title,
    page_icon="🧊",
    layout="wide",
    initial_sidebar_state="expanded",
)
st.title("Module dev helper")
if module_name:
    st.write(f"**Module**: *{module_name}*")

st.sidebar.markdown("## Settings")

_kiara_config = os.environ.get("KIARA_CONFIG", None)
if _kiara_config:
    kiara_config = json.loads(_kiara_config)

kiara_streamlit.init(kiara_config=kiara_config)

allow_module_config = True
module = st.kiara.module_select(
    module_name=module_name,
    allow_module_config=allow_module_config,
    key="module_select_box_dev",
)

if module is None:
    st.stop()

st.header("Module documentation")
full_doc = module.get_type_metadata().documentation.full_doc
st.markdown(full_doc)

st.header("Inputs")

input_slots = None
if f"{module_name}_input_slots" in st.session_state:
    input_slots = st.session_state[f"{module_name}_input_slots"]
    if len(input_slots) != len(module.input_schemas):
        st.session_state.pop(f"{module_name}_input_slots")
        input_slots = None
    else:
        for field, schema in module.input_schemas.items():
            _temp = input_slots.get(field, None)
            if not _temp:
                st.session_state.pop(f"{module_name}_input_slots")
                input_slots = None
                break
            elif schema.dict() != module.input_schemas[field].dict():
                st.session_state.pop(f"{module_name}_input_slots")
                input_slots = None
                break

if input_slots is None:
    input_slots = SlottedValueSet.from_schemas(
        module.input_schemas,
        kiara=st.kiara,
        read_only=False,
        check_for_sameness=True,
    )
    st.session_state[f"{module_name}_input_slots"] = input_slots


output_slots = None
if f"{module_name}_output_slots" in st.session_state:
    output_slots = st.session_state[f"{module_name}_output_slots"]
    if len(output_slots) != len(module.output_schemas):
        st.session_state.pop(f"{module_name}_output_slots")
        output_slots = None
    else:
        for field, schema in module.output_schemas.items():
            _temp = output_slots.get(field, None)
            if not _temp:
                st.session_state.pop(f"{module_name}_output_slots")
                output_slots = None
                break
            elif schema.dict() != module.output_schemas[field].dict():
                st.session_state.pop(f"{module_name}_output_slots")
                output_slots = None
                break

if output_slots is None:
    output_slots = SlottedValueSet.from_schemas(
        module.output_schemas, kiara=st.kiara, read_only=False
    )
    st.session_state[f"{module_name}_output_slots"] = output_slots

op_inputs = st.kiara.valueset_input(
    valueset_schema=module.input_schemas, key=f"module_auto_render_{module_name}"
)

# if "initial_values_set" not in st.session_state:
#     input_slots.set_values(**op_inputs)
#     st.session_state["initial_values_set"] = True

inputs_sidebar = st.sidebar.expander("Inputs", expanded=True)
preview_map_input = {}
sample_map_input = {}
for field_name, slot in input_slots.items():
    inputs_sidebar.write(f"### {field_name}")
    preview_map_input[field_name] = inputs_sidebar.checkbox(
        "preview", value=False, key=f"preview_input_{field_name}"
    )

    op_type: typing.Optional[SampleValueOperationType] = st.kiara.operation_mgmt.operation_types.get("sample", None)  # type: ignore
    if op_type:
        ops = op_type.get_operations_for_value_type(slot.type_name)
        if "percent" in ops.keys():
            sample_field = inputs_sidebar.checkbox(
                "sample", value=False, key=f"sample_check_{field_name}"
            )
            if sample_field:
                sample_map_input[field_name] = inputs_sidebar.slider(
                    "percent",
                    min_value=0,
                    max_value=100,
                    value=10,
                    key=f"sample_{field_name}",
                )

if sample_map_input:

    for field, sample_size in sample_map_input.items():
        sample_op: typing.Optional[
            OperationType
        ] = st.kiara.operation_mgmt.operation_types.get("sample")
        assert sample_op is not None
        perc_op = sample_op.get_operations_for_value_type(  # type: ignore
            input_slots.get(field).type_name  # type: ignore
        )[  # type: ignore
            "percent"  # type: ignore
        ]  # type: ignore
        result = perc_op.module.run(
            _attach_lineage=False, value_item=op_inputs[field], sample_size=sample_size
        )
        op_inputs[field] = result.get_value_obj("sampled_value")

input_slots.set_values(**op_inputs)


if any(preview_map_input.values()):
    st.header("Input preview")
    st.kiara.write_valueset(
        input_slots,
        as_columns=True,
        fields=(k for k, v in preview_map_input.items() if v),
    )

outputs_sidebar = st.sidebar.expander("Outputs", expanded=True)
preview_map_output = {}
for field_name in output_slots.keys():
    outputs_sidebar.write(f"### {field_name}")
    preview_map_output[field_name] = outputs_sidebar.checkbox(
        "preview", value=True, key=f"preview_output_{field_name}"
    )


run_button = st.button("Run")

job_log = st.empty()

st.header("Outputs")


def run():

    processor = st.kiara.default_processor
    pipeline_id = "__na__"
    job_id = processor.start(
        pipeline_id=pipeline_id,
        pipeline_name=pipeline_id,
        step_id=pipeline_id,
        module=module,
        inputs=input_slots,
        outputs=output_slots,
    )
    processor.wait_for(job_id)
    job_details = processor.get_job_details(job_id)
    runtime = job_details.runtime
    if job_details.status == JobStatus.SUCCESS:
        job_log.markdown(f"Success! Runtime: {runtime} seconds.")
    elif job_details.status == JobStatus.FAILED:
        jl_c = job_log.container()
        jl_c.error(f"Run failed: {job_details.error}. Runtime: {runtime} seconds.")

        if hasattr(job_details, "exception") and job_details.exception:
            jl_exp = jl_c.expander("Exception")
            jl_exp.write(job_details.exception)


if run_button:

    input_slots.set_values(**op_inputs)

    if not input_slots.items_are_valid():
        st.write("Inputs not ready.")
    else:
        run()

st.kiara.write_valueset(
    output_slots,
    fields=(k for k, v in preview_map_output.items() if v),
    add_save_option=True,
    separator=None,
    key=f"{module_name}_result_set_preview",
)
