# -*- coding: utf-8 -*-

"""Ask for an integer, and print it out.
"""

import streamlit as st

import kiara_streamlit

kiara_streamlit.init()

result = st.kiara.value_input_integer(label="Enter your age", default=100)
st.write(result)
