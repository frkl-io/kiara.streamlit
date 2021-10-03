# -*- coding: utf-8 -*-

"""Render a select box for table values.
"""

import streamlit as st
from kiara.data import Value

import kiara_streamlit

kiara_streamlit.init()

table_alias = st.kiara.value_select_box(value_type="table", add_no_value_option=True)
if not table_alias:
    st.write("No table selected.")
else:
    table_value: Value = st.kiara.get_value(table_alias)
    st.write(table_value.get_value_data().to_pandas())
