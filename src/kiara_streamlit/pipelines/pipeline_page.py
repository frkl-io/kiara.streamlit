# -*- coding: utf-8 -*-
import abc
import typing
import uuid

import streamlit as st
from kiara import Pipeline
from kiara.data import Value, ValueSet
from kiara.data.values.value_set import check_valueset_valid
from kiara.pipeline.controller.batch import BatchControllerManual
from kiara.processing import Job, JobStatus
from streamlit.delta_generator import DeltaGenerator

from kiara_streamlit import KiaraStreamlit
from kiara_streamlit.pipelines import PipelineApp


class PipelinePage(abc.ABC):
    """A class to encapsulate a single page in a streamlit-rendered kiara pipeline."""

    def __init__(self, title: str):

        self._id: str = str(uuid.uuid4())

        self._app: typing.Optional[PipelineApp] = None
        self._title: str = title

    @property
    def app(self) -> PipelineApp:

        if self._app is None:
            raise Exception("App not initialized yet.")

        return self._app

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
        return self._title

    @property
    def ktx(self) -> KiaraStreamlit:
        return self.app.kiara_streamlit

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
        render_results: bool = False,
        container: DeltaGenerator = st,
    ) -> typing.Mapping[str, typing.Union[bool, Exception]]:
        """Set one or several pipeline inputs."""

        return self.ktx.set_pipeline_inputs(
            pipeline=self.pipeline,
            inputs=inputs,
            render_results=render_results,
            container=container,
        )

    def check_valueset_valid(self, value_set: typing.Mapping[str, Value]) -> bool:
        """Check whether all values in a value set have valid values."""

        return check_valueset_valid(value_set=value_set)

    def get_invalid_values(
        self, value_set: typing.Mapping[str, Value]
    ) -> typing.List[str]:

        return sorted((k for k, v in value_set.items() if not v.item_is_valid()))

    def get_step_inputs(self, step_id: str) -> ValueSet:

        return self.pipeline.get_step_inputs(step_id)

    def get_step_outputs(self, step_id: str) -> ValueSet:

        return self.pipeline.get_step_outputs(step_id)

    def process_stage(
        self, stage_nr: int, render_result: bool = False, container: DeltaGenerator = st
    ) -> typing.Mapping[int, typing.Mapping[str, typing.Union[None, str, Exception]]]:
        """Process all steps within the pipeline that are part of the specified stage (or a required stage below)."""

        process_result: typing.Mapping[
            int, typing.Mapping[str, typing.Union[None, str, Exception]]
        ] = self.pipeline_controller.process_stage(stage_nr=stage_nr)
        if render_result:
            self.render_stage_processing_result(
                process_result, only_stage=stage_nr, container=container
            )

        return process_result

    def get_processing_job_details(self, job_or_step_id: str) -> Job:

        job = self.pipeline_controller.get_job_details(job_or_step_id)
        if job is None:
            raise Exception(f"No job for job or step id: {job_or_step_id}.")
        return job

    def render_stage_processing_result(
        self,
        result: typing.Mapping[
            int, typing.Mapping[str, typing.Union[None, str, Exception]]
        ],
        only_stage: typing.Optional[int] = None,
        container: DeltaGenerator = st,
    ):
        """Render the result of a stage processing command into the specified container."""

        # exceptions = { field: d for field, d in result.items() if isinstance(d, Exception) }
        #
        # if exceptions:
        #     expander = st.expander("Processing details (Errors)", expanded=True)
        #     for step_id, exc in exceptions.items():
        #         expander.markdown(f"#### Error in step: {step_id}")
        #         expander.write(exc)
        #     return None
        # else:

        if only_stage is None:
            raise NotImplementedError()

        details = result.get(only_stage, None)

        if not details:
            expander = container.expander(
                "Processing details (Skipped)", expanded=False
            )
            expander.write(f"No processing done for stage '{only_stage}'.")
            return

        results = {}

        failed = False
        for step_id, job_id in details.items():

            if job_id is None:
                # TODO: check, is this correct
                failed = True
                break
            if isinstance(job_id, Exception):
                failed = True
                break

            job_details = self.pipeline_controller.get_job_details(job_id)
            if not job_details:
                raise Exception(f"No job details for job id: {job_id}")
            if job_details.status == JobStatus.FAILED:
                step = self.pipeline.get_step(step_id)
                if step.required:
                    failed = True
                    break

        if failed:
            expander = container.expander("Processing details (Failed)", expanded=False)
        else:
            expander = container.expander(
                "Processing details (Success)", expanded=False
            )

        for step_id, job_id in details.items():

            expander.markdown(f"#### Details for processing step: {step_id}")
            if job_id is None:
                expander.write("-- skipped --")
            elif isinstance(job_id, Exception):
                expander.write(str(job_id))
                expander.write(job_id)
            else:
                job_details = self.pipeline_controller.get_job_details(job_id)

                if job_details is None:
                    raise Exception(f"No job details for job id: {job_id}.")
                runtime = job_details.runtime
                if job_details.status == JobStatus.SUCCESS:
                    expander.markdown(f"Success! Runtime: {runtime} seconds.")
                elif job_details.status == JobStatus.FAILED:
                    jl_c = expander.container()
                    jl_c.error(
                        f"Run failed: {job_details.error}. Runtime: {runtime} seconds."
                    )

                    if hasattr(job_details, "exception") and job_details.exception:
                        jl_c.write(job_details.exception)

                outputs = self.pipeline.get_step_outputs(step_id=step_id)
                results[step_id] = outputs

        return results

    def process_step(self, step_id: str):
        """Process the specified step (incl. all steps of required stages that come before).

        Other steps in the same stage will not be processed.
        """

        raise NotImplementedError()

    @abc.abstractmethod
    def run_page(self, st: DeltaGenerator, kiara_streamlit: KiaraStreamlit):
        pass


