# -*- coding: utf-8 -*-

"""Virtual module that is used as base for [PipelineModule][kiara.pipeline.module.PipelineModule] classes that are auto-generated
from pipeline descriptions under this folder."""
import typing

import streamlit as st
from kiara import KiaraEntryPointItem, Pipeline, find_pipeline_base_path_for_module
from kiara.pipeline.config import PipelineConfig
from kiara.pipeline.controller.batch import BatchControllerManual
from kiara.utils import log_message

if typing.TYPE_CHECKING:
    from kiara_streamlit.pipelines.pages import PipelinePage

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
            app = PipelineApp(pipeline=pipeline)  # type: ignore
            st.session_state["__pipeline_app__"] = app

            if pages:
                for page in pages:
                    app.add_page(page)

        else:
            app = st.session_state["__pipeline_app__"]

        return app

    def __init__(self, pipeline: str, nav_horizontal: bool = False):

        self._pipeline_config: PipelineConfig = PipelineConfig.create_pipeline_config(
            config=pipeline, kiara=st.kiara
        )
        self._pipeline_controller = BatchControllerManual(kiara=st.kiara)
        self._pipeline: Pipeline = self._pipeline_config.create_pipeline(
            controller=self._pipeline_controller, kiara=st.kiara
        )
        self._pages: typing.Dict[int, PipelinePage] = {}
        self._nav_horizontal: bool = nav_horizontal

    @property
    def pipeline(self) -> Pipeline:
        return self._pipeline

    @property
    def pipeline_controller(self) -> BatchControllerManual:
        return self._pipeline_controller

    @property
    def pages(self) -> typing.Mapping[int, "PipelinePage"]:
        return self._pages

    def add_page(self, page: "PipelinePage"):

        page.set_app(self)
        self._pages[len(self._pages) + 1] = page

    def run(self):

        if not self._pages:
            st.write("No pages")
            return

        page_params = st.experimental_get_query_params()
        page_id = page_params.get("page", [None])[0]
        if not page_id:
            page_id = self._pages[1].id
        page_nr = -1
        for p_nr, page in self._pages.items():
            if page.id == page_id:
                page_nr = p_nr
                break

        if page_nr < 1:
            page_nr = 1
            page_id = self._pages[1].id

        # selection = next(iter(self._pages.keys()))
        if self._nav_horizontal:
            raise NotImplementedError()
        else:
            md = "# Pages\n\n"
            st.sidebar.markdown(md)
            for page_idx, page in self._pages.items():
                if st.sidebar.button(
                    page.title, key=f"{self._pipeline.id}_{page.title}_{page_idx}"
                ):
                    page_nr = page_idx
                    page_id = page.id

        st.sidebar.markdown("---\n# Info")
        st.experimental_set_query_params(page=self._pages[page_nr].id)
        print(f"Run page: {page_nr} - {page_id}")

        st.header(self._pages[page_nr].title)
        self._pages[page_nr].run_page(st=st)

        status_expander = st.sidebar.expander("Pipeline status", expanded=False)
        st.kiara.pipeline_status(pipeline=self._pipeline, container=status_expander)
