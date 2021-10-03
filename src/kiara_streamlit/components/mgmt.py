# -*- coding: utf-8 -*-
import ast
import inspect
import os
import typing
from ast import Attribute, Call, Constant, Expr, Import, ImportFrom
from pathlib import Path

import streamlit as st
from kiara.defaults import DEFAULT_NO_DESC_VALUE
from kiara.metadata.core_models import DocumentationMetadataModel
from kiara.utils import camel_case_to_snake_case
from pydantic import validate_arguments
from pydantic.decorator import ValidatedFunction
from pydantic.main import BaseModel
from streamlit.delta_generator import DeltaGenerator

from kiara_streamlit.components import KiaraComponentMixin
from kiara_streamlit.components.operations import KiaraOperationComponentsMixin
from kiara_streamlit.components.tabular_data import TableComponentsMixin
from kiara_streamlit.components.value_info import KiaraValueInfoComponentsMixin
from kiara_streamlit.components.value_input import KiaraInputComponentsMixin
from kiara_streamlit.defaults import EXAMPLE_BASE_DIR, TEMPLATES_BASE_DIR
from kiara_streamlit.utils import render_example_template


def _extract_component_class_name(cls: typing.Type[KiaraComponentMixin]):

    if hasattr(cls, "_type_name"):
        return cls._type_name  # type: ignore

    result = camel_case_to_snake_case(cls.__name__)
    if result.endswith("_mixin"):
        result = result[0:-6]
    if result.endswith("_components"):
        result = result[0:-11]

    if result.startswith("kiara_"):
        result = result[6:]
    return result


class EmbeddExampleTransformer(ast.NodeTransformer):
    def __init__(self):

        self._lines_to_remove: typing.Set[int] = set()

    @property
    def lines_to_remove(self) -> typing.Set[int]:
        return self._lines_to_remove

    def visit_ImportFrom(self, node: ImportFrom) -> typing.Any:

        if (
            node.module == "kiara_streamlit"
            and len(node.names) == 1
            and node.names[0].name == "KiaraStreamlit"
        ):
            self._lines_to_remove.add(node.lineno)
        return None

    def visit_Import(self, node: Import) -> typing.Any:
        if (
            len(node.names) == 1
            and node.names[0].name == "streamlit"
            and node.names[0].asname == "st"
        ):
            self._lines_to_remove.add(node.lineno)
        elif len(node.names) == 1 and node.names[0].name == "kiara_streamlit":
            self._lines_to_remove.add(node.lineno)
        return node

    def visit_Expr(self, node: Expr) -> typing.Any:

        if isinstance(node.value, Constant) and isinstance(node.value.value, str):
            lno = node.lineno
            elno = node.end_lineno
            assert lno is not None
            assert elno is not None
            for i in range(lno, elno + 1):
                self._lines_to_remove.add(i)
        elif isinstance(node.value, Call):
            if isinstance(node.value.func, Attribute) and node.value.func.attr == "init" and node.value.func.value.id == "kiara_streamlit":  # type: ignore
                self._lines_to_remove.add(node.lineno)
        return node


