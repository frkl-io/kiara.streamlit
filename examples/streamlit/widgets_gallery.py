# -*- coding: utf-8 -*-

import streamlit as st

import kiara_streamlit
from kiara_streamlit.components.mgmt import ComponentMgmt

st.set_page_config(page_title="kiara-streamlit component gallery", layout="wide")

kiara_streamlit.init(kiara_config={"extra_pipeline_folders": []})

component_mgmt: ComponentMgmt = st.kiara_components

component_collection = st.sidebar.selectbox(
    "Select a component collection", options=component_mgmt.component_collections
)

all_funcs = sorted(
    component_mgmt.get_components_of_collection(
        component_collection=component_collection
    ).keys()
)

func_name = st.selectbox(label="Component", options=["-- all --"] + all_funcs)

if func_name == "-- all --":
    for func_name, model in component_mgmt.get_components_of_collection(
        component_collection=component_collection
    ).items():
        component_mgmt.render_component_doc(
            component_collection=component_collection, component_name=func_name
        )
else:
    component_mgmt.render_component_doc(
        component_collection=component_collection, component_name=func_name
    )
