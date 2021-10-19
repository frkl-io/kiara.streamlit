# -*- coding: utf-8 -*-
import streamlit as st

import kiara_streamlit

st.set_page_config(page_title="Kiara experiment: dynamic operation", layout="centered")

kiara_streamlit.init()

if st.kiara.wants_onboarding():
    print("ONBOARDING")
    if st.kiara.onboard_page():
        st.experimental_rerun()

else:
    print("NOT ONBOARDING")
    selected_table = st.kiara.value_input_table(
        label="Select table",
        add_no_value_option=True,
        onboard_options={"enabled": True, "source_default": "folder"},
        key="selected_table",
    )

    if selected_table:
        st.dataframe(selected_table.get_value_data().to_pandas())
