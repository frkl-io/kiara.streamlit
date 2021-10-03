# -*- coding: utf-8 -*-
import os
import sys

from appdirs import AppDirs

kiara_streamlit_app_dirs = AppDirs("kiara-streamlit", "frkl")

if not hasattr(sys, "frozen"):
    KIARA_STREAMLIT_MODULE_BASE_FOLDER = os.path.dirname(__file__)
    """Marker to indicate the base folder for the `kiara_streamlit` module."""
else:
    KIARA_STREAMLIT_MODULE_BASE_FOLDER = os.path.join(sys._MEIPASS, "kiara_streamlit")  # type: ignore
    """Marker to indicate the base folder for the `kiara_streamlit` module."""

KIARA_RESOURCES_FOLDER = os.path.join(KIARA_STREAMLIT_MODULE_BASE_FOLDER, "resources")
"""Default resources folder for this package."""
