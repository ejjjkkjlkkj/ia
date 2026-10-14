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

    def test_unknown_character_fails(self):
        with self.assertRaises(NEXORASyntaxError):
            tokenize("print(1); @")

if __name__ == "__main__":
    unittest.main()
