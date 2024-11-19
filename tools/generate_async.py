#!/usr/bin/env python
"""Program to automatically generate asynchronous code from the synchronous counterpart.

This script is made solely for PRAW. Do not attempt to use this outside of PRAW use
cases.

The following heavily relies on proper typing in the package. Bad typing WILL lead to
BAD generated async code.

Not everything is to be blindly made awaitable. This algorithm permit us to scan which
element invoke blocking I/O code and link dependants.

REQUIRES: git, black, docstrfmt, and ruff installed.

exit codes:
    - 0: The asynchronous code is up-to-date
    - 1: The asynchronous code is outdated
    - 2: Generated async is invalid (syntax error)
    - 3: Third-party tool not found (black, ruff or git)
    - 4: Other errors (check stderr)

"""
from __future__ import annotations

import os.path
import shutil
import sys
import inspect
import importlib
import ast
import logging
import typing
from os import getcwd
from tempfile import TemporaryDirectory
from pathlib import Path
import re
from types import ModuleType
from typing import Callable
from subprocess import Popen, PIPE, CalledProcessError
import argparse

import niquests

# Use the local PRAW over the site-package PRAW.
if "/tools" in getcwd():
    sys.path.insert(0, "..")
else:
    sys.path.insert(0, ".")

import prawcore

logger = logging.getLogger()
logger.setLevel(logging.INFO)
explain_handler = logging.StreamHandler()
explain_handler.setFormatter(
    logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
)
logger.addHandler(explain_handler)


def black_reformat(tmp_dir: str) -> list[str]:
    """Simply run black and retrieve which file were reformatted if any."""
    process = Popen(f"black {tmp_dir}", shell=True, stdout=PIPE, stderr=PIPE)
    stdout, stderr = process.communicate()

    stdout, stderr = stdout.decode(), stderr.decode()

    if stderr:
        reformatted = []

        for line in stderr.splitlines(keepends=False):
            if line.startswith("reformatted"):
                reformatted.append(line)

        return reformatted

    return []


def docstrfmt_reformat(tmp_dir: str) -> list[str]:
    process = Popen(f"docstrfmt {tmp_dir}", shell=True, stdout=PIPE, stderr=PIPE)
    stdout, stderr = process.communicate()

    stdout, stderr = stdout.decode(), stderr.decode()

    if stderr:
        reformatted = []

        for line in stderr.splitlines(keepends=False):
            if line.startswith("Reformatted"):
                reformatted.append(line)

        return reformatted

    return []


def ruff_reformat(tmp_dir: str) -> list[str]:
    """Run Ruff linter and extract unfixable errors if any."""
    process = Popen(f"ruff format {tmp_dir}", shell=True, stdout=PIPE, stderr=PIPE)
    stdout, stderr = process.communicate()

    stdout, stderr = stdout.decode(), stderr.decode()

    if stderr:
        raise IOError(stderr)

    if stdout:
        reformatted = []

        for line in stdout.splitlines(keepends=False):
            reformatted.append(line)

        return reformatted

    return []


def git_diff(file_main: str, file_generated: str) -> list[str]:
    """Simple git diff between two files."""
    process = Popen(
        f"git diff --no-index {file_main} {file_generated}",
        shell=True,
        stdout=PIPE,
        stderr=PIPE,
    )
    stdout, stderr = process.communicate()

    stdout, stderr = stdout.decode(), stderr.decode()

    if stderr:
        raise IOError(stderr)

    if stdout:
        patch_lines = []

        for line in stdout.splitlines(keepends=False):
            patch_lines.append(line)

        return patch_lines

    return []


def preg_replace(
    src_str: str,
    pattern_in: str,
    insert: str,
    after: str | None = None,
    before: str | None = None,
    callback_ignore_if: Callable[[list[str]], bool] | None = None,
    extraneous_space: bool = True,
) -> str:
    """Smart regex replace function. It does not replace twice if replacement was already applied."""
    if extraneous_space:
        insert += " "

    def _inner_repl(m: re.Match[str]) -> str:
        full_string = m.string[m.span()[0] : m.span()[1]]

        if insert in m.string[m.span()[0] - len(insert) : m.span()[0] + len(insert)]:
            return full_string

        if callback_ignore_if is not None:
            if callback_ignore_if(list(m.groups())) is True:
                return full_string

        if after is not None:
            sub_idx = full_string.index(after)
            sub_idx += len(after)
            return full_string[:sub_idx] + insert + full_string[sub_idx:]
        elif before is not None:
            sub_idx = full_string.index(before)
            return full_string[:sub_idx] + insert + full_string[sub_idx:]

        if insert in full_string:
            return full_string

        first_printable_idx = 0

        for c in full_string:
            if c.isprintable() and c.isspace() is False:
                first_printable_idx = full_string.index(c)
                break

        return (
            full_string[:first_printable_idx]
            + insert
            + full_string[first_printable_idx:]
        )

    return re.sub(re.compile(pattern_in), _inner_repl, src_str)


