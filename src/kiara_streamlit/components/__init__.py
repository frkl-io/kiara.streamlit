# -*- coding: utf-8 -*-
import typing

import streamlit as st
from kiara import Kiara
from kiara.data import Value
from kiara.data.registry import DataRegistry
from kiara.workflow.kiara_workflow import KiaraWorkflow
from streamlit.delta_generator import DeltaGenerator

if typing.TYPE_CHECKING:
    pass

IMPORT_OPTION = "-- import file --"

# mypy: ignore-errors


class KiaraComponentMixin(object):
    @classmethod
    def create_components_class(
        cls, name: str, *mixins: typing.Iterable[typing.Type["KiaraComponentMixin"]]
    ):

        cls = type(name, tuple(mixins), {})
        return cls

    def __init__(self, **kwargs):

        self._kiara: typing.Optional[Kiara] = None

    @property
    def kiara(self) -> Kiara:

        if self._kiara is None:
            raise Exception("Kiara object not set (yet).")
        return self._kiara

    @property
    def data_store(self) -> DataRegistry:
        return self.kiara.data_store

    @property
    def data_registry(self) -> DataRegistry:
        return self.kiara.data_registry


class KiaraBaseWidgetsMixin(KiaraComponentMixin):
    def value_data(self, value_id: str, container: DeltaGenerator = st):

        value: Value = self.data_store.get_value_obj(value_id, raise_exception=True)
        value_data = value.get_value_data()
        if value.type_name == "table":
            container.dataframe(value_data.to_pandas())
        else:
            container.write(value_data)


class KiaraWorkflowWidgetsMixin(KiaraComponentMixin):
    def workflow_status(self, workflow_alias: str, container: DeltaGenerator = st):

        workflow: KiaraWorkflow = self.get_workflow(workflow_alias)

        state = workflow.get_current_state()
        for step_id, status in state.step_states.items():
            container.markdown(f" - *{step_id}*: {status.name}")

    # def create_workflow_inputs_container(self, workflow_alias: str, container: DeltaGenerator=st):
    #
    #     workflow = self.get_workflow(workflow_alias=workflow_alias)
    #     self.create_input_fields(value_set=workflow.inputs, container=container)
    #
    # def create_steps_details(self, workflow_alias: str, container: DeltaGenerator=st):
    #
    #     workflow = self.get_workflow(workflow_alias=workflow_alias)
    #     for step_id, desc in workflow.steps.steps.items():
    #
    #         exp = container.expander(f"Step: {step_id}")
    #         exp.write(desc.step.module.module_instance_doc)
    #         inputs = workflow.pipeline.get_step_inputs(step_id)
    #         outputs = workflow.pipeline.get_step_outputs(step_id)
    #         exp.write("inputs")
    #         self.create_output_fields(inputs, container=exp)
    #         exp.write("outputs")
    #         self.create_output_fields(outputs, container=exp)
    #
    # def create_workflow_outputs_container(self, workflow_alias: str, container: DeltaGenerator=st):
    #
    #     workflow = self.get_workflow(workflow_alias)
    #     self.create_output_fields(workflow.outputs, container=container)


