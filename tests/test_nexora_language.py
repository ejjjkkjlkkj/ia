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

    def test_reserved_words_cannot_be_binding_names(self):
        with self.assertRaisesRegex(NEXORASyntaxError, "non-reserved identifier"):
            run("let print = 1;")

    def test_oversized_source_is_rejected(self):
        with self.assertRaisesRegex(NEXORASyntaxError, "source byte limit"):
            tokenize(" " * 1_000_001)

    def test_oversized_integer_literal_is_rejected(self):
        with self.assertRaisesRegex(NEXORASyntaxError, "4096-bit limit"):
            run("print(" + "9" * 1235 + ");")

    def test_integer_literal_within_digit_count_but_over_bit_limit_is_rejected(self):
        with self.assertRaisesRegex(NEXORASyntaxError, "4096-bit limit"):
            run("print(" + "9" * 1234 + ");")

    def test_numeric_overflow_is_reported_as_language_error(self):
        literal = "9" * 1200
        with self.assertRaisesRegex(NEXORARuntimeError, "numeric operation exceeds supported range"):
            run(f"print(({literal}) / 1);")

    def test_deep_expression_fails_with_language_error(self):
        source = "print(" + "+".join(["1"] * 1500) + ");"
        with self.assertRaisesRegex(NEXORARuntimeError, "maximum evaluation depth exceeded"):
            run(source)

    def test_invalid_json_string_escape_fails(self):
        with self.assertRaises(NEXORASyntaxError):
            run(r'print("\\q");')

    def test_unterminated_string_fails(self):
        with self.assertRaises(NEXORASyntaxError):
            tokenize('print("unterminated);')

    def test_excessive_parenthesis_nesting_is_a_syntax_error(self):
        source = "print(" + "(" * 2000 + "1" + ")" * 2000 + ");"
        with self.assertRaisesRegex(NEXORASyntaxError, "nesting depth"):
            run(source)

    def test_unknown_character_fails(self):
        with self.assertRaises(NEXORASyntaxError):
            tokenize("print(1); @")

    def test_token_count_is_bounded(self):
        source = "1;" * 50_001
        with self.assertRaisesRegex(NEXORASyntaxError, "token limit exceeded"):
            tokenize(source)

    def test_invalid_unicode_scalar_is_rejected(self):
        with self.assertRaisesRegex(NEXORASyntaxError, "invalid Unicode"):
            tokenize(chr(0xD800))


if __name__ == "__main__":
    unittest.main()
