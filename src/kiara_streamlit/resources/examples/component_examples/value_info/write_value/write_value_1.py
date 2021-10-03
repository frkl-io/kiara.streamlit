# -*- coding: utf-8 -*-

"""Ask the user to select a value of any type, then render metadata and value data itself onto the page.
"""

import streamlit as st
from kiara.data import Value

import kiara_streamlit

kiara_streamlit.init()

selected_alias = st.kiara.value_select_box(value_type="any")
value: Value = st.kiara.get_value(selected_alias)
st.write(f"Selected value type: **{value.type_name}**")
metadata_expander = st.expander("Value metadata", expanded=False)
metadata_expander.write(value.get_metadata())
st.kiara.write_value(value)
