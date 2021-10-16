# -*- coding: utf-8 -*-

"""Display a combobox where users can select a module, but don't allow module configuration.

This means that only modules that don't require configuration and operations will be present in the module selection list.
"""

import streamlit as st

import kiara_streamlit

kiara_streamlit.init()

module = st.kiara.module_select(
    allow_module_config=False, key="module_select_no_config"
)
if module:
    st.write(f"Created module object: {module}")
    expander = st.expander("Module details")
    expander.write(module.info.dict())
