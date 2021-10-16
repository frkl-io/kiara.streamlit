# -*- coding: utf-8 -*-

"""Let the user select a module, then render a panel that allows the user to enter a module configuration for that module type.

If successful, create a module with that configuration, and write its info.
"""

import streamlit as st

import kiara_streamlit

kiara_streamlit.init()

module_type = st.selectbox("Select a module", options=st.kiara.available_module_types)

module_config = st.kiara.module_config_panel(module_type=module_type)
if module_config is None:
    st.write("No module selected.")
else:
    module = st.kiara.create_module(
        module_type=module_type, module_config=module_config
    )
    st.write("Successfully created module with config:")
    st.write(module_config.dict())
    expander = st.expander("Module details")
    expander.write(module.info.dict())
