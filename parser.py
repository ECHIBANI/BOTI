# ============================================================
# parser.py — Analyseur syntaxique pour le langage BOTI
# Responsabilité : construire l'AST (Arbre Syntaxique Abstrait)
#                  à partir de la liste de tokens produite par le lexer
# ============================================================

from lexer import (
    Token,
    TOKEN_IDENTIFIER, TOKEN_NUMBER, TOKEN_STRING,
    TOKEN_OP_PLUS, TOKEN_OP_MINUS, TOKEN_OP_MUL, TOKEN_OP_DIV,
    TOKEN_EOF
)


# ── Nœuds de l'AST ────────────────────────────────────────

class ASTNode:
    """Classe de base pour tous les nœuds de l'arbre syntaxique."""
    pass


class ProgramNode(ASTNode):
    """
    Nœud racine du programme.
    Contient la liste ordonnée de toutes les instructions.
    """
    def __init__(self, statements: list):
        self.statements = statements   # Liste de nœuds instruction

    def __repr__(self):
        return f"ProgramNode({self.statements})"


class OperationNode(ASTNode):
    """
    Nœud représentant une opération incrémentale.
    Exemples : x += 5  |  total -= 3  |  score *= 2  |  ratio /= 4
    """
    def __init__(self, variable: str, operator: str, operand, line: int):
        self.variable = variable   # Nom de la variable cible
        self.operator = operator   # Opérateur : '+=', '-=', '*=', '/='
        self.operand  = operand    # Valeur numérique de l'opération
        self.line     = line       # Numéro de ligne (pour les erreurs)

    def __repr__(self):
        return f"OperationNode({self.variable} {self.operator} {self.operand}, ligne={self.line})"


class OutputNode(ASTNode):
    """
    Nœud représentant une instruction d'affichage de chaîne.
    Exemple : "Bonjour le monde"
    """
    def __init__(self, value: str, line: int):
        self.value = value   # Texte à afficher (sans guillemets)
        self.line  = line    # Numéro de ligne (pour les erreurs)

    def __repr__(self):
        return f"OutputNode({self.value!r}, ligne={self.line})"


# ── Erreur syntaxique ──────────────────────────────────────

class ParseError(Exception):
    """
    Erreur levée lorsque le parser rencontre une construction syntaxique invalide.
    Porte le numéro de ligne pour permettre à l'interpréteur de s'arrêter
    exactement à la bonne ligne.
    """
    def __init__(self, message: str, line: int = 0):
        super().__init__(message)
        self.line = line   # Ligne où l'erreur syntaxique a été détectée


# ── Correspondance opérateur token → symbole ──────────────
OPERATOR_MAP = {
    TOKEN_OP_PLUS : '+=',
    TOKEN_OP_MINUS: '-=',
    TOKEN_OP_MUL  : '*=',
    TOKEN_OP_DIV  : '/=',
}


class Parser:
    """
    Analyseur syntaxique du langage BOTI.

    Consomme la liste de tokens et construit un AST en suivant la grammaire :

        programme     → instruction*
        instruction   → operation | affichage
        operation     → IDENTIFIER opérateur NUMBER
        affichage     → STRING
        opérateur     → '+=' | '-=' | '*=' | '/='
    """

    def __init__(self, tokens: list[Token]):
        self.tokens  = tokens   # Liste complète des tokens
        self.pos     = 0        # Index du token courant

    # ── Accesseurs internes ───────────────────────────────

    def _current(self) -> Token:
        """Retourne le token courant sans avancer."""
        return self.tokens[self.pos]

    def _advance(self) -> Token:
        """Retourne le token courant et avance d'une position."""
        token = self.tokens[self.pos]
        if self.pos < len(self.tokens) - 1:
            self.pos += 1
        return token

    def _expect(self, *expected_types: str) -> Token:
        """
        Vérifie que le token courant est d'un des types attendus,
        puis avance et retourne ce token.
        Lève ParseError si le type ne correspond pas.
        """
        token = self._current()
        if token.type not in expected_types:
            types_str = ' ou '.join(expected_types)
            raise ParseError(
                f"[Ligne {token.line}] Attendu {types_str}, "
                f"trouvé {token.type!r} ({token.value!r})",
                line=token.line
            )
        return self._advance()

    # ── Règles de grammaire ───────────────────────────────

    def parse(self) -> ProgramNode:
        """
        Point d'entrée du parser.
        Analyse l'ensemble du programme et retourne un ProgramNode.
        """
        statements = []

        while self._current().type != TOKEN_EOF:
            stmt = self._parse_statement()
            if stmt is not None:
                statements.append(stmt)

        return ProgramNode(statements)

    def _parse_statement(self) -> ASTNode:
        """
        Analyse une instruction unique.
        Détermine s'il s'agit d'une opération ou d'un affichage.
        """
        token = self._current()

        if token.type == TOKEN_IDENTIFIER:
            # Instruction de type opération : x += 5
            return self._parse_operation()

        elif token.type == TOKEN_STRING:
            # Instruction d'affichage : "texte"
            return self._parse_output()

        else:
            # Token inattendu en début d'instruction
            self._advance()  # Consommation pour éviter une boucle infinie
            raise ParseError(
                f"[Ligne {token.line}] Instruction invalide : "
                f"token {token.type!r} ({token.value!r}) inattendu",
                line=token.line
            )

    def _parse_operation(self) -> OperationNode:
        """
        Analyse une opération incrémentale.
        Format attendu : IDENTIFIER opérateur NUMBER
        """
        # 1. Lecture du nom de la variable
        id_token = self._expect(TOKEN_IDENTIFIER)

        # 2. Lecture de l'opérateur (+=, -=, *=, /=)
        op_token = self._expect(
            TOKEN_OP_PLUS, TOKEN_OP_MINUS, TOKEN_OP_MUL, TOKEN_OP_DIV
        )

        # 3. Lecture de la valeur numérique
        num_token = self._expect(TOKEN_NUMBER)

        # Conversion du type de token en symbole lisible
        operator = OPERATOR_MAP[op_token.type]

        return OperationNode(
            variable=id_token.value,
            operator=operator,
            operand=num_token.value,
            line=id_token.line
        )

    def _parse_output(self) -> OutputNode:
        """
        Analyse une instruction d'affichage.
        Format attendu : STRING
        """
        str_token = self._expect(TOKEN_STRING)
        return OutputNode(value=str_token.value, line=str_token.line)
