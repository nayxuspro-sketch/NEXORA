# -*- coding: utf-8 -*-
"""NEXORA : pourquoi les ventes du jour n'apparaissaient pas (et la correction).

SYMPTOMES SIGNALES
  - l'ecran /sales/ affichait des donnees qui ne correspondaient pas aux ventes
    du jour (3 ventes fictives, dates du 29/09/2026) ;
  - les ventes encaissees au POS ne se retrouvaient pas dans la base.

CAUSE, ENTIEREMENT DANS LE FRONTEND (le serveur est juste) :

  1. lib/auth.tsx : sans session enregistree, l'application se CONNECTAIT
     ELLE-MEME en « mode demonstration » avec le jeton
     « demo_active_token_nexora ». Ce jeton n'est pas un JWT : apiRequest ne
     l'envoie donc jamais. Toutes les requetes partaient ANONYMES.
  2. app/login/page.tsx : si le backend ne repondait pas, le formulaire
     fabriquait un FAUX jeton JWT et un faux utilisateur, et annoncait une
     connexion reussie. Le faux jeton etant refuse par le serveur, chaque
     requete renvoyait une erreur.
  3. Depuis le correctif de securite P0, ces requetes anonymes ou a faux jeton
     sont REFUSEES (avant, elles passaient : c'etait la faille corrigee).
     Resultat : plus aucune donnee reelle n'arrivait dans les ecrans.
  4. Mais le frontend MASQUAIT ces erreurs :
       - 5 ecrans (dont /sales/) affichaient des donnees INVENTEES
         (placeholderData) a la place des vraies ;
       - la caisse fabriquait un FAUX TICKET quand l'enregistrement echouait
         (le recu s'affichait, le panier se vidait, rien n'arrivait en base).

CE QUE FAIT CE CORRECTEUR (dans VOS fichiers, avec sauvegardes) :

  - lib/auth.tsx : plus de session de demonstration. Un jeton valide (JWT) est
    exige, sinon la garde des routes conduit a la page de connexion.
  - app/login/page.tsx : plus de fausse connexion. Si le serveur ne repond pas,
    le message le dit clairement et rien n'est simule.
  - lib/api.ts : plus aucun enregistrement simule ; un 401/403 affiche
    « session refusee : reconnectez-vous » ; le backend est cherche sur le
    proxy, puis 8008, puis 8000 ; le message d'erreur dit que RIEN n'a ete
    enregistre.
  - app/pos/page.tsx : plus de ticket de secours. Si l'enregistrement echoue,
    l'utilisateur voit l'echec et le panier N'EST PAS vide.
  - app/sales/page.tsx : plus de ventes fictives, et un bandeau d'erreur
    honnete avec un bouton « Reessayer ».
  - reports / inventory / automation : les donnees inventees sont retirees de
    la meme facon.

Verification apres correction : aucun placeholderData, aucun jeton de
demonstration, aucun faux ticket, accents equilibres, et vos correctifs
anterieurs (bilan vendeur du POS, etc.) restent intacts.

Usage, dans le dossier du projet (celui qui contient manage.py) :

    py corriger_ventes_fantomes.py --verifier   # fait le point, ne modifie rien
    py corriger_ventes_fantomes.py              # corrige
    py corriger_ventes_fantomes.py --racine D:\\NEXORA
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

DOSSIER_SAUVEGARDE = 'sauvegardes-ventes-fantomes'
PREFIXE_FRONTEND = Path('frontend/src')

FICHIERS_ECRANS = [
    'app/sales/page.tsx',
    'app/pos/page.tsx',
    'app/reports/page.tsx',
    'app/inventory/page.tsx',
    'app/automation/page.tsx',
]

MARQUEURS_INTERDITS = [
    ('placeholderData', 'donnees inventees affichees a la place des vraies'),
    ('demo_active_token_nexora', 'jeton de demonstration jamais envoye au serveur'),
    ('DEFAULT_DEMO_USER', 'utilisateur de demonstration'),
    ('validJwtAdmin', 'faux jeton JWT du formulaire de connexion'),
    ('validJwtCashier', 'faux jeton JWT du formulaire de connexion'),
    ('handleQuickFill', 'remplissage des comptes de demonstration'),
    ('simulatedCreated', 'enregistrement simule quand le serveur ne repond pas'),
]

MARQUEURS_A_GARDER = [
    ('app/pos/page.tsx', 'export-seller-pdf', 'bilan vendeur du POS (correctif v3.1)'),
    ('app/sales/page.tsx', 'export-seller-pdf', 'bilan ventes de l ecran des ventes'),
]


# --------------------------------------------------------------- outils de code

def lire_fichier(chemin):
    """Lit un fichier en ramenant les fins de ligne a \n.

    Retourne (texte, retours_crlf, bom). Les fichiers d'un projet Windows sont
    souvent en CRLF : sans cette normalisation, aucune ancre ne correspondrait.
    """
    donnees = chemin.read_bytes()
    bom = donnees.startswith(b'\xef\xbb\xbf')
    texte = donnees.decode('utf-8-sig')
    n_crlf = texte.count('\r\n')
    n_lf = texte.count('\n') - n_crlf
    return texte.replace('\r\n', '\n'), n_crlf > n_lf, bom


def ecrire_fichier(chemin, texte, crlf=False, bom=False):
    """Reecrit le fichier en conservant ses fins de ligne et son BOM d'origine."""
    sortie = texte.replace('\n', '\r\n') if crlf else texte
    donnees = sortie.encode('utf-8')
    if bom:
        donnees = b'\xef\xbb\xbf' + donnees
    chemin.write_bytes(donnees)


