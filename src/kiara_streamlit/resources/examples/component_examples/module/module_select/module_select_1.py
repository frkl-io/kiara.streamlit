# -*- coding: utf-8 -*-

"""Display a combobox where users can select a module and enter module config.
"""

import streamlit as st

import kiara_streamlit

kiara_streamlit.init()

module = st.kiara.module_select(allow_module_config=True, key="module_select")
if module:
    st.write(f"Created module object: {module}")
    expander = st.expander("Module details")
    expander.write(module.info.dict())