def get_owned_by_module_path(my_type: type) -> str:
    """Retrieve the module Python source path."""
    return importlib.import_module(my_type.__module__).__file__


def get_definitions_in_module(my_type: type) -> list[str]:
    """Retrieve the list of declaration issued from the module that host 'my_type'."""
    symbols_by_import = list(
        map(lambda e: e[1] if e[1] is not None else e[0], get_import_made_by(my_type))
    )
    symbols = []

    for symbol, _ in inspect.getmembers(importlib.import_module(my_type.__module__)):
        if symbol not in symbols_by_import and symbol.startswith("__") is False:
            symbols.append(symbol)

    return symbols


def get_root_module_from(my_type: type, level: int = 0) -> str:
    """Infer the module MINUS given level depth. Starting from given 'my_type'."""
    tree = my_type.__module__.split(".")
    return ".".join(tree[: len(tree) - level])


def get_import_made_by(my_type: type) -> list[tuple[str, str | None]]:
    """List every import made in module that host 'my_type'."""
    required_import = []

    with open(get_owned_by_module_path(my_type), "r") as fp:
        file_ast = ast.parse(fp.read())

    # Walk every node in the tree
    for node in ast.walk(file_ast):
        # If the node is 'import x', then extract the module names
        if isinstance(node, ast.Import):
            required_import.extend([(x.name, None) for x in node.names])

        # If the node is 'from x import y', then extract the module name
        #   and check level so we can ignore relative imports
        if isinstance(node, ast.ImportFrom):
            for name in node.names:
                if node.module is None:
                    required_import.append(
                        (
                            (
                                node.module
                                if node.level == 0
                                else f"{get_root_module_from(my_type, node.level)}.{name.name}"
                            ),
                            None,
                        )
                    )
                else:
                    required_import.append(
                        (
                            (
                                node.module
                                if node.level == 0
                                else f"{get_root_module_from(my_type, node.level)}.{node.module}"
                            ),
                            name.name,
                        )
                    )

    return required_import


def parse_constructor_attrs(my_type: type) -> list[tuple[str, str, str | None]]:
    """Tries to uncover attributes initialized in constructor of 'my_type'."""
    raw_init = inspect.getsource(my_type.__init__)

    attributes = []

    for line in raw_init.splitlines(keepends=False):
        if "self." in line and " = " in line:
            attr_definition, attr_default_assignment = tuple(
                line.split(" = ", maxsplit=1)
            )

            attr_definition = attr_definition.replace("self.", "").strip()

            if "." in attr_definition:
                continue

            if ":" in attr_definition:
                attr_definition, attr_annotation = tuple(
                    attr_definition.split(": ", maxsplit=1)
                )
            else:
                attr_annotation = None

            attr_default_assignment = attr_default_assignment.strip()

            attributes.append(
                (attr_definition, attr_default_assignment, attr_annotation)
            )

    return attributes


