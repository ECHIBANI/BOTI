# ============================================================
# semantic.py — Analyseur sémantique et interpréteur pour BOTI
# Responsabilité :
#   1. Vérifier la sémantique de l'AST (types, divisions par zéro, etc.)
#   2. Exécuter le programme instruction par instruction
#   3. S'arrêter précisément sur la ligne fautive (lignes 1→n-1 exécutées)
#   4. Interpoler les variables dans les chaînes : "val = {x}"
#
# Nouveautés v1.1 :
#   - Exécution ligne par ligne : si l'instruction n échoue, toutes les
#     instructions 1 → n-1 ont déjà été exécutées et leurs effets sont visibles.
#   - Interpolation de variables dans les chaînes de sortie :
#       "la valeur de a = {a}"  →  affiche  "la valeur de a = 42"
#     Si la variable n'existe pas encore, elle vaut 0 (règle BOTI).
#     Un nom entre accolades inconnu du lexer reste affiché tel quel.
# ============================================================

import re
from parser import ProgramNode, OperationNode, OutputNode


class SemanticError(Exception):
    """
    Erreur levée lors d'une violation sémantique (ex : division par zéro).
    Porte le numéro de ligne pour l'affichage précis dans main.py.
    """
    def __init__(self, message: str, line: int = 0):
        super().__init__(message)
        self.line = line   # Ligne où l'erreur s'est produite


class SymbolTable:
    """
    Table des symboles du programme BOTI.

    Toutes les variables sont initialisées à 0 automatiquement
    lors de leur première utilisation (déclaration implicite).
    """

    def __init__(self):
        # Dictionnaire interne : nom → valeur numérique
        self._symbols: dict[str, float] = {}

    def get(self, name: str) -> float:
        """
        Retourne la valeur de la variable.
        Si elle n'a jamais été utilisée, elle est créée à 0.
        """
        if name not in self._symbols:
            # Initialisation implicite à 0
            self._symbols[name] = 0
        return self._symbols[name]

    def set(self, name: str, value: float) -> None:
        """Enregistre ou met à jour la valeur d'une variable."""
        self._symbols[name] = value

    def exists(self, name: str) -> bool:
        """Vérifie si une variable a déjà été définie."""
        return name in self._symbols

    def dump(self) -> dict:
        """Retourne une copie de la table pour inspection / débogage."""
        return dict(self._symbols)

    def __repr__(self):
        entries = ', '.join(f"{k}={v}" for k, v in self._symbols.items())
        return f"SymbolTable({{{entries}}})"


# ── Pattern de détection des interpolations {nom_variable} ──
# Correspond à {identifiant} avec identifiant = lettre/underscore suivi de mots
_INTERP_PATTERN = re.compile(r'\{([a-zA-Z_]\w*)\}')


