# -*- coding: utf-8 -*-

"""Render a simple checkbox.
"""

import streamlit as st

import kiara_streamlit

kiara_streamlit.init()

result = st.kiara.value_input_boolean(label="Is it really true?", default=True)
st.write(result)
