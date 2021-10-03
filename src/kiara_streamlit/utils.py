# -*- coding: utf-8 -*-
import os
import typing
from pathlib import Path

import networkx as nx
import streamlit as st
from jinja2 import Environment, FileSystemLoader
from kiara import Pipeline, PipelineStructure
from kiara.workflow.kiara_workflow import KiaraWorkflow
from networkx import Graph
from streamlit.delta_generator import DeltaGenerator

from kiara_streamlit.defaults import TEMPLATES_BASE_DIR


def get_structure(pipeline: typing.Union[Pipeline, PipelineStructure, KiaraWorkflow]):

    if isinstance(pipeline, Pipeline):
        structure: PipelineStructure = pipeline.structure
    elif isinstance(pipeline, KiaraWorkflow):
        structure = pipeline.pipeline.structure
    elif isinstance(pipeline, PipelineStructure):
        structure = pipeline
    else:
        raise TypeError(f"Invalid type: {type(pipeline)}")

    return structure


def create_execution_graph(
    pipeline: typing.Union[Pipeline, PipelineStructure, KiaraWorkflow]
) -> str:

    structure = get_structure(pipeline)

    dot = nx.nx_pydot.to_pydot(structure.execution_graph)
    graph = dot.to_string()
    return graph


def create_data_flow_graph(
    pipeline: typing.Union[Pipeline, PipelineStructure, KiaraWorkflow],
    simple_graph: bool = True,
) -> str:

    structure = get_structure(pipeline)

    if simple_graph:
        dot = nx.nx_pydot.to_pydot(structure.data_flow_graph_simple)
    else:
        dot = nx.nx_pydot.to_pydot(structure.data_flow_graph)
    graph = dot.to_string()
    return graph


def write_graph(graph: Graph, container: DeltaGenerator = st):

    container.graphviz_chart(graph)


def render_example_template(
    component_name: str,
    example_doc: typing.Optional[str] = None,
    example_args: typing.Optional[str] = None,
    template: typing.Union[None, str, Path] = None,
) -> str:

    if not template:
        template = os.path.join(TEMPLATES_BASE_DIR, "component_example.py.j2")

    if isinstance(template, str):
        template = Path(template)

    loader = FileSystemLoader(template.parent)
    env = Environment(loader=loader)

    template_obj = env.get_template(template.name)

    rendered = template_obj.render(
        component_name=component_name,
        example_doc=example_doc,
        example_args=example_args,
    )
    return rendered
