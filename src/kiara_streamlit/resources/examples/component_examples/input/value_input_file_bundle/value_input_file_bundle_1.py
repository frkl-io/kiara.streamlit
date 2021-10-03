# -*- coding: utf-8 -*-

"""Select a file_bundle, and display the files it contains, along with their sizes in bytes..
"""

import streamlit as st
from kiara.data import Value
from kiara_modules.core.metadata_schemas import KiaraFileBundle

import kiara_streamlit

kiara_streamlit.init()

result: Value = st.kiara.value_input_file_bundle(label="Select the file bundle")
expander = st.expander("File bundle content")
file_bundle: KiaraFileBundle = result.get_value_data()
expander.write(
    "\n".join(
        [
            f"- {file_name} (size: *{details.size}* bytes)"
            for file_name, details in file_bundle.included_files.items()
        ]
    )
)
