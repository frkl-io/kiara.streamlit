# -*- coding: utf-8 -*-
import os
import sys

from appdirs import AppDirs

kiara_stremalit_app_dirs = AppDirs("kiara-streamlit", "frkl")

if not hasattr(sys, "frozen"):
    KIARA_MODULE_BASE_FOLDER = os.path.dirname(__file__)
    """Marker to indicate the base folder for the `kiara_streamlit` module."""
else:
    KIARA_MODULE_BASE_FOLDER = os.path.join(sys._MEIPASS, "kiara")  # type: ignore
    """Marker to indicate the base folder for the `kiara_streamlit` module."""

KIARA_STREAMLIT_RESOURCES_FOLDER = os.path.join(KIARA_MODULE_BASE_FOLDER, "resources")
"""Default resources folder for this package."""

MODULE_DEV_STREAMLIT_FILE = os.path.join(
    KIARA_STREAMLIT_RESOURCES_FOLDER, "module_dev.py"
)
EXAMPLE_BASE_DIR = os.path.join(KIARA_STREAMLIT_RESOURCES_FOLDER, "examples")
TEMPLATES_BASE_DIR = os.path.join(KIARA_STREAMLIT_RESOURCES_FOLDER, "templates")
