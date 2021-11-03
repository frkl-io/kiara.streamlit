# -*- coding: utf-8 -*-
import abc
import typing
import uuid

import streamlit as st
from kiara.data import Value, ValueSet
from kiara.data.values import ValueSchema
from kiara.data.values.value_set import SlottedValueSet
from kiara.metadata.core_models import DocumentationMetadataModel
from kiara.module_config import ModuleTypeConfigSchema
from kiara.operations import Operation


class OperationPage(abc.ABC):
    def __init__(self, operation: typing.Union[Operation, str]):

        self._id = str(uuid.uuid4())

        if isinstance(operation, str):
            operation = st.kiara.get_operation(operation)
        self._operation: Operation = operation  # type: ignore

        self._input_value: typing.Optional[Value] = None
        self._result_values: typing.Optional[ValueSet] = None
        self._selected_field: typing.Optional[str] = None
        self._cache: typing.Dict[str, typing.Any] = {}

    @property
    def operation(self) -> Operation:
        return self._operation

    @property
    def doc(self) -> DocumentationMetadataModel:
        return self.operation.doc

    @property
    def input_value(self) -> typing.Optional[Value]:
        return self._input_value

    @input_value.setter
    def input_value(self, value: Value):
        # if value is None:
        #     raise Exception("No value provided.")
        # if not value.item_is_valid():
        #     raise Exception("Provided value is not valid.")
        # if self._value is not None:
        #     raise Exception("Value already set for page.")

        self._input_value = value

    @property
    def result_values(self) -> typing.Optional[ValueSet]:
        return self._result_values

    @result_values.setter
    def result_values(self, values: ValueSet):
        # if value is None:
        #     raise Exception("No value provided.")
        # if not value.item_is_valid():
        #     raise Exception("Provided value is not valid.")
        # if self._value is not None:
        #     raise Exception("Value already set for page.")

        self._result_values = values

    @property
    def selected_field(self) -> typing.Optional[str]:
        return self._selected_field

    @selected_field.setter
    def selected_field(self, field_name: str):
        self._selected_field = field_name

    def get_selected_value(self):

        if (
            self._selected_field is None
            or self._result_values is None
            or not self._result_values.items_are_valid()
        ):
            return None

        return self._result_values.get_value_obj(self._selected_field)

    @property
    def page_id(self) -> str:
        return self._id

    def get_page_key(self, sub_key: typing.Optional[str] = None) -> str:
        if sub_key:
            return f"_pipeline_page_{self.page_id}_{sub_key}"
        else:
            return f"_pipeline_page_{self.page_id}"

    @property
    def module_type_id(self) -> str:
        return self._operation.module._module_type_id  # type: ignore

    @property
    def module_config(self) -> ModuleTypeConfigSchema:
        return self._operation.module.config

    def run_page(self, is_last_page: bool) -> typing.Optional[ValueSet]:

        if is_last_page:
            if self.input_value is None:
                raise Exception(
                    f"Can't run page '{self.page_id}': input not set (yet)."
                )
            result: typing.Optional[ValueSet] = self._run_page(self.input_value)
            if result is not None and result.items_are_valid():
                self.result_values = result
        else:
            st.write(f"SKIPPING STEP: {self.module_type_id}")

        return self.result_values

    @abc.abstractmethod
    def _run_page(self, value: Value) -> typing.Optional[ValueSet]:
        pass


class FirstOperationPage(OperationPage):
    @property
    def id(self) -> str:
        return "Select dataset"

    @property
    def doc(self) -> DocumentationMetadataModel:
        return DocumentationMetadataModel.from_string("Select existing dataset.")

    def run_page(self, is_last_page: bool) -> typing.Optional[ValueSet]:

        if is_last_page:
            result: typing.Optional[ValueSet] = self._run_page(None)  # type: ignore
            if result is not None and result.items_are_valid():
                self.result_values = result
        else:
            st.write(f"SKIPPING STEP: {self.module_type_id}")

        return self.result_values

    def _run_page(self, value: Value) -> typing.Optional[ValueSet]:

        assert value is None

        value = st.kiara.value_select_panel(
            allow_preview=False, key=self.get_page_key("data_centric_select_root_value")
        )
        if value is None:
            return None
        else:
            value_set = SlottedValueSet.from_schemas(
                schemas={"dataset": ValueSchema(type=value.type_name)},
                initial_values={"dataset": value},
            )
            return value_set

    @property
    def module_type_id(self) -> str:
        return "select_dataset"  # type: ignore