def _debut_de_chaine(texte, i):
    """Vrai si le guillemet a la position i ouvre une chaine de code.

    En JSX, l'apostrophe du texte francais (n'a, l'Encaissement, d'un) ne doit
    pas etre prise pour un guillemet : sinon l'analyse avale tout le fichier.
    Regle : une apostrophe precedee d'une lettre ou d'un chiffre est du texte.
    """
    if i == 0:
        return True
    return not texte[i - 1].isalnum()


def _fin_bloc(texte, index_accolade):
    """Index de l'accolade fermante correspondante (chaines/commentaires ignores)."""
    profondeur = 0
    i = index_accolade
    n = len(texte)
    while i < n:
        c = texte[i]
        if c in '\'"`' and _debut_de_chaine(texte, i):
            quote = c
            i += 1
            while i < n:
                if texte[i] == '\\':
                    i += 2
                    continue
                if texte[i] == quote:
                    break
                i += 1
        elif c == '/' and i + 1 < n and texte[i + 1] == '/':
            while i < n and texte[i] != '\n':
                i += 1
            continue
        elif c == '/' and i + 1 < n and texte[i + 1] == '*':
            fin = texte.find('*/', i + 2)
            i = (fin + 2) if fin != -1 else n
            continue
        elif c == '{':
            profondeur += 1
        elif c == '}':
            profondeur -= 1
            if profondeur == 0:
                return i
        i += 1
    return -1


def supprimer_propriete(texte, nom):
    """Supprime les blocs `nom: { ... },` (chaines et commentaires respectes)."""
    supprimees = 0
    while True:
        marqueur = '%s:' % nom
        position = texte.find(marqueur)
        if position == -1:
            break
        accolade = texte.find('{', position + len(marqueur))
        if accolade == -1:
            break
        fin = _fin_bloc(texte, accolade)
        if fin == -1:
            break
        debut_ligne = texte.rfind('\n', 0, position) + 1
        apres = fin + 1
        while apres < len(texte) and texte[apres] in ' \t':
            apres += 1
        if apres < len(texte) and texte[apres] == ',':
            apres += 1
        while apres < len(texte) and texte[apres] in ' \t':
            apres += 1
        if apres < len(texte) and texte[apres] == '\n':
            apres += 1
        texte = texte[:debut_ligne] + texte[apres:]
        supprimees += 1
    return texte, supprimees


