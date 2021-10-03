# -*- coding: utf-8 -*-

"""Render all inputs for a the 'table.cut_column' operation.

This looks at the required input schema for the operation, and renders a table-select component, as well as a text input
field so the user can enter the column name to cut.

This example illustrates some of the shortcomings of this approach,
because the column name ideally would be a select box that only contains the available column names of the selected table.
In this instance, this could be easily solved by writing a few more lines of code, and manually creating the two required
input components.
"""

import streamlit as st

import kiara_streamlit

kiara_streamlit.init()

op_inputs = st.kiara.operation_inputs("table.cut_column")
if not op_inputs["column_name"]:
    columns = op_inputs["table"].get_metadata("table")["table"]["column_names"]
    st.info(f"Available column names: {', '.join(columns)}")
else:
    try:
        resulting_column = st.kiara.run(
            "table.cut_column",
            inputs=op_inputs,
            resolve_result=True,
            output_name="array",
        )
        st.write(resulting_column.to_pandas())
    except Exception as e:
        st.error(f"Could not run operation: {e}")
