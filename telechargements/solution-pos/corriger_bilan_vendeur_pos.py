#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NEXORA — CORRECTIF v2 : bilan de vente par vendeur au POS

Pourquoi une version 2 ?
  Sur votre machine, apps\\sales\\pdf_seller_report.py n'était pas au chemin
  attendu et votre frontend\\src\\app\\pos\\page.tsx ne correspondait pas au
  fichier du dépôt (v1.3.9). La v1 ne modifie RIEN quand elle ne reconnaît pas
  un fichier : rien n'a été abîmé.

Ce que fait la v2 :
  1. AUTODÉTECTION : cherche les vrais fichiers partout sous la racine du
     projet (apps/sales/pdf_seller_report.py, src/app/pos/page.tsx), en
     ignorant node_modules, .git, venv, __pycache__, dist, build...
     Si le fichier n'est pas trouvé par son nom, il est aussi cherché par son
     CONTENU (mot-clé export-seller-pdf dans les .py).
  2. REPÈRES TOLÉRANTS : les insertions sont repérées par expressions
     régulières (espaces, retours à la ligne, commentaires variables), et non
     plus par des blocs au caractère près.
  3. Le correctif backend est posé juste AVANT la construction du PDF : le
     calcul du vendeur est donc toujours remplacé, quelle que soit la version
     de la vue.
  4. DIAGNOSTIC : écrit toujours DIAGNOSTIC-POS.txt (à côté de ce script) avec
     les chemins trouvés et les extraits de vos fichiers ; en cas d'échec,
     envoyez ce fichier tel quel : la correction sera adaptée à vos lignes.

Aucun fichier n'est modifié si un repère essentiel manque (arrêt par fichier).
Une sauvegarde est faite avant toute écriture.

Usage :
    py corriger_bilan_vendeur_pos.py --racine D:\\NEXORA
    py corriger_bilan_vendeur_pos.py --racine D:\\NEXORA --verifier
    py corriger_bilan_vendeur_pos.py --racine D:\\NEXORA --dry-run
    py corriger_bilan_vendeur_pos.py --racine D:\\NEXORA --diagnostic
