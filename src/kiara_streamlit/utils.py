# -*- coding: utf-8 -*-
import os
import sys
import typing
from pathlib import Path

import click
import networkx as nx
import streamlit as st
from jinja2 import Environment, FileSystemLoader
from kiara import Kiara, Pipeline, PipelineStructure
from kiara.utils.modules import find_all_module_python_files, find_file_for_module
from kiara.workflow.kiara_workflow import KiaraWorkflow
from networkx import Graph
from streamlit import bootstrap
from streamlit.cli import ACCEPTED_FILE_EXTENSIONS, _main_run
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


def calculate_env_config(kiara: Kiara, module_name: typing.Optional[str] = None):

    python_path = []
    if module_name:

        if module_name not in kiara.available_module_types and not os.path.isfile(
            os.path.realpath(module_name)
        ):
            print()
            print(
                f"Can't launch dev UI for module '{module_name}': module not available."
            )
            sys.exit(1)

        if not os.path.isfile(os.path.realpath(module_name)):
            # means not a pipeline file
            python_path_to_watch = find_file_for_module(
                module_name=module_name, kiara=kiara
            )

            _python_path = os.environ.get("PYTHONPATH", None)
            if _python_path:
                python_path = _python_path.split(":")

            if python_path_to_watch not in python_path:
                python_path.append(python_path_to_watch)
        else:
            _python_path = os.environ.get("PYTHONPATH", None)
            pipeline_folder_to_watch = os.path.dirname(os.path.realpath(module_name))
            if _python_path:
                python_path = _python_path.split(":")

            if pipeline_folder_to_watch not in python_path:
                python_path.append(pipeline_folder_to_watch)

        os.environ["DEV_MODULE_NAME"] = module_name

    else:
        all_paths = find_all_module_python_files(kiara=kiara)
        _python_path = os.environ.get("PYTHONPATH", None)
        if _python_path:
            python_path = _python_path.split(":")

        filtered = (
            p for p in all_paths if f"{os.sep}kiara{os.sep}src{os.sep}" not in p
        )
        python_path.extend(filtered)

    python_path_export = ":".join(python_path)
    kiara_config = kiara.config.json()
    # os.environ["PYTHONPATH"] = python_path_export
    # os.environ["KIARA_CONFIG"] = kiara_config

    return {"PYTHON_PATH": python_path_export, "KIARA_CONFIG": kiara_config}


def run_streamlit(
    kiara: Kiara,
    streamlit_app_path: str,
    module_name: typing.Optional[str] = None,
    streamlit_flags: typing.Optional[typing.Mapping[str, typing.Any]] = None,
):

    env_config = calculate_env_config(kiara=kiara, module_name=module_name)

    for k, v in env_config.items():
        os.environ[k] = v

    if not streamlit_flags:
        streamlit_flags = {}

    bootstrap.load_config_options(flag_options=streamlit_flags)

    _, extension = os.path.splitext(streamlit_app_path)
    if extension[1:] not in ACCEPTED_FILE_EXTENSIONS:
        if extension[1:] == "":
            raise click.BadArgumentUsage(
                "Streamlit requires raw Python (.py) files, but the provided file has no extension.\nFor more information, please see https://docs.streamlit.io"
            )
        else:
            raise click.BadArgumentUsage(
                "Streamlit requires raw Python (.py) files, not %s.\nFor more information, please see https://docs.streamlit.io"
                % extension
            )

    if not os.path.exists(streamlit_app_path):
        raise click.BadParameter("File does not exist: {}".format(streamlit_app_path))
    _main_run(streamlit_app_path, None, flag_options=streamlit_flags)