class StagePage(PipelinePage):
    """A page that renders a UI for a specific pipeline stage."""

    def __init__(self, title: str, stage: int):

        self._stage: int = stage
        super().__init__(title=title)

    def run_page(self, st: DeltaGenerator, ktx: KiaraStreamlit):

        base_key = f"_pipeline_{self.id}_{self._stage}"

        stage_inputs = self.get_pipeline_inputs_for_stage(self._stage)

        st.markdown("### Inputs")
        stage_input_data = ktx.valueset_input(
            stage_inputs, key=f"{base_key}_stage_inputs", defaults=stage_inputs
        )
        inputs_status_exp = st.expander("Inputs status", expanded=False)
        self.set_pipeline_inputs(
            inputs=stage_input_data, render_results=True, container=inputs_status_exp
        )

        stage_inputs = self.get_pipeline_inputs_for_stage(self._stage)

        process_columns = st.columns((2, 8))
        process_result_placeholder = process_columns[1]
        result_container = process_result_placeholder.empty()

        process_btn = process_columns[0].button(
            "Process", key=f"{base_key}_process_button"
        )

        if process_btn:
            invalid = self.get_invalid_values(stage_inputs)
            if invalid:
                _exp = result_container.expander("Processing details (skipped)")
                _exp.write(
                    f"Not processing stage, inputs contain invalid items: {', '.join(invalid)}."
                )
            else:
                self.process_stage(
                    self._stage, render_result=True, container=result_container
                )

        else:
            _exp = result_container.expander("Processing details")
            _exp.write("-- n/a --")

        st.markdown("### Outputs")
        step_outputs_exp = st.expander("Step outputs", expanded=False)
        for step_id in self.get_step_ids_for_stage(self._stage):
            step_outputs_exp.write(f"#### Step output: '{step_id}")
            _outputs = self.get_step_outputs(step_id)
            self.ktx.valueset_info(_outputs, container=step_outputs_exp)

        st.markdown("#### Pipeline outputs")
        outputs = self.get_pipeline_outputs_for_stage(self._stage)
        if not outputs:
            st.markdown("This stage does not contribute an overall pipeline output.")
        else:
            st.markdown(outputs)
