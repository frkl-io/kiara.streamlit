# -*- coding: utf-8 -*-

"""Print a modules configuration as table..
"""

import streamlit as st

import kiara_streamlit

kiara_streamlit.init()

module = st.kiara.module_select(
    allow_module_config=False, key="module_select_no_config"
)
if module:
    st.write(f"Module configuration for: {module._module_type_id}")
    st.kiara.write_module_config(module, show_type=True, show_desc=True)
