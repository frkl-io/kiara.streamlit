# -*- coding: utf-8 -*-

"""Request the user to select one of the existing stored values of type 'array'.

Then, use the result to print the metadata and content of the returned 'Value' object.
"""

import pyarrow as pa
import streamlit as st
from kiara.data import Value

import kiara_streamlit

kiara_streamlit.init()

result: Value = st.kiara.value_input_array(label="Select the array you want to use")

metadata_expander = st.expander("Array metadata", expanded=False)
metadata_expander.write(result.get_metadata())

data_expander = st.expander("Array data", expanded=False)

array: pa.Array = result.get_value_data()
# currently, streamlit does not support printing native Arrow arrays, in the future,
# the '.to_pandas()' method should not be required anymore for this
data_expander.write(array.to_pandas())