def equilibre(texte):
    """Equilibre de (), {} et [] hors chaines et commentaires."""
    piles = []
    paires = {')': '(', '}': '{', ']': '['}
    i, n = 0, len(texte)
    while i < n:
        c = texte[i]
        if c in '\'"`' and _debut_de_chaine(texte, i):
            quote = c
            i += 1
            while i < n:
                if texte[i] == '\\':
                    i += 2
                    continue
                if texte[i] == quote:
                    break
                i += 1
        elif c == '/' and i + 1 < n and texte[i + 1] == '/':
            while i < n and texte[i] != '\n':
                i += 1
            continue
        elif c == '/' and i + 1 < n and texte[i + 1] == '*':
            fin = texte.find('*/', i + 2)
            i = (fin + 2) if fin != -1 else n
            continue
        elif c in '({[':
            piles.append(c)
        elif c in ')}]':
            if not piles or piles[-1] != paires[c]:
                return False, 'fermeture inattendue « %s »' % c
            piles.pop()
        i += 1
    if piles:
        return False, 'ouverts non fermes : %s' % ''.join(piles)
    return True, 'equilibre'


def remplacer(texte, avant, apres):
    """Remplacement exact, une seule fois. Retourne (texte, fait)."""
    if texte.count(avant) == 1:
        return texte.replace(avant, apres, 1), True
    return texte, False


def remplacer_entre(texte, debut, fin, remplacement):
    """Remplace tout ce qui va du debut a la fin (incluses). Retourne (texte, fait)."""
    try:
        i = texte.index(debut)
        j = texte.index(fin, i) + len(fin)
    except ValueError:
        return texte, False
    return texte[:i] + remplacement + texte[j:], True


# ------------------------------------------------------------------- patchs

def corriger_ecrans(racine):
    """Retire les donnees inventees (placeholderData) de tous les ecrans."""
    rapport = []
    for relatif in FICHIERS_ECRANS:
        chemin = racine / PREFIXE_FRONTEND / relatif
        if not chemin.exists():
            rapport.append((relatif, 0, 'fichier absent'))
            continue
        texte, retours, bom = lire_fichier(chemin)
        if 'placeholderData' not in texte:
            rapport.append((relatif, 0, 'deja sans donnees inventees'))
            continue
        avant = texte
        texte, n = supprimer_propriete(texte, 'placeholderData')
        if n:
            ok, message = equilibre(texte)
            if not ok:
                rapport.append((relatif, 0, 'ANNULE : %s' % message))
                continue
            ecrire_fichier(chemin, texte, retours, bom)
        rapport.append((relatif, n, 'corrige' if n else 'deja sans donnees inventees'))
        del avant
    return rapport


def corriger_bandeau_ventes(racine):
    """Ajoute un bandeau d'erreur honnete (avec Reessayer) sur /sales/."""
    chemin = racine / PREFIXE_FRONTEND / 'app/sales/page.tsx'
    if not chemin.exists():
        return 'fichier absent', False
    texte, retours, bom = lire_fichier(chemin)
    if 'Aucune donnee' in texte and 'refetch' in texte:
        return 'bandeau deja present', False

    avant = """  const { data: salesData, isLoading } = useQuery<PaginatedResponse<Sale>>({"""
    apres = """  const { data: salesData, isLoading, isError, error, refetch } = useQuery<PaginatedResponse<Sale>>({"""
    texte, ok1 = remplacer(texte, avant, apres)

    avant2 = """        <DataTable
          columns={columns}
          data={salesData?.results || []}
          isLoading={isLoading}"""
    apres2 = """        {isError && (
          <div className="flex flex-col gap-2 rounded-lg border border-red-500/40 bg-red-500/10 p-4 text-sm text-red-200 sm:flex-row sm:items-center sm:justify-between">
            <span>
              Aucune donnee n'a ete chargee depuis le serveur :{' '}
              {(error as any)?.message || 'erreur inconnue'}. Les ventes ci-dessous ne
              sont PAS la liste officielle.
            </span>
            <button
              type="button"
              onClick={() => refetch()}
              className="rounded-md border border-red-400/60 px-3 py-1.5 text-xs font-semibold text-red-100 hover:bg-red-500/20"
            >
              Reessayer
            </button>
          </div>
        )}

        <DataTable
          columns={columns}
          data={salesData?.results || []}
          isLoading={isLoading}"""
    texte, ok2 = remplacer(texte, avant2, apres2)

    if ok1 and ok2:
        ok, message = equilibre(texte)
        if not ok:
            return 'ANNULE : %s' % message, False
        ecrire_fichier(chemin, texte, retours, bom)
        return 'bandeau d erreur ajoute', True
    return 'ancres introuvables (ok1=%s, ok2=%s)' % (ok1, ok2), False


