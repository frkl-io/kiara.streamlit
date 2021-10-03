# -*- coding: utf-8 -*-

"""TODO: example documentation
"""

import streamlit as st

import kiara_streamlit

kiara_streamlit.init()

result = st.kiara.value_select_box(arg1="x", arg2="y")
st.write(result)
