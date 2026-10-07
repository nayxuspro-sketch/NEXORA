#!/usr/bin/env python3
"""Patch ciblé du périmètre du bilan vendeur NEXORA.

Le rapport actuel agrège les ventes de l'entreprise. Cette correction limite
le queryset ``sales_qs`` d'un utilisateur CASHIER aux ventes dont ``seller`` est
cet utilisateur. Les rôles de direction/gestion conservent leur rapport global.
Le script ne touche ni à la base de données ni aux autres fichiers Python.
"""
from __future__ import annotations

import ast
import datetime as dt
import os
import sys
import tempfile
from pathlib import Path

MARKER = "# NEXORA_FIX_BILAN_VENDEUR_V1"
PATCH_LINES = (
    MARKER,
    "if getattr(request.user, 'role', None) == 'CASHIER':",
    "    sales_qs = sales_qs.filter(seller=request.user)",
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
    return (
        manager.attr == "objects"
        and isinstance(manager.value, ast.Name)
        and manager.value.id == "Sale"
    )


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
    owner_check = "obj.seller==user" in permission_compact
    if not cashier_check or not owner_check:
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
        if not isinstance(ancestor, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if "request" not in function_arguments(ancestor):
            continue
        candidates.append((ancestor, node))

    if len(candidates) != 1:
        raise PatchError(
            "Impossible d'identifier sans ambiguïté l'unique queryset sales_qs "
            "(Sale.objects.filter(company, status, created_at__gte) dans une vue "
            "recevant request). Aucune modification effectuée."
        )
    return candidates[0]


def function_already_scoped(function: ast.AST) -> bool:
    for node in ast.walk(function):
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
            continue
        if node.func.attr != "filter" or not isinstance(node.func.value, ast.Name):
            continue
        if node.func.value.id != "sales_qs":
            continue
        if any(keyword.arg == "seller" for keyword in node.keywords):
            return True
    return False


def patch_file(path: Path, *, dry_run: bool = False) -> tuple[str, Path | None]:
    text, bom = read_utf8(path)
    if MARKER in text:
        return "PATCH_DÉJÀ_PRÉSENT", None

    try:
        tree = ast.parse(text, filename=str(path))
    except SyntaxError as exc:
        raise PatchError(f"Le fichier cible contient déjà une erreur Python : {exc}") from exc

    function, assignment = locate_query(tree)
    if function_already_scoped(function):
        return "QUERYSET_DÉJÀ_FILTRÉ_PAR_SELLER", None

    lines = text.splitlines(keepends=True)
    end_line = getattr(assignment, "end_lineno", None)
    if end_line is None:
        raise PatchError("Cette version de Python ne fournit pas end_lineno; aucune modification.")
    newline = "\r\n" if "\r\n" in text else "\n"
    assignment_line = lines[assignment.lineno - 1]
    indent = assignment_line[: len(assignment_line) - len(assignment_line.lstrip(" \t"))]
    block = newline + newline.join(indent + item if i else indent + item for i, item in enumerate(PATCH_LINES)) + newline
    updated = "".join(lines[:end_line]) + block + "".join(lines[end_line:])

    try:
        ast.parse(updated, filename=str(path))
    except SyntaxError as exc:
        raise PatchError(f"Le patch proposé ne passe pas l'analyse syntaxique : {exc}") from exc

    if dry_run:
        return f"PATCH_PRÊT fonction={function.name} ligne={assignment.lineno}", None

    timestamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    backup = path.with_name(f"{path.name}.pre-bilan-vendeur-{timestamp}.bak")
    original = path.read_bytes()
    backup.write_bytes(original)

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
        # Le fichier source n'est remplacé qu'après validation et sauvegarde.
        raise

    return f"PATCH_APPLIQUÉ fonction={function.name} ligne={assignment.lineno}", backup


def main() -> int:
    if os.name == "nt":
        default_root = Path(r"D:\NEXORA")
    else:
        default_root = Path.cwd()

    if len(sys.argv) > 1 and sys.argv[1] == "--dry-run":
        dry_run = True
        args = sys.argv[2:]
    else:
        dry_run = False
        args = sys.argv[1:]

    root = Path(args[0]).resolve() if args else default_root.resolve()
    try:
        confirm_project(root)
        target = root / "apps" / "reports" / "views.py"
        # Prévalidation avant toute sauvegarde ou édition.
        source, _ = read_utf8(target)
        tree = ast.parse(source, filename=str(target))
        function, assignment = locate_query(tree)
        print(f"CIBLE={target}")
        print(f"VUE={function.name}; LIGNE_QUERY={assignment.lineno}")
        print("RÈGLE=les comptes CASHIER ne verront que les ventes seller=request.user")
        print("AUTRES_RÔLES=inchangés; rapport global conservé")
        print("BASE_DE_DONNÉES=aucune lecture/écriture; aucune migration")

        if not dry_run:
            answer = input("Tapez OUI pour sauvegarder puis appliquer ce patch : ").strip()
            if answer != "OUI":
                print("ANNULÉ — aucune modification.")
                return 2

        result, backup = patch_file(target, dry_run=dry_run)
        print(result)
        if backup:
            print(f"SAUVEGARDE={backup}")
        print("TEST_SYNTAXE=PASS")
        return 0
    except (PatchError, OSError, SyntaxError) as exc:
        print(f"ERREUR_SANS_MODIFICATION={exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
