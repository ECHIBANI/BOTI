"""
Tests unitaires pour l'interpréteur BOTI.

Couvre les trois composants du pipeline :
  - Lexer   : tokenisation du code source
  - Parser  : construction de l'AST
  - Semantic: exécution et sémantique

Exécution :
  python -m pytest tests/
  # ou
  python tests/test_boti.py
"""

import sys
import os

# Ajout du répertoire parent au path pour les imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lexer import Lexer, LexerError, TOKEN_IDENTIFIER, TOKEN_NUMBER, TOKEN_STRING, TOKEN_OP_PLUS, TOKEN_OP_MINUS, TOKEN_OP_MUL, TOKEN_OP_DIV, TOKEN_EOF
from parser import Parser, ParseError
from semantic import Interpreter, SemanticError


# ══════════════════════════════════════════════════════════
# Tests du Lexer
# ══════════════════════════════════════════════════════════

class TestLexer:

    def _tokenize(self, source: str):
        return Lexer(source).tokenize()

    def test_simple_addition(self):
        tokens = self._tokenize("x += 5")
        assert tokens[0].type == TOKEN_IDENTIFIER
        assert tokens[0].value == "x"
        assert tokens[1].type == TOKEN_OP_PLUS
        assert tokens[2].type == TOKEN_NUMBER
        assert tokens[2].value == 5
        assert tokens[3].type == TOKEN_EOF

    def test_operators(self):
        ops = [("+=", TOKEN_OP_PLUS), ("-=", TOKEN_OP_MINUS),
               ("*=", TOKEN_OP_MUL), ("/=", TOKEN_OP_DIV)]
        for op_str, expected_type in ops:
            tokens = self._tokenize(f"x {op_str} 1")
            assert tokens[1].type == expected_type, f"Opérateur {op_str} non reconnu"

    def test_string_token(self):
        tokens = self._tokenize('"Bonjour le monde"')
        assert tokens[0].type == TOKEN_STRING
        assert tokens[0].value == "Bonjour le monde"  # Sans guillemets

    def test_string_with_interpolation(self):
        tokens = self._tokenize('"val = {x}"')
        assert tokens[0].type == TOKEN_STRING
        assert tokens[0].value == "val = {x}"

    def test_comment_ignored(self):
        tokens = self._tokenize("## ceci est un commentaire ##")
        assert len(tokens) == 1
        assert tokens[0].type == TOKEN_EOF

    def test_float_number(self):
        tokens = self._tokenize("x += 3.14")
        assert tokens[2].value == 3.14

    def test_integer_number(self):
        tokens = self._tokenize("x += 42")
        assert tokens[2].value == 42
        assert isinstance(tokens[2].value, int)

    def test_line_tracking(self):
        tokens = self._tokenize("x += 1\ny += 2")
        # x est ligne 1, y est ligne 1 (après le newline ignoré, le lexer compte correctement)
        assert tokens[0].line == 1   # x
        assert tokens[3].line == 2   # y

    def test_invalid_character_raises(self):
        try:
            Lexer("x @= 5").tokenize()
            assert False, "Aurait dû lever LexerError"
        except LexerError as e:
            assert e.line >= 1

    def test_multiline_program(self):
        source = "a += 1\nb += 2\nc += 3"
        tokens = self._tokenize(source)
        # 3 instructions × 3 tokens + EOF = 10 tokens
        assert tokens[-1].type == TOKEN_EOF


# ══════════════════════════════════════════════════════════
# Tests du Parser
# ══════════════════════════════════════════════════════════

class TestParser:

    def _parse(self, source: str):
        tokens = Lexer(source).tokenize()
        return Parser(tokens).parse()

    def test_parse_operation(self):
        from parser import OperationNode
        program = self._parse("x += 5")
        assert len(program.statements) == 1
        stmt = program.statements[0]
        assert isinstance(stmt, OperationNode)
        assert stmt.variable == "x"
        assert stmt.operator == "+="
        assert stmt.operand == 5

    def test_parse_all_operators(self):
        from parser import OperationNode
        sources = ["x += 1", "x -= 1", "x *= 1", "x /= 1"]
        ops = ["+=", "-=", "*=", "/="]
        for source, expected_op in zip(sources, ops):
            program = self._parse(source)
            assert program.statements[0].operator == expected_op

    def test_parse_output(self):
        from parser import OutputNode
        program = self._parse('"Bonjour"')
        assert len(program.statements) == 1
        stmt = program.statements[0]
        assert isinstance(stmt, OutputNode)
        assert stmt.value == "Bonjour"

    def test_parse_multiple_statements(self):
        program = self._parse("x += 1\ny += 2\n\"fin\"")
        assert len(program.statements) == 3

    def test_parse_error_missing_number(self):
        try:
            self._parse("x +=")
            assert False, "Aurait dû lever ParseError"
        except ParseError as e:
            assert e.line >= 1


