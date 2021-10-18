# -*- coding: utf-8 -*-
import typing

import networkx as nx
import streamlit as st
from kiara import Pipeline
from kiara.data import Value
from kiara.pipeline.controller.batch import BatchControllerManual
from kiara.processing import Job, JobStatus
from streamlit.delta_generator import DeltaGenerator

from kiara_streamlit.components import KiaraComponentMixin


class KiaraPipelineComponentsMixin(KiaraComponentMixin):
    def pipeline_status(
        self, pipeline: Pipeline, container: DeltaGenerator = st
    ) -> None:

        md = "### **Inputs**\n"
        for stage, fields in pipeline.get_pipeline_inputs_by_stage().items():
            md = f"{md}\n"
            for field in fields:
                value = pipeline.inputs[field]
                md = f"{md}* **{field}**: *{value.item_status()}*\n"

        md = f"\n{md}### **Steps**\n"
        for stage, steps in pipeline.get_steps_by_stage().items():
            md = f"{md}\n"
            for step_id in steps.keys():
                job_details = pipeline._controller.get_job_details(step_id)
                if job_details is None:
                    status = "not run yet"
                elif job_details.status == JobStatus.FAILED:
                    status = "failed"
                else:
                    status = "finished"

                md = f"{md}* **{step_id}**: *{status}*\n"

        md = f"\n{md}### **Outputs**\n"
        for stage, fields in pipeline.get_pipeline_outputs_by_stage().items():
            md = f"{md}\n"
            for field in fields:
                value = pipeline.outputs[field]
                status = "ready" if value.is_set else "not ready"
                md = f"{md}* **{field}**: *{status}*\n"

        container.markdown(md)

    def set_pipeline_inputs(
        self,
        pipeline: Pipeline,
        inputs: typing.Mapping[str, typing.Any],
        render_errors: bool = True,
        container: DeltaGenerator = st,
    ) -> typing.Mapping[str, typing.Union[Value, Exception]]:
        """Set one, several or all inputs of a pipeline.

        If 'render_results' is set to True, an informational component about the status of each of the just set
        inputs will be rendered.
        """

        cleaned_inputs: typing.Dict[str, typing.Any] = {}
        result: typing.Dict[str, typing.Union[Value, Exception]] = {}
        for k, v in inputs.items():
            if isinstance(v, Value):
                cleaned_inputs[k] = v

            current = pipeline.inputs.get(k)
            assert isinstance(current, Value)
            if not current.is_set:
                cleaned_inputs[k] = v
            else:
                if current.get_value_data() != v:
                    cleaned_inputs[k] = v
                else:
                    result[k] = current

        if cleaned_inputs:
            _set_result = pipeline.inputs.set_values(**cleaned_inputs)
            result.update(_set_result)

        if render_errors:

            md = ""
            for field_name in sorted(result.keys()):
                _result = result[field_name]
                if isinstance(_result, Exception):
                    md = f"{md}\n* **{field_name}**: *{_result}*"
                # else:
                #     status = pipeline.inputs[field_name].item_status()
                #     md = f"{md}\n* **{field_name}**: *{status}*"

            if md:
                container.error(md)

        return result

    def check_pipeline_step_requirements_valid(
        self,
        pipeline: Pipeline,
        step_id: str,
        render_details: bool = True,
        container: DeltaGenerator = st,
    ) -> typing.List[str]:
        """Check whether all dependency steps for the specified step are ready.

        Returns all step_ids of steps that are not.
        """

        execution_graph: nx.DiGraph = pipeline.structure.execution_graph

        requirements = set()
        for node in execution_graph.nodes:
            if node in [step_id, "__root__"]:
                continue
            try:
                shortest_path = nx.shortest_path(execution_graph, node, step_id)
                shortest_path.remove(step_id)
                for item in shortest_path:
                    if pipeline.get_step(item).required:
                        requirements.add(item)
            except Exception:
                # means no path
                pass

        not_ready = []
        for step_id in requirements:
            if not pipeline.controller.step_is_finished(step_id=step_id):
                not_ready.append(step_id)

        if render_details and not_ready:
            md = "Not ready to process this step yet. Missing required step(s):"
            for step_id in not_ready:
                md = f"{md}\n  - {step_id}"

            container.error(md)

        return not_ready

    def check_pipeline_stage_requirements_valid(
        self,
        pipeline: Pipeline,
        stage: int,
        render_details: bool = True,
        container: DeltaGenerator = st,
    ) -> bool:
        """Check if all the required inputs for this stage are valid.

        If 'render_details' is set to True, an error message with details for invalid inputs will be displayed if there
        are any.

        Returns 'True' if all requirements are fulfilled, otherwise 'False'.
        """

        pipeline_status = pipeline.controller.check_inputs_status()
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

    def process_pipeline_stage(
        self,
        pipeline: Pipeline,
        stage_nr: int,
        render_result: bool = False,
        container: DeltaGenerator = st,
    ) -> typing.Mapping[int, typing.Mapping[str, typing.Union[None, str, Exception]]]:
        """Process all steps within the pipeline that are part of the specified stage (or a required stage below).

        Returns a dict with the stage id as key, and another dict with step_id as key and processing result as value.
        TODO: explain result dict structure
        """

        if not isinstance(pipeline.controller, BatchControllerManual):
            raise Exception(
                "Invalid pipeline controller type: only 'BatchControllerManual' supported at the moment."
            )

        process_result: typing.Mapping[
            int, typing.Mapping[str, typing.Union[None, str, Exception]]
        ] = pipeline.controller.process_stage(stage_nr=stage_nr)
        if render_result:
            self.render_pipeline_stage_processing_result(
                pipeline=pipeline,
                result=process_result,
                only_stage=stage_nr,
                container=container,
            )

        return process_result

    def get_pipeline_processing_job_details(
        self, pipeline: Pipeline, job_or_step_id: str
    ) -> Job:
        """Return job details for the specified job id within a pipeline."""

        job = pipeline.controller.get_job_details(job_or_step_id)
        if job is None:
            raise Exception(f"No job for job or step id: {job_or_step_id}.")
        return job

    def render_pipeline_step_processing_result(
        self,
        pipeline: Pipeline,
        result: str,
        container: DeltaGenerator = st,
    ):
        """Render the result of a step processing command into the specified container."""

        container.write(result)

    def render_pipeline_stage_processing_result(
        self,
        pipeline: Pipeline,
        result: typing.Mapping[
            int, typing.Mapping[str, typing.Union[None, str, Exception]]
        ],
        only_stage: typing.Optional[int] = None,
        container: DeltaGenerator = st,
    ):
        """Render the result of a stage processing command into the specified container."""

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

            job_details = pipeline.controller.get_job_details(job_id)
            if not job_details:
                raise Exception(f"No job details for job id: {job_id}")
            if job_details.status == JobStatus.FAILED:
                step = pipeline.get_step(step_id)
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
                job_details = pipeline.controller.get_job_details(job_id)

                if job_details is None:
                    raise Exception(f"No job details for job id: {job_id}.")

                runtime = job_details.runtime

                if job_details.status == JobStatus.SUCCESS:
                    md = f"{md} (success): runtime: {runtime} sec"
                elif job_details.status == JobStatus.FAILED:
                    step = pipeline.get_step(step_id)
                    if step.required:
                        md = f"{md} (failed:\n    - error: {job_details.error}"
                        md = f"{md}\n    - runtime: {runtime} sec"
                    else:
                        md = f"{md} (failed): not required"

                outputs = pipeline.get_step_outputs(step_id=step_id)
                results[step_id] = outputs

        if failed:
            container.error(md)
        else:
            container.markdown(md)

        return results

    def process_pipeline_step(
        self,
        pipeline: Pipeline,
        step_id: str,
        wait_for_processing_to_finish: bool = True,
        render_result: bool = False,
        container: DeltaGenerator = st,
    ) -> str:
        """Process the specified step (incl. all steps of required stages that come before).

        Other steps in the same stage will not be processed.
        """
        job_id = pipeline.controller.process_step(
            step_id=step_id, wait=wait_for_processing_to_finish, raise_exception=False
        )

        job = pipeline.controller.get_job_details(job_id)
        assert job is not None

        if job.status == JobStatus.SUCCESS:
            r = "Success"
        elif job.status == JobStatus.FAILED:
            r = f"Failed: {job.error}"

        # process_result: typing.Mapping[str, typing.Union[None, str, Exception]] = r
        process_result: str = r

        if render_result and process_result:
            self.render_pipeline_step_processing_result(
                pipeline=pipeline, result=process_result, container=container
            )

        return process_result