def corriger_auth(racine):
    """lib/auth.tsx : plus de session de demonstration."""
    chemin = racine / PREFIXE_FRONTEND / 'lib/auth.tsx'
    if not chemin.exists():
        return 'fichier absent', False
    texte, retours, bom = lire_fichier(chemin)
    if 'DEFAULT_DEMO_USER' not in texte:
        return 'deja sans session de demonstration', False

    texte, ok1 = remplacer(texte, """// Utilisateur administrateur par defaut securise pre-connecte pour garantir l'immediatete d'usage
const DEFAULT_DEMO_USER: User = {""",
        """// NOTE : aucune session de demonstration. L'acces aux donnees exige un vrai
// jeton emis par le serveur (voir ci-dessous).
const _ANCIEN_UTILISATEUR_DE_DEMONSTRATION_RETIRE: User = {""")
    if not ok1:
        texte, ok1 = remplacer(texte, """// Utilisateur administrateur par défaut sécurisé pré-connecté pour garantir l'immédiateté d'usage
const DEFAULT_DEMO_USER: User = {""",
            """// NOTE : aucune session de demonstration. L'acces aux donnees exige un vrai
// jeton emis par le serveur (voir ci-dessous).
const _ANCIEN_UTILISATEUR_DE_DEMONSTRATION_RETIRE: User = {""")

    texte, ok2 = remplacer(texte,
        """  const [user, setUser] = useState<User | null>(DEFAULT_DEMO_USER);
  const [token, setToken] = useState<string | null>('demo_active_token_nexora');
  const [isLoading, setIsLoading] = useState(false);""",
        """  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);""")

    texte, ok3 = remplacer(texte,
        """    const activeUser =
      sessionStorage.getItem('nexora_session_user') ||
      sessionStorage.getItem('nexora_user') ||
      localStorage.getItem('nexora_session_user') ||
      localStorage.getItem('nexora_user');""",
        """    const activeUser =
      sessionStorage.getItem('nexora_session_user') ||
      sessionStorage.getItem('nexora_user') ||
      localStorage.getItem('nexora_session_user') ||
      localStorage.getItem('nexora_user');

    // Un jeton de demonstration ne vaut rien : le serveur le refuse.
    const jetonUtilisable = !!activeToken && activeToken.startsWith('eyJ');""")

    texte, ok4 = remplacer(texte,
        """    if (activeToken && activeUser) {""",
        """    if (jetonUtilisable && activeUser) {""")

    texte, ok5 = remplacer(texte,
        """    // Par défaut : initialiser la session prête à l'emploi avec l'utilisateur administrateur principal
    sessionStorage.setItem('nexora_session_token', 'demo_active_token_nexora');
    sessionStorage.setItem('nexora_session_user', JSON.stringify(DEFAULT_DEMO_USER));
    localStorage.setItem('nexora_session_token', 'demo_active_token_nexora');
    localStorage.setItem('nexora_session_user', JSON.stringify(DEFAULT_DEMO_USER));
    setToken('demo_active_token_nexora');
    setUser(DEFAULT_DEMO_USER);
    setIsLoading(false);""",
        """    // Aucune session utilisable : on ne simule rien. La garde des routes
    // conduit a la page de connexion, ou l'utilisateur s'authentifie vraiment.
    if (activeToken && !jetonUtilisable) {
      sessionStorage.removeItem('nexora_session_token');
      sessionStorage.removeItem('nexora_session_user');
      localStorage.removeItem('nexora_session_token');
      localStorage.removeItem('nexora_session_user');
    }
    setToken(null);
    setUser(null);
    setIsLoading(false);""")

    if not (ok1 and ok2 and ok3 and ok4 and ok5):
        return 'ancres introuvables (%s%s%s%s%s)' % (ok1, ok2, ok3, ok4, ok5), False
    ok, message = equilibre(texte)
    if not ok:
        return 'ANNULE : %s' % message, False
    ecrire_fichier(chemin, texte, retours, bom)
    return 'session de demonstration retiree', True


