# -*- coding: utf-8 -*-
"""Inspection statique et sans secret du module Django de configuration."""

import ast
import importlib.machinery
import os
import re
import sys
from pathlib import Path

SENSITIVE = {"SECRET_KEY", "DATABASES", "CORS_ALLOWED_ORIGINS", "ALLOWED_HOSTS", "CSRF_TRUSTED_ORIGINS"}
BOOL_OR_NUMBER = {
    "DEBUG", "CORS_ALLOW_ALL_ORIGINS", "CORS_ORIGIN_ALLOW_ALL", "SECURE_SSL_REDIRECT",
    "SESSION_COOKIE_SECURE", "CSRF_COOKIE_SECURE", "SECURE_HSTS_SECONDS",
    "SECURE_CONTENT_TYPE_NOSNIFF", "SECURE_PROXY_SSL_HEADER",
}


def yes_no(value):
    return "YES" if value else "NO"


def is_env_expression(node):
    for child in ast.walk(node):
        if isinstance(child, ast.Name) and child.id.lower() in ("env", "environ", "getenv"):
            return True
        if isinstance(child, ast.Attribute) and child.attr.lower() in ("environ", "getenv"):
            return True
    return False


def literal(node):
    try:
        return ast.literal_eval(node)
    except (ValueError, TypeError, SyntaxError):
        return None


def assigned_names(target):
    if isinstance(target, ast.Name):
        yield target.id
    elif isinstance(target, (ast.Tuple, ast.List)):
        for child in target.elts:
            yield from assigned_names(child)


def assignments(tree):
    result = {}
    for node in tree.body:
        if isinstance(node, ast.Assign):
            names = []
            for target in node.targets:
                names.extend(assigned_names(target))
            for name in names:
                result.setdefault(name, []).append((node.lineno, node.value))
        elif isinstance(node, ast.AnnAssign):
            for name in assigned_names(node.target):
                if node.value is not None:
                    result.setdefault(name, []).append((node.lineno, node.value))
    return result


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


def package_locations(spec):
    if spec is None:
        return []
    locations = list(spec.submodule_search_locations or [])
    if locations:
        return [Path(item).resolve() for item in locations]
    if spec.origin:
        return [Path(spec.origin).resolve().parent]
    return []


def under_root(path, root):
    try:
        return os.path.commonpath([os.path.normcase(str(path)), os.path.normcase(str(root))]) == os.path.normcase(str(root))
    except (OSError, ValueError):
        return False


def find_settings_source(root):
    manage = root / "manage.py"
    if not manage.is_file():
        return None, "manage.py missing"
    text = manage.read_text(encoding="utf-8", errors="replace")
    match = re.search(
        r"setdefault\s*\(\s*['\"]DJANGO_SETTINGS_MODULE['\"]\s*,\s*['\"]([^'\"]+)['\"]",
        text,
    )
    if not match:
        return None, "settings module could not be parsed from manage.py"
    module_name = match.group(1)
    parts = module_name.split(".")
    spec = importlib.machinery.PathFinder.find_spec(parts[0], sys.path)
    locations = package_locations(spec)
    candidates = []
    for location in locations:
        if len(parts) > 1:
            rel = Path(*parts[1:])
            for candidate in (location / rel.with_suffix(".py"), location / rel / "__init__.py"):
                if candidate.is_file():
                    candidates.append(candidate.resolve())
        elif spec and spec.origin and Path(spec.origin).is_file():
            candidates.append(Path(spec.origin).resolve())
    if not candidates:
        return None, module_name
    return candidates[0], module_name


