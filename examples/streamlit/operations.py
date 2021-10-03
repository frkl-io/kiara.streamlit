# -*- coding: utf-8 -*-
import streamlit as st

import kiara_streamlit

st.set_page_config(page_title="Kiara experiment: dynamic operation", layout="centered")

kiara_streamlit.init()

st.header("Dynamic module input/output generation")

desc = """
---

This streamlit app lets you run all (well, most) operations that are available in *kiara*.

Its inputs and output widgets are entirely auto-generated and assembled. Some value types are not
supported (yet), and some operations don't make sense in a context like this. Also, for the table-related
operations you'll have to have some tables loaded into the *kiara* data store, otherwise they'll not
be useful, since data onboarding can't be done here (yet).

Some operations that are interesting to try out:

- any of the `*.extract_metadata.*` ones
- any of the `*.calculate_hash.*` ones
- any of the `logic.*` ones
- `table.data_profile`
- `table.sample`
- `table.export`
- `table.import_from.file_path.string`
- `table.import_from.folder_path.string`
- `file.convert_to.table`
- `file_bundle.convert_to.table`

---
"""


st.markdown(desc)

operation_id = st.selectbox("Select operation", st.kiara.operation_mgmt.profiles.keys())

st.title(f"Operation: {operation_id}")

operation = st.kiara.get_operation(operation_id)
st.markdown(operation.doc.full_doc)

result = {}
st.header("Inputs")

op_inputs = st.kiara.operation_inputs(
    operation, defaults={"query": "select * from data"}
)

run_button = st.button("Run")
if run_button:
    op_outputs = st.kiara.run(operation, inputs=op_inputs)
    st.kiara.write_valueset(op_outputs)
