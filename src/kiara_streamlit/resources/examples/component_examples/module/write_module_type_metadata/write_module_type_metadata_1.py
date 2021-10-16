# -*- coding: utf-8 -*-

"""Let the user select a module, then print out type metadata for the selected module.
"""

import streamlit as st

import kiara_streamlit

kiara_streamlit.init()

module = st.kiara.module_select(allow_module_config=False, key="module_select")
if module:
    st.kiara.write_module_type_metadata(module=module)
