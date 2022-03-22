# -*- coding: utf-8 -*-
import typing

import pyarrow as pa
import streamlit as st
from kiara.data import ValueSet
from streamlit.delta_generator import DeltaGenerator
from streamlit_ace import st_ace

from kiara_streamlit.components import KiaraComponentMixin


class TableComponentsMixin(KiaraComponentMixin):
    def sql_query(
        self,
        table_name: typing.Optional[str] = None,
        use_sidebar: bool = False,
        show_preview_table_option: bool = False,
        show_preview_table_option_default: bool = False,
        show_table_metadata_option: bool = False,
        show_metadata_option_default: bool = False,
        show_sampling_option: bool = False,
        show_save_option: bool = False,
        editor_height: typing.Optional[int] = None,
        key: typing.Optional[str] = None,
        container: DeltaGenerator = st,
    ):
        """Render a sql query editor.

        This component has a few configuration options (to be documented). If you don't provide a 'table_name' argument, a selectbox will be rendered
        that lets the user choose one of the tables in the kiara data store.
        There are also options to show/hide other usability helpers like a source table preview, sampling option, etc.
        """

        if not table_name:
            table_name = self.value_select_box(  # type: ignore
                value_type="table",
                add_no_value_option=True,
                key=key,
                container=st.sidebar if use_sidebar else container,
            )

        source_table = None

        if show_preview_table_option:
            if use_sidebar:
                show_table = st.sidebar.checkbox(
                    "Show source table", value=show_preview_table_option_default
                )
            else:
                show_table = container.checkbox(
                    "Show source table", value=show_preview_table_option_default
                )

        if show_table_metadata_option:

            if use_sidebar:
                show_metadata = st.sidebar.checkbox(
                    "Show source table metadata", value=show_metadata_option_default
                )
            else:
                show_metadata = container.checkbox(
                    "Show source table metadata", value=show_metadata_option_default
                )

        sample_size = 100
        sampled = False
        if show_sampling_option:
            if use_sidebar:
                show_sampling = st.sidebar.checkbox("Sample data", value=False)
            else:
                show_sampling = container.checkbox("Sample data", value=False)

            if show_sampling:
                if use_sidebar:
                    sample_size = st.sidebar.slider(
                        "Sample size (in %)", min_value=0, max_value=100, value=100
                    )
                else:
                    sample_size = container.slider(
                        "Sample size (in %)", min_value=0, max_value=100, value=100
                    )

                if sample_size < 100:
                    sampled = True

        def get_source_table():
            source_table = self.data_store.get_value_obj(table_name)
            # size = source_table.get_metadata('table')['table']['size']

            if sampled:
                result = self.run_operation(  # type: ignore
                    "table.sample.percent",
                    inputs={"value_item": source_table, "sample_size": sample_size},
                )
                source_table = result.get_value_obj("sampled_value")

            return source_table

        if show_preview_table_option:

            if show_table:  # noqa

                if sampled:
                    st.subheader("Source table (sampled)")
                else:
                    st.subheader("Source table")

                if not table_name:
                    container.write("No table selected")
                else:
                    if source_table is None:
                        source_table = get_source_table()

                    source_table_data: pa.Table = source_table.get_value_data()
                    container.dataframe(source_table_data.to_pandas())

        if show_table_metadata_option:

            if show_metadata:  # noqa
                container.subheader("Source table metadata")
                if not table_name:
                    container.write("No table selected")
                else:
                    if source_table is None:
                        source_table = get_source_table()
                    container.write(source_table.get_metadata("table"))

        container.subheader("SQL query")
        container.caption(
            "Create your sql query, use 'data' as the relation name. E.g 'SELECT * FROM data'."
        )
        sql_query = st_ace(
            height=editor_height,
            language="sql",
            auto_update=False,
            show_gutter=False,
            keybinding="emacs",
            key=f"{key}_sql_editor" if key else None,
        )

        op_outputs: typing.Optional[ValueSet] = None

        if table_name and sql_query:
            try:
                if source_table is None:
                    source_table = get_source_table()

                op_outputs = self.run_operation(  # type: ignore
                    "table.query.sql",
                    inputs={"table": source_table, "query": sql_query},
                )
            except Exception as e:
                container.error(str(e))
                # container.write(e)

        container.subheader("Query result")

        if op_outputs and op_outputs.items_are_valid():
            self.write_valueset(op_outputs, container=container)  # type: ignore
        else:
            container.write("-- no result --")

        if show_save_option:
            exp = container.expander("Save result")
            alias = exp.text_input("Alias")
            save_button = exp.button("Save")

            if save_button:
                if not alias:
                    exp.write("No alias provided.")
                elif op_outputs is None or not op_outputs.items_are_valid():
                    exp.write("No query result.")
                else:
                    q_result = op_outputs.get_value_obj("query_result")
                    q_result.save([alias])
                    st.experimental_rerun()
