# -*- coding: utf-8 -*-

"""TODO: example documentation
"""

import streamlit as st

import kiara_streamlit

kiara_streamlit.init()

result = st.kiara.value_input_file_path(label="Enter a path to a file")
st.write(result)
