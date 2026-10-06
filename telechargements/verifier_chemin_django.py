# -*- coding: utf-8 -*-
"""Verifie sans importer Django ou toucher a la base ou aux secrets quel code Python est resolu."""

import ast
import importlib.machinery
import os
import re
import sys
from pathlib import Path


def yes_no(value):
    return "YES" if value else "NO"


def is_under(path, root):
    try:
        path_text = os.path.normcase(os.path.realpath(str(path)))
        root_text = os.path.normcase(os.path.realpath(str(root)))
        return os.path.commonpath([path_text, root_text]) == root_text
    except (OSError, ValueError):
        return False


def package_locations(spec):
    if spec is None:
        return []
    locations = list(spec.submodule_search_locations or [])
    if locations:
        return [Path(p).resolve() for p in locations]
    if spec.origin:
        return [Path(spec.origin).resolve().parent]
    return []


def sys_path_mutation(tree):
    def is_sys_path(node):
        if isinstance(node, ast.Attribute) and node.attr == "path":
            return isinstance(node.value, ast.Name) and node.value.id == "sys"
        if isinstance(node, ast.Subscript):
            return is_sys_path(node.value)
        return False

    for node in ast.walk(tree):
        if isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            if any(is_sys_path(target) for target in targets):
                return True
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            if node.func.attr in ("append", "extend", "insert") and is_sys_path(node.func.value):
                return True
    return False


root = Path(__file__).resolve().parent
manage = root / "manage.py"
print("PROJECT_ROOT_HAS_MANAGE_PY=" + yes_no(manage.is_file()))
print("PYTHON_EXECUTABLE_AVAILABLE=YES")

if not manage.is_file():
    print("STOP=Extract this package next to manage.py in the confirmed project folder.")
    sys.exit(2)

try:
    source = manage.read_text(encoding="utf-8", errors="replace")
except OSError:
    source = ""
match = re.search(
    r"setdefault\s*\(\s*['\"]DJANGO_SETTINGS_MODULE['\"]\s*,\s*['\"]([^'\"]+)['\"]",
    source,
)
settings_module = match.group(1) if match else "UNRESOLVED"
print("DJANGO_SETTINGS_MODULE=" + settings_module)
try:
    manage_tree = ast.parse(source)
    print("MANAGE_PY_ACTUAL_SYS_PATH_MUTATION=" + yes_no(sys_path_mutation(manage_tree)))
except SyntaxError:
    print("MANAGE_PY_ACTUAL_SYS_PATH_MUTATION=UNREADABLE")

settings_package = settings_module.split(".", 1)[0] if settings_module != "UNRESOLVED" else "config"
settings_spec = importlib.machinery.PathFinder.find_spec(settings_package, sys.path)
settings_locations = package_locations(settings_spec)
settings_candidates = []
if settings_spec is not None:
    module_parts = settings_module.split(".")[1:]
    for location in settings_locations:
        base = location
        if module_parts:
            relative = Path(*module_parts)
            candidates = [base / relative.with_suffix(".py"), base / relative / "__init__.py"]
            settings_candidates.extend(candidate.resolve() for candidate in candidates if candidate.is_file())
settings_in_project = bool(settings_candidates) and all(is_under(path, root) for path in settings_candidates)
print("SETTINGS_PACKAGE_FOUND=" + yes_no(settings_spec is not None))
print("SETTINGS_PACKAGE_MATCHES_PROJECT=" + yes_no(bool(settings_locations) and all(is_under(p, root) for p in settings_locations)))
print("SETTINGS_FILE_CANDIDATE_COUNT=" + str(len(settings_candidates)))
print("SETTINGS_FILE_MATCHES_PROJECT=" + yes_no(settings_in_project))

apps_spec = importlib.machinery.PathFinder.find_spec("apps", sys.path)
apps_locations = package_locations(apps_spec)
print("APPS_PACKAGE_FOUND=" + yes_no(apps_spec is not None))
print("APPS_PACKAGE_MATCHES_PROJECT=" + yes_no(bool(apps_locations) and all(is_under(p, root) for p in apps_locations)))

for label, relative in (
    ("ACCOUNTS_SETTINGS_VIEWS", Path("accounts") / "settings_views.py"),
    ("COMMON_AUTHENTICATION", Path("common") / "authentication.py"),
):
    candidates = [location / relative for location in apps_locations]
    existing = [candidate.resolve() for candidate in candidates if candidate.is_file()]
    print(label + "_FOUND=" + yes_no(bool(existing)))
    print(label + "_MATCHES_PROJECT=" + yes_no(bool(existing) and all(is_under(p, root) for p in existing)))

if settings_spec is None or apps_spec is None or not settings_in_project or not apps_locations:
    print("RESULT=PATH_MISMATCH_OR_INCOMPLETE")
    sys.exit(1)
if not all(is_under(p, root) for p in apps_locations):
    print("RESULT=PATH_MISMATCH_OR_INCOMPLETE")
    sys.exit(1)
print("RESULT=PROJECT_IMPORTS_MATCH_CURRENT_FOLDER")
print("NOTE=No Django app code was imported; no database or secrets were accessed.")
