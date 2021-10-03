# -*- coding: utf-8 -*-
import json

import streamlit as st
from kiara import PipelineStructure
from kiara.pipeline.config import PipelineConfig
from streamlit_ace import st_ace

import kiara_streamlit
from kiara_streamlit import KiaraStreamlit
from kiara_streamlit.utils import (
    create_data_flow_graph,
    create_execution_graph,
    write_graph,
)

kiara_streamlit.init()

st.set_page_config(page_title="Kiara experiment: pipeline structure", layout="wide")

st.header("Dynamic pipeline creation/rendering.")

desc = """
---

This streamlit app assemble a *kiara* pipeline description in json format, and renders it (if valid) as a network graph.

The data-flow graphs have some minor errors artefacts, this is a bug in the rendering library.

This is a very simple description you can use to try out:

```
{
  "module_type_name": "xor",
  "documentation": "Returns 'True' if exactly one of it's two inputs is 'True'.",
  "steps": [
    {
      "module_type": "logic.or",
      "step_id": "or"
    },
    {
      "module_type": "logic.nand",
      "step_id": "nand"
    },
    {
      "module_type": "logic.and",
      "step_id": "and",
      "input_links": {
        "a": "or.y",
        "b": "nand.y"
      }
    }
  ],
  "input_aliases": {
    "or__a": "a",
    "or__b": "b",
    "nand__a": "a",
    "nand__b": "b"
  },
  "output_aliases": {
    "and__y": "y"
  }
}
```

---
"""

st.markdown(desc)

ktx: KiaraStreamlit = st.get_ktx()

left, right = st.columns(2)

with left.container():
    text_area = st_ace(
        height=600,
        language="json",
        auto_update=False,
        show_gutter=False,
        keybinding="emacs",
    )
    # text_area = left.text_area("Pipeline structure", height=600)

valid = True
try:
    pipeline_config = json.loads(text_area)
except Exception as e:
    st.warning(f"Invalid json syntax: {e}")
    valid = False


if valid:
    try:
        mc = PipelineConfig(**pipeline_config)
    except Exception as e:
        st.warning(f"Invalid pipeline configuration: {e}")
        valid = False

if valid:
    st.session_state["last_valid_json"] = text_area
    st.session_state["last_valid_config"] = mc
    structure = PipelineStructure(config=mc, kiara=ktx.kiara)
    st.session_state["last_valid_structure"] = structure

else:
    if st.session_state.get("last_valid_structure"):
        structure = st.session_state.last_valid_structure
    else:
        structure = None

if structure:
    if not valid:
        right.write("Pipeline structure invalid, using last valid configuration.")
    else:
        right.write("Pipeline structure valid.")

    graph_type = right.radio(
        "Graph type_name", ["execution", "data-flow (simple)", "data-flow (full)"]
    )
    if graph_type == "execution":
        graph = create_execution_graph(structure)
    elif graph_type == "data-flow (simple)":
        graph = create_data_flow_graph(structure, simple_graph=True)
    else:
        graph = create_data_flow_graph(structure, simple_graph=False)
    write_graph(graph, container=right)
