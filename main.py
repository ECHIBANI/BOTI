# ============================================================
# main.py — Point d'entrée principal de l'interpréteur BOTI
# Responsabilité :
#   - Lire le code source (fichier ou saisie utilisateur)
#   - Orchestrer le pipeline : Lexer → Parser → Interpréteur
#   - Proposer un mode REPL interactif
#   - Afficher les erreurs avec : numéro de ligne, type, message
#
# Nouveautés v1.1 :
#   - Affichage d'erreur structuré : ligne | type | message
#   - Exécution partielle garantie : les lignes 1→n-1 sont toujours exécutées
#   - Interpolation de variables dans les chaînes : "val = {x}"
# ============================================================

import sys

from lexer    import Lexer,       LexerError
from parser   import Parser,      ParseError
from semantic import Interpreter, SemanticError


# ── Bannière ───────────────────────────────────────────────
BANNER = """
╔══════════════════════════════════════════╗
║   Interpréteur BOTI  —  v1.1             ║
║   Tapez 'quitter' ou 'exit' pour sortir  ║
║   Tapez 'vars' pour voir les variables   ║
║   Tapez 'aide' pour l'aide               ║
╚══════════════════════════════════════════╝
"""

AIDE = """
Syntaxe BOTI :
  x += 5               → ajoute 5 à x
  x -= 3               → soustrait 3 de x
  x *= 2               → multiplie x par 2
  x /= 4               → divise x par 4
  "texte"              → affiche le texte
  "val = {x}"          → affiche la valeur de x dans la chaîne
  ## commentaire ##    → ligne ignorée

Comportement des erreurs :
  Si l'erreur est à la ligne n :
    → les lignes 1 à n-1 sont exécutées normalement
    → l'exécution s'arrête à la ligne n
    → un message clair indique : ligne | type | cause

Commandes REPL :
  vars            → affiche les variables en mémoire
  aide            → affiche cette aide
  quitter / exit  → quitte le REPL
"""


# ══════════════════════════════════════════════════════════
# Affichage d'erreur structuré
# ══════════════════════════════════════════════════════════

# Correspondance type d'erreur → libellé lisible
_LABELS_ERREUR = {
    'LexerError'   : 'Erreur LEXICALE   ',
    'ParseError'   : 'Erreur SYNTAXIQUE ',
    'SemanticError': 'Erreur SÉMANTIQUE ',
}

def afficher_erreur(erreur: Exception, source_lines: list[str] = None) -> None:
    """
    Affiche un message d'erreur structuré et lisible.

    Format :
    ┌─────────────────────────────────────────────┐
    │ ❌  Erreur SÉMANTIQUE  —  Ligne 5            │
    │    Division par zéro pour la variable 'x'   │
    │    > x /= 0                                 │
    └─────────────────────────────────────────────┘

    Paramètres :
      erreur       : l'exception levée (LexerError, ParseError, SemanticError)
      source_lines : liste des lignes du code source (pour afficher la ligne fautive)
    """
    # Récupération du type et de la ligne
    type_nom   = type(erreur).__name__
    label      = _LABELS_ERREUR.get(type_nom, f'Erreur ({type_nom})')
    num_ligne  = getattr(erreur, 'line', 0)
    message    = str(erreur)

    # Nettoyage du message : on retire le préfixe "[Ligne N]" déjà dans le message
    # pour ne pas le doubler avec notre propre affichage structuré
    import re
    message_propre = re.sub(r'^\[Ligne \d+\]\s*', '', message)

    print()
    print(f"  ┌{'─' * 55}┐")

    # Ligne 1 : type + numéro de ligne
    if num_ligne:
        titre = f"  ❌  {label}  —  Ligne {num_ligne}"
    else:
        titre = f"  ❌  {label}"
    print(f"  │  {titre}")

    # Ligne 2 : message d'erreur
    print(f"  │     {message_propre}")

    # Ligne 3 (optionnelle) : contenu de la ligne fautive dans le source
    if source_lines and num_ligne and 1 <= num_ligne <= len(source_lines):
        ligne_code = source_lines[num_ligne - 1].strip()
        if ligne_code:
            print(f"  │     ▶  {ligne_code}")

    print(f"  └{'─' * 55}┘")
    print()


