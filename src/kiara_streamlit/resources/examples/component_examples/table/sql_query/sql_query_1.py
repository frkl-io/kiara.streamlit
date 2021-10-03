# -*- coding: utf-8 -*-

"""Display a sql query editor.
"""

import streamlit as st

import kiara_streamlit

kiara_streamlit.init()

result = st.kiara.sql_query(show_sampling_option=True, show_preview_table_option=True)
st.write(result)
