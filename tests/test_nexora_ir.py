import json
import unittest

from nexora_language import parse
from nexora_ir import NEXORAIRError, decode_ir, encode_ast, execute_ir

class NEXORAIRTests(unittest.TestCase):
    def test_versioned_round_trip_is_deterministic(self):
        ast = parse('let café = "Bonjour 世界"; print(2 + 3 * 4);')
        first = encode_ast(ast)
        self.assertEqual(first, encode_ast(ast))
        self.assertEqual(decode_ir(first)["kind"], "program")
        self.assertEqual(json.loads(first)["version"], 1)

    def test_rejects_unknown_version(self):
        doc = json.loads(encode_ast(parse("print(1);")))
        doc["version"] = 99
        with self.assertRaisesRegex(NEXORAIRError, "unsupported"):
            decode_ir(json.dumps(doc))

    def test_rejects_extra_fields(self):
        with self.assertRaises(NEXORAIRError):
            decode_ir(json.dumps({"format":"nexora-ir","version":1,"ast":{"kind":"number","value":1,"children":[],"exec":"bad"}}))

    def test_rejects_invalid_operator(self):
        doc = json.loads(encode_ast(parse("print(1 + 2);")))
        doc["ast"]["children"][0]["children"][0]["value"] = "__import__"
        with self.assertRaisesRegex(NEXORAIRError, "operator"):
            decode_ir(json.dumps(doc))

    def test_rejects_wrong_arity(self):
        doc = json.loads(encode_ast(parse("print(1);")))
        doc["ast"]["children"][0]["children"] = []
        with self.assertRaisesRegex(NEXORAIRError, "requires"):
            decode_ir(json.dumps(doc))

    def test_execute_ir_matches_reference_program(self):
        source = 'let total = 2 + 3 * 4; print(total); print("bonjour " + "monde");'
        self.assertEqual(execute_ir(encode_ast(parse(source))), [14, "bonjour monde"])

    def test_execute_ir_preserves_float_arithmetic_semantics(self):
        self.assertEqual(execute_ir(encode_ast(parse("print((5 / 2) + 1);"))), [3.5])

    def test_execute_ir_rejects_undefined_identifier(self):
        with self.assertRaisesRegex(ValueError, "undefined variable"):
            execute_ir(encode_ast(parse("print(absent);")))

    def test_execute_ir_rejects_boolean_arithmetic(self):
        with self.assertRaisesRegex(ValueError, "numeric operands"):
            execute_ir(encode_ast(parse("print(true + 1);")))

    def test_decode_rejects_invalid_binding_name(self):
        doc = json.loads(encode_ast(parse("let x = 1;")))
        doc["ast"]["children"][0]["value"] = "not valid"
        with self.assertRaisesRegex(NEXORAIRError, "identifier"):
            execute_ir(json.dumps(doc))

    def test_execute_ir_rejects_division_by_zero(self):
        with self.assertRaisesRegex(ValueError, "division by zero"):
            execute_ir(encode_ast(parse("print(4 / 0);")))

    def test_decode_rejects_duplicate_json_keys(self):
        duplicate = (
            '{"format":"nexora-ir","format":"other","version":1,'
            '"ast":{"kind":"program","value":null,"children":[]}}'
        )
        with self.assertRaisesRegex(NEXORAIRError, "duplicate JSON"):
            decode_ir(duplicate)

    def test_decode_rejects_nonstandard_numeric_constants(self):
        data = (
            '{"format":"nexora-ir","version":1,"ast":'
            '{"kind":"number","value":NaN,"children":[]}}'
        )
        with self.assertRaisesRegex(NEXORAIRError, "non-standard JSON"):
            decode_ir(data)

    def test_decode_normalizes_excessive_json_nesting(self):
        data = (
            '{"format":"nexora-ir","version":1,"ast":'
            + "[" * 2_000 + "null" + "]" * 2_000 + "}"
        )
        with self.assertRaisesRegex(NEXORAIRError, "invalid IR JSON"):
            decode_ir(data)

    def test_decode_rejects_invalid_unicode_scalar(self):
        with self.assertRaisesRegex(NEXORAIRError, "invalid Unicode"):
            decode_ir(chr(0xD800))

    def test_ir_conformance_corpus_matches_reference_interpreter(self):
        programs = [
            "print(1 + 2 * 3);",
            "let x = 9; print(-x + 4);",
            'let café = "bonjour " + "monde"; print(café);',
            "let ok = true; print(ok);",
            "print((5 / 2) + 1);",
            "let a = 7; let b = 6; print(a * b - 2);",
        ]
        from nexora_language import run
        for source in programs:
            with self.subTest(source=source):
                expected = run(source)
                actual = execute_ir(encode_ast(parse(source)))
                self.assertEqual(actual, expected)

    def test_decode_rejects_integer_literal_over_4096_bits(self):
        value = "9" * 1234
        data = (
            '{"format":"nexora-ir","version":1,"ast":'
            '{"kind":"number","value":' + value + ',"children":[]}}'
        )
        with self.assertRaisesRegex(NEXORAIRError, "4096-bit limit"):
            decode_ir(data)

    def test_execute_ir_normalizes_large_integer_float_conversion(self):
        value = "9" * 1233
        data = (
            '{"format":"nexora-ir","version":1,"ast":'
            '{"kind":"program","value":null,"children":['
            '{"kind":"print","value":null,"children":['
            '{"kind":"binary","value":"/","children":['
            '{"kind":"number","value":' + value + ',"children":[]},'
            '{"kind":"number","value":1,"children":[]} ]}]}]}'
        )
        with self.assertRaisesRegex(ValueError, "numeric operation exceeds supported range"):
            execute_ir(data)

if __name__ == "__main__":
    unittest.main()
