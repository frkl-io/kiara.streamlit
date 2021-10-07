# -*- coding: utf-8 -*-
import json
import os
import typing

import streamlit as st

import kiara_streamlit

module_name: typing.Optional[str] = os.environ.get("DEV_MODULE_NAME", None)

if not module_name:
    page_title = "kiara module info"
else:
    page_title = f"kiara module info for: {module_name}"

st.set_page_config(
    page_title=page_title,
    page_icon="🧊",
    layout="wide",
    initial_sidebar_state="expanded",
)
st.title(page_title)

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

full_doc = module.get_type_metadata().documentation.full_doc

pipeline_str = ""
if module.is_pipeline() and not pipeline_str == "pipeline":
    pipeline_str = " (pipeline module)"
st.markdown(f"## Module documentation for: *{module._module_type_id}*{pipeline_str}")
st.markdown(full_doc)

st.markdown("## Module configuration")
st.kiara.write_module_config(module)

inp_col, out_col = st.columns(2)
inp_col.markdown("## Module inputs")

st.kiara.valueset_schema_info(module.input_schemas, container=inp_col)

out_col.markdown("## Module outputs")
st.kiara.valueset_schema_info(
    module.output_schemas, show_required=False, show_default=False, container=out_col
)

st.markdown("## Metadata")
st.kiara.write_module_type_metadata(module=module)
st.markdown("## Source")
st.kiara.write_module_processing_code(module=module)