class Interpreter:
    """
    Interpréteur du langage BOTI.

    Parcourt l'AST nœud par nœud et :
      - exécute les opérations incrémentales sur les variables
      - affiche les chaînes de caractères (avec interpolation des {variables})
      - maintient la table des symboles à jour
      - s'arrête sur la ligne fautive après avoir exécuté toutes les lignes précédentes
    """

    def __init__(self):
        # Table des symboles partagée pour tout le programme
        self.symbols = SymbolTable()

    def execute(self, program: ProgramNode) -> None:
        """
        Point d'entrée de l'exécution.

        Exécute les instructions une par une dans l'ordre.
        Si l'instruction n échoue, les instructions 1 → n-1 ont déjà
        produit leurs effets (variables mises à jour, affichages faits).
        L'erreur est ensuite remontée avec son numéro de ligne.
        """
        for statement in program.statements:
            # Chaque instruction est exécutée indépendamment.
            # Une exception ici remonte directement vers main.py
            # qui affichera le message et le numéro de ligne.
            self._execute_statement(statement)

    def _execute_statement(self, node) -> None:
        """
        Dispatche l'exécution vers la méthode appropriée
        en fonction du type de nœud AST.
        """
        if isinstance(node, OperationNode):
            self._execute_operation(node)
        elif isinstance(node, OutputNode):
            self._execute_output(node)
        else:
            # Type de nœud inconnu (ne devrait pas arriver si le parser est correct)
            raise SemanticError(
                f"Nœud AST inconnu : {type(node).__name__}",
                line=0
            )

    def _execute_operation(self, node: OperationNode) -> None:
        """
        Exécute une opération incrémentale sur une variable.

        Vérifications sémantiques :
          - La valeur de l'opérande doit être numérique
          - La division par zéro est interdite

        En cas d'erreur, lève SemanticError avec node.line, ce qui permet
        à main.py de savoir exactement à quelle ligne l'erreur s'est produite.
        """
        # Validation : l'opérande doit être un nombre
        if not isinstance(node.operand, (int, float)):
            raise SemanticError(
                f"[Ligne {node.line}] L'opérande de '{node.variable}' "
                f"doit être numérique, reçu : {type(node.operand).__name__}",
                line=node.line
            )

        # Validation : division par zéro
        if node.operator == '/=' and node.operand == 0:
            raise SemanticError(
                f"[Ligne {node.line}] Division par zéro interdite "
                f"pour la variable '{node.variable}'",
                line=node.line
            )

        # Récupération de la valeur actuelle (initialisée à 0 si inconnue)
        current = self.symbols.get(node.variable)
        operand = node.operand

        # Application de l'opération
        if node.operator == '+=':
            result = current + operand
        elif node.operator == '-=':
            result = current - operand
        elif node.operator == '*=':
            result = current * operand
        elif node.operator == '/=':
            result = current / operand
        else:
            # Ne devrait jamais arriver (le parser valide les opérateurs)
            raise SemanticError(
                f"[Ligne {node.line}] Opérateur inconnu : '{node.operator}'",
                line=node.line
            )

        # Mise à jour de la table des symboles
        self.symbols.set(node.variable, result)

    def _execute_output(self, node: OutputNode) -> None:
        """
        Exécute une instruction d'affichage avec interpolation des variables.

        Syntaxe d'interpolation : {nom_variable} dans la chaîne.
        Exemple : "la valeur de a = {a}"  →  affiche  "la valeur de a = 42"

        Règles d'interpolation :
          - {var} est remplacé par la valeur numérique de var (0 si non définie)
          - La valeur est affichée comme entier si elle est entière (42 et non 42.0)
          - Si {xyz} n'est pas un identifiant valide, il reste tel quel dans la chaîne
        """
        # Validation : la valeur doit être une chaîne
        if not isinstance(node.value, str):
            raise SemanticError(
                f"[Ligne {node.line}] La valeur d'affichage doit être "
                f"une chaîne, reçu : {type(node.value).__name__}",
                line=node.line
            )

        # Interpolation des {variables} dans la chaîne
        texte_final = self._interpoler(node.value)
        print(texte_final)

    def _interpoler(self, texte: str) -> str:
        """
        Remplace toutes les occurrences de {nom_variable} dans le texte
        par la valeur actuelle de la variable correspondante.

        Exemples :
          "bonjour {prenom}"  →  "bonjour Alice"  (si prenom = "Alice")
          "x vaut {x}"        →  "x vaut 10"      (si x = 10)
          "ratio = {r}"       →  "ratio = 3.5"    (si r = 3.5)
          "pas de var ici"    →  "pas de var ici" (inchangé)

        Si la variable n'a jamais été assignée, elle vaut 0 (règle BOTI).
        """
        def remplacer(match):
            nom = match.group(1)   # Nom de la variable capturée entre {}
            valeur = self.symbols.get(nom)

            # Affichage propre : pas de ".0" pour les entiers
            if isinstance(valeur, float) and valeur == int(valeur):
                return str(int(valeur))
            return str(valeur)

        return _INTERP_PATTERN.sub(remplacer, texte)

    def get_variable(self, name: str) -> float:
        """Accès public à la valeur d'une variable (utile pour les tests)."""
        return self.symbols.get(name)

    def dump_symbols(self) -> dict:
        """Retourne l'état complet de la table des symboles."""
        return self.symbols.dump()