"""

from __future__ import annotations

import argparse
import ast
import datetime
import hashlib
import os
import re
import shutil
import sys

# ------------------------------------------------------------------ constantes

DOSSIERS_IGNORES = {
    'node_modules', '.git', '.next', '.nuxt', 'dist', 'build', 'out', 'coverage',
    '__pycache__', '.venv', 'venv', 'env', 'ENV', '.mypy_cache', '.pytest_cache',
    '.turbo', '.idea', '.vscode', 'staticfiles', 'media',
}

# Préfixes de dossiers à ne jamais analyser : ce sont nos propres sauvegardes ou
# des copies du paquet de correctif, pas le code de l'application.
PREFIXES_IGNORES = ('sauvegardes-bilan-pos', 'correctif-bilan', 'nexora-correction')

SHA_BACKEND_ORIGINE = '7fb10a4f340a6c069e16f67265e30da99173647ce635be49ef25a1f23ca762eb'
SHA_POS_ORIGINE = '0467033fd972a8cde0cf35fd115b1d1b6c7e151caee659cf6f9dde632a3996d4'

# Noms volontairement préfixés : ils ne peuvent pas entrer en collision avec une
# correction déjà présente dans votre fichier (écrite par une autre session).
NOM_JSON_ERROR = '_nexora_json_error'
NOM_RESOLVE = '_nexora_resolve_seller'
NOM_VENTES = '_nexora_ventes_du_vendeur'
MARQUEUR_BACKEND = 'def %s(company, seller_param):' % NOM_RESOLVE
MARQUEUR_POS = 'pos-vendeurs-bilan'


# ------------------------------------------------------------------ utilitaires

def sha256(chemin):
    try:
        with open(chemin, 'rb') as fichier:
            return hashlib.sha256(fichier.read()).hexdigest()
    except OSError:
        return ''


def lire(chemin):
    with open(chemin, 'r', encoding='utf-8-sig', newline='') as fichier:
        brut = fichier.read()
    crlf = '\r\n' in brut
    return brut.replace('\r\n', '\n').replace('\r', '\n'), crlf


def ecrire(chemin, texte, crlf):
    sortie = texte.replace('\n', '\r\n') if crlf else texte
    with open(chemin, 'w', encoding='utf-8', newline='') as fichier:
        fichier.write(sortie)


def extraire(texte, motif, maximum=40):
    """Lignes contenant le motif (pour le diagnostic)."""
    lignes = []
    for numero, ligne in enumerate(texte.splitlines(), 1):
        if re.search(motif, ligne):
            lignes.append('%6d | %s' % (numero, ligne.rstrip()[:180]))
            if len(lignes) >= maximum:
                break
    return lignes


def parcourir(racine):
    for dossier, sous_dossiers, fichiers in os.walk(racine):
        sous_dossiers[:] = [d for d in sous_dossiers
                            if d not in DOSSIERS_IGNORES
                            and not d.lower().startswith(PREFIXES_IGNORES)]
        yield dossier, fichiers


def chercher_par_nom(racine, nom_fichier, motif_chemin=None, maximum=12):
    trouves = []
    for dossier, fichiers in parcourir(racine):
        if nom_fichier not in fichiers:
            continue
        chemin = os.path.join(dossier, nom_fichier)
        if motif_chemin and not re.search(motif_chemin, chemin.replace('\\', '/'), re.I):
            continue
        trouves.append(chemin)
        if len(trouves) >= maximum:
            break
    return trouves


def chercher_par_nom_approchant(racine, fragments=('seller', 'pdf'), extension='.py', maximum=12):
    """Fichiers .py dont le nom contient les fragments (ex. pdf_seller.py, seller_report.py)."""
    trouves = []
    for dossier, fichiers in parcourir(racine):
        for nom in fichiers:
            if not nom.lower().endswith(extension):
                continue
            minuscule = nom.lower()
            if all(fragment in minuscule for fragment in fragments):
                trouves.append(os.path.join(dossier, nom))
                if len(trouves) >= maximum:
                    return trouves
    return trouves


def chercher_par_contenu(racine, motifs, extension='.py', maximum=6, limite_octets=400000):
    trouves = []
    for dossier, fichiers in parcourir(racine):
        for nom in fichiers:
            if not nom.endswith(extension):
                continue
            chemin = os.path.join(dossier, nom)
            try:
                if os.path.getsize(chemin) > limite_octets:
                    continue
                with open(chemin, 'r', encoding='utf-8', errors='ignore') as fichier:
                    contenu = fichier.read()
            except OSError:
                continue
            if any(motif in contenu for motif in motifs):
                trouves.append(chemin)
                if len(trouves) >= maximum:
                    return trouves
    return trouves


def racine_projet(chemin, limite=8):
    """Dossier du projet qui contient ce fichier : le premier parent avec manage.py."""
    dossier = os.path.dirname(os.path.abspath(chemin))
    for _ in range(limite):
        if os.path.isfile(os.path.join(dossier, 'manage.py')):
            return dossier
        parent = os.path.dirname(dossier)
        if parent == dossier:
            break
        dossier = parent
    return None


def contient(chemin, motifs):
    try:
        with open(chemin, 'r', encoding='utf-8', errors='ignore') as fichier:
            contenu = fichier.read()
    except OSError:
        return {}
    return {motif: (motif in contenu) for motif in motifs}


def indices_de_vie(racine):
    """Éléments qui montrent que ce dossier est celui qui est réellement utilisé."""
    if not racine:
        return [],
    indices = []
    for relatif in ('frontend/node_modules', 'frontend/.next', 'frontend/package.json',
                    'manage.py', 'db.sqlite3'):
        if os.path.exists(os.path.join(racine, *relatif.split('/'))):
            indices.append(relatif)
    return indices


def choisir_paire(candidats_backend, candidats_pos):
    """Choisit le couple (backend, écran POS) du MÊME projet.

    Priorités : mêmes racines de projet ; le backend contient la vue
    SellerSalesReportPdfView ; l'écran POS contient le bilan vendeur
    (export-seller-pdf) ; chemins conformes à l'arborescence du dépôt ;
    projet « vivant » (node_modules, manage.py...).
    """
    meilleure = None
    details = []

    for backend in candidats_backend or [None]:
        for pos in candidats_pos or [None]:
            if backend is None and pos is None:
                continue

            points = 0
            raisons = []

            racine_backend = racine_projet(backend) if backend else None
            racine_pos = racine_projet(pos) if pos else None

            if backend and pos and racine_backend and racine_backend == racine_pos:
                points += 1000
                raisons.append('même dossier de projet')
            elif backend and pos and racine_backend and racine_pos:
                points -= 200
                raisons.append('deux dossiers de projet DIFFÉRENTS')

            if backend:
                marques = contient(backend, ['SellerSalesReportPdfView', 'sales_qs'])
                if marques.get('SellerSalesReportPdfView'):
                    points += 300
                    raisons.append('backend : vue du bilan vendeur présente')
                else:
                    points -= 300
                    raisons.append('backend : vue du bilan vendeur ABSENTE')
                if re.search(r'apps[/\\]sales[/\\]pdf_seller_report\.py$', backend, re.I):
                    points += 100
                    raisons.append('chemin conforme (apps/sales/pdf_seller_report.py)')
                if racine_backend:
                    points += 50

            if pos:
                marques = contient(pos, ['export-seller-pdf', 'sellerPdfPeriod'])
                if marques.get('export-seller-pdf'):
                    points += 300
                    raisons.append('écran POS : bouton/bilan vendeur présent')
                else:
                    points -= 300
                    raisons.append('écran POS : bilan vendeur ABSENT de ce fichier')
                if re.search(r'app[/\\]pos[/\\]page\.tsx$', pos, re.I):
                    points += 100
                    raisons.append('chemin conforme (app/pos/page.tsx)')
                if racine_pos:
                    points += 50
                if racine_pos and racine_pos == racine_backend:
                    for indice in indices_de_vie(racine_pos):
                        points += 10
                        raisons.append('indice de projet actif : %s' % indice)
                if pos and 'Downloads' in pos:
                    points -= 100
                    raisons.append('fichier situé dans Téléchargements')

            points -= (len(backend or '') + len(pos or '')) // 50
            details.append((points, backend, pos, raisons))
            if meilleure is None or points > meilleure[0]:
                meilleure = (points, backend, pos, raisons)

    if meilleure is None:
        return None, None, [], sorted(details, key=lambda d: -d[0])
    return meilleure[1], meilleure[2], meilleure[3], sorted(details, key=lambda d: -d[0])


def choisir_backend(candidats):
    if not candidats:
        return None

    def score(chemin):
        normalise = chemin.replace('\\', '/').lower()
        points = 0
        if 'apps/sales' in normalise:
            points += 100
        if normalise.endswith('apps/sales/pdf_seller_report.py'):
            points += 50
        if '/sales/' in normalise:
            points += 10
        return (-points, len(normalise))

    return sorted(candidats, key=score)[0]


def choisir_pos(candidats):
    if not candidats:
        return None

    def score(chemin):
        normalise = chemin.replace('\\', '/').lower()
        points = 0
        if normalise.endswith('app/pos/page.tsx'):
            points += 100
        if '/pos/page.tsx' in normalise:
            points += 50
        return (-points, len(normalise))

    return sorted(candidats, key=score)[0]


# -------------------------------------------------------------------- backend

HELPER_JSON_ERROR = '''def {nom_json}(message, statut=400):
    """Reponse JSON d'erreur (le renderer de cette vue est binaire : pas de Response DRF)."""
    return HttpResponse(
        json.dumps({{'detail': message}}, ensure_ascii=False),
        status=statut,
        content_type='application/json; charset=utf-8',
    )


