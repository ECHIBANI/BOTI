# ============================================================
# lexer.py — Analyseur lexical pour le langage BOTI
# Responsabilité : transformer le code source en liste de tokens
#
# Nouveautés v1.1 :
#   - Le numéro de ligne est capturé AVANT la consommation du token
#     (le compteur de '\n' s'incrémente après), ce qui garantit que
#     chaque token porte le numéro de la ligne où il commence.
#   - Les chaînes de type "texte {var} suite" sont conservées brutes
#     (avec les accolades) afin que l'interpréteur puisse interpoler
#     les variables au moment de l'exécution.
# ============================================================

import re

# ── Types de tokens reconnus par le lexer ──────────────────
TOKEN_IDENTIFIER = 'IDENTIFIER'   # Nom de variable (ex: x, compteur)
TOKEN_NUMBER     = 'NUMBER'       # Valeur numérique (ex: 42, 3.14)
TOKEN_STRING     = 'STRING'       # Chaîne de caractères (ex: "Bonjour {x}")
TOKEN_OP_PLUS    = 'OP_PLUS'      # Opérateur +=
TOKEN_OP_MINUS   = 'OP_MINUS'     # Opérateur -=
TOKEN_OP_MUL     = 'OP_MUL'      # Opérateur *=
TOKEN_OP_DIV     = 'OP_DIV'       # Opérateur /=
TOKEN_COMMENT    = 'COMMENT'      # Commentaire ## ... ##
TOKEN_NEWLINE    = 'NEWLINE'      # Fin de ligne
TOKEN_EOF        = 'EOF'          # Fin du fichier


class Token:
    """Représente un token unique avec son type, sa valeur et son numéro de ligne."""

    def __init__(self, type_: str, value, line: int):
        self.type  = type_   # Type du token (ex: IDENTIFIER)
        self.value = value   # Valeur brute (ex: "x" ou 42)
        self.line  = line    # Numéro de ligne pour les messages d'erreur

    def __repr__(self):
        return f"Token({self.type}, {self.value!r}, ligne={self.line})"


class LexerError(Exception):
    """
    Erreur levée lorsque le lexer rencontre un caractère ou une syntaxe invalide.
    Porte le numéro de ligne pour un affichage d'erreur précis.
    """
    def __init__(self, message: str, line: int = 0):
        super().__init__(message)
        self.line = line   # Ligne où l'erreur a été détectée


class Lexer:
    """
    Analyseur lexical du langage BOTI.

    Parcourt le code source caractère par caractère et produit
    une liste de Token prêts à être consommés par le parser.

    Chaque Token mémorise son numéro de ligne de départ, ce qui
    permet à l'interpréteur d'exécuter les instructions ligne par
    ligne et de s'arrêter précisément sur la ligne fautive.
    """

    # Règles de tokenisation sous forme de (pattern, type_token)
    # L'ordre est important : les opérateurs composés avant les simples
    TOKEN_RULES = [
        (r'\+='            , TOKEN_OP_PLUS),
        (r'-='             , TOKEN_OP_MINUS),
        (r'\*='            , TOKEN_OP_MUL),
        (r'/='             , TOKEN_OP_DIV),
        (r'##.*?##'        , TOKEN_COMMENT),        # Commentaire ## ... ##
        (r'"[^"]*"'        , TOKEN_STRING),          # Chaîne entre guillemets (avec {vars})
        (r'[0-9]+\.?[0-9]*', TOKEN_NUMBER),          # Entier ou flottant
        (r'[a-zA-Z_]\w*'  , TOKEN_IDENTIFIER),       # Identifiant / variable
        (r'\n'             , TOKEN_NEWLINE),          # Saut de ligne
        (r'[ \t\r]+'       , None),                  # Espaces ignorés (None)
    ]

    # Compilation unique des patterns pour la performance
    _COMPILED_RULES = [
        (re.compile(pattern, re.DOTALL), token_type)
        for pattern, token_type in TOKEN_RULES
    ]

    def __init__(self, source_code: str):
        self.source = source_code   # Code source brut
        self.pos    = 0             # Position courante dans la chaîne
        self.line   = 1             # Numéro de ligne courant (commence à 1)

    def tokenize(self) -> list[Token]:
        """
        Parcourt tout le code source et retourne la liste complète des tokens.
        Les commentaires et les espaces sont ignorés.

        Garantie : chaque Token.line correspond à la ligne où commence le token
        dans le source original, ce qui permet à l'interpréteur de savoir
        exactement à quelle ligne correspond chaque instruction.
        """
        tokens = []

        while self.pos < len(self.source):
            # Capture du numéro de ligne AVANT de consommer le token
            line_avant = self.line
            match = self._next_match()

            if match is None:
                # Aucune règle ne correspond : caractère invalide
                bad_char = self.source[self.pos]
                raise LexerError(
                    f"[Ligne {self.line}] Caractère invalide : {bad_char!r}",
                    line=self.line
                )

            token_type, value, matched_text = match

            # Mise à jour du compteur de lignes (après consommation)
            self.line += matched_text.count('\n')

            if token_type is None:
                # Espace ou tabulation → ignoré
                pass
            elif token_type == TOKEN_COMMENT:
                # Commentaire → ignoré
                pass
            elif token_type == TOKEN_NEWLINE:
                # Saut de ligne → ignoré
                pass
            elif token_type == TOKEN_NUMBER:
                # Conversion de la valeur numérique (int ou float)
                num_val = float(value) if '.' in value else int(value)
                tokens.append(Token(TOKEN_NUMBER, num_val, line_avant))
            elif token_type == TOKEN_STRING:
                # On conserve le contenu brut (sans guillemets extérieurs).
                # Les {variables} seront interpolées à l'exécution par l'interpréteur.
                tokens.append(Token(TOKEN_STRING, value[1:-1], line_avant))
            else:
                tokens.append(Token(token_type, value, line_avant))

        # Ajout du token de fin de fichier
        tokens.append(Token(TOKEN_EOF, None, self.line))
        return tokens

    def _next_match(self):
        """
        Essaie chaque règle de tokenisation à la position courante.
        Retourne (token_type, value, matched_text) ou None si aucune règle ne correspond.
        """
        remaining = self.source[self.pos:]

        for pattern, token_type in self._COMPILED_RULES:
            m = pattern.match(remaining)
            if m:
                matched_text = m.group(0)
                self.pos += len(matched_text)   # Avancement du curseur
                return token_type, matched_text, matched_text

        return None  # Aucune règle ne correspond
