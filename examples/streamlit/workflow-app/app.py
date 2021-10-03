# -*- coding: utf-8 -*-
import os

import streamlit as st

import kiara_streamlit
from kiara_streamlit import KiaraStreamlit
from kiara_streamlit.pipelines import PipelineApp
from kiara_streamlit.pipelines.pipeline_page import StagePage

st.set_page_config(page_title="Kiara-streamlit auto-rendered pipeline", layout="wide")

pipelines_folder = os.path.join(os.path.dirname(__file__), "pipelines")

kiara_streamlit.init(pipelines_folders=[pipelines_folder])
ktx: KiaraStreamlit = st.get_ktx()

params = st.experimental_get_query_params()


def local_css(file_name):
    path = os.path.join(os.path.dirname(__file__), file_name)
    with open(path) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


def remote_css(url):
    st.markdown(f'<link href="{url}" rel="stylesheet">', unsafe_allow_html=True)


def icon(icon_name):
    st.markdown(f'<i class="material-icons">{icon_name}</i>', unsafe_allow_html=True)


# local_css("style.css")
# remote_css('https://fonts.googleapis.com/icon?family=Material+Icons')

pages = [
    StagePage("Onboarding", 1),
    StagePage("Column-mapping", 2),
    StagePage("Augment graph", 3),
]


app = PipelineApp.create(
    pipeline="/home/markus/projects/dharpa/kiara.streamlit/examples/streamlit/workflow-app/pipelines/workflow.json",
    pages=pages,
)
app.run()
