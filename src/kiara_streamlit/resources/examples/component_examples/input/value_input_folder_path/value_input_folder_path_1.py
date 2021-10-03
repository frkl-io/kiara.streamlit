# -*- coding: utf-8 -*-

"""TODO: example documentation
"""

import streamlit as st

import kiara_streamlit

kiara_streamlit.init()

result = st.kiara.value_input_folder_path(label="Enter the path to a folder.")
st.write(result)