def corriger_login(racine):
    """app/login/page.tsx : plus de fausse connexion."""
    chemin = racine / PREFIXE_FRONTEND / 'app/login/page.tsx'
    if not chemin.exists():
        return 'fichier absent', False
    texte, retours, bom = lire_fichier(chemin)
    if 'validJwtAdmin' not in texte and 'handleQuickFill' not in texte:
        return 'deja sans fausse connexion', False

    ligne_trompeuse = (
        "      throw new Error('Identifiants incorrects. Cliquez sur le bouton "
        '\"Directeur\" ci-dessous pour vous connecter immédiatement.\');'
    )
    message_honnete = (
        "      throw new Error('Connexion impossible : identifiants refuses par le serveur, "
        "ou serveur de donnees injoignable. Aucune connexion n\\'a ete simulee. "
        "Verifiez que le backend est demarre (start-local.bat), puis reessayez.');"
    )

    # 1) retirer toute la branche « Mode Demo » (faux jetons JWT) jusqu'a la
    #    ligne trompeuse incluse, remplacee par un message honnete
    fait1 = False
    for commentaire in ('// 2. Mode Démo / Autonome Local garanti sans échec :',
                        '// 2. Mode Demo / Autonome Local garanti sans echec :',
                        '// 2. Mode Démo / Autonome Local garanti sans échec:',
                        '// 2. Mode Demo / Autonome Local garanti sans echec:'):
        # l'indentation de la ligne d'origine est conservee : la 1re ligne du
        # message ne doit donc pas etre indente (sinon 12 espaces au lieu de 6)
        texte, fait1 = remplacer_entre(texte, commentaire, ligne_trompeuse, message_honnete.lstrip(' '))
        if fait1:
            break

    # 2) supprimer le panneau des comptes de demonstration
    texte, fait2 = remplacer_entre(
        texte,
        '          {/* Quick Login Presets for easy demonstration */}',
        '</div>\n          </div>\n',
        '')
    # 3) supprimer le remplissage automatique des comptes demo
    texte, fait3 = remplacer_entre(
        texte,
        '  const handleQuickFill = (roleEmail: string, rolePass: string) => {',
        '  };\n\n  return (',
        '  return (')

    # 5) retirer les icones qui ne servaient qu'au panneau de demonstration
    texte, _ = remplacer(
        texte,
        "import { Lock, Mail, Store, ShieldCheck, ArrowRight, AlertCircle } from 'lucide-react';",
        "import { Lock, Mail, ArrowRight, AlertCircle } from 'lucide-react';")

    if not (fait1 and fait2 and fait3):
        return 'ancres introuvables (mode demo=%s, panneau=%s, remplissage=%s)' % (fait1, fait2, fait3), False
    # 4) nettoyage cosmetique : lignes ne contenant que des espaces
    texte = '\n'.join('' if ligne.strip() == '' else ligne for ligne in texte.split('\n'))
    ok, message = equilibre(texte)
    if not ok:
        return 'ANNULE : %s' % message, False
    ecrire_fichier(chemin, texte, retours, bom)
    return 'fausse connexion retiree', True


