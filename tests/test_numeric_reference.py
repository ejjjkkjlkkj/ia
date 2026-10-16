import json
import math
import unittest
from pathlib import Path

from ia_reference.numeric import cross_entropy, matmul, matvec, softmax
from ia_reference.causal_attention import causal_scaled_dot_product_attention


class NumericReferenceTests(unittest.TestCase):
    def test_versioned_shared_reference_vectors(self):
        vector_file = Path(__file__).resolve().parents[1] / "data" / "reference-vectors-v1.json"
        document = json.loads(vector_file.read_text(encoding="utf-8"))
        self.assertEqual(document["schema_version"], 1)
        self.assertEqual(document["contract"], "ia-numeric-reference-v1")
        tolerance = document["absolute_tolerance"]
        self.assertGreaterEqual(len(document["vectors"]), 5)

        def assert_nested_close(actual, expected):
            if isinstance(expected, list):
                self.assertIsInstance(actual, list)
                self.assertEqual(len(actual), len(expected))
                for actual_item, expected_item in zip(actual, expected):
                    assert_nested_close(actual_item, expected_item)
            else:
                self.assertAlmostEqual(actual, expected, delta=tolerance)

        for vector in document["vectors"]:
            with self.subTest(vector=vector["id"]):
                inputs = vector["input"]
                operation = vector["operation"]
                if operation == "matvec":
                    actual = matvec(inputs["matrix"], inputs["vector"])
                elif operation == "matmul":
                    actual = matmul(inputs["left"], inputs["right"])
                elif operation == "softmax":
                    actual = softmax(inputs["logits"])
                elif operation == "cross_entropy":
                    actual = cross_entropy(inputs["logits"], inputs["target_index"])
                elif operation == "causal_attention":
                    actual = causal_scaled_dot_product_attention(
                        inputs["query"], inputs["key"], inputs["value"]
                    )
                else:
                    self.fail(f"Unknown reference-vector operation: {operation}")
                assert_nested_close(actual, vector["expected"])

    def test_matvec_reference_result(self):
        self.assertEqual(matvec([[1, 2], [3, 4]], [5, 6]), [17.0, 39.0])

    def test_matmul_reference_result(self):
        self.assertEqual(
            matmul([[1, 2, 3], [4, 5, 6]], [[7, 8], [9, 10], [11, 12]]),
            [[58.0, 64.0], [139.0, 154.0]],
        )

    def test_softmax_is_stable_and_normalized(self):
        result = softmax([1000.0, 1001.0, 999.0])
        self.assertTrue(all(math.isfinite(item) for item in result))
        self.assertAlmostEqual(sum(result), 1.0, places=12)
        self.assertGreater(result[1], result[0])

    def test_cross_entropy_matches_known_value(self):
        self.assertAlmostEqual(cross_entropy([0.0, 0.0], 0), math.log(2.0))
        self.assertGreater(cross_entropy([0.0, 2.0], 0), cross_entropy([0.0, 2.0], 1))

    def test_rejects_shape_errors(self):
        with self.assertRaisesRegex(ValueError, "columns must match vector"):
            matvec([[1, 2]], [1])
        with self.assertRaisesRegex(ValueError, "columns must match right matrix rows"):
            matmul([[1, 2]], [[1, 2]])

    def test_rejects_invalid_numeric_inputs(self):
        for bad in (True, float("nan"), float("inf"), 1_000_001):
            with self.subTest(value=bad):
                with self.assertRaises(ValueError):
                    softmax([bad, 0.0])
        with self.assertRaisesRegex(ValueError, "rectangular"):
            matmul([[1.0], [2.0, 3.0]], [[1.0], [2.0]])
        with self.assertRaisesRegex(ValueError, "target_index"):
            cross_entropy([1.0, 2.0], True)
        with self.assertRaisesRegex(ValueError, "outside"):
            cross_entropy([1.0, 2.0], 2)

    def test_rejects_integer_outside_float_range_as_value_error(self):
        with self.assertRaisesRegex(ValueError, "finite numbers"):
            softmax([10 ** 10000, 0])

    def test_bounded_large_inputs_remain_finite(self):
        result = matvec([[1_000_000.0, 1_000_000.0]], [1_000_000.0, 1_000_000.0])
        self.assertEqual(result, [2_000_000_000_000.0])
        self.assertTrue(all(math.isfinite(item) for item in result))


if __name__ == "__main__":
    unittest.main()
