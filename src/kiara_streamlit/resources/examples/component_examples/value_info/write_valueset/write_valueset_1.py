# -*- coding: utf-8 -*-

"""Print the result of any operation, and add a 'Save' option so users can save any of the results.

TODO: need a better example, and create a pipeline that actually has multiple outputs to showcase what this component can do.
"""

import streamlit as st

import kiara_streamlit

kiara_streamlit.init()

query = st.text_input("SQL query:", value="select * from data")
op_id = "table.query.sql"
inputs = {"table": st.kiara.get_value("journal_nodes_table"), "query": query}

try:
    op_results = st.kiara.get_operation(op_id).run(**inputs)
    st.kiara.write_valueset(value_set=op_results, add_save_option=True)
except Exception as e:
    st.error(f"Query failed: {e}")