class ExampleCode(object):
    @classmethod
    def find_example_files(
        cls, examples_base_dir: str
    ) -> typing.Dict[str, typing.Dict[str, str]]:

        if not os.path.isdir(examples_base_dir):
            return {}

        result: typing.Dict[str, typing.Dict[str, str]] = {}
        for root, dirnames, filenames in os.walk(examples_base_dir, topdown=True):

            for f in filenames:
                full = os.path.join(root, f)
                if os.path.isfile(full) and f.endswith(".py"):
                    rel_path = os.path.relpath(os.path.dirname(full), examples_base_dir)
                    result.setdefault(rel_path.replace(os.path.sep, "."), {})[
                        f[0:-3]
                    ] = full

        return result

    @classmethod
    def find_examples(
        cls, examples_base_dir: str
    ) -> typing.Dict[str, typing.Dict[str, "ExampleCode"]]:

        files = cls.find_example_files(examples_base_dir=examples_base_dir)

        result: typing.Dict[str, typing.Dict[str, ExampleCode]] = {}
        for category, examples in files.items():
            for example_name, example_file in examples.items():
                ex_code = cls.load(
                    example_file=example_file,
                    category_name=category,
                    example_name=example_name,
                )
                result.setdefault(category, {})[example_name] = ex_code

        return result

    @classmethod
    def load(
        cls,
        example_file: str,
        category_name: typing.Optional[str] = None,
        example_name: typing.Optional[str] = None,
    ) -> "ExampleCode":

        with open(example_file, "r") as source:
            source_code = source.read()

        return ExampleCode(
            category_name=category_name,
            example_name=example_name,
            full_source_code=source_code,
            path=example_file,
        )

    def __init__(
        self,
        full_source_code: str,
        category_name: typing.Optional[str] = None,
        example_name: typing.Optional[str] = None,
        path: typing.Optional[str] = None,
    ):

        self._full_source_code: str = full_source_code

        self._category_name: typing.Optional[str] = category_name
        self._example_name: typing.Optional[str] = example_name

        self._path: typing.Optional[str] = path

        self._minimal_source_code: typing.Optional[str] = None
        self._doc: typing.Optional[DocumentationMetadataModel] = None

    @property
    def minimal_source_code(self) -> str:

        if self._minimal_source_code is None:
            self._parse_source_code()
        return self._minimal_source_code  # type: ignore

    @property
    def doc(self) -> DocumentationMetadataModel:

        if self._doc is None:
            self._parse_source_code()
        return self._doc  # type: ignore

    def _parse_source_code(self) -> None:

        tree = ast.parse(self._full_source_code)

        doc = ast.get_docstring(tree)
        if not doc:
            doc = DEFAULT_NO_DESC_VALUE

        self._doc = DocumentationMetadataModel.from_string(doc)

        transformer = EmbeddExampleTransformer()
        transformer.visit(tree)

        new_code_lines = []

        first_line = False
        for lineno, line in enumerate(self._full_source_code.split("\n"), start=1):

            if lineno in transformer.lines_to_remove:
                continue

            if (not line or line.startswith("# -*- ")) and not first_line:
                continue

            first_line = True
            new_code_lines.append(line)

        self._minimal_source_code = "\n".join(new_code_lines)


class AllComponentsMixin(
    # KiaraFileComponentsMixin,
    KiaraOperationComponentsMixin,
    # KiaraPipelineComponentsMixin,
    TableComponentsMixin,
    KiaraValueInfoComponentsMixin,
    KiaraInputComponentsMixin,
):
    pass


