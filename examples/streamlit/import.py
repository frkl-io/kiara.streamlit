# -*- coding: utf-8 -*-
import typing

import streamlit as st
from kiara.operations import Operation
from kiara.operations.data_import import DataImportOperationType

import kiara_streamlit
from kiara_streamlit import KiaraStreamlit

kiara_streamlit.init()

st.set_page_config(page_title="Kiara experiment: data import", layout="centered")

st.header("Dynamic importing values")

desc = """
---

This streamlit app lets you import value objects into the *kiara* data store.

First, select the value type_name you want to import, then the type_name/profile of the source (in most cases this will be a file or folder path string). The whole thing is a bit confusing at the moment though, because it is missing good descriptions of the import operations.

Not many value type_name import operations are implemented yet, so this is not really super use-ful yet. It should demonstrate the principle though.

---
"""

st.markdown(desc)

ktx: KiaraStreamlit = st.get_ktx()

operations: DataImportOperationType = ktx.kiara.operation_mgmt.get_operations("import")

import_ops: typing.Dict[str, typing.Dict[str, typing.Dict[str, Operation]]] = {}

for vt in ktx.kiara.type_mgmt.value_type_names:
    ops = operations.get_import_operations_for_type(vt)
    for source_type, _ops in ops.items():
        for k, v in _ops.items():
            import_ops.setdefault(vt, {}).setdefault(source_type, {})[k] = _ops

target_type = st.selectbox("Value type_name to import:", import_ops.keys())

profiles = {}
for k, v in import_ops[target_type].items():
    for _k, _v in v.items():
        if _k in profiles.keys():
            _k = f"{_k} (k)"
        profiles[_k] = _v[_k]
source_profile = st.selectbox("Select the source profile", profiles)

operation = profiles[source_profile]
st.markdown(operation.doc.full_doc)

result = {}
st.header("Inputs")

op_inputs = ktx.operation_inputs(operation)

run_button = st.button("Run")
if run_button:
    op_outputs = ktx.run_operation(operation, inputs=op_inputs)
    ktx.valueset_info(op_outputs)
