#!/usr/bin/env python3
"""Ajoute un filtre de vendeur au queryset du bilan NEXORA.

Les comptes CASHIER restent limités à leurs propres ventes. Les rôles de gestion
peuvent sélectionner un vendeur avec le paramètre HTTP seller_id; sans ce
paramètre, le bilan d'entreprise reste global.
"""
from __future__ import annotations

import ast
import datetime as dt
import os
import sys
import tempfile
from pathlib import Path

MARKER_V1 = "# NEXORA_FIX_BILAN_VENDEUR_V1"
MARKER_V2 = "# NEXORA_FIX_BILAN_VENDEUR_V2"
PATCH_LINES = (
    MARKER_V2,
    "if getattr(request.user, 'role', None) == 'CASHIER':",
    "    sales_qs = sales_qs.filter(seller=request.user)",
    "else:",
    "    params = getattr(request, 'query_params', None)",
    "    if params is None:",
    "        params = getattr(request, 'GET', {})",
    "    seller_id = params.get('seller_id')",
    "    if seller_id not in (None, ''):",
    "        sales_qs = sales_qs.filter(seller_id=seller_id)",
)


class PatchError(Exception):
    pass


def read_utf8(path: Path) -> tuple[str, bytes]:
    raw = path.read_bytes()
    bom = b"\xef\xbb\xbf" if raw.startswith(b"\xef\xbb\xbf") else b""
    try:
        return raw[len(bom):].decode("utf-8"), bom
    except UnicodeDecodeError as exc:
        raise PatchError(f"Le fichier n'est pas en UTF-8 : {path}") from exc


def function_arguments(node: ast.FunctionDef | ast.AsyncFunctionDef) -> set[str]:
    args = list(node.args.posonlyargs) + list(node.args.args) + list(node.args.kwonlyargs)
    if node.args.vararg:
        args.append(node.args.vararg)
    if node.args.kwarg:
        args.append(node.args.kwarg)
    return {arg.arg for arg in args}


def is_sale_filter_call(node: ast.AST) -> bool:
    if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
        return False
    if node.func.attr != "filter" or not isinstance(node.func.value, ast.Attribute):
        return False
    manager = node.func.value
    return manager.attr == "objects" and isinstance(manager.value, ast.Name) and manager.value.id == "Sale"


def assigned_name(node: ast.AST, name: str) -> bool:
    targets = node.targets if isinstance(node, ast.Assign) else [node.target] if isinstance(node, ast.AnnAssign) else []
    return any(isinstance(target, ast.Name) and target.id == name for target in targets)


def confirm_project(root: Path) -> None:
    required = [
        root / "manage.py",
        root / "apps" / "reports" / "views.py",
        root / "apps" / "sales" / "models.py",
        root / "apps" / "accounts" / "models.py",
        root / "apps" / "common" / "permissions.py",
    ]
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        raise PatchError("Fichiers attendus absents :\n  " + "\n  ".join(missing))

    sale_text, _ = read_utf8(root / "apps" / "sales" / "models.py")
    account_text, _ = read_utf8(root / "apps" / "accounts" / "models.py")
    permission_text, _ = read_utf8(root / "apps" / "common" / "permissions.py")
    if "seller" not in sale_text or "ForeignKey" not in sale_text:
        raise PatchError("Le modèle Sale ne confirme pas le champ vendeur ForeignKey.")
    if "CASHIER" not in account_text:
        raise PatchError("Le rôle CASHIER n'est pas présent dans apps/accounts/models.py.")
    permission_compact = "".join(permission_text.split())
    cashier_check = "role=='CASHIER'" in permission_compact or 'role=="CASHIER"' in permission_compact
    if not cashier_check or "obj.seller==user" not in permission_compact:
        raise PatchError("La règle obj.seller == user pour le rôle CASHIER n'est pas confirmée.")


def locate_query(tree: ast.Module) -> tuple[ast.FunctionDef | ast.AsyncFunctionDef, ast.AST]:
    parents: dict[ast.AST, ast.AST] = {}
    for parent in ast.walk(tree):
        for child in ast.iter_child_nodes(parent):
            parents[child] = parent

    candidates: list[tuple[ast.FunctionDef | ast.AsyncFunctionDef, ast.AST]] = []
    for node in ast.walk(tree):
        if not assigned_name(node, "sales_qs"):
            continue
        value = node.value if isinstance(node, (ast.Assign, ast.AnnAssign)) else None
        if not is_sale_filter_call(value):
            continue
        keywords = {kw.arg for kw in value.keywords if kw.arg is not None}
        if not {"company", "status", "created_at__gte"}.issubset(keywords):
            continue
        ancestor: ast.AST | None = node
        while ancestor is not None and not isinstance(ancestor, (ast.FunctionDef, ast.AsyncFunctionDef)):
            ancestor = parents.get(ancestor)
        if isinstance(ancestor, (ast.FunctionDef, ast.AsyncFunctionDef)) and "request" in function_arguments(ancestor):
            candidates.append((ancestor, node))

    if len(candidates) != 1:
        raise PatchError(
            "Impossible d'identifier sans ambiguïté le queryset sales_qs "
            "(Sale.objects.filter(company, status, created_at__gte) dans une vue recevant request). "
            "Aucune modification effectuée."
        )
    return candidates[0]


