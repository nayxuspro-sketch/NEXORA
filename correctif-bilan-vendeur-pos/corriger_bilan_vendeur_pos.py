#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NEXORA — CORRECTIF : bilan de vente par vendeur AU NIVEAU DU POS

Corrige les deux fichiers responsables du bouton « Mon Bilan Vente PDF » du POS
(export /api/v1/sales/export-seller-pdf/) :

 1. apps/sales/pdf_seller_report.py
    - identification STRICTE du vendeur (identifiant UUID, email ou nom
      d'utilisateur) : un vendeur demandé mais introuvable renvoie 404 au lieu
      de produire silencieusement le bilan d'un AUTRE vendeur (cause du bug) ;
    - le bilan est TOUJOURS limité à un seul vendeur : les ventes de tout le
      monde ne sont plus additionnées quand le vendeur n'est pas résolu ;
    - seules les ventes VALIDÉES (statut COMPLETED) sont comptabilisées ;
      brouillons et ventes annulées sont exclus ;
    - un compte de rôle CASHIER n'obtient que son propre bilan.

 2. frontend/src/app/pos/page.tsx
    - le champ « Compte Vendeur / Caissier » (saisie libre d'email, source
      d'erreurs) devient une LISTE DÉROULANTE des vendeurs de l'entreprise ;
    - le vendeur connecté est présélectionné ;
    - l'identifiant technique du vendeur (seller_id) est transmis au serveur,
      y compris sur le bouton « Ouvrir dans un onglet ».

Le script :
  * reconnaît vos fichiers (empreinte SHA-256) ou, à défaut, applique les
    insertions par repères vérifiés ;
  * sauvegarde les deux fichiers avant toute écriture ;
  * ne réécrit rien si le correctif est déjà présent (relançable) ;
  * s'arrête SANS RIEN ÉCRIRE si un repère manque, en indiquant les lignes.

Usage (PowerShell) :
    py corriger_bilan_vendeur_pos.py --racine D:\\NEXORA
    py corriger_bilan_vendeur_pos.py --racine D:\\NEXORA --verifier
    py corriger_bilan_vendeur_pos.py --racine D:\\NEXORA --dry-run
"""

from __future__ import annotations

import argparse
import ast
import datetime
import hashlib
import os
import shutil
import sys

CHEMIN_BACKEND = os.path.join('apps', 'sales', 'pdf_seller_report.py')
CHEMIN_POS = os.path.join('frontend', 'src', 'app', 'pos', 'page.tsx')

# Empreintes des fichiers d'origine (dépôt GitHub, tag v1.3.9)
SHA_BACKEND_ORIGINE = '7fb10a4f340a6c069e16f67265e30da99173647ce635be49ef25a1f23ca762eb'
SHA_POS_ORIGINE = '0467033fd972a8cde0cf35fd115b1d1b6c7e151caee659cf6f9dde632a3996d4'

# Marqueurs signalant que le correctif est déjà appliqué
MARQUEUR_BACKEND = 'def resolve_seller(company, seller_param):'
MARQUEUR_POS = 'pos-vendeurs-bilan'


class ErreurCorrectif(Exception):
    pass


def sha256(chemin):
    with open(chemin, 'rb') as f:
        return hashlib.sha256(f.read()).hexdigest()


def lire(chemin):
    with open(chemin, 'r', encoding='utf-8-sig', newline='') as f:
        brut = f.read()
    crlf = '\r\n' in brut
    return brut.replace('\r\n', '\n').replace('\r', '\n'), crlf


def ecrire(chemin, texte, crlf):
    sortie = texte.replace('\n', '\r\n') if crlf else texte
    with open(chemin, 'w', encoding='utf-8', newline='') as f:
        f.write(sortie)


def indentation_de(chemin, texte):
    """Retourne l'indentation majoritaire des lignes du fichier (pour les diagnostics)."""
    return texte


def reperes(texte, motif, maximum=5):
    lignes = []
    for numero, ligne in enumerate(texte.splitlines(), 1):
        if motif in ligne:
            lignes.append('%5d | %s' % (numero, ligne.rstrip()[:150]))
        if len(lignes) >= maximum:
            break
    return lignes


# --------------------------------------------------------------- backend ----

HELPERS_BACKEND = '''def json_error(message, statut=400):
    """Réponse JSON d'erreur (le renderer de cette vue est binaire, on ne passe pas par Response)."""
    return HttpResponse(
        json.dumps({'detail': message}, ensure_ascii=False),
        status=statut,
        content_type='application/json; charset=utf-8',
    )


def resolve_seller(company, seller_param):
    """Retrouve le vendeur demandé : identifiant (UUID), email, nom complet ou username.

    Résolution dans l'ordre : identifiant technique, email exact, nom d'utilisateur,
    nom complet, puis email partiel (refusé si plusieurs vendeurs correspondent).

    Retourne (vendeur, message d'erreur) :
      - (vendeur, None)      : vendeur identifié ;
      - (None, None)         : aucun vendeur demandé (comportement par défaut) ;
      - (None, 'message')    : vendeur demandé mais introuvable. Le bilan ne doit
        JAMAIS être produit silencieusement pour un autre vendeur.
    """
    if not seller_param:
        return None, None

    parametre = str(seller_param).strip()
    utilisateurs = User.objects.filter(company=company)

    # Le modèle utilisateur du projet peut ne pas avoir de champ « username »
    # (dans NEXORA, la connexion se fait par email) : on teste sa présence.
    champs_modele = {champ.name for champ in User._meta.get_fields()}
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
        # Nom complet « Prénom Nom »
        prenom, nom = parametre.split(None, 1)
        vendeur = utilisateurs.filter(
            first_name__iexact=prenom, last_name__iexact=nom
        ).first()

    if vendeur is None:
        # Compatibilité : recherche partielle sur l'email. Refusée si ambiguë,
        # pour ne jamais produire le bilan d'un vendeur différent de celui visé.
        candidats = list(utilisateurs.filter(email__icontains=parametre)[:2])
        if len(candidats) > 1:
            return None, (
                "Plusieurs vendeurs correspondent à « %s ». Choisissez le vendeur "
                "dans la liste pour éviter toute confusion." % parametre
            )
        vendeur = candidats[0] if candidats else None

    if vendeur is None and a_un_username:
        vendeur = utilisateurs.filter(username__icontains=parametre).first()

    if vendeur:
        return vendeur, None

    return None, (
        "Aucun vendeur de cette entreprise ne correspond à « %s ». "
        "Choisissez un compte vendeur valide." % parametre
    )


def sales_queryset_for_seller(company, seller_user, start_date, end_date):
    """Ventes réellement prises en compte dans le bilan d'un vendeur.

    Strictement limitées à ce vendeur ET aux ventes validées (statut COMPLETED),
    ce qui exclut les brouillons et les ventes annulées.
    """
    return Sale.objects.filter(
        company=company,
        seller=seller_user,
        status=SaleStatus.COMPLETED,
        created_at__gte=start_date,
        created_at__lte=end_date,
    )


'''

BLOC_BACKEND_ANCIEN = '''        # Identify target seller
        seller_user = None
        if seller_param:
            seller_user = User.objects.filter(company=company).filter(
                id=seller_param if len(seller_param) == 36 else None
            ).first() or User.objects.filter(company=company, email__icontains=seller_param).first()

        if not seller_user and request.user.is_authenticated:
            seller_user = request.user

        if not seller_user:
            # Fallback to cashier or first user with sales
            first_sale = Sale.objects.filter(company=company).exclude(seller=None).first()
            if first_sale:
                seller_user = first_sale.seller
            else:
                seller_user = User.objects.filter(company=company).first()

        # Filter sales strictly for THIS seller
        sales_qs = Sale.objects.filter(
            company=company,
            created_at__gte=start_date,
            created_at__lte=end_date
        )

        if seller_param and seller_user:
            sales_qs = sales_qs.filter(seller=seller_user)
'''

BLOC_BACKEND_NOUVEAU = '''        # ------------------------------------------------------------------
        # Identification STRICTE du vendeur (correctif « bilan par vendeur »)
        # ------------------------------------------------------------------
        seller_user, erreur_vendeur = resolve_seller(company, seller_param)
        if erreur_vendeur:
            return json_error(erreur_vendeur, 404)

        role_courant = getattr(request.user, 'role', None)
        if role_courant == 'CASHIER' and getattr(request.user, 'is_authenticated', False):
            # Un caissier ne peut consulter que son propre bilan
            if seller_user is None or str(seller_user.id) != str(request.user.id):
                seller_user = request.user

        if not seller_user and getattr(request.user, 'is_authenticated', False):
            seller_user = request.user

        if not seller_user:
            # Aucun vendeur précisé : premier vendeur ayant réellement des ventes
            premiere_vente = Sale.objects.filter(company=company).exclude(seller=None).first()
            if premiere_vente:
                seller_user = premiere_vente.seller
            else:
                seller_user = User.objects.filter(company=company).first()

        if not seller_user:
            return json_error("Aucun vendeur n'a pu être déterminé pour ce bilan.", 400)

        # Le bilan est TOUJOURS strictement limité à ce vendeur (et aux ventes validées)
        sales_qs = sales_queryset_for_seller(company, seller_user, start_date, end_date)
'''


def remplacements_backend():
    return [
        ("from apps.common.renderers import PassthroughBinaryRenderer\n",
         "import json\nimport uuid\n\nfrom apps.common.renderers import PassthroughBinaryRenderer\n",
         'imports json/uuid'),
        ("from apps.sales.models import Sale, SaleItem, Payment\n",
         "from apps.sales.models import Sale, SaleItem, Payment, SaleStatus\n",
         'import SaleStatus'),
        ("class SellerSalesReportPdfView(APIView):",
         HELPERS_BACKEND + "class SellerSalesReportPdfView(APIView):",
         'fonctions resolve_seller / sales_queryset_for_seller'),
        ("    - seller_id (optional, defaults to request.user if seller or first seller)\n",
         "    - seller_id (facultatif) : identifiant du vendeur ; le paramètre\n"
         "      « seller » est aussi accepté (UUID, email ou nom d'utilisateur).\n"
         "      Fourni mais introuvable => réponse 404, jamais le bilan d'un autre.\n"
         "    - Sans paramètre : bilan de l'utilisateur connecté, sinon du premier\n"
         "      vendeur ayant des ventes (comportement d'origine).\n"
         "    - Un compte de rôle CASHIER n'obtient que son propre bilan.\n"
         "    - Seules les ventes VALIDÉES (statut COMPLETED) sont comptabilisées.\n",
         'documentation de la vue'),
        ("        seller_param = request.query_params.get('seller_id') or request.query_params.get('seller')\n",
         "        seller_param = (\n"
         "            request.query_params.get('seller_id')\n"
         "            or request.query_params.get('seller')\n"
         "            or ''\n"
         "        ).strip()\n",
         'lecture du paramètre seller_id/seller'),
        (BLOC_BACKEND_ANCIEN, BLOC_BACKEND_NOUVEAU, 'bloc de sélection du vendeur'),
    ]


# -------------------------------------------------------------- frontend ----

def remplacements_pos():
    return [
        ("""  const [sellerPdfPeriod, setSellerPdfPeriod] = React.useState({
    start_date: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
    end_date: new Date().toISOString().split('T')[0],
    seller_email: '',
  });""",
         """  const [sellerPdfPeriod, setSellerPdfPeriod] = React.useState({
    start_date: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
    end_date: new Date().toISOString().split('T')[0],
    seller_id: '',
    seller_email: '',
  });""",
         'état du vendeur sélectionné'),

        ("""  // Set default seller email from current user
  React.useEffect(() => {
    if (authUser?.email) {
      setSellerPdfPeriod((prev) => ({ ...prev, seller_email: authUser.email }));
    }
  }, [authUser]);""",
         """  // Liste des vendeurs / caissiers de l'entreprise : alimente la liste déroulante du bilan
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

  // Par défaut : le vendeur connecté (son identifiant technique = filtre fiable côté serveur)
  React.useEffect(() => {
    if (authUser) {
      setSellerPdfPeriod((prev) => ({
        ...prev,
        seller_id: prev.seller_id || (authUser as any).id || '',
        seller_email: prev.seller_email || authUser.email || '',
      }));
    }
  }, [authUser]);""",
         'chargement de la liste des vendeurs'),

        ("""      const queryParams = new URLSearchParams({
        start_date: sellerPdfPeriod.start_date,
        end_date: sellerPdfPeriod.end_date,
        ...(sellerPdfPeriod.seller_email ? { seller: sellerPdfPeriod.seller_email } : {}),
      });""",
         """      const queryParams = new URLSearchParams({
        start_date: sellerPdfPeriod.start_date,
        end_date: sellerPdfPeriod.end_date,
      });
      if (sellerPdfPeriod.seller_id) {
        queryParams.set('seller_id', sellerPdfPeriod.seller_id);
      } else if (sellerPdfPeriod.seller_email) {
        queryParams.set('seller', sellerPdfPeriod.seller_email);
      }""",
         'paramètres envoyés au serveur'),

        ("              href={`/api/v1/sales/export-seller-pdf/?start_date=${sellerPdfPeriod.start_date}&end_date=${sellerPdfPeriod.end_date}${sellerPdfPeriod.seller_email ? `&seller=${encodeURIComponent(sellerPdfPeriod.seller_email)}` : ''}&_t=${Date.now()}`}",
         "              href={`/api/v1/sales/export-seller-pdf/?start_date=${sellerPdfPeriod.start_date}&end_date=${sellerPdfPeriod.end_date}${sellerPdfPeriod.seller_id ? `&seller_id=${encodeURIComponent(sellerPdfPeriod.seller_id)}` : sellerPdfPeriod.seller_email ? `&seller=${encodeURIComponent(sellerPdfPeriod.seller_email)}` : ''}&_t=${Date.now()}`}",
         'lien « Ouvrir dans un onglet »'),

        ("""          <div>
            <label className="text-xs font-semibold text-muted-foreground block mb-1">
              Compte Vendeur / Caissier
            </label>
            <Input
              value={sellerPdfPeriod.seller_email}
              onChange={(e) => setSellerPdfPeriod({ ...sellerPdfPeriod, seller_email: e.target.value })}
              placeholder="Ex: caissier@nexora-bf.com"
            />
            <p className="text-[10px] text-muted-foreground mt-1">
              Filtre automatique : seules les transactions encaissées par ce vendeur seront extraites.
            </p>
          </div>""",
         """          <div>
            <label className="text-xs font-semibold text-muted-foreground block mb-1">
              Compte Vendeur / Caissier
            </label>
            {vendeurs.length > 0 ? (
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
            )}
            <p className="text-[10px] text-muted-foreground mt-1">
              Le bilan est strictement limité aux ventes validées encaissées par ce vendeur sur la période choisie.
            </p>
          </div>""",
         'liste déroulante des vendeurs'),
    ]


# ------------------------------------------------------------------ moteur ----

def appliquer(chemin, remplacements, marqueur, sha_origine, nom, dry_run, journal):
    if not os.path.exists(chemin):
        journal.append((nom, 'FICHIER INTROUVABLE', False))
        return False, False

    texte, crlf = lire(chemin)
    empreinte = sha256(chemin)

    if marqueur in texte:
        journal.append((nom, 'déjà corrigé', True))
        return False, True

    identique_origine = (empreinte == sha_origine)
    manquants = [libelle for ancien, _, libelle in remplacements if ancien not in texte]

    if manquants:
        journal.append((nom, 'REPÈRES ABSENTS : ' + ', '.join(manquants), False))
        return False, False

    nouveau = texte
    for ancien, remplacement, _ in remplacements:
        nouveau = nouveau.replace(ancien, remplacement, 1)

    if nom.endswith('.py'):
        try:
            ast.parse(nouveau)
        except SyntaxError as exc:
            journal.append((nom, 'résultat invalide (%s) — rien écrit' % exc, False))
            return False, False

    if dry_run:
        journal.append((nom, 'simulation OK (%d insertions)' % len(remplacements), True))
        return False, identique_origine

    ecrire(chemin, nouveau, crlf)
    journal.append((nom, 'corrigé (%d insertions%s)' % (
        len(remplacements),
        ', fichier identique à la version d’origine' if identique_origine else ', fichier local adapté'), True))
    return True, True


def main(argv=None):
    parseur = argparse.ArgumentParser(description="Correctif du bilan de vente par vendeur au POS.")
    parseur.add_argument('--racine', default=None, help="Racine du projet (défaut : D:\\NEXORA si présent)")
    parseur.add_argument('--dry-run', action='store_true', help="Simule sans rien écrire")
    parseur.add_argument('--verifier', action='store_true', help="État seulement")
    options = parseur.parse_args(argv)

    if options.racine:
        racine = os.path.abspath(options.racine)
    elif os.path.isdir('D:\\NEXORA'):
        racine = 'D:\\NEXORA'
    else:
        racine = os.getcwd()

    print('=' * 76)
    print('NEXORA — bilan de vente par vendeur (POS) : correctif ciblé')
    print('=' * 76)
    print('Racine du projet : %s' % racine)
    if not os.path.isdir(racine):
        print("ERREUR : dossier inexistant.")
        return 2

    backend = os.path.join(racine, CHEMIN_BACKEND)
    page_pos = os.path.join(racine, CHEMIN_POS)
    for chemin, nom in ((backend, CHEMIN_BACKEND), (page_pos, CHEMIN_POS)):
        etat = 'présent' if os.path.exists(chemin) else 'ABSENT'
        print('  %-45s %s' % (nom, etat))
    print('-' * 76)

    if options.verifier:
        journal = []
        for chemin, remplacements, marqueur, sha_origine, nom in (
            (backend, remplacements_backend(), MARQUEUR_BACKEND, SHA_BACKEND_ORIGINE, CHEMIN_BACKEND),
            (page_pos, remplacements_pos(), MARQUEUR_POS, SHA_POS_ORIGINE, CHEMIN_POS),
        ):
            if not os.path.exists(chemin):
                journal.append((nom, 'FICHIER INTROUVABLE', False))
                continue
            texte, _ = lire(chemin)
            if marqueur in texte:
                journal.append((nom, 'déjà corrigé', True))
            else:
                manquants = [l for a, _, l in remplacements if a not in texte]
                journal.append((nom, ('à corriger — repères absents : ' + ', '.join(manquants)) if manquants else 'à corriger', not manquants))
        for nom, etat, ok in journal:
            print('  %-45s %s' % (nom, etat))
        return 0 if all(ok for _, _, ok in journal) else 1

    # sauvegarde
    if not options.dry_run:
        horodatage = datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
        dossier = os.path.join(racine, 'sauvegardes-bilan-pos-%s' % horodatage)
        copies = 0
        for chemin, rel in ((backend, CHEMIN_BACKEND), (page_pos, CHEMIN_POS)):
            if os.path.exists(chemin):
                cible = os.path.join(dossier, rel)
                os.makedirs(os.path.dirname(cible), exist_ok=True)
                shutil.copy2(chemin, cible)
                copies += 1
        print('Sauvegarde : %s (%d fichier(s))' % (dossier, copies))
        print('-' * 76)

    journal = []
    resultats = []
    for chemin, remplacements, marqueur, sha_origine, nom in (
        (backend, remplacements_backend(), MARQUEUR_BACKEND, SHA_BACKEND_ORIGINE, CHEMIN_BACKEND),
        (page_pos, remplacements_pos(), MARQUEUR_POS, SHA_POS_ORIGINE, CHEMIN_POS),
    ):
        modifie, ok = appliquer(chemin, remplacements, marqueur, sha_origine, nom, options.dry_run, journal)
        resultats.append(ok)

    for nom, etat, _ in journal:
        print('  %-45s %s' % (nom, etat))

    print('-' * 76)
    if not all(resultats):
        print('ARRÊT : un repère est introuvable (ou un fichier manque).')
        print('Aucun fichier n’a été modifié par cette exécution pour l’élément en échec.')
        for chemin, nom in ((backend, CHEMIN_BACKEND), (page_pos, CHEMIN_POS)):
            if os.path.exists(chemin):
                texte, _ = lire(chemin)
                for motif in ('class SellerSalesReportPdfView', 'seller_id', 'Compte Vendeur'):
                    reperes_trouves = reperes(texte, motif)
                    if reperes_trouves:
                        print('  repères dans %s (motif « %s ») :' % (nom, motif))
                        for ligne in reperes_trouves:
                            print('    ' + ligne)
        return 1

    if options.dry_run:
        print('Mode simulation : aucun fichier n’a été modifié.')
        return 0

    print('Correctif appliqué.')
    print('  Backend  : apps/sales/pdf_seller_report.py')
    print('  Frontend : frontend/src/app/pos/page.tsx')
    print()
    print('À faire ensuite :')
    print('  1. Redémarrez Django (le serveur recharge le fichier Python).')
    print('  2. Redémarrez le frontend : cd frontend  puis  npm run dev')
    print('  3. POS : bouton « Mon Bilan Vente PDF » -> la liste déroulante des')
    print('     vendeurs remplace la saisie libre de l’email. Choisissez un vendeur :')
    print('     le PDF ne doit contenir QUE ses ventes validées du POS.')
    print()
    print('Vérification automatique conseillée :')
    print('  py manage.py test tests.test_bilan_vendeur_pos -v 2')
    return 0


if __name__ == '__main__':
    sys.exit(main())