'''

HELPER_RESOLVE = '''def {nom_resolve}(company, seller_param):
    """Retrouve le vendeur demande : identifiant (UUID), email, nom complet ou username.

    Resolution dans l'ordre : identifiant technique, email exact, nom
    d'utilisateur, nom complet, puis email partiel (refuse s'il est ambigu).

    Retourne (vendeur, message d'erreur) :
      - (vendeur, None)      : vendeur identifie ;
      - (None, None)         : aucun vendeur demande (comportement par defaut) ;
      - (None, 'message')    : vendeur demande mais introuvable. Le bilan ne doit
        JAMAIS etre produit silencieusement pour un autre vendeur.
    """
    if not seller_param:
        return None, None

    parametre = str(seller_param).strip()
    utilisateurs = User.objects.filter(company=company)

    # Le modele utilisateur du projet peut ne pas avoir de champ « username »
    # (dans NEXORA, la connexion se fait par email) : on teste sa presence.
    try:
        champs_modele = {{champ.name for champ in User._meta.get_fields()}}
    except Exception:
        champs_modele = {{'email', 'first_name', 'last_name', 'username'}}
    a_un_username = 'username' in champs_modele

    identifiant = None
    try:
        identifiant = uuid.UUID(parametre)
    except (ValueError, TypeError, AttributeError):
        identifiant = None

    if identifiant is not None:
        vendeur = utilisateurs.filter(id=identifiant).first()
        if vendeur:
            return vendeur, None

    vendeur = utilisateurs.filter(email__iexact=parametre).first()

    if vendeur is None and a_un_username:
        vendeur = utilisateurs.filter(username__iexact=parametre).first()

    if vendeur is None and ' ' in parametre:
        # Nom complet « Prenom Nom »
        prenom, nom = parametre.split(None, 1)
        vendeur = utilisateurs.filter(
            first_name__iexact=prenom, last_name__iexact=nom
        ).first()

    if vendeur is None:
        # Compatibilite : recherche partielle sur l'email, refusee si ambigue,
        # pour ne jamais produire le bilan d'un vendeur different de celui vise.
        candidats = list(utilisateurs.filter(email__icontains=parametre)[:2])
        if len(candidats) > 1:
            return None, (
                "Plusieurs vendeurs correspondent a « %s ». Choisissez le vendeur "
                "dans la liste pour eviter toute confusion." % parametre
            )
        vendeur = candidats[0] if candidats else None

    if vendeur is None and a_un_username:
        vendeur = utilisateurs.filter(username__icontains=parametre).first()

    if vendeur:
        return vendeur, None

    return None, (
        "Aucun vendeur de cette entreprise ne correspond a « %s ». "
        "Choisissez un compte vendeur valide." % parametre
    )


'''

HELPER_VENTES = '''def {nom_ventes}(company, seller_user, start_date, end_date):
    """Ventes reellement prises en compte dans le bilan d'un vendeur.

    Strictement limitees a ce vendeur ET aux ventes validees (statut COMPLETED),
    ce qui exclut les brouillons et les ventes annulees.
    """
    try:
        from apps.sales.models import SaleStatus
    except Exception:
        SaleStatus = None
    statut_valide = getattr(SaleStatus, 'COMPLETED', 'COMPLETED')
    return Sale.objects.filter(
        company=company,
        seller=seller_user,
        status=statut_valide,
        created_at__gte=start_date,
        created_at__lte=end_date,
    )


'''

HELPERS_BACKEND = (
    HELPER_JSON_ERROR.format(nom_json=NOM_JSON_ERROR)
    + HELPER_RESOLVE.format(nom_resolve=NOM_RESOLVE)
    + HELPER_VENTES.format(nom_ventes=NOM_VENTES)
)

BLOC_BACKEND = '''{ind}# ------------------------------------------------------------------
{ind}# CORRECTIF « bilan de vente par vendeur » (insertion automatique v2)
{ind}# Le vendeur est identifié STRICTEMENT ; s'il est introuvable le bilan n'est
{ind}# jamais produit pour un autre vendeur, et le résultat est TOUJOURS limité
{ind}# aux ventes validées (statut COMPLETED) de CE vendeur.
{ind}# ------------------------------------------------------------------
{ind}seller_param = (
{ind}    request.query_params.get('seller_id')
{ind}    or request.query_params.get('seller')
{ind}    or ''
{ind}).strip()

{ind}seller_user, erreur_vendeur = {nom_resolve}(company, seller_param)
{ind}if erreur_vendeur:
{ind}    return {nom_json}(erreur_vendeur, 404)

{ind}role_courant = getattr(request.user, 'role', None)
{ind}if role_courant == 'CASHIER' and getattr(request.user, 'is_authenticated', False):
{ind}    # Un caissier ne peut consulter que son propre bilan
{ind}    if seller_user is None or str(getattr(seller_user, 'id', '')) != str(request.user.id):
{ind}        seller_user = request.user

{ind}if not seller_user and getattr(request.user, 'is_authenticated', False):
{ind}    seller_user = request.user

{ind}if not seller_user:
{ind}    # Aucun vendeur précisé : premier vendeur ayant réellement des ventes
{ind}    premiere_vente = Sale.objects.filter(company=company).exclude(seller=None).first()
{ind}    if premiere_vente:
{ind}        seller_user = premiere_vente.seller
{ind}    else:
{ind}        seller_user = User.objects.filter(company=company).first()

{ind}if not seller_user:
{ind}    return {nom_json}("Aucun vendeur n'a pu être déterminé pour ce bilan.", 400)

{ind}# Le bilan est TOUJOURS strictement limité à ce vendeur
{ind}sales_qs = {nom_ventes}(company, seller_user, start_date, end_date)

