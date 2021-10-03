# -*- coding: utf-8 -*-

"""Render a collection of input widgets to ask for age and name, then print the result.
"""

import streamlit as st

import kiara_streamlit

kiara_streamlit.init()

schema = {"age": "integer", "name": "string"}
defaults = {"age": 42, "name": "Pasternak"}
result = st.kiara.valueset_input(valueset_schema=schema, defaults=defaults)
st.write(result)
