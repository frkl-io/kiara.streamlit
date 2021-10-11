# -*- coding: utf-8 -*-
import typing

from streamlit.delta_generator import DeltaGenerator

from kiara_streamlit.pipelines.pages import PipelinePage


class StepPage(PipelinePage):
    """A page that renders a UI for a specific pipeline stage."""

    def __init__(self, id: str, config: typing.Mapping[str, typing.Any] = None):

        super().__init__(id=id, config=config)

    @property
    def step_id(self):

        step = self.page_config.get("step_id", self.id)
        return step

    def run_page(self, st: DeltaGenerator):

        # make sure all required previous steps are ready
        self.check_step_requirements_valid(self.step_id)

        step_inputs = self.get_pipeline_inputs_for_step(self.step_id)

        st.markdown("### Inputs")
        # render a set of input components for this step
        step_input_data = st.kiara.valueset_input(
            step_inputs, key=self.get_page_key("step_inputs"), defaults=step_inputs
        )

        # set the inputs we got from the user
        self.set_pipeline_inputs(inputs=step_input_data, render_errors=True)

        process_btn = st.button("Process", key=self.get_page_key("process_button"))

        # check if the process button was clicked
        if process_btn:
            # get updated pipeline inputs after user input
            pipeline_step_inputs = self.get_step_inputs(self.step_id)

            # check if all inputs are valid, otherwise render error and do nothing
            invalid = self.check_invalid_values(pipeline_step_inputs, render_error=True)
            if not invalid:
                # process the step
                print("PROCESSING")
                self._cache["last_processing_result"] = self.process_step(
                    self.step_id, render_result=False
                )

        last_processing_result = self._cache.get("last_processing_result", None)
        if last_processing_result is not None:
            # here we print the results of the processing (if there are any)
            # the reason this is stored in the object is to be able to display the results if the user
            # navigated away and back from/to this page
            self.render_step_processing_result(last_processing_result, container=st)

        # let the user choose whether they want to see all step outputs
        show_step_outputs = st.checkbox("Show step outputs", value=False)
        if show_step_outputs:
            _outputs = self.get_step_outputs(self.step_id)
            st.kiara.write_valueset(
                _outputs, key=self.get_page_key("step_output_preview"), container=st
            )

        # let the user choose whether they want to see pipeline outputs of this stage (if any)
        outputs = self.get_pipeline_outputs_for_step(self.step_id)
        if outputs:
            # if there are any pipeline outputs produced in this stage, display them here
            show_outputs = st.checkbox("Show pipeline outputs", value=True)
            if show_outputs:
                st.kiara.write_valueset(
                    outputs,
                    add_save_option=True,
                    container=st,
                    key=self.get_page_key("pipeline_output_preview"),
                )
