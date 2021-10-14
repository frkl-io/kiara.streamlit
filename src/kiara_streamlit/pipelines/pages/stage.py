# -*- coding: utf-8 -*-
import typing

from streamlit.delta_generator import DeltaGenerator

from kiara_streamlit.pipelines.pages import PipelinePage


class StagePage(PipelinePage):
    """A page that renders a UI for a specific pipeline stage."""

    def __init__(self, id: str, config: typing.Mapping[str, typing.Any] = None):

        if config is None:
            config = {}
        self._stage: int = config.get("stage", None)
        if self._stage is None:
            raise Exception(
                "Invalid config for pipeline page of type 'stage': no 'stage' configuration provided."
            )
        if not isinstance(self._stage, int):
            raise Exception(
                "Invalid config for pipeline page of type 'stage': 'stage' configuration must be an integer."
            )

        super().__init__(id=id)

    def run_page(self, st: DeltaGenerator):

        # make sure all required inputs for the steps in this stage are ready
        self.check_stage_requirements_valid(self._stage)

        # retrieve all relevant inputs for this stage
        stage_inputs = self.get_pipeline_inputs_for_stage(self._stage)

        st.markdown("### Inputs")
        # render a set of input components for this stage
        stage_input_data = st.kiara.valueset_input(
            stage_inputs, key=self.get_page_key("stage_inputs"), defaults=stage_inputs
        )

        # set the inputs we got from the user
        self.set_pipeline_inputs(inputs=stage_input_data, render_errors=True)

        process_btn = st.button("Process", key=self.get_page_key("process_button"))

        # check if the process button was clicked
        if process_btn:
            # get updated pipeline inputs after user input
            pipeline_stage_inputs = self.get_pipeline_inputs_for_stage(self._stage)

            # check if all inputs are valid, otherwise render error and do nothing
            invalid = self.check_invalid_values(
                pipeline_stage_inputs, render_error=True
            )
            if not invalid:
                # process all steps in this stage
                self._cache["last_processing_results"] = self.process_stage(
                    self._stage, render_result=False, container=st
                )

        last_processing_results = self._cache.get("last_processing_results", None)
        if last_processing_results is not None:
            # here we print the results of the processing (if there are any)
            # the reason this is stored in the object is to be able to display the results if the user
            # navigated away and back from/to this page
            self.render_stage_processing_result(
                last_processing_results, only_stage=self._stage, container=st
            )

        # let the user choose whether they want to see all step outputs
        show_step_outputs = st.checkbox("Show step outputs", value=False)
        if show_step_outputs:
            # if the user wants to check step outputs, he can choose to
            for step_id in self.get_step_ids_for_stage(self._stage):
                st.write(f"#### Step output: '{step_id}")
                _outputs = self.get_step_outputs(step_id)
                st.kiara.write_valueset(
                    _outputs, key=self.get_page_key("step_output_preview"), container=st
                )

        # let the user choose whether they want to see pipeline outputs of this stage (if any)
        outputs = self.get_pipeline_outputs_for_stage(self._stage)
        if outputs:
            # if there are any pipeline outputs produced in this stage, display them here
            show_outputs = st.checkbox("Show pipeline outputs", value=True)
            if show_outputs:
                st.kiara.write_valueset(
                    outputs,
                    add_save_option=True,
                    key=self.get_page_key("pipeline_output_preview"),
                    container=st,
                )
