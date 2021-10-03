# -*- coding: utf-8 -*-

"""Top-level package for kiara_streamlit."""


import logging
import os
import typing

import streamlit as st
from kiara import KiaraEntryPointItem, find_kiara_modules_under
from kiara.config import KiaraConfig

from kiara_streamlit.streamlit import KiaraStreamlit

__author__ = """Markus Binsteiner"""
__email__ = "markus@frkl.io"

log = logging.getLogger("kiara.streamlit")

KIARA_METADATA = {
    "authors": [{"name": __author__, "email": __email__}],
    "description": "Streamlit UI for kiara workflows",
    "references": {
        "source_repo": {
            "desc": "The project git repository.",
            "url": "https://github.com/DHARPA-Project/kiara.streamlit",
        },
        "documentation": {
            "desc": "The url for the project documentation.",
            "url": "https://dharpa.org/kiara.streamlit/",
        },
    },
    "tags": ["streamlit"],
    "labels": {"package": "kiara_streamlit"},
}

modules: KiaraEntryPointItem = (find_kiara_modules_under, ["kiara_streamlit"])


def init(
    kiara_config: typing.Union[
        None, KiaraConfig, typing.Mapping[str, typing.Any]
    ] = None
) -> KiaraStreamlit:
    @st.experimental_singleton
    def get_ktx() -> KiaraStreamlit:

        ktx = KiaraStreamlit(kiara_config=kiara_config)
        return ktx

    if not hasattr(st, "kiara"):
        ktx = get_ktx()
        setattr(st, "kiara", ktx)
        setattr(st, "kiara_components", ktx._component_mgmt)
    else:
        ktx = st.kiara
    return ktx


def get_version():
    from pkg_resources import DistributionNotFound, get_distribution

    try:
        # Change here if project is renamed and does not equal the package name
        dist_name = __name__
        __version__ = get_distribution(dist_name).version
    except DistributionNotFound:

        try:
            version_file = os.path.join(os.path.dirname(__file__), "version.txt")

            if os.path.exists(version_file):
                with open(version_file, encoding="utf-8") as vf:
                    __version__ = vf.read()
            else:
                __version__ = "unknown"

        except (Exception):
            pass

        if __version__ is None:
            __version__ = "unknown"

    return __version__