def corriger_api(racine):
    """lib/api.ts : plus d'enregistrement simule, message honnete, port 8000."""
    chemin = racine / PREFIXE_FRONTEND / 'lib/api.ts'
    if not chemin.exists():
        return 'fichier absent', False
    texte, retours, bom = lire_fichier(chemin)
    faits = []
    modifie = False

    # 1) retirer l'enregistrement simule en cas de panne du serveur
    if 'simulatedCreated' in texte:
        texte, fait = remplacer_entre(
            texte,
            "  // Si le backend Django n'est pas lancé localement, simuler la réussite de l'enregistrement en mémoire locale",
            "    } catch {}\n  }\n",
            "  // Aucun enregistrement simule : si le serveur ne repond pas, l'appel\n"
            "  // echoue. Une vente annoncee doit exister en base, sinon c'est un mensonge.\n")
        modifie = modifie or fait
        faits.append('enregistrement simule retire' if fait else 'ECHEC retrait simulation')

    # 2) chercher aussi le backend sur le port 8000 (documente dans BACKEND.md)
    ancien_cibles = """  const targets = [
    `/api/v1${cleanEndpoint}`,
    `http://127.0.0.1:8008/api/v1${cleanEndpoint}`
  ];"""
    nouvelles_cibles = """  const targets = [
    `/api/v1${cleanEndpoint}`,
    `http://127.0.0.1:8008/api/v1${cleanEndpoint}`,
    `http://127.0.0.1:8000/api/v1${cleanEndpoint}`
  ];"""
    texte, fait = remplacer(texte, ancien_cibles, nouvelles_cibles)
    modifie = modifie or fait
    faits.append('repli 8000 ajoute' if fait else 'cibles inchangees (deja a jour)')

    # 3) un refus d'authentification doit etre dit clairement (une seule fois)
    ancre_refus = """      if (!response.ok) {
        throw new ApiError("""
    bloc_refus = """      if (response.status === 401 || response.status === 403) {
        throw new ApiError(
          'Acces refuse par le serveur : session expiree ou droits insuffisants.'
          + ' Reconnectez-vous, puis reessayez. Rien n\\'a ete simule.',
          'session_refusee',
          data,
          response.status
        );
      }

      if (!response.ok) {
        throw new ApiError("""
    if 'session_refusee' in texte:
        faits.append('message de session deja clair')
    else:
        texte, fait = remplacer(texte, ancre_refus, bloc_refus)
        modifie = modifie or fait
        faits.append('message de session clair' if fait else 'refus deja clair')

    # 4) message final honnete : ce qui a ete essaye, et le fait que rien n'a ete enregistre
    nouveau_final = """  throw new ApiError(
    'Le serveur backend n\\'est pas joignable (essaye : proxy /api/v1, puis 127.0.0.1:8008, puis 127.0.0.1:8000). '
    + 'RIEN n\\'a ete enregistre : demarrez le backend avec start-local.bat, puis reessayez.',
    'backend_offline',
    null,
    503
  );"""
    if 'essaye : proxy /api/v1' in texte:
        faits.append('message final deja honnete')
    else:
        texte, fait = remplacer_entre(
            texte,
            "  throw new ApiError(\n    'Le serveur backend",
            "    503\n  );",
            nouveau_final)
        modifie = modifie or fait
        faits.append('message final honnete' if fait else 'ECHEC message final')

    if any(f.startswith('ECHEC') for f in faits):
        return ' ; '.join(faits), False
    ok, message = equilibre(texte)
    if not ok:
        return 'ANNULE : %s' % message, False
    ecrire_fichier(chemin, texte, retours, bom)
    return ' ; '.join(faits), modifie


def corriger_pos(racine):
    """app/pos/page.tsx : plus de faux ticket quand l'enregistrement echoue."""
    chemin = racine / PREFIXE_FRONTEND / 'app/pos/page.tsx'
    if not chemin.exists():
        return 'fichier absent', False
    texte, retours, bom = lire_fichier(chemin)
    if 'VNT-' not in texte:
        return 'deja sans ticket de secours', False
    ancien = """      try {
        return await apiRequest('/sales/', {
          method: 'POST',
          body: JSON.stringify(payload),
        });
      } catch {
        return {
          reference: `VNT-${Date.now().toString().slice(-6)}`,
          total_amount: totalTTC.toString(),
          subtotal_amount: discountedSubtotal.toString(),
          tax_amount: totalTVA.toString(),
          paid_amount: totalTTC.toString(),
          customer_name: selectedCustomer?.name || 'Client Comptoir',
          created_at: new Date().toISOString(),
        };
      }"""
    nouveau = """      // Une panne du serveur ne doit jamais fabriquer un faux ticket : le recu
      // ne s'affiche que pour une vente reellement enregistree en base.
      return await apiRequest('/sales/', {
        method: 'POST',
        body: JSON.stringify(payload),
      });"""
    texte, fait = remplacer(texte, ancien, nouveau)
    if not fait:
        return 'bloc introuvable : fichier non modifie', False
    ok, message = equilibre(texte)
    if not ok:
        return 'ANNULE : %s' % message, False
    ecrire_fichier(chemin, texte, retours, bom)
    return 'ticket de secours retire', True


def nettoyer_auth_residu(racine):
    """Retire l'ancien objet utilisateur de demonstration (devenu inutile)."""
    chemin = racine / PREFIXE_FRONTEND / 'lib/auth.tsx'
    if not chemin.exists():
        return 'fichier absent', False
    texte, retours, bom = lire_fichier(chemin)
    if '_ANCIEN_UTILISATEUR_DE_DEMONSTRATION_RETIRE' not in texte:
        return 'rien a nettoyer', False
    texte, fait = remplacer_entre(
        texte,
        'const _ANCIEN_UTILISATEUR_DE_DEMONSTRATION_RETIRE: User = {',
        '};\n',
        '')
    if not fait:
        return 'objet introuvable : fichier non modifie', False
    ok, message = equilibre(texte)
    if not ok:
        return 'ANNULE : %s' % message, False
    ecrire_fichier(chemin, texte, retours, bom)
    return 'ancien utilisateur de demonstration retire', True


