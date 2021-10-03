# -*- coding: utf-8 -*-
import copy
import typing
from functools import partial

import streamlit as st
from kiara import Kiara
from kiara.config import KiaraConfig

from kiara_streamlit.components.mgmt import AllComponentsMixin, ComponentMgmt
from kiara_streamlit.defaults import EXAMPLE_BASE_DIR


class KiaraStreamlit(object):
    def __init__(
        self,
        kiara_config: typing.Union[
            None, KiaraConfig, typing.Mapping[str, typing.Any]
        ] = None,
    ):

        if not kiara_config:
            kiara_config = KiaraConfig()
        elif isinstance(kiara_config, typing.Mapping):
            kiara_config = KiaraConfig(**kiara_config)
        elif not isinstance(kiara_config, KiaraConfig):
            raise TypeError(
                f"Invalid type for 'kiara_config' argument: {type(kiara_config)}"
            )

        self._kiara_config: KiaraConfig = kiara_config

        self._component_mgmt = ComponentMgmt(example_base_dir=EXAMPLE_BASE_DIR)

        self._avail_kiara_methods: typing.Set[str] = set((x for x in dir(Kiara)))
        self._avail_component_names: typing.Set[str] = set(
            self._component_mgmt.component_names
        )
        # TODO: check duplicates
        _temp = copy.copy(self._avail_component_names)
        _temp.update(self._avail_kiara_methods)
        self._avail_methods: typing.Set[str] = _temp

    def __getattr__(self, item):

        if item in self._avail_kiara_methods:
            return getattr(self.kiara, item)

        elif item in self._avail_component_names:
            comp = self._get_component(item)
            return comp

        return AttributeError(f"Kiara context object does not have attribute '{item}'.")

    @property
    def kiara(self) -> Kiara:

        if "__kiara__" not in st.session_state.keys():
            kiara = Kiara(config=self._kiara_config.copy())
            print(f"KIARA CREATED: {kiara._id}")
            st.session_state["__kiara__"] = kiara
        return st.session_state.__kiara__

    @property
    def components(self) -> AllComponentsMixin:

        if "__kiara_components__" not in st.session_state.keys():
            comps = AllComponentsMixin()
            comps._kiara = self.kiara
            st.session_state["__kiara_components__"] = comps
        return st.session_state.__kiara_components__

    def _get_component(self, component_name) -> typing.Callable:

        ga_func = self._component_mgmt.get_component(component_name)
        comp_func = partial(ga_func, self.components)

        return comp_func

    def __dir__(self) -> typing.Iterable[str]:

        return self._avail_methods


# class KiaraStreamlit(
#     Kiara,
#     KiaraBaseWidgetsMixin,
#     KiaraInputWidgetsMixin,
#     KiaraValueInfoWidgetsMixin,
#     KiaraWorkflowWidgetsMixin,
#     KiaraOperationWidgetsMixin,
#     KiaraPipelineWidgetsMixin,
#     TableWidgetsMixin,
# ):
#     def __init__(self, pipelines_folders: typing.Optional[typing.Iterable[str]] = None):
#
#         self._workflows: typing.Dict[str, KiaraWorkflow] = {}
#         self._valuesets: typing.Dict[str, ValueSet] = {}
#         self._cached_inputs: typing.Dict[str, typing.Any] = {}
#
#         if pipelines_folders is None:
#             pipelines_folders = []
#
#         kc = KiaraConfig(extra_pipeline_folders=pipelines_folders)
#         Kiara.__init__(self, config=kc)
#
#     def save_input_to_cache(self, key: str, value: typing.Any):
#         self._cached_inputs[key] = value
#
#     def get_input_from_cache(self, key: str) -> typing.Any:
#         result = self._cached_inputs.get(key, None)
#         return result
#
#     def store_valueset(self, key: str, valueset: ValueSet, force: bool = False):
#
#         if key in self._valuesets.keys():
#             if not force:
#                 raise Exception(
#                     f"There is already a valueset stored under key: {key}. Use the 'force' parameter if you intend to overwrite."
#                 )
#
#         self._valuesets[key] = valueset
#
#     def load_valueset(self, key: str) -> typing.Optional[ValueSet]:
#         return self._valuesets.get(key, None)

# def create_workflow(self, workflow_alias: str, module_type: str) -> KiaraWorkflow:
#
#     if workflow_alias in self._workflows.keys():
#         raise Exception(f"Workflow with alias '{workflow_alias}' already exists.")
#
#     controller = BatchControllerManual()
#     workflow = self._kiara.create_workflow(
#         module_type, workflow_id=workflow_alias, controller=controller
#     )
#     self._workflows[workflow_alias] = workflow
#
#     return workflow
#
# def get_workflow(self, workflow_alias: str) -> KiaraWorkflow:
#
#     if workflow_alias not in self._workflows.keys():
#         raise Exception(f"No workflow with alias '{workflow_alias}' registered.")
#
#     return self._workflows[workflow_alias]


# def import_file_as_type(
#     self,
#     uploaded_file,
#     value_type: str,
#     aliases: typing.Optional[typing.Iterable[str]] = None,
#     file_aliases: typing.Optional[typing.Iterable[str]] = None,
# ) -> typing.Optional[Value]:
#
#     if not uploaded_file:
#         return None
#
#     convert_operations: ConvertValueOperationType = (
#         self._kiara.operation_mgmt.get_operations("convert")
#     )
#     ops = convert_operations.get_operations_for_target_type(value_type)
#
#     if "file" not in ops.keys():
#         raise Exception(
#             f"Can't import file: no operation to convert from 'file' to '{value_type}' registered."
#         )
#
#     imported_value = self.import_file(
#         uploaded_file=uploaded_file, aliases=file_aliases
#     )
#
#     op = ops["file"]
#     imported_type = op.module.run(value_item=imported_value)
#     value_item = imported_type.get_value_obj("value_item")
#     value_md = value_item.save(aliases=aliases)
#
#     value = self._kiara.data_store.load_value(value_md.value_id)
#     return value