# ══════════════════════════════════════════════════════════
# Tests de l'Interpréteur (sémantique)
# ══════════════════════════════════════════════════════════

def _run(source: str) -> Interpreter:
    """Helper : exécute du code BOTI et retourne l'interpréteur."""
    tokens = Lexer(source).tokenize()
    program = Parser(tokens).parse()
    interp = Interpreter()
    interp.execute(program)
    return interp


class TestInterpreter:

    def test_addition(self):
        interp = _run("x += 10")
        assert interp.get_variable("x") == 10

    def test_addition_accumulation(self):
        interp = _run("x += 10\nx += 5")
        assert interp.get_variable("x") == 15

    def test_subtraction(self):
        interp = _run("x += 20\nx -= 7")
        assert interp.get_variable("x") == 13

    def test_multiplication(self):
        interp = _run("x += 6\nx *= 7")
        assert interp.get_variable("x") == 42

    def test_division(self):
        interp = _run("x += 100\nx /= 4")
        assert interp.get_variable("x") == 25

    def test_implicit_init_at_zero(self):
        """Une variable non initialisée vaut 0."""
        interp = _run("x += 5")
        assert interp.get_variable("x") == 5
        # y n'a jamais été utilisé, mais get_variable l'initialise à 0
        assert interp.get_variable("y") == 0

    def test_division_by_zero_raises(self):
        try:
            _run("x += 10\nx /= 0")
            assert False, "Aurait dû lever SemanticError"
        except SemanticError as e:
            assert e.line >= 1
            assert "zéro" in str(e).lower() or "zero" in str(e).lower()

    def test_multiple_variables(self):
        interp = _run("a += 3\nb += 7\nc += 2")
        assert interp.get_variable("a") == 3
        assert interp.get_variable("b") == 7
        assert interp.get_variable("c") == 2

    def test_dump_symbols(self):
        interp = _run("x += 1\ny += 2")
        symbols = interp.dump_symbols()
        assert "x" in symbols
        assert "y" in symbols
        assert symbols["x"] == 1
        assert symbols["y"] == 2

    def test_float_result(self):
        interp = _run("x += 10\nx /= 3")
        result = interp.get_variable("x")
        assert abs(result - 10/3) < 1e-9

    def test_interpolation_in_output(self, capsys=None):
        """Test indirect : vérifie que l'interpolation ne lève pas d'exception."""
        _run('x += 42\n"valeur = {x}"')  # Ne doit pas lever d'exception

    def test_partial_execution_before_error(self):
        """Les instructions avant l'erreur doivent avoir été exécutées."""
        try:
            tokens = Lexer("x += 10\nx += 5\nx /= 0").tokenize()
            program = Parser(tokens).parse()
            interp = Interpreter()
            interp.execute(program)
        except SemanticError:
            # x doit valoir 15 (les deux premières lignes ont été exécutées)
            assert interp.get_variable("x") == 15


# ══════════════════════════════════════════════════════════
# Runner simple (sans pytest)
# ══════════════════════════════════════════════════════════

def run_tests_simple():
    """Exécute tous les tests sans dépendance pytest."""
    import traceback

    test_classes = [TestLexer, TestParser, TestInterpreter]
    total = passed = failed = 0

    print("=" * 55)
    print("  Tests BOTI")
    print("=" * 55)

    for cls in test_classes:
        print(f"\n[{cls.__name__}]")
        instance = cls()
        for name in dir(cls):
            if not name.startswith("test_"):
                continue
            total += 1
            method = getattr(instance, name)
            try:
                method()
                print(f"  OK  {name}")
                passed += 1
            except Exception as exc:
                print(f"  FAIL {name}")
                print(f"     {type(exc).__name__}: {exc}")
                failed += 1

    print("\n" + "=" * 55)
    print(f"  Résultat : {passed}/{total} réussis  |  {failed} échoués")
    print("=" * 55)
    return failed == 0


if __name__ == "__main__":
    success = run_tests_simple()
    sys.exit(0 if success else 1)
