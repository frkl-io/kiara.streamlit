# -*- coding: utf-8 -*-

"""This module contains the value type_name classes that are used in the ``kiara_streamlit`` package.
"""
from kiara import KiaraEntryPointItem
from kiara.utils.class_loading import find_value_types_under

value_types: KiaraEntryPointItem = (
    find_value_types_under,
    ["kiara_streamlit.value_types"],
)
