# -*- coding: utf-8 -*-

import streamlit as st

import kiara_streamlit
from kiara_streamlit.data_centric import DataCentricApp

st.set_page_config(page_title="Kiara experiment: data-centric workflows", layout="wide")

if "workflow_pages" not in st.session_state.keys():
    st.session_state.workflow_pages = {}

kiara_streamlit.init()

st.header("Data-centric workflows")

app = DataCentricApp.create(config={"show_pipeline_status": True})

app.run()
