# -*- coding: utf-8 -*-
import abc
import typing

import streamlit as st
from kiara import Pipeline
from kiara.data import Value, ValueSet
from kiara.data.values.value_set import check_valueset_valid
from kiara.pipeline.controller.batch import BatchControllerManual
from kiara.processing import Job
from streamlit.delta_generator import DeltaGenerator

from kiara_streamlit.pipelines import PipelineApp


class PipelinePage(abc.ABC):
    """A class to encapsulate a single page in a streamlit-rendered kiara pipeline."""

    def __init__(
        self, id: str, config: typing.Optional[typing.Mapping[str, typing.Any]] = None
    ):

        if config is None:
            config = {}

        self._app: typing.Optional[PipelineApp] = None
        self._id: str = id
        self._config: typing.Mapping[str, typing.Any] = config
        self._cache: typing.Dict[str, typing.Any] = {}

    @property
    def app(self) -> PipelineApp:

        if self._app is None:
            raise Exception("App not initialized yet.")

        return self._app

    @property
    def page_config(self) -> typing.Mapping[str, typing.Any]:
        return self._config

    def get_page_key(self, sub_key: typing.Optional[str] = None) -> str:
        if sub_key:
            return f"_pipeline_page_{self.id}_{sub_key}"
        else:
            return f"_pipeline_page_{self.id}"

    def set_app(self, app: PipelineApp):
        self._app = app

    @property
    def pipeline(self) -> Pipeline:
        return self.app._pipeline

    @property
    def pipeline_controller(self) -> BatchControllerManual:
        return self.app._pipeline_controller

    @property
    def id(self) -> str:
        return self._id

    @property
    def title(self) -> str:
        return self.page_config.get("title", self.id)

    def get_all_step_ids(self) -> typing.Iterable[str]:

        return self.pipeline.step_ids

    def get_step_ids_for_stage(self, stage: int) -> typing.Iterable[str]:
        """Return all step ids for the specified stage."""

        return self.pipeline.get_steps_by_stage().get(stage, {}).keys()

    def get_pipeline_inputs(self, *input_fields: str) -> typing.Mapping[str, Value]:
        """Get the current values for one, several or all pipeline inputs fields.

        If no input field is specified, all inputs will be returned as a dict with the field name as key, and the
        Value object as value, otherwise a dict with only the requested field names will be returned.
        """

        invalid = [f for f in input_fields if f not in self.pipeline.inputs.keys()]
        if invalid:
            raise Exception(
                f"Invalid input fields name(s) '{', '.join(invalid)}', available field(s): {', '.join(self.pipeline.inputs.keys())}."
            )

        if not input_fields:
            _input_fields: typing.Iterable[str] = self.pipeline.inputs.keys()
        else:
            _input_fields = input_fields

        value_set = {field: self.pipeline.inputs[field] for field in _input_fields}
        return value_set

    def get_pipeline_outputs(self, *output_fields: str) -> typing.Mapping[str, Value]:
        """Get the current values for one, several or all pipeline outputs.

        If no pipeline output is specified, all outputs will be returned as a dict with the field name as key, and the
        Value object as value, otherwise a dict with only the requested field names will be returned.
        """

        invalid = [f for f in output_fields if f not in self.pipeline.outputs.keys()]
        if invalid:
            raise Exception(
                f"Invalid input fields name(s) '{', '.join(invalid)}', available field(s): {', '.join(self.pipeline.outputs.keys())}."
            )

        if not output_fields:
            _output_fields: typing.Iterable[str] = self.pipeline.outputs.keys()
        else:
            _output_fields = output_fields

        value_set = {field: self.pipeline.outputs[field] for field in _output_fields}
        return value_set

    def get_pipeline_inputs_for_step(self, step_id: str) -> typing.Mapping[str, Value]:
        """Get any relevant pipeline inputs that feed (directly) into step.

        This method does not return any step inputs that are connected to another steps output.
        """

        fields = self.pipeline.get_pipeline_inputs_for_step(step_id=step_id)
        return {field: self.pipeline.inputs[field] for field in fields}

    def get_pipeline_outputs_for_step(self, step_id: str) -> typing.Mapping[str, Value]:
        """Get any pipeline outputs that are produced by the specified step.

        This method does not return any step outputs that are not connected to a pipeline output.
        """

        fields = self.pipeline.get_pipeline_outputs_for_step(step_id)
        return {field: self.pipeline.outputs[field] for field in fields}

    def get_pipeline_inputs_for_stage(self, stage: int) -> typing.Mapping[str, Value]:
        """Get relevant pipeline inputs that are required by the specified step.

        Inputs of previous steps are not returned by this method.
        """

        fields = self.pipeline.get_pipeline_inputs_for_stage(stage=stage)
        return {field: self.pipeline.inputs[field] for field in fields}

    def get_pipeline_outputs_for_stage(self, stage: int) -> typing.Mapping[str, Value]:
        """Get pipeline outputs that are produced by this step."""

        fields = self.pipeline.get_pipeline_outputs_for_stage(stage=stage)
        return {field: self.pipeline.outputs[field] for field in fields}

    def set_pipeline_inputs(
        self,
        inputs: typing.Mapping[str, typing.Any],
        render_errors: bool = True,
        container: DeltaGenerator = st,
    ) -> typing.Mapping[str, typing.Union[bool, Exception]]:
        """Set one or several pipeline inputs."""

        return st.kiara.set_pipeline_inputs(
            pipeline=self.pipeline,
            inputs=inputs,
            render_errors=render_errors,
            container=container,
        )

    def check_valueset_valid(self, value_set: typing.Mapping[str, Value]) -> bool:
        """Check whether all values in a value set have valid values."""

        return check_valueset_valid(value_set=value_set)

    def check_stage_requirements_valid(
        self, stage: int, render_details: bool = True, container: DeltaGenerator = st
    ) -> bool:
        """Check if all the required inputs for this stage are valid.

        If 'render_details' is set to True, an error message with details for invalid inputs will be displayed if there
        are any.
        """

        return st.kiara.check_pipeline_stage_requirements_valid(
            pipeline=self.pipeline,
            stage=stage,
            render_details=render_details,
            container=container,
        )

    def check_step_requirements_valid(
        self, step_id: str, render_details: bool = True, container: DeltaGenerator = st
    ) -> typing.List[str]:

        return st.kiara.check_pipeline_step_requirements_valid(
            pipeline=self.pipeline,
            step_id=step_id,
            render_details=render_details,
            container=container,
        )

    def check_invalid_values(
        self,
        value_set: typing.Mapping[str, Value],
        render_error: bool = False,
        error_title: str = "Invalid inputs:",
        container: DeltaGenerator = st,
    ) -> typing.List[str]:
        """Check whether the provided value set has any invalid inputs, if, return their field names.

        If 'render_error' is set to True, an error message is displayed if any invalid found.
        """

        invalid = sorted((k for k, v in value_set.items() if not v.item_is_valid()))

        if render_error and invalid:
            md = error_title
            for i in invalid:
                md = f"{md}\n  - {i}"
            container.error(md)

        return invalid

    def get_step_inputs(self, step_id: str) -> ValueSet:

        return self.pipeline.get_step_inputs(step_id)

    def get_step_outputs(self, step_id: str) -> ValueSet:

        return self.pipeline.get_step_outputs(step_id)

    def process_stage(
        self, stage_nr: int, render_result: bool = False, container: DeltaGenerator = st
    ) -> typing.Mapping[int, typing.Mapping[str, typing.Union[None, str, Exception]]]:
        """Process all steps within the pipeline that are part of the specified stage (or a required stage below)."""

        return st.kiara.process_pipeline_stage(
            pipeline=self.pipeline,
            stage_nr=stage_nr,
            render_result=render_result,
            container=container,
        )

    def get_processing_job_details(self, job_or_step_id: str) -> Job:

        return st.kiara.get_pipeline_processing_job_details(
            pipeline=self.pipeline, job_or_step_id=job_or_step_id
        )

    def render_step_processing_result(
        self,
        result: str,
        container: DeltaGenerator = st,
    ):
        """Render the result of a step processing command into the specified container."""

        st.kiara.render_pipeline_step_processing_result(
            pipeline=self.pipeline, result=result, container=container
        )

    def render_stage_processing_result(
        self,
        result: typing.Mapping[
            int, typing.Mapping[str, typing.Union[None, str, Exception]]
        ],
        only_stage: typing.Optional[int] = None,
        container: DeltaGenerator = st,
    ):
        """Render the result of a stage processing command into the specified container."""

        st.kiara.render_pipeline_stage_processing_result(
            pipeline=self.pipeline,
            result=result,
            only_stage=only_stage,
            container=container,
        )

    def process_step(
        self,
        step_id: str,
        wait_for_processing_to_finish: bool = True,
        render_result: bool = False,
        container: DeltaGenerator = st,
    ) -> str:
        """Process the specified step (incl. all steps of required stages that come before).

        Other steps in the same stage will not be processed.
        """

        return st.kiara.process_pipeline_step(
            pipeline=self.pipeline,
            step_id=step_id,
            wait_for_processing_to_finish=wait_for_processing_to_finish,
            render_result=render_result,
            container=container,
        )

    @abc.abstractmethod
    def run_page(self, st: DeltaGenerator):
        pass
