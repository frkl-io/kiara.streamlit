# -*- coding: utf-8 -*-

"""Render a date selection widget, and print the day of the selected date.
"""
import datetime

import streamlit as st

import kiara_streamlit

kiara_streamlit.init()

result: datetime.date = st.kiara.value_input_date(
    label="Enter a date.", default="1919-01-01"
)
st.write(result.day)
