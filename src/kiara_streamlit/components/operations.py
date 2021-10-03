# -*- coding: utf-8 -*-
import typing

import streamlit as st
from kiara.data import Value, ValueSet
from kiara.operations import Operation
from streamlit.delta_generator import DeltaGenerator

from kiara_streamlit.components import KiaraComponentMixin


class KiaraOperationComponentsMixin(KiaraComponentMixin):
    def operation_inputs(
        self,
        operation: typing.Union[str, Operation],
        defaults: typing.Optional[typing.Mapping[str, typing.Any]] = None,
        key: typing.Optional[str] = None,
        container: DeltaGenerator = st,
    ):

        if isinstance(operation, str):
            operation = self.get_operation(operation)

        if key:
            key = f"{key}_{operation.id}"
        else:
            key = operation.id

        return self.valueset_input(  # type: ignore
            operation.input_schemas,
            defaults=defaults,
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
