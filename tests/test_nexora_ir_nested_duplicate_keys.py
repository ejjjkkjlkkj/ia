import unittest

from nexora_ir import NEXORAIRError, decode_ir


class NEXORADuplicateNestedJSONKeyTests(unittest.TestCase):
    def test_rejects_duplicate_keys_inside_ast_nodes(self):
        payload = (
            '{"format":"nexora-ir","version":1,"ast":'
            '{"kind":"program","value":null,"children":['
            '{"kind":"number","kind":"string","value":1,"children":[]}'
            ']}}'
        )
        with self.assertRaisesRegex(NEXORAIRError, "duplicate JSON object key"):
            decode_ir(payload)


if __name__ == "__main__":
    unittest.main()