def load_annotation(raw_annotation: str) -> type:
    """Dumb & straightforward annotation loader. Meant to import a single type."""
    imported_module = importlib.import_module(".".join(raw_annotation.split(".")[:-1]))
    return getattr(imported_module, raw_annotation.split(".")[-1])


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Asynchronous Code Generator for PRAW")
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        default=False,
        dest="verbose",
        help="Enable DEBUG logging",
    )
    parser.add_argument(
        "-f",
        "--fix",
        action="store_true",
        default=False,
        dest="fix",
        help="Applies the newer version of generated modules",
    )
    parser.add_argument(
        "-s",
        "--sync-diff",
        action="store_true",
        default=False,
        dest="main_diff",
        help="Render the differences between the synchronous parts and the newly generated asynchronous ones",
    )
    parser.add_argument(
        "-a",
        "--async-diff",
        action="store_true",
        default=False,
        dest="async_diff",
        help="Render the differences between the old async and newest async generated modules",
    )

    args = parser.parse_args(sys.argv[1:])

    if args.verbose:
        logger.setLevel(logging.DEBUG)

    should_write_into_package: bool = args.fix is True
    should_display_diff_sync_async: bool = args.main_diff is True
    should_display_diff_async_async: bool = args.async_diff is True

    try:
        logger.info("Scanning the top-level package __init__ to grab public references")

        #: directly exposed API (public)
        top_level_types: list[type] = []
        #: not directly exposed in __init__ but required by references in __init__
        indirect_types: list[type] = []
        #: we need to list them so that we can properly remap import in generated async src
        package_submodules: list[str] = []

        # we want to parse the top-level public API
        # that what we care about.
        # first step is to identify every 'class' that could
        # need async convertion.
        for name, target_type in inspect.getmembers(prawcore):
            if isinstance(target_type, ModuleType):
                if name == "_async":
                    continue
                if "prawcore." not in str(target_type):
                    continue
                package_submodules.append(name)
            # we need to exclude:
            #   A) already Async prefixed
            #   B) things that aren't package related (e.g. not prawcore)
            #   C) that aren't class definition.
            #   D) or that are Exception.
            if (
                "Async" in name
                or "prawcore" not in str(target_type)
                or hasattr(target_type, "__base__") is False
                or hasattr(target_type, "__cause__") is True
            ):
                logger.debug(f"Reference '{name}' ignored/excluded")
                continue

            if target_type not in top_level_types:
                logger.debug(f"Root reference added '{name}'")
                top_level_types.append(target_type)

            if target_type.__bases__:
                for parent_type in target_type.__bases__:
                    if parent_type is object:
                        continue
                    if parent_type not in top_level_types:
                        logger.debug(
                            f"Parent reference added '{parent_type.__name__}' from '{name}'"
                        )
                        top_level_types.append(parent_type)
                    for sub_class_of_parent in parent_type.__subclasses__():
                        if sub_class_of_parent is target_type:
                            continue
                        if sub_class_of_parent not in top_level_types:
                            logger.debug(
                                f"Child reference added '{sub_class_of_parent.__name__}' from '{parent_type.__name__}'"
                            )
                            top_level_types.append(sub_class_of_parent)

        logger.info(f"Found references: {', '.join(str(r) for r in top_level_types)}")

        #: class that should have async counterpart
        require_async_class: list[type] = []
        #: attrs that are compatible with async but are sync here
        require_async_attribute: dict[type, list[tuple[str, type]]] = {}
        #: methods that use those attrs
        require_async_method: dict[type, list[str]] = {}
        #: callable/callback within a class
        require_async_callable: dict[type, list[str]] = {}
        #: callable raw annotations for later convertion
        require_async_callable_annotations: dict[type, list[str]] = {}

        logger.info("Starting in-depth analysis of references (class w/ attributes)")

        # then we'll need to identify across multiple iteration
        # what actually is eligible to async convertion
        # e.g. class uses niquests.Session
        iter_count = 0

        while True:
            ref_count = 0
            logger.debug(f"Analysis iteration n°{iter_count + 1}")

            for target_type in top_level_types + indirect_types:
                logger.debug(f"Inspecting {target_type}")
                # we want to look at the constructor first.
                have_constructor = False
                try:
                    annotations_constructor_for_type = (
                        target_type.__init__.__annotations__
                    )
                    have_constructor = True
                except (
                    AttributeError
                ):  # class does not necessarily define a constructor (e.g. ABC class)
                    annotations_constructor_for_type = {}

                import_clauses_in_module = get_import_made_by(target_type)

                # detect class dependant (but not exposed directly)
                for dep_mod, dep_reference in import_clauses_in_module:
                    if (
                        not dep_mod.startswith("prawcore.")
                        or dep_reference is None
                        or dep_reference[0].islower()
                    ):
                        continue

                    dep_type = load_annotation(f"{dep_mod}.{dep_reference}")

                    if (
                        hasattr(dep_type, "__base__") is False
                        or hasattr(dep_type, "__cause__") is True
                    ):
                        continue

                    if dep_type in top_level_types:
                        continue
                    if dep_type not in indirect_types:
                        ref_count += 1
                        indirect_types.append(dep_type)
                        logger.debug(
                            f"Adding reference '{dep_type}' as indirect (not top level) dependency of '{target_type}'"
                        )

                definitions_in_module = get_definitions_in_module(target_type)

                for local_definition in definitions_in_module:
                    if local_definition.islower():
                        continue

                    dep_type = load_annotation(
                        f"{get_root_module_from(target_type)}.{local_definition}"
                    )

                    if (
                        hasattr(dep_type, "__base__") is False
                        or hasattr(dep_type, "__cause__") is True
                    ):
                        continue
                    if dep_type in top_level_types:
                        continue
                    if dep_type not in indirect_types:
                        ref_count += 1
                        indirect_types.append(dep_type)
                        logger.debug(
                            f"Adding reference '{dep_type}' as indirect (local) dependency of '{target_type}'"
                        )

                if have_constructor:
                    attrs_in_module = parse_constructor_attrs(target_type)
                else:
                    attrs_in_module = []

                interpreted_constructor_args = []

                for arg_name, arg_type in annotations_constructor_for_type.items():
                    arg_type = arg_type.replace("| None", "").strip()

                    if arg_type.islower():  # built-in types (str, float, ...)
                        continue

                    # this removes subscript on things like typing.Callable[...]
                    # we want typing.Callable only.
                    arg_type_no_sub = arg_type.split("[", maxsplit=1)[0]

                    full_type = None

                    for module, element in import_clauses_in_module:
                        if element == arg_type_no_sub:
                            full_type = f"{module}.{element}"
                            break

                    if full_type is None and arg_type in definitions_in_module:
                        full_type = (
                            f"{get_root_module_from(target_type)}.{arg_type_no_sub}"
                        )

                    interpreted_constructor_args.append((arg_name, full_type, arg_type))

                attrs_in_module_rebuilt = []

                for attr, assignment, annotation in attrs_in_module:
                    if annotation is None:
                        for x, y, z in interpreted_constructor_args:
                            if x in assignment:
                                annotation = ".".join(y.split(".")[:-1]) + "." + z
                                break
                    attrs_in_module_rebuilt.append((attr, assignment, annotation))

                for attr, assignment, annotation in attrs_in_module_rebuilt:
                    if annotation is None:
                        continue

                    annotation_light = annotation.replace("| None", "").strip()

                    # remove subscr / args in annotation in order to import it
                    if "[" in annotation_light:
                        annotation_light = annotation_light[
                            : annotation_light.index("[")
                        ]

                    if annotation_light.islower():  # built-in types (str, float, ...)
                        continue

                    loaded_type = load_annotation(annotation_light)

                    if (
                        loaded_type in require_async_class
                        or loaded_type == niquests.Session
                    ):
                        if target_type not in require_async_class:
                            ref_count += 1
                            require_async_class.append(target_type)
                            if target_type.__subclasses__():
                                for child_target in target_type.__subclasses__():
                                    if child_target not in require_async_class:
                                        require_async_class.append(child_target)
                        if target_type not in require_async_attribute:
                            require_async_attribute[target_type] = []

                        if (attr, loaded_type) not in require_async_attribute[
                            target_type
                        ]:
                            require_async_attribute[target_type].append(
                                (attr, loaded_type)
                            )
                    elif loaded_type is typing.Callable:
                        # don't mark callable without args or return as "convertible to async"
                        # we assume they don't block I/O
                        if "[" in annotation:
                            if target_type not in require_async_method:
                                require_async_method[target_type] = []
                            if target_type not in require_async_callable_annotations:
                                require_async_callable_annotations[target_type] = []

                            if (
                                annotation
                                not in require_async_callable_annotations[target_type]
                            ):
                                require_async_callable_annotations[target_type].append(
                                    annotation
                                )

                            if attr not in require_async_method[target_type]:
                                require_async_method[target_type].append(attr)

            iter_count += 1

            if ref_count == 0:
                logger.debug(
                    f"Exiting in-depth analysis at iteration n°{iter_count + 1}"
                )
                break

        logger.info("Starting simple base/child inheritance logic")

        inherent_convert_async = []

        # if a "base" class need to be converted to async
        # then, we automatically grab every child for convertion.
        for tbc_async in require_async_class:
            for tbc_async_subclass in tbc_async.__subclasses__():
                if (
                    tbc_async_subclass not in require_async_class
                    and tbc_async_subclass not in inherent_convert_async
                ):
                    logger.debug(
                        f"Reference {tbc_async_subclass} is added because {tbc_async} requires async convertion (as parent)"
                    )
                    inherent_convert_async.append(tbc_async_subclass)

        require_async_class.extend(inherent_convert_async)

        logger.info("Starting methods inspection in references")

        method_only_convert_async = []

        # we now need to scan which methods need to be converted to async
        while True:
            # this var is needed to know when to stop the loop
            # basically, ref_count means how many finding (e.g. to async required)
            # has been found.
            # we iterate because previous loop contain new reference that can be
            # referenced later by other methods/class.
            ref_count = 0

            for tbc_async in require_async_class + indirect_types:
                for potential_method_name in dir(tbc_async):
                    if potential_method_name.startswith("__"):
                        continue

                    potential_method = getattr(tbc_async, potential_method_name)

                    if callable(potential_method):
                        if "self" not in inspect.signature(potential_method).parameters:
                            continue

                        any_callable_in_parameters = False

                        for p, t in inspect.signature(
                            potential_method
                        ).parameters.items():
                            if (
                                isinstance(t.annotation, str)
                                and "Callable" in t.annotation
                            ):
                                any_callable_in_parameters = True
                                if tbc_async not in require_async_callable:
                                    require_async_callable[tbc_async] = []
                                if tbc_async not in require_async_callable_annotations:
                                    require_async_callable_annotations[tbc_async] = []
                                require_async_callable[tbc_async].append(p)
                                require_async_callable_annotations[tbc_async].append(
                                    t.annotation
                                )

                        raw_method_source = inspect.getsource(potential_method)

                        try:
                            async_attrs = require_async_attribute[tbc_async]
                        except KeyError:
                            try:
                                async_attrs = require_async_attribute[
                                    tbc_async.__base__
                                ]
                            except KeyError:
                                async_attrs = []

                        for attr_name, attr_type in async_attrs:
                            if re.findall(
                                rf"self\.{attr_name}\.(.*)\(", raw_method_source
                            ):
                                if tbc_async not in require_async_method:
                                    require_async_method[tbc_async] = []

                                if (
                                    potential_method_name
                                    not in require_async_method[tbc_async]
                                ):
                                    require_async_method[tbc_async].append(
                                        potential_method_name
                                    )
                                    ref_count += 1
                                    logger.debug(
                                        f"Method '{potential_method_name}' in reference {tbc_async} need to be converted to async. Reason: usage of attribute '{attr_name}' bound to '{attr_type}'"
                                    )
                                    break

                        for _ in require_async_method:
                            for require_async_method_future in require_async_method[_]:
                                if (
                                    f".{require_async_method_future}("
                                    in raw_method_source
                                ):
                                    if (
                                        tbc_async in require_async_method
                                        and potential_method_name
                                        not in require_async_method[tbc_async]
                                    ):
                                        require_async_method[tbc_async].append(
                                            potential_method_name
                                        )
                                        ref_count += 1
                                        logger.debug(
                                            f"Method '{potential_method_name}' in reference {tbc_async} need to be converted to async. Reason: usage of method {require_async_method_future}"
                                        )
                                        break

                        if any_callable_in_parameters:
                            if tbc_async not in require_async_method:
                                require_async_method[tbc_async] = []

                            if (
                                potential_method_name
                                not in require_async_method[tbc_async]
                            ):
                                require_async_method[tbc_async].append(
                                    potential_method_name
                                )
                                ref_count += 1
                                logger.debug(
                                    f"Method '{potential_method_name}' in reference {tbc_async} need to be converted to async. Reason: usage of callback"
                                )
                                if (
                                    tbc_async not in require_async_class
                                    and tbc_async not in method_only_convert_async
                                ):
                                    method_only_convert_async.append(tbc_async)

                        if "sleep(" in raw_method_source:
                            if tbc_async not in require_async_method:
                                require_async_method[tbc_async] = []

                            if (
                                potential_method_name
                                not in require_async_method[tbc_async]
                            ):
                                require_async_method[tbc_async].append(
                                    potential_method_name
                                )
                                ref_count += 1
                                logger.debug(
                                    f"Method '{potential_method_name}' in reference {tbc_async} need to be converted to async. Reason: usage of function sleep"
                                )
                                if (
                                    tbc_async not in require_async_class
                                    and tbc_async not in method_only_convert_async
                                ):
                                    method_only_convert_async.append(tbc_async)

            if ref_count == 0:
                break

        # some class need to be async due to a method
        # using I/O blocking functions like sleep.
        # it is detected later in the process because
        # the constructor wasn't specified or none of the attrs
        # were async "compatible".
        require_async_class.extend(method_only_convert_async)

        logger.info("Analysis ended.")

        # output primarily analysis results, mapping.
        for tbc_async in require_async_class:
            logger.info(f"Reference '{tbc_async}' need async counterpart")

        for tbc_async in require_async_attribute:
            logger.info(
                f"Reference '{tbc_async}' attributes: {', '.join(str(e) for e in require_async_attribute[tbc_async])}"
            )

        for tbc_async in require_async_method:
            logger.info(
                f"Reference '{tbc_async}' methods: {', '.join(require_async_method[tbc_async])}"
            )

        file_to_copy = []
        tbd_async_module = []

        # determine what file need to be duplicated
        for tbc_async in require_async_method:
            file = get_owned_by_module_path(tbc_async)

            if file not in file_to_copy:
                file_to_copy.append(file)
                tbd_async_module.append(get_root_module_from(tbc_async))

        logger.info(f"Async module required: {tbd_async_module}")
        logger.info(
            f"The following files(modules) need to be duplicated: {file_to_copy}"
        )

        need_remap_submodule_level_import = []

        for pkg_submodule in package_submodules:
            if f"prawcore.{pkg_submodule}" not in tbd_async_module:
                need_remap_submodule_level_import.append(pkg_submodule)

        logger.info(
            f"The following submodules are untouched: {need_remap_submodule_level_import}"
        )

        # we'll start to duplicate and patch the required files
        # with acquired knowledge about the package structure
        # and internal relationships.
        with TemporaryDirectory(prefix="prawcore_async", delete=False) as tmp_dir:
            logger.info(f"Provisioning temporary directory at '{tmp_dir}'")

            logger.info(
                f"Copying project configuration (pyproject.toml) to '{tmp_dir}'"
            )

            # we need this, because we want our project configuration
            # to be applied as is. not the default one upon post-fmt
            # (e.g. tools like black, ruff, etc...)
            tmp_module_path = os.path.join(tmp_dir, "pyproject.toml")
            shutil.copy(
                os.path.join(Path(file_to_copy[0]).parent.parent, "pyproject.toml"),
                tmp_module_path,
            )

            package_tmp_rootdir = os.path.join(tmp_dir, "prawcore")

            os.mkdir(package_tmp_rootdir)

            shutil.copy(
                os.path.join(Path(file_to_copy[0]).parent, "__init__.py"),
                package_tmp_rootdir,
            )

            subpackage_tmp_rootdir = os.path.join(package_tmp_rootdir, "_async")

            os.mkdir(subpackage_tmp_rootdir)

            os.mknod(os.path.join(subpackage_tmp_rootdir, "__init__.py"))

            for file_path in file_to_copy:
                logger.info(f"Copy and patch module '{file_path}'")

                tmp_module_path = os.path.join(
                    subpackage_tmp_rootdir, Path(file_path).name
                )
                shutil.copy(file_path, tmp_module_path)

                with open(tmp_module_path, "r", encoding="utf-8") as fp:
                    tmp_src_raw = fp.read()

                # we don't want absolute import as it is messing
                # with following "relative" import adjustments.
                if "from prawcore." in tmp_src_raw:
                    tmp_src_raw = tmp_src_raw.replace("from prawcore.", "from .")

                # if we don't duplicate submodule 'X' then we'll need to import
                # it from a level higher as generated code will lie in a subpackage.
                for untouched_submodule in need_remap_submodule_level_import:
                    clause_a = f"from .{untouched_submodule} import"
                    patch_a = clause_a.replace(".", "..")

                    clause_b = f"from . import {untouched_submodule}"
                    patch_b = clause_b.replace(".", "..")

                    if clause_a in tmp_src_raw:
                        tmp_src_raw = tmp_src_raw.replace(clause_a, patch_a)

                    if clause_b in tmp_src_raw:
                        tmp_src_raw = tmp_src_raw.replace(clause_b, patch_b)

                # usually it's about importing __version__ or alike root module attribute
                if "from . import __" in tmp_src_raw:
                    tmp_src_raw = tmp_src_raw.replace(
                        "from . import __", "from .. import __"
                    )

                for tbd_async in require_async_class:
                    # class rename
                    if f"class {tbd_async.__name__}" in tmp_src_raw:
                        tmp_src_raw = tmp_src_raw.replace(
                            f"class {tbd_async.__name__}",
                            f"class Async{tbd_async.__name__}",
                        )

                    # typing rename
                    if f" {tbd_async.__name__}" in tmp_src_raw:
                        tmp_src_raw = tmp_src_raw.replace(
                            f" {tbd_async.__name__}", f" Async{tbd_async.__name__}"
                        )

                    # class inheritance rename
                    if f"({tbd_async.__name__}):" in tmp_src_raw:
                        tmp_src_raw = tmp_src_raw.replace(
                            f"({tbd_async.__name__}):", f"(Async{tbd_async.__name__}):"
                        )

                    # special edge case rename
                    if f"({tbd_async.__name__}" in tmp_src_raw:
                        tmp_src_raw = tmp_src_raw.replace(
                            f"({tbd_async.__name__}", f"(Async{tbd_async.__name__}"
                        )

                    # typing subscription arg rename
                    if f"[{tbd_async.__name__}" in tmp_src_raw:
                        tmp_src_raw = tmp_src_raw.replace(
                            f"[{tbd_async.__name__}", f"[Async{tbd_async.__name__}"
                        )

                    # do the same as above for kept "Callable" annotations
                    # to ensure we can properly patch it (for Awaitable)
                    if tbd_async in require_async_callable_annotations:
                        require_async_callable_annotations_patched = []

                        for callable_annot in require_async_callable_annotations[
                            tbd_async
                        ]:
                            require_async_callable_annotations_patched.append(
                                callable_annot.replace(
                                    f"[{tbd_async.__name__}",
                                    f"[Async{tbd_async.__name__}",
                                )
                            )

                        require_async_callable_annotations[tbd_async] = (
                            require_async_callable_annotations_patched
                        )

                    # docstr replace
                    if f":class:`.{tbd_async.__name__}`" in tmp_src_raw:
                        tmp_src_raw = tmp_src_raw.replace(
                            f":class:`.{tbd_async.__name__}`",
                            f":class:`.Async{tbd_async.__name__}`",
                        )

                    # automatically convert contextmgr magic methods to async counterpart
                    if "def __enter__(" in tmp_src_raw:
                        tmp_src_raw = tmp_src_raw.replace(
                            "def __enter__(", "async def __aenter__("
                        )
                        tmp_src_raw = tmp_src_raw.replace(
                            "def __exit__(", "async def __aexit__("
                        )

                    # time.sleep is blocking, convert it to asyncio and make it await(ed)
                    if "time.sleep(" in tmp_src_raw:
                        tmp_src_raw = preg_replace(
                            tmp_src_raw,
                            rf"time\.sleep\(",
                            insert="await",
                            before="time.",
                        )
                        tmp_src_raw = tmp_src_raw.replace("time.sleep", "asyncio.sleep")

                    # obviously niquests.Session
                    if "niquests.Session(" in tmp_src_raw:
                        tmp_src_raw = tmp_src_raw.replace(
                            "niquests.Session(", "niquests.AsyncSession("
                        )
                    if " Session(" in tmp_src_raw:
                        tmp_src_raw = tmp_src_raw.replace(" Session(", " AsyncSession(")
                    if ": niquests.Session" in tmp_src_raw:
                        tmp_src_raw = tmp_src_raw.replace(
                            ": niquests.Session", ": niquests.AsyncSession"
                        )

                    # we assume every method "sleep" is blocking I/O
                    # and already made awaitable.
                    tmp_src_raw = preg_replace(
                        tmp_src_raw,
                        rf"(.*)\.sleep\(\)",
                        insert="await",
                    )

                    # we should add asyncio import if any function invoked in it.
                    if (
                        "asyncio." in tmp_src_raw
                        and "import asyncio" not in tmp_src_raw
                    ):
                        first_import_idx = tmp_src_raw.index("\nimport")
                        tmp_src_raw = (
                            tmp_src_raw[0:first_import_idx]
                            + "import asyncio\n"
                            + tmp_src_raw[first_import_idx:]
                        )

                    if tbd_async in require_async_attribute:
                        if tbd_async in require_async_attribute:
                            for attr_name, attr_type in require_async_attribute[
                                tbd_async
                            ]:
                                # not every method from given (eligible async) attr can be awaited.
                                # act with caution. We'll probe our internal map "class -> awaitable methods"
                                # to know if await is required.
                                def _inner_check_method_awaitable(
                                    detect_match: list[str],
                                ) -> bool:
                                    _inner_method_call = detect_match[0]
                                    if attr_type not in require_async_method:
                                        return False
                                    if (
                                        _inner_method_call
                                        in require_async_method[attr_type]
                                    ):
                                        return True
                                    return False

                                tmp_src_raw = preg_replace(
                                    tmp_src_raw,
                                    rf" self.{attr_name}\.(.*)\((.*)\)$",
                                    insert="await",
                                    before="self.",
                                    callback_ignore_if=_inner_check_method_awaitable,
                                )

                    if tbd_async in require_async_callable:
                        for callable_name in require_async_callable[tbd_async]:
                            tmp_src_raw = preg_replace(
                                tmp_src_raw,
                                rf"{callable_name}\((?!self)",
                                insert="await",
                                before=callable_name,
                            )

                    if tbd_async in require_async_callable_annotations:
                        # every Callable annot need to be converted to returning Awaitable
                        # two fmt: Callable (e.g. without args) --> Callable[[], Awaitable[None]]
                        # or     : Callable[[...], ...] need to become Callable[[.....], Awaitable[...]]
                        for callable_annot in require_async_callable_annotations[
                            tbd_async
                        ]:
                            if callable_annot.endswith("]"):
                                callable_annot = callable_annot.replace("typing.", "")
                                tmp_src_raw = tmp_src_raw.replace(
                                    callable_annot,
                                    preg_replace(
                                        callable_annot,
                                        r"Callable\[\[(.*)\], (.*)\]",
                                        insert="Awaitable[",
                                        after=", ",
                                        extraneous_space=False,
                                    )
                                    + "]",
                                )

                    if (
                        "Awaitable[" in tmp_src_raw
                        and "import Awaitable" not in tmp_src_raw
                    ):
                        first_import_idx = tmp_src_raw.index("\nimport")
                        tmp_src_raw = (
                            tmp_src_raw[0:first_import_idx]
                            + "\nfrom typing import Awaitable\n"
                            + tmp_src_raw[first_import_idx:]
                        )

                    if tbd_async in require_async_method:
                        for method_name in require_async_method[tbd_async]:
                            tmp_src_raw = preg_replace(
                                tmp_src_raw,
                                rf"def {method_name}\(",
                                insert="async",
                                before="def",
                            )
                            tmp_src_raw = preg_replace(
                                tmp_src_raw,
                                rf"self.(.*)\.{method_name}\(",
                                insert="await",
                                before="self.",
                            )
                            tmp_src_raw = preg_replace(
                                tmp_src_raw,
                                rf"self\.{method_name}\(",
                                insert="await",
                                before="self.",
                            )
                            tmp_src_raw = preg_replace(
                                tmp_src_raw,
                                rf"super\(\)\.{method_name}\(",
                                insert="await",
                                before="super(",
                            )

                # finally write the resulting patched source to tmp module file
                with open(tmp_module_path, "w", encoding="utf-8") as fp:
                    fp.write(tmp_src_raw)

        # We need to reformat / lint the output
        # So that the git diff will actually be
        # useful.
        logger.info("Run black fmt over newly generated source")

        try:
            reformatted_modules = black_reformat(tmp_dir)
        except IOError as e:
            logger.error(str(e))
            shutil.rmtree(tmp_dir)
            exit(2)
        except CalledProcessError as e:
            logger.critical(str(e))
            shutil.rmtree(tmp_dir)
            exit(3)

        if not reformatted_modules:
            logger.info("Black report nothing to be reformatted")
        else:
            for refmt in reformatted_modules:
                logger.info(refmt)

        logger.info("Run Ruff fmt/lint over newly generated source")

        try:
            reformatted_modules = ruff_reformat(tmp_dir)
        except IOError as e:
            logger.error(str(e))
            shutil.rmtree(tmp_dir)
            exit(2)
        except CalledProcessError as e:
            logger.critical(str(e))
            shutil.rmtree(tmp_dir)
            exit(3)

        if not reformatted_modules:
            logger.info("Ruff report nothing to be reformatted")
        else:
            for refmt in reformatted_modules:
                logger.info(refmt)

        logger.info("Run docstrfmt fmt over newly generated source")

        try:
            reformatted_modules = docstrfmt_reformat(tmp_dir)
        except IOError as e:
            logger.error(str(e))
            shutil.rmtree(tmp_dir)
            exit(2)
        except CalledProcessError as e:
            logger.critical(str(e))
            shutil.rmtree(tmp_dir)
            exit(3)

        if not reformatted_modules:
            logger.info("docstrfmt report nothing to be reformatted")
        else:
            for refmt in reformatted_modules:
                logger.info(refmt)

        any_diff_async_async: bool = False

        # now we check the diff between (sync) main and new generation
        for file_path in file_to_copy:
            logger.info(f"Scan difference with '{file_path}'")

            root_package_dir = Path(file_path).parent
            expected_package_async_loc = os.path.join(
                root_package_dir, f"_async/{Path(file_path).name}"
            )

            logger.info(f"Expected destination '{expected_package_async_loc}'")

            tmp_module_path = os.path.join(subpackage_tmp_rootdir, Path(file_path).name)

            if should_display_diff_sync_async:
                try:
                    patch = git_diff(file_path, tmp_module_path)
                except CalledProcessError as e:
                    logger.critical(str(e))
                    shutil.rmtree(tmp_dir)
                    exit(3)

                for line in patch:
                    logger.info(line)

            if os.path.exists(expected_package_async_loc):
                try:
                    patch = git_diff(expected_package_async_loc, tmp_module_path)
                except CalledProcessError as e:
                    logger.critical(str(e))
                    shutil.rmtree(tmp_dir)
                    exit(3)

                if should_display_diff_async_async:
                    for line in patch:
                        logger.info(line)

                if len(patch) > 1:
                    logger.warning(
                        f"Async source for '{expected_package_async_loc}' is outdated"
                    )
                    any_diff_async_async = True

                if should_write_into_package:
                    if not os.path.exists(str(root_package_dir) + "/_async"):
                        os.mkdir(str(root_package_dir) + "/_async")
                    shutil.copy(tmp_module_path, expected_package_async_loc)
            else:
                any_diff_async_async = True
                logger.warning(
                    f"non-existent async module '{expected_package_async_loc}'. need git add on it."
                )

        if any_diff_async_async:
            if should_write_into_package is False:
                logger.warning(
                    "Async code is outdated. Run the script with --fix to update the async parts"
                )
            else:
                logger.info("Async code successfully updated to latest (sync) changes")
            shutil.rmtree(tmp_dir)
            exit(1)
        else:
            logger.info("Async code is already up-to-date!")

        shutil.rmtree(tmp_dir)
    except Exception as e:
        logger.critical(str(e))
        exit(4)
