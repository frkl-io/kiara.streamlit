# -*- coding: utf-8 -*-

"""Render an input component that returns a 'table' value object.
"""

import streamlit as st
from kiara.data import Value

import kiara_streamlit

kiara_streamlit.init()

result: Value = st.kiara.value_input(value_schema="table", label="Select the table")

no_rows = result.get_metadata("table")["table"]["rows"]
column_names = result.get_metadata("table")["table"]["column_names"]

st.write(f"The selected table has '{no_rows}' rows and the following column names:")
st.write(column_names)