def describe(name, node):
    value = literal(node)
    env_source = yes_no(is_env_expression(node))
    if name in SENSITIVE:
        return "line={}; value=REDACTED; environment_reference={}".format(node.lineno, env_source)
    if name in ("ALLOWED_HOSTS", "CORS_ALLOWED_ORIGINS", "CSRF_TRUSTED_ORIGINS"):
        if isinstance(value, (list, tuple, set)):
            wildcard = name == "ALLOWED_HOSTS" and "*" in value
            return "line={}; count={}; wildcard={}; values=REDACTED; environment_reference={}".format(
                node.lineno, len(value), yes_no(wildcard), env_source
            )
        return "line={}; value=DYNAMIC_OR_REDACTED; environment_reference={}".format(node.lineno, env_source)
    if name in BOOL_OR_NUMBER:
        if isinstance(value, (bool, int, float)) or value is None:
            return "line={}; value={}; environment_reference={}".format(node.lineno, value, env_source)
        return "line={}; value=DYNAMIC; environment_reference={}".format(node.lineno, env_source)
    if name in ("MIDDLEWARE", "INSTALLED_APPS") and isinstance(value, (list, tuple)):
        strings = [item for item in value if isinstance(item, str)]
        if name == "MIDDLEWARE":
            return "line={}; count={}; SecurityMiddleware={}; XFrameOptionsMiddleware={}; values=REDACTED".format(
                node.lineno,
                len(value),
                yes_no(any(item.endswith("SecurityMiddleware") for item in strings)),
                yes_no(any(item.endswith("XFrameOptionsMiddleware") for item in strings)),
            )
        return "line={}; count={}; JWT_BLACKLIST={}; WHITENOISE={}; values=REDACTED".format(
            node.lineno,
            len(value),
            yes_no("rest_framework_simplejwt.token_blacklist" in strings),
            yes_no(any("whitenoise" in item.lower() for item in strings)),
        )
    if name == "LOGGING" and isinstance(value, dict):
        handlers = value.get("handlers", {})
        return "line={}; handlers_count={}; values=REDACTED".format(
            node.lineno, len(handlers) if isinstance(handlers, dict) else "DYNAMIC"
        )
    if name == "SIMPLE_JWT" and isinstance(value, dict):
        rotate = value.get("ROTATE_REFRESH_TOKENS", "UNSPECIFIED")
        return "line={}; ROTATE_REFRESH_TOKENS={}; token_values=REDACTED".format(node.lineno, rotate)
    return "line={}; type={}; environment_reference={}".format(node.lineno, type(node).__name__, env_source)


root = Path(__file__).resolve().parent
settings_file, settings_module = find_settings_source(root)
print("PROJECT_ROOT_HAS_MANAGE_PY=" + yes_no((root / "manage.py").is_file()))
print("DJANGO_SETTINGS_MODULE=" + str(settings_module))

try:
    manage_tree = ast.parse((root / "manage.py").read_text(encoding="utf-8", errors="replace"))
    print("MANAGE_PY_ACTUAL_SYS_PATH_MUTATION=" + yes_no(sys_path_mutation(manage_tree)))
except (OSError, SyntaxError):
    print("MANAGE_PY_ACTUAL_SYS_PATH_MUTATION=UNREADABLE")

if settings_file is None:
    print("SETTINGS_SOURCE_FOUND=NO")
    print("RESULT=INSPECTION_INCOMPLETE")
    sys.exit(1)

settings_in_project = under_root(settings_file, root)
print("SETTINGS_SOURCE_RELATIVE=" + (str(settings_file.relative_to(root)) if settings_in_project else "OUTSIDE_PROJECT"))
print("SETTINGS_SOURCE_MATCHES_PROJECT=" + yes_no(settings_in_project))
if not settings_in_project:
    print("RESULT=SOURCE_OUTSIDE_PROJECT")
    sys.exit(1)
relative = settings_file.relative_to(root)
try:
    source = settings_file.read_text(encoding="utf-8", errors="replace")
    tree = ast.parse(source, filename=str(relative))
except (OSError, SyntaxError) as exc:
    print("SETTINGS_SOURCE_PARSE=FAIL")
    print("SETTINGS_SOURCE_ERROR_TYPE=" + type(exc).__name__)
    print("RESULT=INSPECTION_INCOMPLETE")
    sys.exit(1)

found = assignments(tree)
keys = (
    "DEBUG", "ALLOWED_HOSTS", "CORS_ALLOW_ALL_ORIGINS", "CORS_ORIGIN_ALLOW_ALL",
    "CORS_ALLOWED_ORIGINS", "CSRF_TRUSTED_ORIGINS", "SECRET_KEY", "DATABASES",
    "SECURE_SSL_REDIRECT", "SESSION_COOKIE_SECURE", "CSRF_COOKIE_SECURE",
    "SECURE_HSTS_SECONDS", "SECURE_PROXY_SSL_HEADER", "SECURE_CONTENT_TYPE_NOSNIFF",
    "MIDDLEWARE", "INSTALLED_APPS", "LOGGING", "SIMPLE_JWT", "STATIC_ROOT", "MEDIA_ROOT",
)
for name in keys:
    rows = found.get(name, [])
    print(name + "_ASSIGNMENT_COUNT=" + str(len(rows)))
    for index, (line, value_node) in enumerate(rows, 1):
        print(name + "_" + str(index) + "=" + describe(name, value_node).replace("line={}".format(value_node.lineno), "line=" + str(line)))

print("NOTE=No setting value, password, SECRET_KEY, hostname or CORS origin is displayed.")
print("RESULT=SOURCE_INSPECTION_OK")
