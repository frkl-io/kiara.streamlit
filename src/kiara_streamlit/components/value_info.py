# -*- coding: utf-8 -*-
import typing

import streamlit as st
from kiara.data import Value, ValueSet
from kiara.data.values import ValueSchema
from kiara.defaults import SpecialValue
from networkx import Graph
from streamlit.delta_generator import DeltaGenerator
from streamlit_observable import observable

from kiara_streamlit.components import KiaraComponentMixin


class KiaraValueInfoComponentsMixin(KiaraComponentMixin):
    def write_value(
        self,
        value: Value,
        key: typing.Optional[str] = None,
        container: DeltaGenerator = st,
    ):
        """Write a value of any (supported) type to a streamlit page/component.

        This auto-selects the appropriate component, based on the values 'type_name' attribute.
        Currently supported types: 'array', 'table', 'network_graph', 'dict'. All other types will be written using the
        generic `st.write(...)` method.
        """
        if (
            value is None
            or not value.item_is_valid()
            or not value.is_set
            or value.is_none
        ):
            container.error("No value")
        else:
            data = value.get_value_data()
            if value.type_name == "table":
                data = data.to_pandas()
            elif value.type_name == "array":
                data = data.to_pandas()
            elif value.type_name == "network_graph":

                graph: Graph = value.get_value_data()

                # nodes = [Node(id=i, label=str(i), size=200) for i in range(len(graph.nodes))]
                # edges = [Edge(source=i, target=j, type="CURVE_SMOOTH") for (i,j) in graph.edges]

                nodes: typing.Dict[str, typing.Dict[str, typing.Any]] = {}
                edges: typing.List[typing.Mapping[str, typing.Any]] = []
                for (s, t) in graph.edges:
                    if s not in nodes.keys():
                        nodes[s] = {"id": str(s), "group": 1}
                    if t not in nodes.keys():
                        nodes[t] = {"id": str(t), "group": 1}

                    edges.append({"source": str(s), "target": str(t), "value": 1})

                cleaned_data = {"nodes": list(nodes.values()), "links": edges}

                observable(
                    notebook="@d3/force-directed-graph",
                    targets=["chart"],
                    redefine={
                        "data": cleaned_data,
                    },
                    key=key,
                    observe=[],
                )
                return
            elif hasattr(data, "dict"):
                data = data.dict()
            else:
                data = value.get_value_data()

            container.write(data)

    # def value_type_specific_metadata(self, value_id: str, container: DeltaGenerator = st):
    #     """Display value-type specific metadata for a value.
    #
    #     This does not print out all available metadata for a value. In most cases, you won't need this.
    #     """
    #
    #     value_obj = self.data_store.get_value_obj(value_id)
    #     value_info = ValueInfo.from_value(value_obj)
    #
    #     if value_info.value_schema.type in value_info.metadata.keys():
    #         md = value_info.metadata[value_info.value_schema.type]["metadata_item"]
    #     else:
    #         md = {}
    #
    #     container.write(md)

    def write_valueset(
        self,
        value_set: typing.Union[ValueSet, typing.Mapping[str, Value]],
        fields: typing.Optional[typing.Iterable[str]] = None,
        as_columns: bool = False,
        separator: typing.Any = None,
        add_save_option: bool = False,
        key: typing.Optional[str] = None,
        container: DeltaGenerator = st,
    ):
        """Display the contents of a set of values.

        This is useful if you don't know in advance with which types of value sets you will be dealing with. This component
        will render an appropriate set of UI elements, either in a row (as columns), or one after the other.

        If using the column display option, 'save' is not supported at the moment.
        """
        if fields:
            _value_set = {}
            for field in fields:
                _value_set[field] = value_set[field]
            value_set = _value_set

        if as_columns:
            columns = container.columns(len(value_set))
            for idx, (field_name, value) in enumerate(value_set.items()):

                columns[idx].markdown(f"***{field_name}***")
                columns[idx].caption(value.value_schema.doc)

                _key = key
                if _key:
                    _key = f"{_key}_write_value_{field_name}"
                else:
                    _key = f"write_value_{field_name}"

                self.write_value(value, key=_key, container=columns[idx])

        else:

            inner = container.container()
            for field_name, value in value_set.items():
                if separator:
                    inner.write(separator)
                inner.markdown(f"***{field_name}***")
                inner.caption(value.value_schema.doc)

                _key = key
                if _key:
                    _key = f"{_key}_write_value_{field_name}"
                else:
                    _key = f"write_value_{field_name}"

                self.write_value(value, container=inner, key=_key)

                if add_save_option and value.is_set:

                    exp = inner.expander("Save result")
                    alias = exp.text_input("Alias", key=f"{_key}_alias_input")
                    save_button = exp.button("Save", key=f"{_key}_save")

                    if save_button:
                        if not alias:
                            exp.write("No alias provided.")
                        elif value is None or not value.item_is_valid():
                            exp.write("No value to save.")
                        else:
                            print("SAVE")
                            value.save([alias])
                            # st.experimental_rerun()

    def valueset_schema_info(
        self,
        valueset: typing.Mapping[str, typing.Union[str, ValueSchema, Value]],
        show_required: bool = True,
        show_default: bool = True,
        container: DeltaGenerator = st,
    ):
        """Display schema info for a set of values as a markdown table."""

        required = " required |" if show_required else ""
        _default = " default |" if show_default else ""
        md = f"| field name | type | {required} {_default} description |"
        md = f"{md}\n| --- | --- | --- | --- |"
        if show_required:
            md = f"{md} --- |"
        if show_default:
            md = f"{md} --- |"
        for field_name, schema in valueset.items():

            if isinstance(schema, str):
                _schema = ValueSchema(type=schema)
            elif isinstance(schema, Value):
                _schema = schema.value_schema
            else:
                _schema = schema

            if show_required:
                req = "yes |" if _schema.is_required() else "no |"
            else:
                req = ""
            if show_default:
                default = _schema.default
                if default in [SpecialValue.NOT_SET, SpecialValue.NO_VALUE, None]:
                    default = " |"
                else:
                    default = f"{default} |"
            else:
                default = ""
            desc = _schema.doc
            md = f"{md}\n|{field_name}|{_schema.type}|{req}{default}{desc}"

        container.markdown(md)
