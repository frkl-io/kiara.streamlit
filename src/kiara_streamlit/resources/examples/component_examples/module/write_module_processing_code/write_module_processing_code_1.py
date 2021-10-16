# -*- coding: utf-8 -*-

"""Let the user select a module, then print out the processing code of that module (or the pipeline configuration in case the module is a pipeline)..
"""

import streamlit as st

import kiara_streamlit

kiara_streamlit.init()

module = st.kiara.module_select(allow_module_config=False, key="module_select")
if module:
    st.kiara.write_module_processing_code(module=module)
