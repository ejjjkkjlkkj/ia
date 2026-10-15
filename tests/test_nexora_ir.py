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

    def test_decode_rejects_surrogate_in_string_literal(self):
        doc = json.loads(encode_ast(parse('print("ok");')))
        doc["ast"]["children"][0]["children"][0]["value"] = "\ud800"
        with self.assertRaisesRegex(NEXORAIRError, "Unicode scalar"):
            decode_ir(json.dumps(doc))

    def test_decode_rejects_integer_literal_over_4096_bits(self):
        doc = json.loads(encode_ast(parse("print(1);")))
        doc["ast"]["children"][0]["children"][0]["value"] = 1 << 4096
        with self.assertRaisesRegex(NEXORAIRError, "4096-bit"):
            decode_ir(json.dumps(doc))

    def test_decode_wraps_json_integer_digit_limit_error(self):
        raw = '{"format":"nexora-ir","version":1,"ast":{"kind":"number","value":' + ("9" * 5000) + ',"children":[]}}'
        with self.assertRaisesRegex(NEXORAIRError, "invalid IR JSON"):
            decode_ir(raw)

    def test_decode_rejects_invalid_identifier_reference(self):
        doc = json.loads(encode_ast(parse("print(valid_name);")))
        doc["ast"]["children"][0]["children"][0]["value"] = "not valid"
        with self.assertRaisesRegex(NEXORAIRError, "identifier"):
            decode_ir(json.dumps(doc))

    def test_decode_rejects_invalid_binding_name(self):
        doc = json.loads(encode_ast(parse("let x = 1;")))
        doc["ast"]["children"][0]["value"] = "not valid"
        with self.assertRaisesRegex(NEXORAIRError, "identifier"):
            execute_ir(json.dumps(doc))


    def test_execute_ir_normalizes_large_integer_division_overflow(self):
        doc = json.loads(encode_ast(parse("print(1 / 1);")))
        doc["ast"]["children"][0]["children"][0]["children"][0]["value"] = 1 << 4095
        with self.assertRaisesRegex(ValueError, "numeric operation overflowed"):
            execute_ir(json.dumps(doc))

    def test_execute_ir_rejects_division_by_zero(self):
        with self.assertRaisesRegex(ValueError, "division by zero"):
            execute_ir(encode_ast(parse("print(4 / 0);")))

if __name__ == "__main__":
    unittest.main()