# ══════════════════════════════════════════════════════════
# Fonction principale du pipeline
# ══════════════════════════════════════════════════════════

def run(source_code: str, interpreter: Interpreter = None, verbose: bool = False) -> Interpreter:
    """
    Exécute un bloc de code BOTI complet.

    Pipeline :
      source_code  →  Lexer  →  tokens
      tokens       →  Parser →  AST
      AST          →  Interpreter : exécution ligne par ligne

    Comportement sur erreur :
      - Les lignes 1 → n-1 ont déjà été exécutées avant l'erreur.
      - L'erreur à la ligne n est affichée avec : numéro de ligne, type, message,
        et la ligne de code fautive extraite du source.

    Paramètres :
      source_code  : code source BOTI en texte brut
      interpreter  : instance existante (pour le REPL, afin de conserver l'état)
      verbose      : si True, affiche les tokens et l'AST pour le débogage

    Retourne l'interpréteur utilisé (permet d'enchaîner les appels).
    """
    if interpreter is None:
        interpreter = Interpreter()

    # Découpage en lignes pour l'affichage de la ligne fautive dans les erreurs
    source_lines = source_code.splitlines()

    try:
        # ── Étape 1 : Analyse lexicale ──────────────────
        lexer  = Lexer(source_code)
        tokens = lexer.tokenize()

        if verbose:
            print("\n── Tokens ──────────────────────────────────")
            for tok in tokens:
                print(f"  {tok}")

        # ── Étape 2 : Analyse syntaxique (construction AST) ─
        parser  = Parser(tokens)
        program = parser.parse()

        if verbose:
            print("\n── AST ──────────────────────────────────────")
            for node in program.statements:
                print(f"  {node}")
            print()

        # ── Étape 3 : Exécution instruction par instruction ──
        # L'interpréteur exécute les instructions dans l'ordre.
        # Si l'instruction n échoue, les instructions 1→n-1 ont déjà
        # produit leurs effets (variables mises à jour, affichages faits).
        interpreter.execute(program)

    except (LexerError, ParseError, SemanticError) as e:
        # Affichage structuré : ligne | type | message | code source
        afficher_erreur(e, source_lines)

    except Exception as e:
        # Erreur inattendue (bug dans l'interpréteur lui-même)
        print(f"\n  ❌  Erreur interne inattendue : {e}\n")

    return interpreter


# ══════════════════════════════════════════════════════════
# Mode REPL interactif
# ══════════════════════════════════════════════════════════

def repl():
    """
    Lance le REPL (Read–Eval–Print Loop) interactif.

    L'état des variables est conservé d'une saisie à l'autre.
    On peut saisir plusieurs lignes en terminant avec une ligne vide.
    """
    print(BANNER)

    # Un seul interpréteur partagé pour toute la session REPL
    interpreter = Interpreter()

    while True:
        try:
            # ── Lecture multiligne ──────────────────────
            first_line = input("BOTI › ").strip()

            # Commandes spéciales REPL
            if first_line.lower() in ('quitter', 'exit', 'q'):
                print("Au revoir !")
                break

            if first_line.lower() == 'vars':
                symboles = interpreter.dump_symbols()
                if symboles:
                    print("\n── Variables en mémoire ─────────────────────")
                    for nom, valeur in symboles.items():
                        val_str = int(valeur) if valeur == int(valeur) else valeur
                        print(f"  {nom} = {val_str}")
                    print()
                else:
                    print("  (aucune variable définie)\n")
                continue

            if first_line.lower() == 'aide':
                print(AIDE)
                continue

            if not first_line:
                continue

            # ── Accumulation des lignes suivantes ───────
            lignes = [first_line]
            while True:
                try:
                    suite = input("       … ").strip()
                    if suite == '':
                        break
                    lignes.append(suite)
                except EOFError:
                    break

            code = '\n'.join(lignes)

            # ── Exécution du bloc saisi ─────────────────
            interpreter = run(code, interpreter=interpreter)

        except KeyboardInterrupt:
            print("\n(interruption — tapez 'quitter' pour sortir)")
        except EOFError:
            print("\nAu revoir !")
            break