class ComponentMgmt(object):
    def __init__(self, example_base_dir: typing.Optional[str] = None):

        if example_base_dir is None:
            example_base_dir = EXAMPLE_BASE_DIR

        self._example_base_dir: str = example_base_dir

        self._components_cls: typing.Type[AllComponentsMixin] = AllComponentsMixin

        # self._all_mixin_classes: typing.Dict[str, typing.Type[KiaraComponentMixin]] = {
        #     _extract_component_class_name(cls): cls
        #     for cls in _get_all_subclasses(KiaraComponentMixin, ignore_abstract=True)
        # }

        subclasses: typing.Iterable[
            typing.Type[typing.Any]
        ] = self._components_cls.__bases__

        self._all_mixin_classes: typing.Dict[str, typing.Type[KiaraComponentMixin]] = {
            _extract_component_class_name(cls): cls
            for cls in subclasses
            if issubclass(cls, KiaraComponentMixin)
        }

        self._components_by_collection: typing.Optional[
            typing.Dict[str, typing.Dict[str, BaseModel]]
        ] = None
        self._components_index: typing.Optional[
            typing.Dict[str, typing.Tuple[str, str]]
        ] = None
        self._docs: typing.Dict[str, typing.Dict[str, DocumentationMetadataModel]] = {}
        self._examples: typing.Optional[
            typing.Dict[str, typing.Dict[str, ExampleCode]]
        ] = None

    @property
    def component_collections(self) -> typing.Iterable[str]:
        return sorted(self._all_mixin_classes.keys())

    @property
    def all_components_by_collection(
        self,
    ) -> typing.Mapping[str, typing.Mapping[str, BaseModel]]:

        if self._components_by_collection is not None:
            return self._components_by_collection

        funcs: typing.Dict[str, typing.Dict[str, BaseModel]] = {}
        index: typing.Dict[str, typing.Tuple[str, str]] = {}
        for component_collection in sorted(self._all_mixin_classes.keys()):

            cls = self._all_mixin_classes[component_collection]

            functions = self._get_mixin_functions(cls)
            for alias in functions.keys():
                if alias in index.keys():
                    raise Exception(f"Duplicate component name: {alias}.")
                index[alias] = (component_collection, alias)

            funcs[component_collection] = functions

        self._components_by_collection = funcs
        self._components_index = index
        return self._components_by_collection

    @property
    def components_index(self) -> typing.Mapping[str, typing.Tuple[str, str]]:

        if self._components_index is None:
            self.all_components_by_collection  # type: ignore
        return self._components_index  # type: ignore

    @property
    def component_names(self) -> typing.Iterable[str]:

        return self.components_index.keys()

    @property
    def examples(self) -> typing.Mapping[str, typing.Mapping[str, ExampleCode]]:

        if self._examples is None:
            self._examples = ExampleCode.find_examples(
                examples_base_dir=self._example_base_dir
            )
        return self._examples

    def get_components_of_collection(
        self, component_collection: str
    ) -> typing.Mapping[str, BaseModel]:

        return self.all_components_by_collection[component_collection]

    def get_examples_for_category(
        self, example_category: str
    ) -> typing.Mapping[str, ExampleCode]:

        return self.examples.get(example_category, {})

    def get_example(
        self, example_category: str, example_name: str
    ) -> typing.Optional[ExampleCode]:

        examples = self.get_examples_for_category(example_category=example_category)

        example = examples.get(example_name, None)
        return example

    @validate_arguments
    def _get_mixin_functions(
        self, cls: typing.Type[KiaraComponentMixin]
    ) -> typing.Dict[str, BaseModel]:
        class Config:
            arbitrary_types_allowed = True

        result: typing.Dict[str, BaseModel] = {}
        for attr_name in dir(cls):

            if attr_name.startswith("_"):
                continue
            attr = getattr(cls, attr_name)
            if not callable(attr):
                continue
            model = self._analyse_component_attr(attr, config=Config)
            if not model:
                continue

            result[attr_name] = model
        return result

    def _analyse_component_attr(
        self, func: typing.Callable, config: typing.Type["Config"]  # type: ignore  # noqa
    ) -> typing.Optional["DecoratorBaseModel"]:  # type: ignore  # noqa

        vd = ValidatedFunction(func, config=config)
        fields = vd.model.__fields__
        if "container" not in fields.keys():
            return None

        return vd.model

    def get_component_from_collection(
        self, component_collection: str, component_name: str
    ) -> typing.Callable:

        cat = self._all_mixin_classes.get(component_collection, None)
        if not cat:
            raise Exception(
                f"No component collection '{component_collection}' available."
            )

        if not hasattr(cat, component_name):
            raise Exception(
                f"No component '{component_name}' in collection '{component_collection}' available."
            )

        return getattr(cat, component_name)

    def get_component(self, component_name: str) -> typing.Callable:

        _temp = self.components_index.get(component_name, None)
        if not _temp:
            raise Exception(f"No component with name '{component_name}' available.")

        func = self.get_component_from_collection(
            component_collection=_temp[0], component_name=_temp[1]
        )
        return func

    def _get_component_model(
        self, component_collection: str, func_name: str
    ) -> BaseModel:

        cat = self._all_mixin_classes.get(component_collection, None)
        if not cat:
            raise Exception(
                f"No component category '{component_collection}' available."
            )

        if not hasattr(cat, func_name):
            raise Exception(
                f"No component '{func_name}' in collection '{component_collection}' available."
            )

        return self.all_components_by_collection[component_collection][func_name]

    def get_doc_for_component(
        self, component_collection: str, component_name: str
    ) -> DocumentationMetadataModel:

        if not self._docs.get(component_collection, {}).get(component_name, None):

            func = self.get_component_from_collection(
                component_collection=component_collection, component_name=component_name
            )
            doc = func.__doc__
            if not doc:
                doc = DEFAULT_NO_DESC_VALUE
            doc = inspect.cleandoc(doc)  # type: ignore

            _doc = DocumentationMetadataModel.from_string(doc)
            self._docs.setdefault(component_collection, {})[component_name] = _doc

        return self._docs[component_collection][component_name]

    def is_input_component(self, component_collection: str, component_name: str):

        model = self._get_component_model(
            component_collection=component_collection, func_name=component_name
        )
        return "key" in model.__fields__.keys()

    def render_component_description(
        self,
        component_collection: str,
        component_name: str,
        full_doc: bool = True,
        container: DeltaGenerator = st,
    ):

        component = self.get_doc_for_component(
            component_collection=component_collection, component_name=component_name
        )
        if full_doc:
            doc = component.full_doc
        else:
            doc = component.description
        container.write(doc)

    def render_component_args_doc(
        self,
        component_collection: str,
        component_name: str,
        container: DeltaGenerator = st,
    ):

        model = self._get_component_model(
            component_collection=component_collection, func_name=component_name
        )

        md = "| field | type | required | default | desc |"
        md = f"{md}\n| --- | --- | --- | --- | --- |"

        fields_required = {}
        fields_optional = {}
        for field_name in sorted(model.__fields__.keys()):

            if field_name in [
                "v__duplicate_kwargs",
                "self",
                "args",
                "kwargs",
                "container",
            ]:
                continue
            details = model.__fields__[field_name]
            if details.required:
                if details.type_ == typing.Any:
                    fields_optional[field_name] = details
                else:
                    fields_required[field_name] = details
            else:
                fields_optional[field_name] = details

        fields_required.update(fields_optional)
        for field_name, details in fields_required.items():

            _type = extract_type_name(details.type_)

            desc = details.field_info.description

            if not desc:
                desc = DEFAULT_NO_DESC_VALUE

            if field_name == "default" and desc == DEFAULT_NO_DESC_VALUE:
                desc = "A default value to use in the input component (if applicable)."
            elif field_name == "label" and desc == DEFAULT_NO_DESC_VALUE:
                desc = "A label for the component. Will be forwarded to the underlying streamlit component(s)."
            elif field_name == "key" and desc == DEFAULT_NO_DESC_VALUE:
                desc = "Will be forwarded to underlying streamlit component(s): an optional string to use as the unique key for the widget. If this is omitted, a key will be generated for the widget based on its content. Multiple widgets of the same type may not share the same key."

            if details.required:
                if details.type_ == typing.Any:
                    req = "no"
                else:
                    req = "yes"
            else:
                req = "no"

            default = details.default
            if default is None:
                default = ""
            md = f"{md}\n| {field_name} | {_type} | {req} | {default} | {desc} |"

        container.markdown(md)

    def render_component_doc(
        self,
        component_collection: str,
        component_name: str,
        incl_component_code: bool = True,
        container: DeltaGenerator = st,
    ):

        example_category = f"component_examples.{component_collection}"

        container.markdown(f"### ***{component_name}***")
        self.render_component_description(
            component_collection=component_collection, component_name=component_name
        )
        arg_expander = container.expander("Supported arguments", expanded=False)
        self.render_component_args_doc(
            component_collection=component_collection,
            component_name=component_name,
            container=arg_expander,
        )
        if incl_component_code:
            component_func = self.get_component_from_collection(
                component_collection=component_collection, component_name=component_name
            )
            code_expander = container.expander("Component code", expanded=False)
            code_expander.markdown(
                f"``` python\n{inspect.getsource(component_func)}\n```"
            )
        container.markdown("##### Examples")
        examples = self.get_examples_for_category(
            example_category=f"{example_category}.{component_name}"
        )
        if not examples:
            container.markdown("###### How to use")
            model = self._get_component_model(
                component_collection=component_collection, func_name=component_name
            )
            if "key" in model.__fields__.keys():
                container.markdown(
                    f"``` python\nresult = st.kiara.{component_name}(...)\nst.write(result)\n```"
                )
            else:
                container.markdown(f"``` python\nst.kiara.{component_name}(...)\n```")
            return
        for example_name, example in examples.items():
            container.markdown(f"###### {example.doc.description}")
            if example.doc.doc:
                container.markdown(example.doc.doc)
            container.markdown(f"``` python\n{example.minimal_source_code}\n```")
            exec(example.minimal_source_code, {"st": st})
            container.markdown("---")

    def create_component_example_file_from_template(
        self,
        component_collection: str,
        component_name: str,
        example_name: typing.Optional[str] = None,
        example_doc: typing.Optional[str] = None,
        example_args: typing.Optional[str] = None,
        template: typing.Union[None, str, Path] = None,
    ):

        if example_name is None:
            example_name = f"{component_name}_1"

        example_name = f"{example_name}.py"

        example_file_path = os.path.join(
            self._example_base_dir,
            "component_examples",
            component_collection,
            component_name,
            example_name,
        )
        if os.path.exists(example_file_path):
            raise Exception(
                f"Can't render example from template, path exists: {example_file_path}"
            )

        os.makedirs(os.path.dirname(example_file_path), exist_ok=True)

        if not template:
            if self.is_input_component(
                component_collection=component_collection, component_name=component_name
            ):
                template = os.path.join(
                    TEMPLATES_BASE_DIR, "component_example_input.py.j2"
                )
            else:
                template = os.path.join(TEMPLATES_BASE_DIR, "component_example.py.j2")
        content = render_example_template(
            component_name=component_name,
            example_doc=example_doc,
            example_args=example_args,
            template=template,
        )

        with open(example_file_path, "wt") as f:
            f.write(content)

        return example_file_path

    def create_missing_example_files(
        self, *component_collections: str
    ) -> typing.Dict[str, typing.Dict[str, typing.Dict[str, str]]]:

        if not component_collections:
            _component_collections: typing.Iterable[str] = self.component_collections
        else:
            _component_collections = component_collections

        result: typing.Dict[str, typing.Dict[str, typing.Dict[str, str]]] = {}

        for component_collection in _component_collections:
            for component_name in self.get_components_of_collection(
                component_collection
            ).keys():
                examples_dir_path = os.path.join(
                    self._example_base_dir,
                    "component_examples",
                    component_collection,
                    component_name,
                )
                os.makedirs(examples_dir_path, exist_ok=True)
                if os.listdir(examples_dir_path):
                    print(
                        f"Not adding example for component '{component_name}': examples dir exists and not empty."
                    )
                    continue

                example_name = f"{component_name}_1"
                example_file = self.create_component_example_file_from_template(
                    component_collection=component_collection,
                    component_name=component_name,
                    example_name=example_name,
                )
                result.setdefault(component_collection, {}).setdefault(
                    component_name, {}
                )[example_name] = example_file

        return result


def extract_type_name(item: typing.Any) -> str:

    if isinstance(item, type):
        item = item.__name__
    elif item == typing.Any:
        item = "any"
    elif isinstance(item, typing._UnionGenericAlias):  # type: ignore
        result = []
        for arg in item.__args__:
            result.append(extract_type_name(arg))
        item = " OR ".join(result)
    else:
        item = str(item)

    item = item.replace("typing.Mapping", "dict")
    item = item.replace("typing.Iterable", "list")
    item = item.replace("typing.Union", "union")
    item = item.replace("kiara.data.values.Value", "Value")
    item = item.replace("NoneType", "None")

    return item