# class Other(object):
#     def create_data_selection(self, value_type: str, container: DeltaGenerator = str):
#         def transform(value_id: str):
#             if value_id == IMPORT_OPTION:
#                 return None
#             return self.data_store.get_value_obj(value_id)
#
#         import_value = container.checkbox(f"Import new {value_type}")
#         if not import_value:
#             all_files = self.data_store.find_all_values_of_type("file")
#             aliases = set()
#             for f in all_files.values():
#                 aliases.update(f.alias_names)
#
#             selected_data = container.selectbox(
#                 f"Select '{value_type}' dataset", sorted(aliases)
#             )
#
#             if selected_data:
#                 value_md = self.data_store.get_value_info(selected_data)
#                 _md = value_md.metadata.get(value_md.value_type, {}).get(
#                     "metadata_item", {}
#                 )
#                 md_str = "| key | value |\n| --- | --- |\n"
#                 for k, v in _md.items():
#                     md_str = md_str + f"| {k} | {v} |\n"
#                 exp = container.expander("Metadata")
#                 exp.markdown(md_str)
#                 select_button = container.button("Select")
#                 if select_button:
#                     new_data = selected_data
#                     return new_data, transform
#
#             return None
#
#         else:
#             with container.container():
#
#                 file_type = None
#                 multiple = False
#
#                 container.write("Import into kiara data-store")
#                 uploaded_files = st.file_uploader(
#                     "Add files", type=file_type, accept_multiple_files=multiple
#                 )
#                 value = ""
#                 if uploaded_files and not multiple:
#                     value = uploaded_files.name
#                 alias = container.text_input("Alias", value=value)
#                 import_button = container.button("Import")
#
#             if import_button:
#                 if not uploaded_files:
#                     container.warning("No files selected")
#                     return None
#
#                 if not alias:
#                     container.warning("No alias provided")
#                     return None
#
#                 value_id = self.onboard_file(uploaded_files, aliases=[alias])
#                 container.info(f"Value '{alias}' (value_id: {value_id}) imported.")
#
#     def create_input_field(
#         self, field_name: str, value: Value, container: DeltaGenerator = str
#     ):
#
#         func_name = f"create_input_field_{value.type_name}"
#         if not hasattr(self, func_name):
#             raise Exception(f"Value type '{value.type_name}' not supported for input.")
#
#         container.write(value.value_schema.doc)
#         func = getattr(self, func_name)
#         default = value.value_schema.default
#         if default in [SpecialValue.NO_VALUE, SpecialValue.NOT_SET]:
#             default = None
#         result = func(
#             field_name=field_name, value=value, default=default, container=container
#         )
#         if isinstance(result, tuple):
#             if len(result) == 1:
#                 new_data = result[0]
#                 callback = None
#             elif len(result) == 2:
#                 new_data = result[0]
#                 callback = result[1]
#             else:
#                 raise Exception(
#                     f"Invalid return value for method '{func_name}. This is a bug."
#                 )
#         else:
#             new_data = result
#             callback = None
#
#         if callback:
#             new_data = callback(new_data)
#
#         if isinstance(new_data, Value):
#             new_data = new_data.get_value_data()
#         try:
#             value.set_value_data(new_data)
#         except Exception as e:
#             print(e)
#
#     def create_input_fields(self, value_set: ValueSet, container: DeltaGenerator = st):
#
#         for idx, (field_name, value) in enumerate(value_set.items()):
#             self.create_input_field(
#                 field_name=field_name, value=value, container=container
#             )
#
#     def create_input_field_boolean(
#         self,
#         field_name: str,
#         value: Value,
#         default: typing.Any,
#         container: DeltaGenerator = st,
#     ):
#
#         new_data = container.checkbox(field_name, value=default)
#         return new_data
#
#     def create_input_field_string(
#         self,
#         field_name: str,
#         value: Value,
#         default: typing.Any,
#         container: DeltaGenerator = st,
#     ):
#
#         if default is None:
#             default = ""
#         new_data = container.text_input(field_name, value=default)
#         return new_data
#
#     def create_input_field_list(
#         self,
#         field_name: str,
#         value: Value,
#         default: typing.Any,
#         container: DeltaGenerator = st,
#     ):
#
#         if default is None:
#             default = []
#         new_data = container.text_area(field_name, value="\n".join(default))
#
#         def transform(text: str):
#             return text.split("\n")
#
#         return new_data, transform
#
#     def create_input_field_file(
#         self,
#         field_name,
#         value: Value,
#         default: typing.Any,
#         container: DeltaGenerator = st,
#     ):
#
#         selection, transform = self.create_data_selection(
#             value_type="file", container=container
#         )
#
#         if not selection:
#             return None
#
#         return selection, transform
#
#     def create_output_fields(self, value_set: ValueSet, container: DeltaGenerator = st):
#
#         # columns = container.columns(len(value_set))
#         for idx, (field_name, value) in enumerate(value_set.items()):
#             self.create_output_field(
#                 field_name=field_name, value=value, container=container
#             )
#
#     def create_output_field(
#         self, field_name: str, value: Value, container: DeltaGenerator = st
#     ):
#
#         func_name = f"create_output_field_{value.type_name}"
#         if not hasattr(self, func_name):
#             raise Exception(f"Value type '{value.type_name}' not supported for output.")
#
#         container.write(value.value_schema.doc)
#         func = getattr(self, func_name)
#         if not value.item_is_valid():
#             value = None
#         func(field_name=field_name, value=value, container=container)
#
#     def create_output_field_table(
#         self,
#         field_name: str,
#         value: typing.Optional[Value],
#         container: DeltaGenerator = st,
#     ):
#
#         if value is None:
#             table: pa.Table = pa.Table.from_pydict({})
#         else:
#             table = value.get_value_data()
#         container.dataframe(table.to_pandas())
#
#     def create_output_field_string(
#         self,
#         field_name: str,
#         value: typing.Optional[Value],
#         container: DeltaGenerator = st,
#     ):
#
#         if value is None:
#             text = ""
#         else:
#             text = value.get_value_data()
#         container.write(text)
#
#     def create_output_field_list(
#         self, field_name, value: typing.Optional[Value], container: DeltaGenerator = st
#     ):
#
#         if value is None:
#             list_value = []
#         else:
#             list_value = value.get_value_data()
#
#         container.write(list_value)
#
#     def create_output_field_dict(
#         self, field_name, value: typing.Optional[Value], container: DeltaGenerator = st
#     ):
#
#         if value is None:
#             dict_value = {}
#         else:
#             dict_value = value.get_value_data()
#
#         container.write(dict_value)
#
#     def create_output_field_file(
#         self, field_name, value: typing.Optional[Value], container: DeltaGenerator = st
#     ):
#
#         if value is None:
#             file_value = {}
#         else:
#             file_value = value.get_value_data().dict()
#
#         container.write(file_value)
