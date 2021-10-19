# -*- coding: utf-8 -*-
import atexit
import copy
import os
import shutil
import typing
import uuid
from functools import partial

import streamlit as st
from kiara import Kiara
from kiara.config import KiaraConfig

from kiara_streamlit.components.mgmt import AllComponentsMixin, ComponentMgmt
from kiara_streamlit.defaults import (
    EXAMPLE_BASE_DIR,
    ONBOARD_MAKER_KEY,
    kiara_stremalit_app_dirs,
)


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

        self._temp_dir = os.path.join(
            kiara_stremalit_app_dirs.user_cache_dir, str(uuid.uuid4())
        )

        def del_temp_dir():
            shutil.rmtree(self._temp_dir, ignore_errors=True)

        atexit.register(del_temp_dir)

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
            comps = AllComponentsMixin(temp_dir=self._temp_dir)
            comps._kiara = self.kiara
            st.session_state["__kiara_components__"] = comps
        return st.session_state.__kiara_components__

    def wants_onboarding(self) -> bool:
        onboarding = st.session_state.get(ONBOARD_MAKER_KEY, None)
        if onboarding and onboarding["enabled"] is True:
            return True
        else:
            st.session_state.pop(ONBOARD_MAKER_KEY, None)
            return False

    def _get_component(self, component_name) -> typing.Callable:

        ga_func = self._component_mgmt.get_component(component_name)
        comp_func = partial(ga_func, self.components)

        return comp_func

    def __dir__(self) -> typing.Iterable[str]:

        return self._avail_methods
