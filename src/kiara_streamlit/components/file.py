# -*- coding: utf-8 -*-
import os
import shutil
import tempfile
import typing

from kiara.data import Value, ValueSet
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

        with tempfile.TemporaryDirectory() as tmpdirname:
            for uf in uploaded_files:
                path = os.path.join(tmpdirname, uf.name)
                with open(path, "wb") as f:
                    f.write(uf.getbuffer())

            inputs = {
                "source": tmpdirname,
                "save": True,
                "aliases": aliases,
            }
            result: ValueSet = self._kiara.run(  # type: ignore
                "file_bundle.import_from.local.folder_path", inputs=inputs
            )
            imported_bundle = result.get_value_obj("value_item")

        shutil.rmtree(tmpdirname, ignore_errors=True)

        return imported_bundle

    def import_file(
        self,
        uploaded_file: UploadedFile,
        # aliases: typing.Optional[typing.Iterable[str]] = None,
    ) -> str:

        # if aliases is None:
        #     aliases = []
        # if isinstance(aliases, str):
        #     aliases = [aliases]

        if not isinstance(uploaded_file, UploadedFile):
            raise TypeError(f"Can't onboard: invalid type '{type(uploaded_file)}'")

        temp_dir = tempfile.TemporaryDirectory()
        path = os.path.join(temp_dir.name, uploaded_file.name)
        with open(path, "wb") as f:
            print(f"Writing {path}")
            f.write(uploaded_file.getbuffer())

            # inputs = {
            #     "source": path,
            #     "save": False,
            #     "aliases": [],
            # }
            # result = self._kiara.run("file.import_from.local.file_path", inputs=inputs)
            # imported_file = result.get_value_obj("value_item")

        return path