# -------------------------------------------------------------- sauvegardes

FICHIERS_SURVEILLES = FICHIERS_ECRANS + ['lib/auth.tsx', 'app/login/page.tsx', 'lib/api.ts']


def sauvegarder(racine, relatif):
    """Copie le fichier d'origine dans le dossier de sauvegarde (une seule fois)."""
    chemin = racine / PREFIXE_FRONTEND / relatif
    if not chemin.exists():
        return
    cible = racine / DOSSIER_SAUVEGARDE / relatif
    if cible.exists():
        return
    cible.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(chemin, cible)


# -------------------------------------------------------------- verification

def verifier(racine):
    """Fait le point : rend la liste (etat, description)."""
    resultats = []

    def lire(relatif):
        chemin = racine / PREFIXE_FRONTEND / relatif
        if not chemin.exists():
            return None
        return chemin.read_text(encoding='utf-8')

    for relatif in FICHIERS_ECRANS:
        texte = lire(relatif)
        if texte is None:
            resultats.append(('ABSENT', relatif))
        elif 'placeholderData' in texte:
            resultats.append(('A FAIRE', '%s : donnees inventees encore presentes' % relatif))
        else:
            resultats.append(('OK', '%s : aucune donnee inventee' % relatif))

    texte = lire('app/sales/page.tsx')
    if texte is not None:
        if 'isError' in texte and 'refetch' in texte:
            resultats.append(('OK', 'app/sales/page.tsx : bandeau d erreur et bouton Reessayer presents'))
        else:
            resultats.append(('A FAIRE', 'app/sales/page.tsx : aucune alerte visible si le serveur echoue'))

    texte = lire('lib/auth.tsx')
    if texte is None:
        resultats.append(('ABSENT', 'lib/auth.tsx'))
    elif 'DEFAULT_DEMO_USER' in texte or 'demo_active_token_nexora' in texte:
        resultats.append(('A FAIRE', 'lib/auth.tsx : session de demonstration encore presente'))
    else:
        resultats.append(('OK', 'lib/auth.tsx : aucun jeton de demonstration'))

    texte = lire('app/login/page.tsx')
    if texte is None:
        resultats.append(('ABSENT', 'app/login/page.tsx'))
    elif 'validJwtAdmin' in texte or 'handleQuickFill' in texte:
        resultats.append(('A FAIRE', 'app/login/page.tsx : fausse connexion encore presente'))
    else:
        resultats.append(('OK', 'app/login/page.tsx : aucune fausse connexion'))

    texte = lire('lib/api.ts')
    if texte is None:
        resultats.append(('ABSENT', 'lib/api.ts'))
    else:
        if 'simulatedCreated' in texte:
            resultats.append(('A FAIRE', 'lib/api.ts : enregistrement simule encore present'))
        else:
            resultats.append(('OK', 'lib/api.ts : aucun enregistrement simule'))
        if '127.0.0.1:8000' in texte:
            resultats.append(('OK', 'lib/api.ts : le backend est aussi cherche sur le port 8000'))
        else:
            resultats.append(('INFO', 'lib/api.ts : repli 8000 absent (port documente dans BACKEND.md)'))

    texte = lire('app/pos/page.tsx')
    if texte is None:
        resultats.append(('ABSENT', 'app/pos/page.tsx'))
    else:
        if 'reference: `VNT-' in texte:
            resultats.append(('A FAIRE', 'app/pos/page.tsx : ticket de secours encore present'))
        else:
            resultats.append(('OK', 'app/pos/page.tsx : aucun ticket de secours'))
        if 'export-seller-pdf' in texte:
            resultats.append(('OK', 'app/pos/page.tsx : bilan vendeur (v3.1) intact'))
        else:
            resultats.append(('ATTENTION', 'app/pos/page.tsx : bilan vendeur introuvable'))

    # syntaxe : accolades, parentheses et crochets equilibres
    for relatif in FICHIERS_SURVEILLES:
        texte = lire(relatif)
        if texte is None:
            continue
        ok, message = equilibre(texte)
        resultats.append(('OK' if ok else 'A FAIRE', '%s : %s' % (relatif, message)))

    return resultats


