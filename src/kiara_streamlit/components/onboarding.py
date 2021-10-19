# -*- coding: utf-8 -*-
import os
import typing

import streamlit as st
from kiara.data import Value
from kiara.operations import Operation
from streamlit.delta_generator import DeltaGenerator

from kiara_streamlit.components import KiaraComponentMixin
from kiara_streamlit.defaults import ONBOARD_MAKER_KEY

CANCEL_MARKER = "__CANCEL__"


class KiaraOnboardingComponentsMixin(KiaraComponentMixin):
    def import_table_from_folder(
        self,
        store_table: typing.Union[bool, str, typing.Iterable[str]] = False,
        key: typing.Optional[str] = None,
        container: DeltaGenerator = st,
    ) -> typing.Union[None, str, Value]:

        folder_path = container.text_input("Specify path to folder", key=key)

        if store_table is True:
            default_alias = ""
            if folder_path:
                default_alias = folder_path.split(os.path.sep)[-1]
            alias = container.text_input("Alias", value=default_alias)
            if alias:
                aliases = [alias]
            else:
                aliases = []
        elif isinstance(store_table, str):
            aliases = [store_table]
        elif isinstance(store_table, typing.Iterable):
            aliases = list(store_table)

        msg_col, cancel_col, onboard_col = container.columns([6, 1, 1])
        msg = msg_col.empty()

        cancel_button = cancel_col.button("Cancel")
        import_button = onboard_col.button("Onboard")

        if cancel_button:
            return CANCEL_MARKER

        if not folder_path:
            msg.write("No folder path specified, not doing anything...")
            return None

        if not os.path.isdir(os.path.realpath(folder_path)):
            msg.write("Specified folder does not exist, doing nothing...")
            return None

        if not import_button:
            return None

        if not aliases:
            msg.info("No alias specfied, not importing folder...")
            return None

        import_op: Operation = st.kiara.get_operation(
            "file_bundle.import_from.local.folder_path"
        )

        with container.spinner("Importing folder..."):
            import_result = import_op.run(source=folder_path)
        imported_file_bundle: Value = import_result.get_value_obj("value_item")

        convert_op: Operation = st.kiara.get_operation("file_bundle.convert_to.table")
        with container.spinner("Converting to table..."):
            convert_result = convert_op.run(value_item=imported_file_bundle)

        table_obj = convert_result.get_value_obj("value_item")
        if store_table is False:
            return table_obj
        else:
            stored = table_obj.save(aliases=aliases)
            if not aliases:
                return stored.id
            else:
                return aliases[0]

    def import_table_from_file(
        self,
        store_table: typing.Union[bool, str, typing.Iterable[str]] = False,
        file_type: typing.Optional[typing.Union[str, typing.List[str]]] = None,
        key: typing.Optional[str] = None,
        container: DeltaGenerator = st,
    ) -> typing.Union[None, str, Value]:

        uploaded_file = st.file_uploader(
            "Select file", type=file_type, accept_multiple_files=False, key=key
        )

        if store_table is True:
            alias = container.text_input("Alias")
            if alias:
                aliases = [alias]
            else:
                aliases = []
        elif isinstance(store_table, str):
            aliases = [store_table]
        elif isinstance(store_table, typing.Iterable):
            aliases = list(store_table)

        msg_col, cancel_col, onboard_col = container.columns([6, 1, 1])
        msg = msg_col.empty()

        cancel_button = cancel_col.button("Cancel")
        import_button = onboard_col.button("Onboard")

        if cancel_button:
            return CANCEL_MARKER

        if not uploaded_file:
            msg.write("No file uploaded, not doing anything...")
            return None

        if not import_button:
            return None

        if not aliases:
            msg.info("No alias specfied, not saving...")
            return None

        convert_op: Operation = st.kiara.get_operation("file.convert_to.table")
        with container.spinner("Importing file..."):
            value_obj = self.import_uploaded_file(uploaded_file)  # type: ignore

        with container.spinner("Converting to table..."):
            convert_result = convert_op.run(value_item=value_obj)

        table_obj = convert_result.get_value_obj("value_item")
        if store_table is False:
            return table_obj
        else:
            stored = table_obj.save(aliases=aliases)
            if not aliases:
                return stored.id
            else:
                return aliases[0]

    def onboard_table(
        self,
        use_sidebar: bool = True,
        key: typing.Optional[str] = None,
        source_default: typing.Optional[str] = "file",
        container: DeltaGenerator = st,
    ) -> typing.Optional[str]:

        options = ["file", "folder"]
        index = 0
        if source_default:
            try:
                index = options.index(source_default)
            except Exception as e:
                print(f"Can't pre-set index: {e}")

        if use_sidebar:
            source = st.sidebar.selectbox(
                "Select table source",
                options=options,
                index=index,
                key=f"_source_select_{key}",
            )
        else:
            source = container.selectbox(
                "Select table source",
                options=options,
                index=index,
                key=f"_source_select_{key}",
            )

        if source == "folder":
            table = self.import_table_from_folder(
                store_table=True, key=key, container=container
            )
        elif source == "file":
            table = self.import_table_from_file(
                store_table=True, key=key, container=container
            )
        else:
            raise NotImplementedError()

        assert isinstance(table, str)

        return table

    def onboard_page(
        self,
        use_sidebar: bool = True,
        key: typing.Optional[str] = None,
        container: DeltaGenerator = st,
    ):

        save_details = st.session_state[ONBOARD_MAKER_KEY]
        save_key = save_details["store_key"]
        value_type = save_details["value_type"]

        source_default = save_details.get("source_default", None)

        if value_type != "table":
            raise NotImplementedError()

        table_alias = self.onboard_table(
            source_default=source_default,
            use_sidebar=use_sidebar,
            key=key,
            container=container,
        )

        if table_alias == CANCEL_MARKER:

            del st.session_state[ONBOARD_MAKER_KEY]
            st.experimental_rerun()
        elif table_alias:

            if save_key in st.session_state.keys():
                del st.session_state[save_key]

            if table_alias:
                st.session_state[save_key] = table_alias

            del st.session_state[ONBOARD_MAKER_KEY]
            st.experimental_rerun()
