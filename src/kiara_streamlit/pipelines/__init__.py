# -*- coding: utf-8 -*-

"""Virtual module that is used as base for [PipelineModule][kiara.pipeline.module.PipelineModule] classes that are auto-generated
from pipeline descriptions under this folder."""
import typing

import streamlit as st
from kiara import KiaraEntryPointItem, Pipeline, find_pipeline_base_path_for_module
from kiara.pipeline.config import PipelineConfig
from kiara.pipeline.controller.batch import BatchControllerManual
from kiara.utils import log_message

from kiara_streamlit import KiaraStreamlit

if typing.TYPE_CHECKING:
    from kiara_streamlit.pipelines.pipeline_page import PipelinePage

pipelines: KiaraEntryPointItem = (
    find_pipeline_base_path_for_module,
    ["kiara_streamlit.pipelines"],
)

KIARA_METADATA = {"tags": ["pipeline"], "labels": {"pipeline": "true"}}


class PipelineApp(object):
    @classmethod
    def create(
        cls,
        pipeline: str,
        pages: typing.Optional[typing.Iterable["PipelinePage"]] = None,
    ) -> "PipelineApp":

        if "__pipeline_app__" not in st.session_state:

            log_message(f"creating pipeline app for pipeline: {pipeline}")
            app = PipelineApp(ktx=st.kiara, pipeline_path=pipeline)  # type: ignore
            st.session_state["__pipeline_app__"] = app

            if not pages:
                raise NotImplementedError()

            for page in pages:
                app.add_page(page)

        else:
            app = st.session_state["__pipeline_app__"]

        return app

    def __init__(
        self, ktx: KiaraStreamlit, pipeline_path: str, nav_horizontal: bool = False
    ):

        self._ktx: KiaraStreamlit = ktx
        self._pipeline_config: PipelineConfig = PipelineConfig.create_pipeline_config(
            config=pipeline_path, kiara=self._ktx.kiara
        )
        self._pipeline_controller = BatchControllerManual(kiara=self._ktx.kiara)
        self._pipeline: Pipeline = self._pipeline_config.create_pipeline(
            controller=self._pipeline_controller, kiara=self._ktx.kiara
        )
        self._pages: typing.Dict[int, PipelinePage] = {}
        self._nav_horizontal: bool = nav_horizontal
        self._current_page: int = 1

    @property
    def kiara_streamlit(self) -> KiaraStreamlit:
        return self._ktx

    def add_page(self, page: "PipelinePage"):

        page.set_app(self)
        self._pages[len(self._pages) + 1] = page

    def run(self):

        if not self._pages:
            st.write("No pages")
            return

        page_nr = self._current_page
        # selection = next(iter(self._pages.keys()))
        if self._nav_horizontal:
            raise NotImplementedError()
        else:
            md = "# Pages\n\n"
            st.sidebar.markdown(md)
            for page_idx, page in self._pages.items():
                if st.sidebar.button(page.title):
                    page_nr = page_idx

        st.sidebar.markdown("---\n# Info")
        self._current_page = page_nr
        print(f"Run page: {self._current_page}")

        st.header(self._pages[self._current_page].title)
        self._pages[page_nr].run_page(st=st, kiara_streamlit=self._ktx)

        status_expander = st.sidebar.expander("Pipeline status", expanded=False)
        self.kiara_streamlit.pipeline_status(
            pipeline=self._pipeline, container=status_expander
        )