# ══════════════════════════════════════════════════════════
# Exemple d'utilisation intégré
# ══════════════════════════════════════════════════════════

EXEMPLE_BOTI = """
## Exemple complet du langage BOTI v1.1 ##

"=== Démonstration BOTI ==="

## Calcul de la somme 10 + 5 ##
somme += 10
somme += 5
"Résultat : somme = {somme}"

## Soustraction ##
resultat += 20
resultat -= 7
"Résultat : resultat = {resultat}"

## Multiplication ##
produit += 6
produit *= 7
"Résultat : produit = {produit}"

## Division ##
quotient += 100
quotient /= 4
"Résultat : quotient = {quotient}"

## Compteur avec plusieurs opérations ##
compteur += 1
compteur += 1
compteur += 1
compteur *= 10
"compteur après 3 incréments puis *10 = {compteur}"

## Interpolation multiple dans une seule chaîne ##
a += 3
b += 7
"a = {a}  |  b = {b}  |  (a et b sont indépendants)"

"=== Programme terminé ==="
"""

EXEMPLE_ERREUR_LIGNE = """
## Test : exécution partielle jusqu'à la ligne d'erreur ##
x += 10
x += 5
"x avant l'erreur = {x}"
x /= 0
"cette ligne ne sera jamais affichée"
"""


def lancer_exemple():
    """
    Exécute l'exemple intégré et affiche l'état final des variables.
    """
    print("═" * 54)
    print("  Exécution de l'exemple BOTI v1.1")
    print("═" * 54)

    interpreter = run(EXEMPLE_BOTI, verbose=False)

    print("── État final des variables ─────────────────────")
    for nom, valeur in interpreter.dump_symbols().items():
        val_str = int(valeur) if valeur == int(valeur) else valeur
        print(f"  {nom} = {val_str}")
    print()

    # Démonstration de l'arrêt à la ligne d'erreur
    print("═" * 54)
    print("  Démonstration : arrêt précis sur la ligne d'erreur")
    print("═" * 54)
    run(EXEMPLE_ERREUR_LIGNE)


# ══════════════════════════════════════════════════════════
# Point d'entrée
# ══════════════════════════════════════════════════════════

def main():
    """
    Gestion des modes de lancement :
      python main.py              → exemple + REPL interactif
      python main.py fichier.boti → exécute un fichier BOTI
      python main.py --repl       → REPL seul (sans exemple)
      python main.py --exemple    → exemple seul (sans REPL)
    """
    args = sys.argv[1:]

    if args and args[0] == '--repl':
        repl()

    elif args and args[0] == '--exemple':
        lancer_exemple()

    elif args and not args[0].startswith('--'):
        # Exécution d'un fichier BOTI
        chemin = args[0]
        try:
            with open(chemin, 'r', encoding='utf-8') as f:
                source = f.read()
            print(f"Exécution de : {chemin}\n" + "─" * 40)
            interpreter = run(source, verbose='--verbose' in args)
            if '--vars' in args:
                print("\n── Variables finales ────────────────────────")
                for nom, val in interpreter.dump_symbols().items():
                    val_str = int(val) if val == int(val) else val
                    print(f"  {nom} = {val_str}")
        except FileNotFoundError:
            print(f"❌ Fichier introuvable : {chemin}")
            sys.exit(1)

    else:
        # Mode par défaut : exemple puis REPL
        lancer_exemple()
        repl()


if __name__ == '__main__':
    main()
