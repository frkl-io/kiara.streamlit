# -*- coding: utf-8 -*-

"""Select a file and print the first few lines of its content.
"""

import streamlit as st
from kiara.data import Value
from kiara_modules.core.metadata_schemas import KiaraFile

import kiara_streamlit

kiara_streamlit.init()

result: Value = st.kiara.value_input_file(label="Select a file.")

content_exp = st.expander("File content", expanded=False)
file_obj: KiaraFile = result.get_value_data()
content = file_obj.read_content(as_str=True, max_lines=50)
content_exp.markdown(f"```\n{content}\n```")
