import json
import unittest

from nexora_language import parse
from nexora_ir import NEXORAIRError, decode_ir, encode_ast

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

if __name__ == "__main__":
    unittest.main()