'''

# Repères (du plus fiable au moins fiable) où insérer le bloc : juste avant la
# construction du rapport, donc après tout calcul antérieur du vendeur.
REPERES_BACKEND = [
    r'^[ \t]*sales\s*=\s*list\(\s*sales_qs\b',
    r'^[ \t]*sales\s*=\s*list\(\s*[^\n]*sales_qs',
    r'^[ \t]*[^\n]*=.*\bsales_qs\.prefetch_related\(',
    r'^[ \t]*[^\n]*\bsales_qs\.order_by\(',
    r'^[ \t]*[^\n]*\bin\s+sales_qs\b',
]


def patch_backend(texte, nom, journal, dry_run):
    modifie = False
    problemes = []

    # 1) imports json / uuid
    premier_import = re.search(r'^(?:import\s|from\s)', texte, re.M)
    if premier_import is None:
        problemes.append("aucune ligne d'import trouvée")
        return texte, modifie, problemes

    manquants = []
    if re.search(r'^\s*import json\b', texte, re.M) is None:
        manquants.append('import json\n')
    if re.search(r'^\s*import uuid\b', texte, re.M) is None:
        manquants.append('import uuid\n')
    if manquants:
        texte = texte[:premier_import.start()] + ''.join(manquants) + texte[premier_import.start():]
        modifie = True
        journal.append('imports json/uuid ajoutés')
    else:
        journal.append('imports json/uuid déjà présents')

    # 2) HttpResponse disponible ?
    if re.search(r'^\s*from django\.http import[^\n]*HttpResponse', texte, re.M) is None:
        if re.search(r'^\s*from django\.http import', texte, re.M):
            texte = re.sub(r'^([ \t]*from django\.http import[ \t]*)([^\n]*)$',
                           lambda m: m.group(1) + m.group(2).rstrip() + ', HttpResponse',
                           texte, count=1, flags=re.M)
        else:
            texte = texte[:premier_import.start()] + 'from django.http import HttpResponse\n' + texte[premier_import.start():]
        modifie = True
        journal.append('import HttpResponse ajouté')
    else:
        journal.append('import HttpResponse déjà présent')

    # 2bis) SaleStatus (statut « validée ») : ajouté à l'import du module si la ligne existe.
    import_sales = re.search(r'^[ \t]*from apps\.sales\.models import[ \t]*([^\n]*)$', texte, re.M)
    if import_sales is not None and 'SaleStatus' not in import_sales.group(1):
        texte = (texte[:import_sales.start(1)] + import_sales.group(1).rstrip() + ', SaleStatus'
                 + texte[import_sales.end(1):])
        modifie = True
        journal.append('import SaleStatus ajouté')
    elif import_sales is not None:
        journal.append('import SaleStatus déjà présent')

    # 3) helpers : insertion INDIVIDUELLE de ceux qui manquent. Les noms sont
    #    préfixés (_nexora_...) : une correction déjà présente dans le fichier ne
    #    peut donc pas empêcher l'insertion, ni provoquer de collision de nom.
    manquants = []
    if 'def %s(' % NOM_JSON_ERROR not in texte:
        manquants.append(HELPER_JSON_ERROR.format(nom_json=NOM_JSON_ERROR))
    if 'def %s(' % NOM_RESOLVE not in texte:
        manquants.append(HELPER_RESOLVE.format(nom_resolve=NOM_RESOLVE))
    if 'def %s(' % NOM_VENTES not in texte:
        manquants.append(HELPER_VENTES.format(nom_ventes=NOM_VENTES))

    if manquants:
        ancre_classe = re.search(r'^class\s+SellerSalesReportPdfView\b', texte, re.M)
        if ancre_classe is None:
            ancre_classe = re.search(r'^class\s+\w*(?:Seller|Sales)\w*(?:Report|Pdf|PDF)\w*\s*\(', texte, re.M)
        if ancre_classe is None:
            # À défaut de classe identifiable, on place les helpers après le dernier import
            dernier_import = None
            for correspondance in re.finditer(r'^(?:import\s|from\s)[^\n]*$', texte, re.M):
                dernier_import = correspondance
            if dernier_import is None:
                problemes.append('ni classe de vue ni import : fichier inattendu')
            else:
                texte = texte[:dernier_import.end() + 1] + '\n\n' + ''.join(manquants) + texte[dernier_import.end() + 1:]
                modifie = True
                journal.append('%d helper(s) inséré(s) après les imports' % len(manquants))
        else:
            texte = texte[:ancre_classe.start()] + ''.join(manquants) + texte[ancre_classe.start():]
            modifie = True
            journal.append('%d helper(s) inséré(s) avant la vue' % len(manquants))
    else:
        journal.append('helpers déjà présents')

    if problemes:
        return texte, modifie, problemes

    # 3bis) information : un correctif différent est peut-être déjà dans le fichier
    autres_correctifs = [nom for nom in ('resolve_seller', 'json_error', 'sales_queryset_for_seller',
                                        'seller_str', 'seller_filtered_qs')
                         if re.search(r'^[ \t]*(?:def\s+%s\b|%s\s*=)' % (re.escape(nom), re.escape(nom)), texte, re.M)]
    if autres_correctifs:
        journal.append('correctif déjà présent dans ce fichier (%s) : conservé, notre version prend le dessus'
                       % ', '.join(autres_correctifs))

    # 4) bloc de sélection stricte du vendeur, posé juste avant le rapport
    if 'erreur_vendeur = %s(' % NOM_RESOLVE in texte:
        journal.append('sélection stricte du vendeur déjà en place')
        return texte, modifie, problemes

    for motif in REPERES_BACKEND:
        correspondance = re.search(motif, texte, re.M)
        if correspondance is None:
            continue
        ligne = correspondance.group(0)
        indentation = re.match(r'[ \t]*', ligne).group(0)
        bloc = BLOC_BACKEND.format(ind=indentation, nom_json=NOM_JSON_ERROR,
                                   nom_resolve=NOM_RESOLVE, nom_ventes=NOM_VENTES)
        texte = texte[:correspondance.start()] + bloc + texte[correspondance.start():]
        modifie = True
        journal.append('sélection stricte du vendeur insérée avant « %s »' % ligne.strip()[:60])
        return texte, modifie, problemes

    problemes.append("point d'insertion du filtre vendeur introuvable "
                     "(aucun de : sales = list(sales_qs…, sales_qs.prefetch_related…)")
    return texte, modifie, problemes


# ------------------------------------------------------------------- frontend

BLOC_FRONT_AVEC_AUTH = '''
  // --- CORRECTIF v2 : liste des vendeurs du bilan (insertion automatique) ---
  const { data: utilisateursResponse } = useQuery<any>({
    queryKey: ['pos-vendeurs-bilan'],
    queryFn: () => apiRequest('/users/?page_size=200'),
    staleTime: 5 * 60 * 1000,
  });

  const vendeurs = React.useMemo(() => {
    const brut: any[] = Array.isArray(utilisateursResponse)
      ? utilisateursResponse
      : (utilisateursResponse?.results || []);
    // L'endpoint /users/ n'est pas filtré par entreprise : on ne garde que la nôtre
    const monEntreprise = (authUser as any)?.company_id || (authUser as any)?.company?.id || '';
    return brut
      .filter((u) => u && u.id && u.is_active !== false)
      .filter((u) => !monEntreprise || !u.company || u.company === monEntreprise)
      .map((u) => ({
        id: String(u.id),
        email: u.email || '',
        label: [u.first_name, u.last_name].filter(Boolean).join(' ').trim() || u.email || String(u.id),
        role: u.role || '',
      }));
  }, [utilisateursResponse, authUser]);

  // Par défaut : le vendeur connecté (identifiant technique = filtre fiable)
  React.useEffect(() => {
    if (authUser) {
      setSellerPdfPeriod((prev: any) => ({
        ...prev,
        seller_id: prev.seller_id || (authUser as any).id || '',
        seller_email: prev.seller_email || (authUser as any).email || '',
      }));
    }
  }, [authUser]);
