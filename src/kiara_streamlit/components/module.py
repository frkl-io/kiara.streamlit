# -*- coding: utf-8 -*-
import json
import os
import pprint
import typing

import streamlit as st
from kiara import KiaraModule
from kiara.metadata.module_models import (
    KiaraModuleConfigMetadata,
    KiaraModuleTypeMetadata,
)
from kiara.module_config import ModuleTypeConfigSchema
from kiara.operations import Operation
from kiara.utils import get_data_from_file
from pydantic import ValidationError
from streamlit.delta_generator import DeltaGenerator

from kiara_streamlit.components import KiaraComponentMixin


class KiaraModuleComponentsMixin(KiaraComponentMixin):
    def module_config_panel(
        self,
        module_type: str,
        module_config: typing.Optional[typing.Mapping[str, typing.Any]] = None,
        key: typing.Optional[str] = None,
        container: DeltaGenerator = st,
    ) -> typing.Optional[ModuleTypeConfigSchema]:
        """Render a set of configuration components for a module config.

        This component does not support the 'container' parameter, which will be ignored if provided.

        Returns the config dict.
        """

        if not module_config:
            module_config = {}

        config_cls = self.kiara.get_module_class(module_type)._config_cls

        c_md = KiaraModuleConfigMetadata.from_config_class(config_cls)
        module_config_default = {}
        for field in sorted(c_md.config_values.keys()):
            val = c_md.config_values[field]
            if field in module_config.keys():
                module_config_default[field] = module_config[field]
            elif val.value_default is not None:
                module_config_default[field] = val.value_default
            else:
                module_config_default[field] = None

        json_str = json.dumps(module_config_default, indent=2)
        edit_col, schema_col = container.columns(2)
        schema_col.write("Configuration schema")
        height = json_str.count("\n") * 32
        config_input = edit_col.text_area(
            "",
            value=json_str,
            height=height,
            help="Provide the module configuration in JSON format.",
        )
        self.write_module_config_schema(module_type, container=schema_col)
        schema_col.write("")

        try:
            result = json.loads(config_input)
        except Exception as e:
            container.error(f"Can't parse json string: {e}")
            return None

        try:
            result_config = config_cls(**result)
        except ValidationError as ve:

            md = "Config validation errors:"
            for ex in ve.errors():
                loc = ", ".join(ex["loc"])
                msg = ex["msg"]
                md = f"{md}\n  - {loc}: *{msg}*"

            container.error(md)
            return None
        except Exception as e:
            container.error(f"Can't create module configuration: {e}")
            return None

        try:
            m = self.kiara.create_module(
                module_type=module_type, module_config=result_config
            )
            m.input_schemas  # noqa
            m.output_schemas  # noqa
        except Exception as e:
            st.error(str(e))
            return None
        return result_config

    def write_module_config_schema(
        self,
        module: typing.Union[str, KiaraModule, typing.Type[KiaraModule]],
        container: DeltaGenerator = st,
    ) -> None:

        if not module:
            st.info("No module selected.")
            return

        if isinstance(module, str):
            m_cls = self.kiara.get_module_class(module)
        elif isinstance(module, KiaraModule):
            m_cls = module.__class__
        else:
            m_cls = module

        cmd = KiaraModuleConfigMetadata.from_config_class(m_cls._config_cls)
        md = "| Key | Type | Required | Default | Description |"
        md = f"{md}\n| --- | --- | --- | --- | --- |"
        for field_name, details in cmd.config_values.items():
            field_type = details.type
            default = details.value_default
            # if default is None:
            #     default = ""
            default = json.dumps(default)
            desc = details.description
            md = f"{md}\n| {field_name} | {'yes' if details.required else 'no'} | {field_type} | {default} | {desc} |"
        container.markdown(md)

    def write_module_config(
        self,
        module: KiaraModule,
        show_type: bool = False,
        show_desc: bool = False,
        container: DeltaGenerator = st,
    ):

        cmd = KiaraModuleConfigMetadata.from_config_class(module._config_cls)

        if show_type:
            _type_str = "Type | "
        else:
            _type_str = ""

        if show_desc:
            _desc_str = "Description | "
        else:
            _desc_str = ""

        md = f"| Key | Value | {_type_str} {_desc_str}"
        md = f"{md}\n| --- | --- |"
        if show_type:
            md = f"{md} --- |"
        if show_desc:
            md = f"{md} --- |"

        for k, v in cmd.config_values.items():
            desc = v.description
            if show_type:
                _type = f"{v.type} | "
            else:
                _type = ""
            if show_desc:
                _desc = f"{desc} | "
            else:
                _desc = ""
            cv = module.get_config_value(k)

            if isinstance(cv, str):
                _v: str = cv
            elif hasattr(cv, "json"):
                _v = cv.json(indent=2)
            elif isinstance(cv, typing.Mapping):
                try:
                    _v = json.dumps(cv)
                except Exception:
                    _v = pprint.pformat(cv)
            elif isinstance(cv, typing.Iterable):
                _temp = []
                for __v in cv:
                    if hasattr(__v, "dict"):
                        __v = __v.dict()
                    else:
                        try:
                            __v = json.dumps(__v)
                        except Exception:
                            pass
                    _temp.append(__v)
                try:
                    _v = json.dumps(_temp)
                except Exception:
                    _v = pprint.pformat(_temp)
            else:
                try:
                    _v = json.dumps(cv)
                except Exception:
                    _v = cv
            md = f"{md}\n| {k} | `{_v}` | {_type} {_desc}"

        container.write(md)

    def module_select(
        self,
        module_name: typing.Optional[str] = None,
        allow_module_config: bool = False,
        key: typing.Optional[str] = None,
        container: DeltaGenerator = st,
    ) -> typing.Optional[KiaraModule]:
        """Render a selectbox with all available modules.

        If a module_name is provided, no selectbox will be rendered, and the provided module will be returned (or an error rendered
        if the module does not exist).

        """

        show_module_edit_panel = True

        if not module_name:

            avail_modules = set(st.kiara.available_operation_ids)
            if allow_module_config:
                avail_modules.update(st.kiara.available_module_types)

            module_name = st.selectbox(
                "Select operation:",
                [""] + sorted(avail_modules),
                key=f"_{key}_module_select_",
            )
            if not module_name:
                # st.write("No module selected, doing nothing...")
                return None

        if not os.path.isfile(os.path.realpath(module_name)):

            if module_name in st.kiara.available_operation_ids:
                op: Operation = st.kiara.get_operation(module_name)
                resolved_module_name = op.module_type
                _module_config = op.module_config
            else:
                m_cls = st.kiara.get_module_class(module_type=module_name)  # type: ignore

                assert m_cls is not None
                # mod_conf = m_cls._config_cls
                _module_config = {}
                resolved_module_name = module_name
                # if mod_conf.requires_config():
                #     st.error("This module requires configuration. This is not supported yet.")
                #     st.stop()
                #
                # try:
                #     module = st.kiara.create_module(module_type=module_name, module_config=module_config)
                # except Exception as e:
                #     st.error(f"Can't create module: {e}")
                #     st.stop()

        else:
            # module is pipeline file
            _module_config = get_data_from_file(module_name)
            resolved_module_name = "pipeline"

        if resolved_module_name != module_name:
            container.markdown(f"Resolved module: `{resolved_module_name}`")

        if show_module_edit_panel:
            expanded = self.kiara.get_module_class(
                module_type=resolved_module_name
            )._config_cls.requires_config(_module_config)
            mod_panel = container.expander("Module configuration", expanded=expanded)
            module_config_obj = self.module_config_panel(
                module_type=resolved_module_name,
                module_config=_module_config,
                key=f"_{key}_module_config_panel_",
                container=mod_panel,
            )
        else:
            try:
                m_cls = self.kiara.get_module_class(module_type=resolved_module_name)
                module_config_obj = m_cls._config_cls(**_module_config)
            except ValidationError as ve:

                md = "Validation errors:"
                for e in ve.errors():
                    loc = ", ".join(e["loc"])
                    msg = e["msg"]
                    md = f"{md}\n  - {loc}: *{msg}*"

                container.error(md)
                return None
            except Exception as e:
                container.error(f"Can't create module config: {e}")
                return None

        if module_config_obj is None:
            return None
        try:
            module = self.kiara.create_module(
                module_type=resolved_module_name, module_config=module_config_obj.dict()
            )
            return module
        except Exception as e:
            container.error(f"Can't create module: {e}")
            return None

    def write_module_processing_code(
        self,
        module: typing.Union[str, KiaraModule, typing.Type[KiaraModule]],
        container: DeltaGenerator = st,
    ):

        if isinstance(module, str):
            module = self.kiara.get_module_class(module_type=module)
            module_config: typing.Optional[ModuleTypeConfigSchema] = None
        elif isinstance(module, KiaraModule):
            module_config = module.config
            module = module.__class__
        else:
            module_config = None

        if module.is_pipeline() and not module._module_type_id == "pipeline":  # type: ignore
            md = "``` json"
            md = f"{md}\n{module.get_type_metadata().pipeline_config.json(indent=2)}"  # type: ignore
        elif module._module_type_id == "pipeline" and module_config is not None:  # type: ignore
            md = "``` json"
            md = f"{md}\n{module_config.json(indent=2)}"
        else:
            md = "``` python"
            md = f"{md}\n{module.get_type_metadata().process_src}"
        md = f"{md}\n```"
        container.write(md)

    def write_module_type_metadata(
        self,
        module: typing.Union[str, KiaraModule, typing.Type[KiaraModule]],
        container: DeltaGenerator = st,
    ):

        if isinstance(module, str):
            module = self.kiara.get_module_class(module_type=module)
        elif isinstance(module, KiaraModule):
            module = module.__class__

        metadata: KiaraModuleTypeMetadata = module.get_type_metadata()

        md = "| Key | Value |"
        md = f"{md}\n| --- | --- |"

        is_pipeline = "yes" if metadata.is_pipeline else "no"
        md = f"{md}\n| Is pipeline | {is_pipeline} |"

        first_line = True
        author_md: str = None  # type: ignore
        for author in metadata.origin.authors:
            if first_line:
                author_md = "| Authors |"
                first_line = False
            else:
                author_md = f"{author_md}\n|   |"
            author_md = f"{author_md} {author.name} ({author.email})"

        md = f"{md}\n{author_md}"

        first_line = True
        ref_md: str = None  # type: ignore

        for ref, link in metadata.context.references.items():
            if first_line:
                ref_md = "| References |"
                first_line = False
            else:
                ref_md = f"{ref_md}\n|   |"
            ref_md = f"{ref_md} {ref}: *{link.url}*"
        md = f"{md}\n{ref_md}"

        md = f"{md}\n| Tags | {', '.join(metadata.context.tags)} |"

        first_line = True
        label_md: str = None  # type: ignore
        for k, v in metadata.context.labels.items():
            if first_line:
                label_md = "| Labels |"
                first_line = False
            else:
                label_md = f"{label_md}\n|   |"
            label_md = f"{label_md} {k}: *{v}*"
        md = f"{md}\n{label_md}"

        python_class = metadata.python_class.full_name
        md = f"{md}\n| Python class | {python_class} |"

        container.write(md)

    def write_module_info_page(
        self, module: KiaraModule, container: DeltaGenerator = st
    ) -> None:

        full_doc = module.get_type_metadata().documentation.full_doc

        pipeline_str = ""
        if module.is_pipeline() and not pipeline_str == "pipeline":
            pipeline_str = " (pipeline module)"
        container.markdown(
            f"## Module documentation for: *{module._module_type_id}*{pipeline_str}"  # type: ignore
        )
        container.markdown(full_doc)

        st.markdown("## Module configuration")
        st.kiara.write_module_config(module, container=container)

        inp_col, out_col = st.columns(2)
        inp_col.markdown("## Module inputs")

        st.kiara.valueset_schema_info(module.input_schemas, container=inp_col)

        out_col.markdown("## Module outputs")
        st.kiara.valueset_schema_info(
            module.output_schemas,
            show_required=False,
            show_default=False,
            container=out_col,
        )

        container.markdown("## Metadata")
        st.kiara.write_module_type_metadata(module=module, container=container)
        container.markdown("## Source")
        st.kiara.write_module_processing_code(module=module, container=container)
