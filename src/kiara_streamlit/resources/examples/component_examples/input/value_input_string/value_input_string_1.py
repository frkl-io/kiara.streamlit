# -*- coding: utf-8 -*-

"""A simple example to render an input text field.
"""

import streamlit as st

import kiara_streamlit

kiara_streamlit.init()

result = st.kiara.value_input_string(label="Enter your name")
st.write(result)
