import unittest

from ia_reference.causal_attention import causal_scaled_dot_product_attention


class CausalAttentionTests(unittest.TestCase):
    def test_single_position_returns_its_value(self):
        result = causal_scaled_dot_product_attention([[1.0, 0.0]], [[1.0, 0.0]], [[3.5, -2.0]])
        self.assertEqual(result, [[3.5, -2.0]])

    def test_future_values_cannot_change_past_outputs(self):
        query = [[1.0], [1.0], [1.0]]
        key = [[1.0], [1.0], [1.0]]
        first = causal_scaled_dot_product_attention(query, key, [[1.0], [2.0], [3.0]])
        changed_future = causal_scaled_dot_product_attention(query, key, [[1.0], [2.0], [-500.0]])
        self.assertEqual(first[0], changed_future[0])
        self.assertEqual(first[1], changed_future[1])
        self.assertNotEqual(first[2], changed_future[2])

    def test_outputs_are_deterministic_and_preserve_value_dimension(self):
        args = ([[1.0, 0.0], [0.0, 1.0]], [[1.0, 0.0], [0.0, 1.0]], [[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]])
        first = causal_scaled_dot_product_attention(*args)
        self.assertEqual(first, causal_scaled_dot_product_attention(*args))
        self.assertEqual(len(first), 2)
        self.assertTrue(all(len(row) == 3 for row in first))

    def test_rejects_mismatched_shapes(self):
        with self.assertRaisesRegex(ValueError, "sequence lengths"):
            causal_scaled_dot_product_attention([[1.0]], [[1.0], [2.0]], [[1.0]])
        with self.assertRaisesRegex(ValueError, "dimensions"):
            causal_scaled_dot_product_attention([[1.0, 2.0]], [[1.0]], [[1.0]])

    def test_rejects_nonfinite_and_ragged_inputs(self):
        with self.assertRaisesRegex(ValueError, "finite"):
            causal_scaled_dot_product_attention([[float("nan")]], [[1.0]], [[1.0]])
        with self.assertRaisesRegex(ValueError, "rectangular"):
            causal_scaled_dot_product_attention([[1.0], [1.0, 2.0]], [[1.0], [1.0]], [[1.0], [2.0]])


if __name__ == "__main__":
    unittest.main()
