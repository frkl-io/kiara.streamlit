# -*- coding: utf-8 -*-
import typing
import uuid

import streamlit as st
from kiara.data.values.value_set import SlottedValueSet

from kiara_streamlit.components import KiaraComponentMixin


class KiaraProcessingElement(object):
    def __init__(
        self,
        module: str,
        module_config: typing.Optional[typing.Mapping[str, typing.Any]] = None,
    ):

        self._id: str = str(uuid.uuid4())

        if module_config is None:
            module_config = {}
        else:
            module_config = dict(module_config)

        self._module_type: str = module
        self._module_config: typing.Dict[str, typing.Any] = module_config

        self._module = st.kiara.create_module(
            module_type=self._module_type, module_config=self._module_config
        )

        self._input_slots = SlottedValueSet.from_schemas(
            self._module.input_schemas,
            kiara=st.kiara,
            read_only=False,
            check_for_sameness=True,
        )
        self._output_slots = SlottedValueSet.from_schemas(
            self._module.output_schemas, kiara=st.kiara, read_only=False
        )


class KiaraProcessingComponentsMixin(KiaraComponentMixin):
    def process_module(self):
        pass
