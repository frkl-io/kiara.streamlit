# -*- coding: utf-8 -*-
import os
import typing
import uuid

import streamlit as st
from kiara.data import Value, ValueSet
from kiara.operations import Operation
from streamlit.uploaded_file_manager import UploadedFile

from kiara_streamlit.components import KiaraComponentMixin


class KiaraFileComponentsMixin(KiaraComponentMixin):
    def import_file_bundle(
        self,
        uploaded_files: typing.Union[typing.Iterable[UploadedFile], UploadedFile],
        aliases: typing.Optional[typing.Iterable[str]] = None,
    ) -> typing.Optional[Value]:

        if not uploaded_files:
            return None

        if aliases is None:
            aliases = []
        if isinstance(aliases, str):
            aliases = [aliases]

        if isinstance(uploaded_files, UploadedFile):
            uploaded_files = [uploaded_files]

        for uf in uploaded_files:
            if not isinstance(uf, UploadedFile):
                raise TypeError(f"Can't onboard: invalid type '{type(uf)}'")

        temp_dir = os.path.join(self.temp_dir, str(uuid.uuid4()))
        os.makedirs(temp_dir)
        for uf in uploaded_files:
            path = os.path.join(temp_dir, uf.name)
            with open(path, "wb") as f:
                f.write(uf.getbuffer())

        inputs = {
            "source": temp_dir,
            "save": True,
            "aliases": aliases,
        }
        result: ValueSet = self._kiara.run(  # type: ignore
            "file_bundle.import_from.local.folder_path", inputs=inputs
        )
        imported_bundle = result.get_value_obj("value_item")

        return imported_bundle

    def import_uploaded_file(
        self,
        uploaded_file: UploadedFile,
        store: typing.Union[bool, str, typing.Iterable[str]] = False,
    ) -> Value:

        if not isinstance(uploaded_file, UploadedFile):
            raise TypeError(f"Can't onboard: invalid type '{type(uploaded_file)}'")

        temp_dir = os.path.join(self.temp_dir, str(uuid.uuid4()))
        os.makedirs(temp_dir)
        path = os.path.join(temp_dir, uploaded_file.name)
        with open(path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        op: Operation = st.kiara.get_operation("file.import_from.local.file_path")
        import_result = op.run(source=path)
        file_obj = import_result.get_value_obj("value_item")

        if store is False:
            return file_obj
        elif store is True:
            stored = file_obj.save()
            return stored
        elif isinstance(store, str):
            stored = file_obj.save(aliases=[store])
            return stored
        elif isinstance(store, typing.Iterable):
            stored = file_obj.save(aliases=store)
            return stored
        else:
            raise NotImplementedError()
