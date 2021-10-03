#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `kiara_modules_default` package."""

import pytest  # noqa

import kiara_streamlit


def test_assert():

    assert kiara_streamlit.get_version() is not None
