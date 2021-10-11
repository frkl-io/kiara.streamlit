# -*- coding: utf-8 -*-
import datetime
import json
import typing

import streamlit as st
from dateutil import parser
from kiara.data import Value, ValueSet
from kiara.data.values import ValueSchema
from kiara.defaults import SpecialValue
from streamlit.delta_generator import DeltaGenerator

from kiara_streamlit.components import KiaraComponentMixin


class KiaraInputComponentsMixin(KiaraComponentMixin):
    """A collection of components that render UI elements to get some sort of user input, and return that input
    in a way that can be meaningfully used in kiara operations and pipelines.

    The important components here are `valueset_input` and `value_input`, which auto-render input components on the type
    of data you expect as a result value. The other components exist mainly to be called by one of those two methods
    under the hood, although the ones that render inputs for non-scalar types like strings and integers can also be
    useful in certain situations.
    """

    def value_select_box(
        self,
        value_type: str,
        label: typing.Optional[str] = None,
        default: typing.Optional[str] = None,
        add_no_value_option: bool = False,
        key: typing.Optional[str] = None,
        container: DeltaGenerator = st,
    ):

        if label is None:
            if value_type == "any":
                label = "Select value"
            else:
                label = f"Select {value_type}"

        if value_type == "any":
            aliases = set(self.data_store.alias_names)
        else:
            all_values = self.data_store.find_all_values_of_type(value_type)
            aliases = set()
            for v_id, value in all_values.items():
                _aliases = self.data_store.find_aliases_for_value(value_item=value)
                aliases.update((a.alias for a in _aliases))

        sorted_aliases = sorted(aliases)

        no_selection_option = f"-- no {value_type} --"
        if add_no_value_option:
            selection = [no_selection_option] + sorted(aliases)
        else:
            selection = sorted(aliases)

        index = 0
        if default and default in sorted_aliases:
            index = selection.index(default)

        user_sel = container.selectbox(
            label=label, options=selection, index=index, key=key
        )

        # if key:
        #     st.session_state[key] = user_sel

        if user_sel == no_selection_option:
            user_sel = None

        return user_sel

    def valueset_input(
        self,
        valueset_schema: typing.Union[
            ValueSet, typing.Mapping[str, typing.Union[str, Value, ValueSchema]]
        ],
        defaults: typing.Optional[typing.Mapping[str, typing.Any]] = None,
        expand_optional: bool = True,
        key: typing.Optional[str] = None,
        container: DeltaGenerator = st,
    ) -> typing.Mapping[str, typing.Any]:
        """Render input widgets for a set of values.

        This function takes a dict as input, containing the requested field name(s) as key(s), and the spec of the
        input as value. This can bei either an object of type 'ValueSchema', or a 'Value' object (in which case the actual
        data of it will be ignored, and only the schema extracted).

        The return value will be a dict with the field name as key(s), and the user input for each field as value(s).
        """

        if defaults is None:
            defaults = {}

        input_schemas = {}
        if isinstance(valueset_schema, ValueSet):
            for field_name, value in valueset_schema.items():
                input_schemas[field_name] = value.value_schema
        elif isinstance(valueset_schema, typing.Mapping):

            for field_name, val in valueset_schema.items():
                if isinstance(val, str):
                    input_schemas[field_name] = ValueSchema(type=val)
                elif isinstance(val, Value):
                    input_schemas[field_name] = val.value_schema
                elif isinstance(val, ValueSchema):
                    input_schemas[field_name] = val
                else:
                    raise TypeError(f"Invalid type for schema: {type(val)}")

        else:
            raise TypeError(
                f"Invalid input type for 'value_set': {type(valueset_schema)}"
            )

        inputs_main = {}
        inputs_other = {}
        for field_name, value_schema in input_schemas.items():
            if value_schema.is_required():
                inputs_main[field_name] = value_schema
            else:
                inputs_other[field_name] = value_schema

        if not inputs_main:
            inputs_main = inputs_other
            inputs_other = {}
        result: typing.Dict[str, typing.Optional[Value]] = {}
        columns_main = container.columns(len(inputs_main))
        for idx, (field_name, value_schema) in enumerate(inputs_main.items()):
            default = defaults.get(field_name, None)
            if default in [SpecialValue.NO_VALUE, SpecialValue.NOT_SET]:
                default = None
            if key is not None:
                _key = f"{key}_{field_name}"
            else:
                _key = field_name
            input = self.value_input(
                value_schema=value_schema,
                label=f"{field_name} ({value_schema.type})",
                default=default,
                key=_key,
                container=columns_main[idx],
            )
            result[field_name] = input

        if inputs_other:
            other_inputs = container.expander(
                "Optional inputs", expanded=expand_optional
            )
            columns_other = other_inputs.columns(len(inputs_other))
            for idx, (field_name, value_schema) in enumerate(inputs_other.items()):
                default = defaults.get(field_name, None)
                if default in [SpecialValue.NO_VALUE, SpecialValue.NOT_SET]:
                    default = None
                if key is not None:
                    _key = f"{key}_{field_name}"
                else:
                    _key = field_name
                input = self.value_input(
                    value_schema=value_schema,
                    label=field_name,
                    default=default,
                    key=_key,
                    container=columns_other[idx],
                )
                result[field_name] = input

        return result

    def value_input(
        self,
        value_schema: typing.Union[str, ValueSchema],
        label: str,
        default: typing.Any = None,
        field_name: typing.Optional[str] = None,
        key: typing.Optional[str] = None,
        container: DeltaGenerator = st,
    ) -> typing.Any:
        """Render input widgets for a value of the specified schema.

        This function will try to find a method with the name `value_input_[value_type]`, and if found, it will
        run it which will render a streamlit input field that is tailored for the specific type. The type will be extracted
        from the provided value_schema.

        The return value of this function is the user input, which will be of the specified type.

        If 'field_name' is specified, a heading with that name will be displayed.
        """

        if isinstance(value_schema, str):
            value_schema = ValueSchema(type=value_schema)

        func_name = f"value_input_{value_schema.type}"
        if not hasattr(self, func_name):
            raise Exception(f"No input widget available for type: {value_schema.type}")

        if field_name:
            container.markdown(f"***{field_name}***")

        func = getattr(self, func_name)

        if default in [SpecialValue.NO_VALUE, SpecialValue.NOT_SET]:
            default = None

        result = func(
            label=label,
            default=default,
            key=key,
            container=container,
        )

        if result is None:
            return None

        # if not isinstance(result, Value):
        #     result = self.data_registry.register_data(value_data=result, value_schema=value_schema)

        return result

    def value_input_boolean(
        self,
        label: str,
        default: typing.Any = None,
        key: typing.Optional[str] = None,
        container: DeltaGenerator = st,
    ) -> bool:
        """Render a checkbox.

        In most cases, you would just use `st.checkbox` directly.
        """

        if isinstance(default, Value):
            if default.is_set:
                default = default.get_value_data()
            else:
                default = None

        new_data = container.checkbox(label, value=default, key=key)

        return new_data

    def value_input_string(
        self,
        label: str,
        default: typing.Any = None,
        value_schema: typing.Optional[ValueSchema] = None,
        field_name: typing.Optional[str] = None,
        key: typing.Optional[str] = None,
        container: DeltaGenerator = st,
    ) -> typing.Optional[str]:
        """Render a text input field."""

        if isinstance(default, Value):
            if default.is_set:
                default = default.get_value_data()
            else:
                default = None

        if default is None:
            default = ""
        text = container.text_input(label, value=default, key=key)

        if not text:
            return None
        else:
            return text

    def value_input_file_path(
        self,
        label: str,
        default: typing.Any = None,
        key: typing.Optional[str] = None,
        container: DeltaGenerator = st,
    ) -> typing.Optional[str]:
        """Render a field that taks a file path string.

        For now, this is the same as the string input field. No validation is done.
        """

        # uploaded = container.file_uploader(label, accept_multiple_files=False, key=key)
        #
        # uploaded_file = None
        # if uploaded:
        #     uploaded_file = self.import_file(uploaded)
        #     assert uploaded_file is not None
        #
        # if uploaded_file:
        #     return uploaded_file
        # else:
        #     return None

        if isinstance(default, Value):
            if default.is_set:
                default = default.get_value_data()
            else:
                default = None

        if default is None:
            default = ""

        text = container.text_input(label, value=default, key=key)

        if not text:
            return None
        else:
            return text

    def value_input_folder_path(
        self,
        label: str,
        default: typing.Any = None,
        key: typing.Optional[str] = None,
        container: DeltaGenerator = st,
    ) -> typing.Optional[str]:
        """Render a field that taks a file path string.

        For now, this is the same as the string input field. No validation is done.
        """

        if isinstance(default, Value):
            if default.is_set:
                default = default.get_value_data()
            else:
                default = None

        if default is None:
            default = ""
        text = container.text_input(label, value=default, key=key)

        if not text:
            return None
        else:
            return text

    def value_input_integer(
        self,
        label: str,
        default: typing.Union[str, int, Value] = None,
        key: typing.Optional[str] = None,
        container: DeltaGenerator = st,
    ):
        """Renders an integer input widget."""

        if isinstance(default, Value):
            assert default.type_name in ["integer", "string"]
            if default.is_set:
                default = default.get_value_data()
            else:
                default = None
        elif isinstance(default, str):
            default = int(default)

        if default is None:
            default = 0
        num_inp = container.number_input(label=label, value=default, key=key)

        return num_inp

    def value_input_table(
        self,
        label: str,
        default: typing.Any = None,
        key: typing.Optional[str] = None,
        container: DeltaGenerator = st,
    ) -> typing.Optional[Value]:
        """Render a combobox that lets a user select a table (alias) and return the associated table."""

        alias = self.value_select_box(
            value_type="table",
            label=label,
            default=default,
            key=key,
            container=container,
        )

        if not alias:
            return None

        value = self.data_store.get_value_obj(alias)
        return value

    def value_input_network_graph(
        self,
        label: str,
        default: typing.Any = None,
        key: typing.Optional[str] = None,
        container: DeltaGenerator = st,
    ) -> typing.Optional[Value]:
        """Render a combobox that lets a user select a table (alias) and return the associated table."""

        alias = self.value_select_box(
            value_type="network_graph",
            label=label,
            default=default,
            key=key,
            container=container,
        )

        if not alias:
            return None

        value = self.data_store.get_value_obj(alias)
        return value

    def value_input_array(
        self,
        label: str,
        default: typing.Any = None,
        key: typing.Optional[str] = None,
        container: DeltaGenerator = st,
    ) -> typing.Optional[Value]:
        """Render a selectbox with all values in the *kiara* data store that are of type 'array'."""

        alias = self.value_select_box(
            value_type="array",
            label=label,
            default=default,
            key=key,
            container=container,
        )

        if not alias:
            return None

        value = self.data_store.get_value_obj(alias)
        return value

    def value_input_any(
        self,
        label: str,
        default: typing.Any = None,
        value_schema: typing.Optional[ValueSchema] = None,
        field_name: typing.Optional[str] = None,
        key: typing.Optional[str] = None,
        container: DeltaGenerator = str,
    ) -> typing.Optional[Value]:
        """Render a combobox that lets the user select any of the items in the kiara data store."""

        alias = self.value_select_box(
            value_type="any", label=label, container=container, key=key
        )

        if not alias:
            return None

        value = self.data_store.get_value_obj(alias)
        return value

    def value_input_dict(
        self,
        label: str,
        default: typing.Any,
        key: typing.Optional[str] = None,
        container: DeltaGenerator = str,
    ) -> typing.Optional[typing.Mapping]:

        if isinstance(default, Value):
            if default.is_set:
                default = default.get_value_data()
            else:
                default = None

        if default is None:
            default = "{}"
        else:
            default = json.dumps(default)
        text = container.text_area(label, value=default, key=key)
        container.caption("Provide a dictionary in JSON format.")
        if not text:
            result = {}
        else:
            result = json.loads(text)

        return result

    def value_input_list(
        self,
        label: str,
        default: typing.Any,
        key: typing.Optional[str] = None,
        container: DeltaGenerator = str,
    ) -> typing.Optional[typing.List]:

        if isinstance(default, Value):
            if default.is_set:
                default = default.get_value_data()
            else:
                default = None

        if default is None:
            default = "[]"
        else:
            default = json.dumps(default)
        text = container.text_area(label, value=default, key=key)
        container.caption("Provide a list in JSON format.")
        if not text:
            result = []
        else:
            result = json.loads(text)

        return result

    def value_input_date(
        self,
        label: str,
        default: typing.Union[datetime.date, datetime.datetime, str, None] = None,
        use_text_input: bool = False,
        key: typing.Optional[str] = None,
        container: DeltaGenerator = st,
    ) -> typing.Optional[datetime.date]:
        """Renders a component to ask the user for a date.

        By default, a date selection widget will be displayed. If 'use_text_input' is set to 'True', a text field will
        be displayed instead.
        """

        if isinstance(default, Value):
            if default.is_set:
                default = default.get_value_data()
            else:
                default = None

        if default is None:
            default = datetime.datetime.now()

        if isinstance(default, datetime.datetime):
            default = default.date()
        elif isinstance(default, str):
            default = parser.parse(default)
            default = default.date()

        if not use_text_input:
            date = container.date_input(label, value=default, key=key)
        else:
            if default:
                default = str(default)
            date_str = container.text_input(label, value=default, key=key)
            if not date_str:
                return None
            parsed = parser.parse(date_str)
            date = parsed.date()

        return date

    def value_input_file(
        self,
        label: str,
        default: typing.Optional[str] = None,
        key: typing.Optional[str] = None,
        container: DeltaGenerator = st,
    ) -> typing.Optional[Value]:
        """Render a selectbox with all value aliases for values of type 'file' in the kiara data store.

        This does not do any onboarding, only already onboarded files can be selected.
        """

        alias = self.value_select_box(
            value_type="file",
            label=label,
            default=default,
            key=key,
            container=container,
        )

        if not alias:
            return None

        value = self.data_store.get_value_obj(alias)
        return value
        # uploaded_file = container.file_uploader(label=label)
        # default_alias = ""
        # if uploaded_file:
        #     default_alias = f"imported_{uploaded_file.name}"
        #
        # alias = container.text_input("Alias", value=default_alias, help="An (optional) alias, to make it easier to find the file in the data store.")
        # if uploaded_file:
        #     aliases = []
        #     if alias:
        #         aliases = [alias]
        #     value = self.import_file(uploaded_file, aliases=aliases)
        #     return value
        # else:
        #     return None

    def value_input_file_bundle(
        self,
        label: str,
        default: typing.Optional[str] = None,
        key: typing.Optional[str] = None,
        container: DeltaGenerator = st,
    ) -> typing.Optional[Value]:
        """Render a selectbox with all value aliases for values of type 'file_fundle' in the kiara data store.

        This does not do any onboarding, only already onboarded files can be selected.
        """

        alias = self.value_select_box(
            value_type="file_bundle",
            label=label,
            default=default,
            key=key,
            container=container,
        )

        if not alias:
            return None

        value = self.data_store.get_value_obj(alias)
        return value
