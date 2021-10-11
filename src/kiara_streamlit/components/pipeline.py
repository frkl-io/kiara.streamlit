# -*- coding: utf-8 -*-
import typing

import streamlit as st
from kiara import Pipeline
from kiara.data import Value
from kiara.processing import JobStatus
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
