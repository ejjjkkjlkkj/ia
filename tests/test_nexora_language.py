import unittest
from nexora_language import NEXORASyntaxError, NEXORARuntimeError, run, tokenize

class NEXORALanguageTests(unittest.TestCase):
    def test_arithmetic_precedence_and_variables(self):
        self.assertEqual(run("let x = 2 + 3 * 4; print(x); print((x - 2) / 3);"), [14, 4.0])

    def test_unicode_identifier_and_text(self):
        self.assertEqual(run('let café = "Bonjour 世界"; print(café);'), ["Bonjour 世界"])

    def test_comments_and_boolean_literals(self):
        self.assertEqual(run('# comment\nlet ok = true; // inline\nprint(ok);'), [True])

    def test_undefined_variable_fails(self):
        with self.assertRaisesRegex(NEXORARuntimeError, "undefined variable"):
            run("print(absent);")

    def test_duplicate_binding_fails(self):
        with self.assertRaisesRegex(NEXORARuntimeError, "already defined"):
            run("let x = 1; let x = 2;")

    def test_division_by_zero_fails(self):
        with self.assertRaisesRegex(NEXORARuntimeError, "division by zero"):
            run("print(4 / 0);")

    def test_boolean_is_not_an_integer(self):
        with self.assertRaisesRegex(NEXORARuntimeError, "numeric operands"):
            run("print(true + 1);")

    def test_float_results_can_be_used_in_arithmetic(self):
        self.assertEqual(run("print((5 / 2) + 1);"), [3.5])

    def test_oversized_source_is_rejected(self):
        with self.assertRaisesRegex(NEXORASyntaxError, "source byte limit"):
            tokenize(" " * 1_000_001)

    def test_oversized_integer_literal_is_rejected(self):
        with self.assertRaisesRegex(NEXORASyntaxError, "4096-bit limit"):
            run("print(" + "9" * 1235 + ");")

    def test_unknown_character_fails(self):
        with self.assertRaises(NEXORASyntaxError):
            tokenize("print(1); @")

if __name__ == "__main__":
    unittest.main()
