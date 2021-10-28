# -*- coding: utf-8 -*-
import re
import typing

import streamlit as st
from kiara.data import Value, ValueSet
from kiara.defaults import DEFAULT_NO_DESC_VALUE
from kiara.operations import Operation
from streamlit.delta_generator import DeltaGenerator

from kiara_streamlit.components import KiaraComponentMixin


class KiaraOperationComponentsMixin(KiaraComponentMixin):
    def operation_inputs(
        self,
        operation: typing.Union[str, Operation],
        defaults: typing.Optional[typing.Mapping[str, typing.Any]] = None,
        constants: typing.Optional[typing.Mapping[str, typing.Any]] = None,
        key: typing.Optional[str] = None,
        container: DeltaGenerator = st,
    ) -> typing.Mapping[str, typing.Any]:
        """Render a set of input components for the specified operation.

        The return value is a dict with the input field names as keys, and the values (either 'raw' Python objects, or
        already onboarded *kiara* `Value` objects). In either case, you can use the result directly to run a *kiara* operation,
        for example like:

        ``` python
        op_id = "table.cut_column"
        inputs = st.kiara.operation_inputs(op_id)
        op_results = kiara.get_operation(op_id).run(**inputs)
        ```
        """

        if isinstance(operation, str):
            operation = self.get_operation(operation)

        if key:
            key = f"{key}_{operation.id}"
        else:
            key = operation.id

        return self.valueset_input(  # type: ignore
            operation.input_schemas,
            defaults=defaults,
            constants=constants,
            key=key,
            container=container,
        )

    def run_operation(
        self,
        operation: typing.Union[str, Operation],
        inputs: typing.Mapping[str, typing.Union[Value, typing.Any]],
    ) -> ValueSet:

        if isinstance(operation, str):
            operation = self.get_operation(operation)

        result = operation.module.run(**inputs)
        return result

    def get_operation(self, operation_id: str) -> Operation:

        return self.kiara.get_operation(operation_id=operation_id)

    def select_matching_operation(
        self,
        value: typing.Optional[Value],
        show_filter_option: bool = True,
        incl_desc: bool = True,
        incl_op_id: bool = False,
        ignore_patterns: typing.Optional[typing.Iterable[str]] = None,
        key: typing.Optional[str] = None,
        container: DeltaGenerator = st,
    ) -> Operation:

        tags = {}
        if value is None or not value.item_is_valid():
            matching: typing.Dict[str, Operation] = {}
        else:

            if ignore_patterns is None:
                ignore_patterns = []

            matching = {}
            for operation_id, operation in self.kiara.operation_mgmt.profiles.items():
                if ignore_patterns:
                    combined_regex = "(?:% s)" % "|".join(ignore_patterns)
                    ignore_match = False
                    if re.match(combined_regex, operation_id):
                        ignore_match = True
                    if ignore_match:
                        continue

                match = False
                for inp_schema in operation.input_schemas.values():
                    if value.type_name == inp_schema.type:
                        match = True
                        break

                if match:
                    matching[operation_id] = operation
                    tags[
                        operation_id
                    ] = operation.module.get_type_metadata().context.tags

        def func(op_id):
            desc = matching[op_id].doc.description
            if desc == DEFAULT_NO_DESC_VALUE:
                desc = op_id

            if incl_desc and incl_op_id:
                if desc == op_id:
                    r = desc
                else:
                    r = f"{op_id} -- {desc}"
            elif incl_op_id or (not incl_desc and not incl_op_id):
                r = op_id
            elif incl_desc:
                r = desc

            return r

        select_empty = container.empty()
        if tags and show_filter_option:
            all_tags = sorted(
                set((elem for iterable in tags.values() for elem in iterable))
            )
            for t in ["core", "playground", "pipeline"]:
                if t in all_tags:
                    all_tags.remove(t)

            show_filter = container.checkbox(
                "Filter operation list using tags", key=f"{key}_tag_filter_ask"
            )
            if show_filter:
                filter = container.multiselect(
                    "Operation must have tags...",
                    options=all_tags,
                    key=f"{key}_tag_filter",
                )
            else:
                filter = None
            if not filter:
                matching_keys: typing.Iterable[str] = matching.keys()
            else:
                matching_keys = set()
                for op_id, _t in tags.items():
                    match = True
                    for _mt in filter:
                        if _mt not in _t:
                            match = False
                            break
                    if match:
                        matching_keys.add(op_id)
        else:
            matching_keys = matching.keys()

        selected = select_empty.selectbox(
            "Select next operation", options=sorted(matching_keys), format_func=func
        )
        if selected is None:
            return None
        else:
            return matching[selected]
