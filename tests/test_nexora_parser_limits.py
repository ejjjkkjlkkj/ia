import unittest
from nexora_language import NEXORASyntaxError, run

class ParserLimitTests(unittest.TestCase):
    def test_deeply_nested_parentheses_raise_language_error(self):
        source = "print(" + "(" * 2000 + "1" + ")" * 2000 + ");"
        with self.assertRaisesRegex(NEXORASyntaxError, "maximum parser nesting depth exceeded"):
            run(source)

    def test_deeply_nested_unary_operators_raise_language_error(self):
        source = "print(" + "-" * 2000 + "1);"
        with self.assertRaisesRegex(NEXORASyntaxError, "maximum parser nesting depth exceeded"):
            run(source)

if __name__ == "__main__":
    unittest.main()
