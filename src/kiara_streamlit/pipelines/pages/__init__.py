# -*- coding: utf-8 -*-
import abc
import typing

import networkx as nx
import streamlit as st
from kiara import Pipeline
from kiara.data import Value, ValueSet
from kiara.data.values.value_set import check_valueset_valid
from kiara.pipeline.controller.batch import BatchControllerManual
from kiara.processing import Job, JobStatus
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

        pipeline_status = self.pipeline_controller.check_inputs_status()
        invalid_inputs = set()
        for i in range(1, stage):
            stage_status = pipeline_status[i]
            for step_id, step_status in stage_status.items():
                if step_status["required"]:
                    invalid_inputs.update(step_status["invalid_inputs"])

        if invalid_inputs:

            if render_details:
                md = (
                    "Not ready to process this stage yet. Missing required step inputs:"
                )
                for ii in invalid_inputs:
                    md = f"{md}\n  - {ii}"
                md = f"{md}\n\nMake sure you have all required pipeline inputs set, and all required steps processed."
                container.error(md)

            return False
        else:
            return True

    def check_step_requirements_valid(
        self, step_id: str, render_details: bool = True, container: DeltaGenerator = st
    ) -> typing.List[str]:

        execution_graph: nx.DiGraph = self.pipeline.structure.execution_graph

        requirements = set()
        for node in execution_graph.nodes:
            if node in [step_id, "__root__"]:
                continue
            try:
                shortest_path = nx.shortest_path(execution_graph, node, step_id)
                shortest_path.remove(step_id)
                for item in shortest_path:
                    if self.pipeline.get_step(item).required:
                        requirements.add(item)
            except Exception:
                # means no path
                pass

        not_ready = []
        for step_id in requirements:
            if not self.pipeline_controller.step_is_finished(step_id=step_id):
                not_ready.append(step_id)

        if render_details and not_ready:
            md = "Not ready to process this step yet. Missing required step(s):"
            for step_id in not_ready:
                md = f"{md}\n  - {step_id}"

            container.error(md)

        return not_ready

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

    def render_step_processing_result(
        self,
        result: str,
        container: DeltaGenerator = st,
    ):
        """Render the result of a step processing command into the specified container."""

        container.write(result)

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
            # expander = container.expander(
            #     "Processing details (Skipped)", expanded=False
            # )
            # expander.write(f"No processing done for stage '{only_stage}'.")
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

        md = "#### Processing log"
        if failed:
            md = f"{md} (failed)"
        else:
            md = f"{md} (success)"

        for step_id, job_id in details.items():

            md = f"{md}\n  - step '{step_id}'"
            if job_id is None:
                md = f"{md} (skipped)"
            elif isinstance(job_id, Exception):
                md = f"{md} (failed):"
                md = f"{md}\n    - {str(job_id)}"
            else:
                job_details = self.pipeline_controller.get_job_details(job_id)

                if job_details is None:
                    raise Exception(f"No job details for job id: {job_id}.")

                runtime = job_details.runtime

                if job_details.status == JobStatus.SUCCESS:
                    md = f"{md} (success): runtime: {runtime} sec"
                elif job_details.status == JobStatus.FAILED:
                    step = self.pipeline.get_step(step_id)
                    if step.required:
                        md = f"{md} (failed:\n    - error: {job_details.error}"
                        md = f"{md}\n    - runtime: {runtime} sec"
                    else:
                        md = f"{md} (failed): not required"

                outputs = self.pipeline.get_step_outputs(step_id=step_id)
                results[step_id] = outputs

        if failed:
            container.error(md)
        else:
            container.markdown(md)

        return results

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
        job_id = self.pipeline_controller.process_step(
            step_id=step_id, wait=wait_for_processing_to_finish, raise_exception=False
        )

        job = self.pipeline_controller.get_job_details(job_id)
        assert job is not None

        if job.status == JobStatus.SUCCESS:
            r = "Success"
        elif job.status == JobStatus.FAILED:
            r = f"Failed: {job.error}"

        # process_result: typing.Mapping[str, typing.Union[None, str, Exception]] = r
        process_result: str = r

        if render_result and process_result:
            self.render_step_processing_result(process_result, container=container)

        return process_result

    @abc.abstractmethod
    def run_page(self, st: DeltaGenerator):
        pass