def custom_seller_filter(function: ast.AST) -> bool:
    for node in ast.walk(function):
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
            continue
        if node.func.attr != "filter" or not isinstance(node.func.value, ast.Name):
            continue
        if node.func.value.id == "sales_qs" and any(kw.arg == "seller" for kw in node.keywords):
            return True
    return False


def prepare_patch(path: Path) -> tuple[str, bytes, str, int, str]:
    text, bom = read_utf8(path)
    try:
        tree = ast.parse(text, filename=str(path))
    except SyntaxError as exc:
        raise PatchError(f"Le fichier cible contient déjà une erreur Python : {exc}") from exc
    function, assignment = locate_query(tree)
    if MARKER_V2 in text:
        return text, bom, "DÉJÀ_APPLIQUÉ_V2", assignment.lineno, function.name
    lines = text.splitlines(keepends=True)
    plain = [line.rstrip("\r\n") for line in lines]
    newline = "\r\n" if "\r\n" in text else "\n"

    old_markers = [i for i, line in enumerate(plain) if line.strip() == MARKER_V1]
    if len(old_markers) > 1:
        raise PatchError("Plusieurs blocs V1 sont présents; aucune modification effectuée.")
    if old_markers:
        index = old_markers[0]
        if index + 2 >= len(plain):
            raise PatchError("Le bloc V1 est incomplet; aucune modification effectuée.")
        marker_line = plain[index]
        indent = marker_line[: len(marker_line) - len(marker_line.lstrip(" \t"))]
        old = [plain[index + i][len(indent):] for i in range(3)]
        expected = [
            MARKER_V1,
            "if getattr(request.user, 'role', None) == 'CASHIER':",
            "    sales_qs = sales_qs.filter(seller=request.user)",
        ]
        if old != expected:
            raise PatchError("Le bloc V1 ne correspond pas au correctif attendu; aucune modification.")
        replacement = [indent + line + newline for line in PATCH_LINES]
        updated = "".join(lines[:index] + replacement + lines[index + 3:])
        operation = "MISE_À_JOUR_V1_VERS_V2"
    else:
        if custom_seller_filter(function):
            raise PatchError("Un filtre seller personnalisé existe déjà; aucune modification automatique.")
        end_line = getattr(assignment, "end_lineno", None)
        if end_line is None:
            raise PatchError("Python ne fournit pas end_lineno; aucune modification.")
        query_line = lines[assignment.lineno - 1]
        indent = query_line[: len(query_line) - len(query_line.lstrip(" \t"))]
        block = newline + newline.join(indent + line for line in PATCH_LINES) + newline
        updated = "".join(lines[:end_line]) + block + "".join(lines[end_line:])
        operation = "AJOUT_FILTRAGE_VENDEUR"

    try:
        ast.parse(updated, filename=str(path))
    except SyntaxError as exc:
        raise PatchError(f"Le patch proposé ne passe pas l'analyse syntaxique : {exc}") from exc
    return updated, bom, operation, assignment.lineno, function.name


def write_patch(path: Path, updated: str, bom: bytes) -> Path:
    timestamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    backup = path.with_name(f"{path.name}.pre-bilan-vendeur-{timestamp}.bak")
    backup.write_bytes(path.read_bytes())
    fd, temporary_name = tempfile.mkstemp(prefix=".nexora-bilan-", suffix=".tmp", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(bom + updated.encode("utf-8"))
        os.replace(temporary, path)
    except Exception:
        try:
            temporary.unlink(missing_ok=True)
        except OSError:
            pass
        raise
    return backup


def main() -> int:
    default_root = Path(r"D:\NEXORA") if os.name == "nt" else Path.cwd()
    argv = sys.argv[1:]
    dry_run = bool(argv and argv[0] == "--dry-run")
    if dry_run:
        argv = argv[1:]
    root = Path(argv[0]).resolve() if argv else default_root.resolve()
    try:
        confirm_project(root)
        target = root / "apps" / "reports" / "views.py"
        updated, bom, operation, line, function = prepare_patch(target)
        print(f"CIBLE={target}")
        print(f"VUE={function}; LIGNE_QUERY={line}")
        print("RÈGLE=CASHIER forcé sur ses ventes; autres rôles filtrables par seller_id")
        print("PARAMÈTRE_HTTP=seller_id (query_params DRF ou GET Django)")
        print("SANS_PARAMÈTRE=rapport global conservé pour les rôles de gestion")
        print("AUCUNE_MIGRATION=oui; aucune vente existante réécrite")
        if operation == "DÉJÀ_APPLIQUÉ_V2":
            print(operation)
            return 0
        if dry_run:
            print(f"PATCH_PRÊT={operation}")
            print("TEST_SYNTAXE=PASS")
            return 0
        answer = input("Tapez OUI pour sauvegarder puis appliquer ce correctif : ").strip()
        if answer != "OUI":
            print("ANNULÉ — aucune modification.")
            return 2
        backup = write_patch(target, updated, bom)
        print(f"PATCH_APPLIQUÉ={operation}")
        print(f"SAUVEGARDE={backup}")
        print("TEST_SYNTAXE=PASS")
        return 0
    except (PatchError, OSError, SyntaxError) as exc:
        print(f"ERREUR_SANS_MODIFICATION={exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
