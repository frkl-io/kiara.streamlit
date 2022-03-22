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
        config: typing.Optional[typing.Mapping[str, typing.Any]] = None,
    ) -> "PipelineApp":

        if "__pipeline_app__" not in st.session_state:

            log_message(f"creating pipeline app for pipeline: {pipeline}")
            app = PipelineApp(pipeline=pipeline, config=config)  # type: ignore
            st.session_state["__pipeline_app__"] = app

            if pages:
                for page in pages:
                    app.add_page(page)

        else:
            app = st.session_state["__pipeline_app__"]

        return app

    def __init__(
        self,
        pipeline: str,
        config: typing.Optional[typing.Mapping[str, typing.Any]] = None,
    ):

        self._pipeline_config: PipelineConfig = PipelineConfig.create_pipeline_config(
            config=pipeline, kiara=st.kiara
        )
        self._pipeline_controller = BatchControllerManual(kiara=st.kiara)
        self._pipeline: Pipeline = self._pipeline_config.create_pipeline(
            controller=self._pipeline_controller, kiara=st.kiara
        )
        self._pages: typing.Dict[int, PipelinePage] = {}

        if config is None:
            config = {}

        self._config: typing.Mapping[str, typing.Any] = config

        self._current_page: int = -1
        self._previous_page: bool = False
        self._next_page: bool = False

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

    def render_navigation(self, page_nr: int) -> int:

        allowed = ["combobox", "buttons"]
        nav_style = self._config.get("navigation_style", "combobox")

        if nav_style not in allowed:
            raise Exception(
                f"Invalid configuration 'navigation_style': {nav_style} (allowed: '{', '.join(nav_style)}')"
            )

        add_page_nr = self._config.get("add_page_nr_to_page_item", True)

        if nav_style == "buttons":
            st.sidebar.markdown("## Workflow steps navigation")
            for page_idx, page in self._pages.items():

                if add_page_nr:
                    page_title = f"{page_idx}. {page.title}"
                else:
                    page_title = page.title

                key = f"_nav_{self._pipeline.id}_{page_title}_{page_idx}"
                if nav_style == "buttons":
                    if st.sidebar.button(page.title, key=key):
                        result = page_idx
        elif nav_style == "combobox":

            if self._previous_page:
                current = st.session_state.current_page
                del st.session_state.current_page
                st.session_state.current_page = current - 1
            if self._next_page:
                current = st.session_state.current_page
                del st.session_state.current_page
                st.session_state.current_page = current + 1

            def format_title(page_nr):
                page = self._pages[page_nr]
                if add_page_nr:
                    page_title = f"{page_nr}. {page.title}"
                else:
                    page_title = page.title
                return page_title

            result = st.sidebar.selectbox(
                "Workflow steps navigation",
                options=self._pages.keys(),
                key="current_page",
                format_func=format_title,
            )

        else:
            raise NotImplementedError()

        self._previous_page = False
        self._next_page = False

        return result

    def run(self):

        if st.kiara.wants_onboarding():
            print("ONBOARDING")
            if st.kiara.onboard_page():
                st.experimental_rerun()
            else:
                return

        if not self._pages:
            st.write("No modules")
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

        # selection = next(iter(self._pages.keys()))
        page_nr = self.render_navigation(page_nr)

        self._current_page = page_nr

        st.experimental_set_query_params(page=self._pages[page_nr].id)
        print(f"Run page: {page_nr} - {self._pages[page_nr].id}")

        st.header(self._pages[page_nr].title)
        self._pages[page_nr].run_page(st=st)

        if self._config.get("show_prev_and_next_buttons", False):
            st.markdown("---")
            left, _, right = st.columns([1, 8, 1])
            if page_nr != min(self._pages.keys()):
                back_button = left.button("previous")
            else:
                back_button = False
            if page_nr != max(self._pages.keys()):
                next_button = right.button("next")
            else:
                next_button = False

            if self._config.get("show_pipeline_status", False):
                st.sidebar.markdown("---\n# Info")
                status_expander = st.sidebar.expander("Pipeline status", expanded=False)
                st.kiara.pipeline_status(
                    pipeline=self._pipeline, container=status_expander
                )

            if back_button:
                self._previous_page = True
                st.experimental_rerun()

            if next_button:
                self._next_page = True
                st.experimental_rerun()