class DefaultOperationPage(OperationPage):
    def _run_page(self, value: Value) -> typing.Optional[ValueSet]:

        match = []
        for field_name, schema in self.operation.input_schemas.items():
            if schema.type == value.type_name:
                match.append(field_name)

        if len(match) == 0:
            raise Exception(
                f"No input with type '{value.type_name}' for operation '{self.operation.id}'."
            )
        elif len(match) > 1:
            raise Exception(
                f"Multiple inputs with type '{value.type_name}' for operation '{self.operation.id}': {', '.join(match)}"
            )

        constants = {match[0]: value}

        op_inputs = st.kiara.operation_inputs(self.operation.id, constants=constants)
        print(op_inputs)
        process_button = st.button("Process")
        if process_button:
            result = st.kiara.run(self.operation, inputs=op_inputs)
            return result
        return None


class DataCentricApp(object):
    @classmethod
    def create(
        cls,
        operation_pages: typing.Optional[typing.Mapping[str, OperationPage]] = None,
        config: typing.Optional[typing.Mapping[str, typing.Any]] = None,
    ) -> "DataCentricApp":

        if "__data_centric_app__" not in st.session_state:

            app = DataCentricApp(operation_pages=operation_pages, config=config)  # type: ignore
            st.session_state["__data_centric_app__"] = app

        else:
            app = st.session_state["__data_centric_app__"]

        return app

    def __init__(
        self,
        operation_pages: typing.Optional[typing.Mapping[str, OperationPage]] = None,
        config: typing.Optional[typing.Mapping[str, typing.Any]] = None,
    ):

        print("CREATING APP")

        if operation_pages is None:
            operation_pages = {}
        self._available_prepared_pages: typing.Mapping[
            str, OperationPage
        ] = operation_pages

        if config is None:
            config = {}
        self._config = config

        self._pages: typing.Dict[int, OperationPage] = {}

        self.add_page(FirstOperationPage(operation=None))  # type: ignore

    def add_page(self, operation_page: typing.Union[str, Operation, OperationPage]):

        if isinstance(operation_page, str):
            if operation_page in self._available_prepared_pages.keys():
                operation_page = self._available_prepared_pages[operation_page]
            else:
                operation_page = st.kiara.get_operation(operation_page)
        if isinstance(operation_page, Operation):
            if operation_page.id in self._available_prepared_pages.keys():
                operation_page = self._available_prepared_pages[operation_page.id]
            else:
                operation_page = DefaultOperationPage(operation=operation_page)

        self._pages[len(self._pages)] = operation_page

    def remove_page(self, amount: int = 1):

        if len(self._pages) <= amount:
            raise Exception(
                f"Can't delete {amount} pages, first step can't be removed."
            )

        i = 0
        for page in reversed(self._pages.keys()):
            self._pages.pop(page)
            i = i + 1
            if i == amount:
                break

    def get_last_page(self) -> OperationPage:

        return self._pages[max(self._pages.keys())]

    def render_navigation(self) -> typing.Mapping[int, bool]:
        st.sidebar.write("### Operations")
        result = {}

        max_page = max(self._pages.keys())

        for nr, op_page in self._pages.items():
            title = op_page.module_type_id
            if title is None:
                title = "Selecting data"

            result[nr] = True
            if len(result) <= 1 or nr != max_page:

                if len(self._pages) > 1:
                    exp = st.sidebar.expander(title, expanded=True)
                    show_details = not exp.checkbox(
                        "Hide", value=False, key=f"hide_details_on_page_{nr}"
                    )
                else:
                    st.sidebar.expander(title, expanded=False)
                    show_details = True
            else:
                exp = st.sidebar.expander(title, expanded=True)
                remove = exp.button("Remove")
                if remove:
                    self.remove_page()
                    st.experimental_rerun()
                show_details = True
            result[nr] = show_details

        return result

    def ask_for_next_operation(
        self, value: typing.Optional[Value]
    ) -> typing.Optional[Operation]:

        st.write("---")
        left, middle, right = st.columns([16, 1, 16])

        right.write("---")

        ignore_patterns = [
            ".*lena.*",
            ".*filter.*_by_date.*",
            ".*tokenize_module_markus.*",
            ".*table.convert.*",
            ".*extract_metadata.*",
            ".*pretty_print.*",
            ".*save",
            "playground.mariella.text_preprocessing.preprocess",
            "playground.markus.topic_modeling.extract_date_and_pub_ref",
            "language.lda.LDA",
            "language.lemmatize.tokens_array",
            "language.tokens.remove_stopwords",
        ]
        next_step: typing.Optional[Operation] = st.kiara.select_matching_operation(
            value=value,
            incl_desc=True,
            incl_op_id=True,
            ignore_patterns=ignore_patterns,
            key="next_operation_selectbox",
            container=left,
        )

        if next_step:
            if next_step.doc.doc:
                right.write(next_step.doc.doc)
            preview_operation = right.checkbox("Display operation details", value=False)

            if preview_operation:
                right.write("**TODO: module details**")
                right.write(f"Operation: {next_step.id}")
                right.write(f"Module: {next_step.module._module_type_id}")  # type: ignore

        select = left.button("Add operation")
        if select:
            if next_step is not None:
                return next_step
            else:
                st.info("No operation selected.")
                return None
        else:
            return None

    def run(self):

        display_details = self.render_navigation()

        # last_values = None
        # last_field = None
        last_value = None

        show_any = any(display_details.values())

        if show_any:
            for page_nr in list(display_details.keys())[0:-1]:
                page = self._pages[page_nr]
                last_value = page.get_selected_value()
                if not last_value:
                    raise Exception(f"No value set for page '{page.module_type_id}'.")
                display = display_details[page_nr]
                if display:
                    exp = st.expander(
                        f"Step {page_nr + 1}: {page.module_type_id} -- {page.doc.description}",
                        expanded=False,
                    )
                    if page.doc.doc is not None:
                        exp.write(page.doc.doc)
                    exp.write("**TODO: inputs used**")
                    exp.write("#### Result preview")
                    st.kiara.write_value(
                        last_value, write_config={"preview": True}, container=exp
                    )

        last_page = self.get_last_page()

        print(f"LAST PAGE: {last_page.module_type_id}")

        if last_value:
            last_page.input_value = last_value

        st.write(
            f"#### Step {max(self._pages.keys()) + 1}: {last_page.module_type_id} -- {last_page.doc.description}"
        )
        if last_page.doc.doc:
            st.write(last_page.doc.doc)
        last_values = last_page.run_page(is_last_page=True)
        print(f"RESULT: {last_values}")
        selected_field = None
        if last_values is not None and last_values.items_are_valid():
            if len(last_values) == 1:
                selected_field = next(iter(last_values.keys()))
            else:
                selected_field = st.selectbox(
                    "Select output to use", options=last_values.keys()
                )

            last_page.selected_field = selected_field

        if len(display_details) == 1:
            label = "Selected data"
        else:
            label = "Operation result"
        expanded = True
        exp = st.expander(label, expanded=expanded)
        selected_value = last_page.get_selected_value()
        st.kiara.write_value(selected_value, container=exp)
        if len(display_details) > 1:
            save_value = st.checkbox(
                "Save value", key=f"value_save_{last_page.page_id}"
            )
            if save_value:
                alias = st.text_input(
                    "Alias", key=f"value_save_alias_{last_page.page_id}"
                )
                save = st.button("Save", key=f"value_save_button_{last_page.page_id}")
                if save:
                    s = selected_value.save(aliases=[alias])
                    st.info(f"Value saved using alias '{alias}', saved id: {s.id}")

        next_operation = self.ask_for_next_operation(value=selected_value)
        if next_operation:
            print(f"ADDING: {next_operation}")
            self.add_page(next_operation)
            st.experimental_rerun()
