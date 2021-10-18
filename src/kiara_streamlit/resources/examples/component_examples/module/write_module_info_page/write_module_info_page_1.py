# -*- coding: utf-8 -*-

"""Let the user select a module, then print out all available information for that module.
"""

import streamlit as st

import kiara_streamlit

kiara_streamlit.init()

module = st.kiara.module_select(
    allow_module_config=False, key="write_module_type_metadata"
)
if module:
    expander = st.expander("Module info")
    st.kiara.write_module_info_page(module=module, container=expander)
