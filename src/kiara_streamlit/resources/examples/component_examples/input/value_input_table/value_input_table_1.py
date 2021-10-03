# -*- coding: utf-8 -*-

"""Render an input field for the user to select a table, then render that table.
"""

import pyarrow as pa
import streamlit as st
from kiara.data import Value

import kiara_streamlit

kiara_streamlit.init()

result: Value = st.kiara.value_input_table(label="Please select a table")
table: pa.Table = result.get_value_data()
st.write(
    table.to_pandas()
)  # the '.to_pandas()' part won't be necessary in the future, but it is for the moment