'''

BLOC_FRONT_SANS_AUTH = '''
  // --- CORRECTIF v2 : liste des vendeurs du bilan (insertion automatique) ---
  const { data: utilisateursResponse } = useQuery<any>({
    queryKey: ['pos-vendeurs-bilan'],
    queryFn: () => apiRequest('/users/?page_size=200'),
    staleTime: 5 * 60 * 1000,
  });

  const vendeurs = React.useMemo(() => {
    const brut: any[] = Array.isArray(utilisateursResponse)
      ? utilisateursResponse
      : (utilisateursResponse?.results || []);
    return brut
      .filter((u) => u && u.id && u.is_active !== false)
      .map((u) => ({
        id: String(u.id),
        email: u.email || '',
        label: [u.first_name, u.last_name].filter(Boolean).join(' ').trim() || u.email || String(u.id),
        role: u.role || '',
      }));
  }, [utilisateursResponse]);
'''

SELECT_VENDEUR = '''{vendeurs.length > 0 ? (
              <select
                aria-label="Choisir le vendeur du bilan"
                value={sellerPdfPeriod.seller_id}
                onChange={(e) => {
                  const choisi = vendeurs.find((v) => v.id === e.target.value);
                  setSellerPdfPeriod({
                    ...sellerPdfPeriod,
                    seller_id: e.target.value,
                    seller_email: choisi?.email || '',
                  });
                }}
                className="w-full h-10 px-3 rounded-md border border-input bg-background text-sm font-semibold"
              >
                <option value="">— Choisir un vendeur —</option>
                {vendeurs.map((v) => (
                  <option key={v.id} value={v.id}>
                    {v.label}
                    {v.email && v.label !== v.email ? ` (${v.email})` : ''}
                  </option>
                ))}
              </select>
            ) : (
              <Input
                value={sellerPdfPeriod.seller_email}
                onChange={(e) => setSellerPdfPeriod({ ...sellerPdfPeriod, seller_email: e.target.value })}
                placeholder="Ex: caissier@nexora-bf.com"
              />
            )}'''


def patch_frontend(texte, journal, dry_run):
    modifie = False
    problemes = []

    # F1) seller_id dans l'état de la période du bilan
    etat = re.search(
        r'const\s*\[\s*sellerPdfPeriod\s*,\s*setSellerPdfPeriod\s*\]\s*=\s*React\.useState\(\s*\{(?P<corps>[^}]*)\}',
        texte, re.S)
    if etat is None:
        problemes.append("état sellerPdfPeriod introuvable (le modal du bilan a peut-être changé)")
    elif 'seller_id' in etat.group('corps'):
        journal.append('seller_id déjà dans l’état de la période')
    else:
        corps = etat.group('corps')
        ligne_email = re.search(r'^([ \t]*)seller_email\s*:', corps, re.M)
        indentation = ligne_email.group(1) if ligne_email else '    '
        insertion = '%sseller_id: \'\',\n%s' % (indentation, indentation)
        debut = etat.start('corps')
        texte = texte[:debut] + '\n' + insertion.rstrip('\n') + texte[debut:]
        modifie = True
        journal.append('seller_id ajouté à l’état de la période')

    # F2) requête des vendeurs + mémo (et présélection du vendeur connecté)
    if MARQUEUR_POS in texte:
        journal.append('liste des vendeurs déjà chargée')
    else:
        declaration = re.search(
            r'^[ \t]*const\s*\{[^}\n]*\bauthUser\b[^}\n]*\}\s*=\s*useAuth\(\s*\)\s*;', texte, re.M)
        if declaration is None:
            declaration = re.search(r'^[ \t]*(?:const|let|var)\s+[^\n=]*\bauthUser\b[^\n=]*=[^\n]*useAuth\([^\n]*\)\s*;?', texte, re.M)
        bloc = BLOC_FRONT_AVEC_AUTH if declaration else BLOC_FRONT_SANS_AUTH
        if declaration is not None:
            texte = texte[:declaration.end()] + '\n' + bloc + texte[declaration.end():]
            journal.append('liste des vendeurs chargée (après la définition de authUser)')
        elif etat is not None:
            fin_etat = texte.find(');', etat.end())
            if fin_etat == -1:
                fin_etat = etat.end()
            texte = texte[:fin_etat + 2] + '\n' + bloc.lstrip('\n') + texte[fin_etat + 2:]
            journal.append('liste des vendeurs chargée (sans authUser : introuvable)')
        else:
            problemes.append("point d'insertion de la liste des vendeurs introuvable")
        modifie = modifie or (declaration is not None or etat is not None)

    # F3) paramètres envoyés au serveur
    if re.search(r"seller_id['\"]?\s*[:,]", texte) and 'queryParams.set' in texte and 'seller_id' in texte.split('queryParams.set')[1][:200]:
        journal.append('paramètre seller_id déjà envoyé')
    else:
        remplacement_effectue = False

        # cas 1 : objet passé à URLSearchParams
        motif_objet = re.compile(
            r'\.\.\.\(\s*sellerPdfPeriod\.seller_email\s*\?\s*\{\s*seller:\s*sellerPdfPeriod\.seller_email\s*\}\s*:\s*\{\}\s*\),',
            re.S)
        if motif_objet.search(texte):
            texte = motif_objet.sub(
                "...(sellerPdfPeriod.seller_id\n"
                "          ? { seller_id: sellerPdfPeriod.seller_id }\n"
                "          : sellerPdfPeriod.seller_email\n"
                "            ? { seller: sellerPdfPeriod.seller_email }\n"
                "            : {}),", texte, count=1)
            remplacement_effectue = True
            journal.append('paramètre seller_id ajouté aux paramètres de l’export')

        # cas 2 : bloc URLSearchParams construit ligne par ligne
        if not remplacement_effectue:
            bloc_params = re.search(r'new URLSearchParams\(\{(?P<corps>[^}]*)\}', texte, re.S)
            if bloc_params is not None and 'seller_id' not in bloc_params.group('corps'):
                corps = bloc_params.group('corps')
                ligne_fin = re.search(r'^([ \t]*)end_date\s*:[^\n]*$', corps, re.M)
                if ligne_fin is not None:
                    indentation = ligne_fin.group(1)
                    ajout = ("\n%sseller_id: sellerPdfPeriod.seller_id || undefined,"
                             "\n%sseller: sellerPdfPeriod.seller_id ? undefined : sellerPdfPeriod.seller_email || undefined,"
                             % (indentation, indentation))
                    position = bloc_params.start('corps') + ligne_fin.end()
                    texte = texte[:position] + ajout + texte[position:]
                    remplacement_effectue = True
                    journal.append('paramètre seller_id ajouté au bloc URLSearchParams')

        # cas 3 : URL écrite à la main dans une chaîne de caractères
        if not remplacement_effectue:
            motif_url = re.compile(r'export-seller-pdf/\?[^`\'"]*')
            correspondance = motif_url.search(texte)
            if correspondance is not None:
                fragment = correspondance.group(0)
                if 'seller_id' not in fragment:
                    nouveau = fragment.replace('start_date=', 'seller_id=${sellerPdfPeriod.seller_id}&start_date=', 1)
                    texte = texte[:correspondance.start()] + nouveau + texte[correspondance.end():]
                    remplacement_effectue = True
                    journal.append('paramètre seller_id ajouté à l’URL d’export')

        if not remplacement_effectue:
            problemes.append("point d'insertion du paramètre seller_id introuvable")

    # F4) lien « Ouvrir dans un onglet »
    motif_lien = re.compile(
        r"\$\{\s*sellerPdfPeriod\.seller_email\s*\?\s*`&seller=\$\{encodeURIComponent\(sellerPdfPeriod\.seller_email\)\}`\s*:\s*''\s*\}")
    if 'seller_id=' in texte and re.search(r'encodeURIComponent\(sellerPdfPeriod\.seller_id\)', texte):
        journal.append('lien direct déjà corrigé')
    elif motif_lien.search(texte):
        texte = motif_lien.sub(
            "${sellerPdfPeriod.seller_id ? `&seller_id=${encodeURIComponent(sellerPdfPeriod.seller_id)}` "
            ": sellerPdfPeriod.seller_email ? `&seller=${encodeURIComponent(sellerPdfPeriod.seller_email)}` : ''}",
            texte, count=1)
        modifie = True
        journal.append('lien « Ouvrir dans un onglet » corrigé')
    else:
        journal.append('lien direct : aucun changement nécessaire (ou forme différente)')

    # F5) liste déroulante dans le modal (facultatif : le backend corrige déjà)
    if 'Choisir le vendeur du bilan' in texte:
        journal.append('liste déroulante déjà en place')
    else:
        motif_ui = re.compile(
            r'(<label[^>]*>\s*Compte Vendeur[^<]*</label>\s*)(<Input\b[\s\S]{0,400}?/>)')
        correspondance = motif_ui.search(texte)
        if correspondance is None:
            journal.append('liste déroulante : zone de saisie non reconnue (facultatif) — '
                           'le paramètre seller_id est bien envoyé, le backend applique le filtre')
        else:
            texte = (texte[:correspondance.start(2)] + SELECT_VENDEUR +
                     texte[correspondance.end(2):])
            modifie = True
            journal.append('liste déroulante des vendeurs insérée dans le modal')

        # texte d'aide
        texte, nombre = re.subn(
            r'Filtre automatique\s*:\s*seules les transactions encaissées par ce vendeur seront extraites\.',
            'Le bilan est strictement limité aux ventes validées encaissées par ce vendeur sur la période choisie.',
            texte, count=1)
        if nombre:
            modifie = True
            journal.append('texte d’aide mis à jour')

    return texte, modifie, problemes


# ------------------------------------------------------------------------ main

def diagnostiquer(dossier_script, backend, pos, journal_cherche, racine):
    lignes = []
    lignes.append('NEXORA — DIAGNOSTIC du bilan par vendeur au POS')
    lignes.append('Généré le %s' % datetime.datetime.now().strftime('%d/%m/%Y à %H:%M:%S'))
    lignes.append('Racine analysée : %s' % racine)
    lignes.append('')
    lignes.append('--- Recherche des fichiers ---')
    lignes.extend(journal_cherche)
    lignes.append('')
    for titre, chemin in (('BACKEND (vue PDF vendeur)', backend), ('FRONTEND (écran POS)', pos)):
        lignes.append('--- %s ---' % titre)
        if not chemin:
            lignes.append('  introuvable')
            lignes.append('')
            continue
        lignes.append('  chemin : %s' % chemin)
        lignes.append('  taille : %s octets' % os.path.getsize(chemin))
        lignes.append('  sha256 : %s' % sha256(chemin))
        texte, _ = lire(chemin)
        motif = (r'seller_param|sales_qs|SellerSalesReportPdfView|export-seller-pdf'
                 if titre.startswith('BACKEND') else r'seller|vendeur|Vendeur')
        lignes.append('  extraits :')
        extraits = extraire(texte, motif, maximum=60)
        lignes.extend(('    ' + ligne) if ligne else ligne for ligne in (extraits or ['    (aucun)']))
        lignes.append('')
    # Le diagnostic est ecrit a cote du .bat (dossier courant) ; a defaut, a cote du script
    for dossier in (os.getcwd(), dossier_script):
        chemin = os.path.join(dossier, 'DIAGNOSTIC-POS.txt')
        try:
            with open(chemin, 'w', encoding='utf-8') as fichier:
                fichier.write('\n'.join(lignes) + '\n')
            return chemin
        except OSError:
            continue
    return '(diagnostic non ecrit : dossier non accessible en ecriture)'


def main(argv=None):
    parseur = argparse.ArgumentParser(description="Correctif v2 du bilan de vente par vendeur au POS (NEXORA).")
    parseur.add_argument('--racine', default=None, help="Racine du projet (défaut : D:\\NEXORA si présent)")
    parseur.add_argument('--racines', default=None,
                         help="Plusieurs racines séparées par ; (ex. \"D:\\NEXORA;C:\\NEXORA\")")
    parseur.add_argument('--dry-run', action='store_true', help="Simule sans rien écrire")
    parseur.add_argument('--verifier', action='store_true', help="État seulement")
    parseur.add_argument('--diagnostic', action='store_true', help="Écrit le diagnostic même en cas de succès")
    options = parseur.parse_args(argv)

    dossier_script = os.path.dirname(os.path.abspath(__file__))

    racines = []
    if options.racines:
        racines = [os.path.abspath(r.strip()) for r in options.racines.split(';') if r.strip()]
    if options.racine:
        racines.insert(0, os.path.abspath(options.racine))
    if not racines:
        for candidat in ('D:\\NEXORA', 'C:\\NEXORA'):
            if os.path.isdir(candidat):
                racines.append(candidat)
    for nom in sorted(os.listdir(os.getcwd())) if os.path.isdir(os.getcwd()) else []:
        chemin = os.path.join(os.getcwd(), nom)
        if nom.upper().startswith('NEXORA') and os.path.isdir(chemin):
            racines.append(chemin)
    if not racines:
        racines = [os.getcwd()]
    racines = [r for r in dict.fromkeys(racines) if os.path.isdir(r)]
    if not racines:
        print('ERREUR : aucun dossier de projet utilisable.')
        return 2
    racine = racines[0]

    print('=' * 76)
    print('NEXORA — bilan de vente par vendeur (POS) : correctif v3 (autodétection)')
    print('=' * 76)
    print('Dossier(s) analysé(s) : %s' % ', '.join(racines))

    journal_cherche = []

    candidats_backend = []
    for racine_courante in racines:
        trouves = chercher_par_nom(racine_courante, 'pdf_seller_report.py')
        journal_cherche.append('%s : pdf_seller_report.py -> %d trouvé(s)' % (racine_courante, len(trouves)))
        candidats_backend.extend(trouves)
    if not candidats_backend:
        for racine_courante in racines:
            journal_cherche.append('  recherche par nom approchant (*seller*pdf*.py) dans %s…' % racine_courante)
            candidats_backend.extend(chercher_par_nom_approchant(racine_courante))
            if candidats_backend:
                break
    if not candidats_backend:
        for racine_courante in racines:
            journal_cherche.append('  recherche par contenu (export-seller-pdf, SellerSalesReportPdfView) dans %s…' % racine_courante)
            candidats_backend.extend(chercher_par_contenu(
                racine_courante, ['export-seller-pdf', 'SellerSalesReportPdfView', 'export_seller_pdf']))
            if candidats_backend:
                break
    for chemin in candidats_backend:
        journal_cherche.append('  %s' % chemin)

    candidats_pos = []
    for racine_courante in racines:
        trouves = chercher_par_nom(racine_courante, 'page.tsx', motif_chemin=r'/pos/')
        journal_cherche.append('%s : pos/page.tsx -> %d trouvé(s)' % (racine_courante, len(trouves)))
        candidats_pos.extend(trouves)
    for chemin in candidats_pos:
        journal_cherche.append('  %s' % chemin)

    backend, pos, raisons, classement = choisir_paire(candidats_backend, candidats_pos)
    journal_cherche.append('')
    journal_cherche.append('Choix retenu : backend=%s | ecran POS=%s' % (backend, pos))
    for ligne in raisons:
        journal_cherche.append('  - %s' % ligne)
    journal_cherche.append('Autres couples examines :')
    for points, b, p, r in classement[1:6]:
        journal_cherche.append('  %5d | %s | %s' % (points, b, p))

    print('  backend  : %s' % (backend or 'INTROUVABLE'))
    print('  écran POS : %s' % (pos or 'INTROUVABLE'))
    if backend:
        r = racine_projet(backend) or '(dossier du projet non identifié)'
        print('  dossier du projet : %s' % r)
        print('  indices            : %s' % (', '.join(indices_de_vie(r)) or 'aucun'))
    for ligne in raisons[:6]:
        print('    - %s' % ligne)
    print('-' * 76)

    etats = []

    # --- état / vérification
    if options.verifier:
        for nom, chemin, marqueur in (('backend', backend, MARQUEUR_BACKEND),
                                      ('frontend', pos, MARQUEUR_POS)):
            if not chemin:
                etats.append((nom, 'FICHIER INTROUVABLE', False))
                continue
            texte, _ = lire(chemin)
            if marqueur in texte:
                etats.append((nom, 'déjà corrigé', True))
            else:
                etats.append((nom, 'à corriger', True))
        for nom, etat, _ in etats:
            print('  %-10s %s' % (nom, etat))
        if options.diagnostic or not all(ok for _, _, ok in etats):
            print('  diagnostic : %s' % diagnostiquer(dossier_script, backend, pos, journal_cherche, racine))
        return 0

    # --- sauvegarde
    a_modifier = [c for c in (backend, pos) if c]
    if a_modifier and not options.dry_run:
        horodatage = datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
        dossiers_sauvegarde = []
        for chemin in a_modifier:
            # la sauvegarde va dans le dossier du PROJET auquel appartient le fichier
            projet = racine_projet(chemin) or racines[0]
            dossier = os.path.join(projet, 'sauvegardes-bilan-pos-%s' % horodatage)
            relatif = os.path.relpath(chemin, projet)
            cible = os.path.join(dossier, relatif)
            os.makedirs(os.path.dirname(cible), exist_ok=True)
            shutil.copy2(chemin, cible)
            if dossier not in dossiers_sauvegarde:
                dossiers_sauvegarde.append(dossier)
        for dossier in dossiers_sauvegarde:
            print('Sauvegarde : %s' % dossier)
        print('-' * 76)

    resultats = []
    deja_en_place = bool(backend) and all((
        MARQUEUR_BACKEND in lire(backend)[0],
        'def %s(' % NOM_JSON_ERROR in lire(backend)[0],
        'def %s(' % NOM_VENTES in lire(backend)[0],
        'erreur_vendeur = %s(' % NOM_RESOLVE in lire(backend)[0],
    )) if backend else False

    # --- backend
    if not backend:
        print('  backend  : FICHIER INTROUVABLE — recherche par contenu effectuée, rien trouvé.')
        resultats.append(False)
    else:
        texte, crlf = lire(backend)
        complet = (MARQUEUR_BACKEND in texte
                   and 'def %s(' % NOM_JSON_ERROR in texte
                   and 'def %s(' % NOM_VENTES in texte
                   and 'erreur_vendeur = %s(' % NOM_RESOLVE in texte)
        if complet:
            print('  backend  : déjà corrigé')
            resultats.append(True)
        else:
            journal_backend = []
            texte, modifie, problemes = patch_backend(texte, backend, journal_backend, options.dry_run)
            for ligne in journal_backend:
                print('    - %s' % ligne)
            if problemes:
                print('  backend  : NON CORRIGÉ — %s' % ' ; '.join(problemes))
                resultats.append(False)
            else:
                try:
                    ast.parse(texte)
                except SyntaxError as erreur:
                    print('  backend  : NON CORRIGÉ — résultat invalide (%s)' % erreur)
                    resultats.append(False)
                else:
                    if options.dry_run:
                        print('  backend  : simulation OK (aucune écriture)')
                    else:
                        ecrire(backend, texte, crlf)
                        print('  backend  : CORRIGÉ (%s)' % backend)
                    resultats.append(True)

    # --- frontend
    if not pos:
        print('  frontend : FICHIER INTROUVABLE')
        resultats.append(False)
    elif 'export-seller-pdf' not in lire(pos)[0] and 'sellerPdfPeriod' not in lire(pos)[0]:
        print('  frontend : CE FICHIER NE CONTIENT PAS LE BILAN VENDEUR — non modifié')
        print('             (%s)' % pos)
        print('             Le bouton « Mon Bilan Vente PDF » n’existe pas dans cet écran :')
        print('             c’est une version plus ancienne du POS. Indiquez le bon dossier,')
        print('             par exemple :  --racines "C:\\NEXORA"')
        resultats.append(None)
    else:
        texte, crlf = lire(pos)
        if MARQUEUR_POS in texte and 'seller_id' in texte:
            print('  frontend : déjà corrigé')
            resultats.append(True)
        else:
            journal = []
            texte_nouveau, modifie, problemes = patch_frontend(texte, journal, options.dry_run)
            for ligne in journal:
                print('    - %s' % ligne)
            if problemes:
                print('  frontend : NON CORRIGÉ — %s' % ' ; '.join(problemes))
                resultats.append(False)
            else:
                if options.dry_run:
                    print('  frontend : simulation OK (aucune écriture)')
                else:
                    ecrire(pos, texte_nouveau, crlf)
                    print('  frontend : CORRIGÉ (%s)' % pos)
                resultats.append(True)

    # --- diagnostic
    chemin_diagnostic = diagnostiquer(dossier_script, backend, pos, journal_cherche, racine)

    print('-' * 76)
    if all(resultats) and resultats:
        print('CORRECTIF EN PLACE.')
        projet = racine_projet(backend) or racine_projet(pos) or racines[0]
        print()
        if deja_en_place and not options.dry_run:
            print('(relance : le correctif était déjà en place, rien n’a été modifié)')
            print()
        print('Projet corrigé : %s' % projet)
        print()
        print('À faire ensuite :')
        print('  1. TESTER LE CORRECTIF : double-cliquez sur')
        print('       TESTER-BILAN-VENDEUR-POS.bat')
        print('     (fichier autonome : il écrit le test dans le projet puis lance')
        print('      manage.py test ; résultat attendu : OK, 14 tests)')
        print('     Équivalent en ligne de commande :')
        print('       cd /d "%s"' % projet)
        print('       py manage.py test tests.test_bilan_vendeur_pos -v 2')
        print('  2. Redémarrez le backend, puis le frontend (dossier frontend :')
        print('       npm run dev ).')
        print('  3. POS : bouton « Mon Bilan Vente PDF » -> le PDF ne contient que les')
        print('     ventes validées du vendeur choisi.')
    else:
        print('ARRÊT PARTIEL : certains éléments n’ont pas pu être corrigés automatiquement.')
        print('Aucun fichier pour lequel un repère manquait n’a été écrit.')
        if any(r is None for r in resultats):
            print()
            print('Un écran POS trouvé ne correspond pas à la version avec le bilan vendeur.')
            print('Si votre application est ailleurs, relancez avec le bon dossier, par exemple :')
            print('    --racines "C:\\NEXORA"   (ou D:\\NEXORA)')
    print()
    print('Diagnostic écrit : %s' % chemin_diagnostic)
    print('En cas d’échec, envoyez ce fichier DIAGNOSTIC-POS.txt : la correction sera')
    print('adaptée à vos lignes exactes.')
    return 0 if all(r in (True, None) for r in resultats) else 1


if __name__ == '__main__':
    sys.exit(main())