def resume(racine):
    """Affiche le rapport de verification. Retourne le nombre de problemes."""
    resultats = verifier(racine)
    problemes = 0
    bloquants = 0
    print('')
    print('ETAT DU FRONTEND NEXORA')
    print('=' * 72)
    for etat, description in resultats:
        print('  [%s] %s' % (etat, description))
        if etat in ('A FAIRE', 'ABSENT'):
            problemes += 1
            if 'bilan vendeur introuvable' not in description:
                bloquants += 1
    print('=' * 72)
    return bloquants


# ------------------------------------------------------------------ principal

def _norme(fichier, resultat):
    """Uniformise (etat, fait) en (fichier, fait, etat)."""
    etat, fait = resultat
    return (fichier, fait, etat)


def main():
    analyseur = argparse.ArgumentParser(
        description='NEXORA : empeche les ventes fantomes (donnees inventees, faux tickets).')
    analyseur.add_argument('--racine', default='.',
                           help='dossier du projet (celui qui contient manage.py)')
    analyseur.add_argument('--verifier', action='store_true',
                           help='fait le point sans rien modifier')
    arguments = analyseur.parse_args()

    racine = Path(arguments.racine).expanduser().resolve()
    if not (racine / 'manage.py').exists() or not (racine / PREFIXE_FRONTEND).is_dir():
        print('Dossier invalide : %s' % racine)
        print('Indiquez la racine du projet (elle doit contenir manage.py et frontend/src).')
        print('Exemple : py %s --racine D:\\NEXORA' % Path(__file__).name)
        return 2

    print('NEXORA : ecran des ventes fiable (fin des ventes fantomes)')
    print('Racine : %s' % racine)
    print('')

    if arguments.verifier:
        problemes = resume(racine)
        if problemes:
            print('Des corrections restent a faire : relancez sans --verifier.')
            return 1
        print('Tout est coherent : les ecrans ne peuvent plus inventer de ventes.')
        return 0

    # sauvegarde des fichiers susceptibles d'etre modifies (originaux conserves)
    for relatif in FICHIERS_SURVEILLES:
        sauvegarder(racine, relatif)

    corrections = [
        ('Ventes fictives des ecrans', corriger_ecrans(racine)),
        ('Bandeau d erreur honnete (ventes)', [_norme('app/sales/page.tsx', corriger_bandeau_ventes(racine))]),
        ('Enregistrement simule (api.ts)', [_norme('lib/api.ts', corriger_api(racine))]),
        ('Faux ticket de la caisse', [_norme('app/pos/page.tsx', corriger_pos(racine))]),
        ('Session de demonstration (auth)', [_norme('lib/auth.tsx', corriger_auth(racine))]),
        ('Utilisateur de demonstration residuel', [_norme('lib/auth.tsx', nettoyer_auth_residu(racine))]),
        ('Fausse connexion (login)', [_norme('app/login/page.tsx', corriger_login(racine))]),
    ]

    print('CORRECTIONS APPLIQUEES')
    print('-' * 72)
    for titre, resultats in corrections:
        for fichier, fait, etat in resultats:
            if fait:
                symbole = 'CORRIGE'
            elif 'deja' in etat or 'rien a nettoyer' in etat:
                symbole = 'DEJA OK'
            else:
                symbole = 'ATTENTION'
            print('  [%-9s] %-22s %s' % (symbole, fichier, etat))

    print('')
    print('Originaux conserves dans : %s/' % DOSSIER_SAUVEGARDE)
    problemes = resume(racine)
    print('')
    if problemes:
        print('ATTENTION : %d point(s) a revoir (voir le tableau ci-dessus).' % problemes)
        return 1
    print('CORRECTION TERMINEE.')
    print('1. Relancez le frontend (npm run dev) et reconnectez-vous : la connexion')
    print('   doit etre REFUSEE si le backend n\'est pas demarre.')
    print('2. Enregistrez une vente : elle doit apparaitre aussitot dans /sales/.')
    print('3. Backend arrete : vous verrez une erreur claire, plus jamais de fausse vente.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
